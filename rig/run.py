"""Run a batch: every repeat of every cell on every prompt, one at a time."""
import datetime
import gzip
import json
import os
import shutil
import signal
import subprocess
import time
import tomllib
from pathlib import Path

from . import ROOT, STATE, prices, sandbox, score
from . import scenario as scenarios
from .harness import HARNESSES


def load_matrix(path=None):
    return tomllib.loads(Path(path or ROOT / "config" / "matrix.toml").read_text())


def plan(matrix, cell_names, prompt_names, repeats):
    cells = {cell["name"]: cell for cell in matrix["cells"]}
    unknown = [name for name in cell_names if name not in cells]
    if unknown:
        raise SystemExit(f"unknown cells: {', '.join(unknown)}")
    # Repeats on the outside, so a slow afternoon hits every cell alike.
    return [(rep, cells[name], prompt)
            for rep in range(1, repeats + 1)
            for name in cell_names for prompt in prompt_names]


def _text(value):
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, check=True).stdout


def _kill_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _stop_on_term(*_):
    raise SystemExit("stopped by SIGTERM")


def _restore_sign_in(snapshots):
    """Copy a refreshed sign-in back, unless the master changed meanwhile."""
    for master, local, before in snapshots:
        if not local.exists():
            continue
        after = local.read_bytes()
        if after != before and master.read_bytes() == before:
            temporary = master.with_name(master.name + ".rig-new")
            temporary.write_bytes(after)
            os.chmod(temporary, 0o600)
            os.replace(temporary, master)


def _choice(final):
    lines = [line.strip() for line in final.splitlines() if line.strip().startswith("CHOICE:")]
    return lines[-1][len("CHOICE:"):].strip() if lines else None


def run_one(scenario, cell, prompt_name, rep, batch, matrix, out_root, keep=False):
    run_id = f"{cell['name']}.{prompt_name}.r{rep}"
    run_dir = STATE / "work" / batch / run_id
    # A stopped run can leave its work folder behind; a resume starts it clean.
    shutil.rmtree(run_dir, ignore_errors=True)
    (run_dir / "home").mkdir(parents=True)
    repo = scenarios.copy_repo(scenario, run_dir / "repo")
    base = _git(repo, "rev-parse", "HEAD").strip()
    start, parse = HARNESSES[cell["harness"]]
    extra = {"scenario": scenario} if cell["harness"] == "fake" else {}
    invocation = start(cell, scenario.prompts[prompt_name], run_dir,
                       matrix["budget_usd"], **extra)
    snapshots = []
    for master, local in invocation.auth:
        if not master.exists():
            raise SystemExit(f"No sign-in at {master}. Run scripts/login.sh first.")
        shutil.copy2(master, local)
        snapshots.append((master, local, master.read_bytes()))
    # The scenario's prepared environment is bound read-only and comes
    # first on PATH, so the agent runs the tests the way the scorer does.
    command = sandbox.command(invocation.argv, cwd=repo,
                              read=[*invocation.read, *scenario.sandbox_read()],
                              write=[run_dir],
                              env={**scenario.sandbox_env(), **invocation.env},
                              network=invocation.network)
    started = time.time()
    timed_out, code = False, None
    # Own process group, so a stop or a timeout ends the whole sandbox:
    # bwrap's --die-with-parent covers its child, not bwrap itself.
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    try:
        out, err = process.communicate(timeout=matrix["timeout_seconds"])
        stdout, stderr, code = _text(out), _text(err), process.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_group(process)
        out, err = process.communicate()
        stdout, stderr = _text(out), _text(err)
    except BaseException:
        _kill_group(process)
        _restore_sign_in(snapshots)
        shutil.rmtree(run_dir, ignore_errors=True)
        raise
    seconds = round(time.time() - started, 1)
    _restore_sign_in(snapshots)
    for _, local in invocation.auth:
        local.unlink(missing_ok=True)

    out = out_root / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    with gzip.open(out / "agent-log.jsonl.gz", "wt") as log:
        log.write(stdout)
    (out / "agent-stderr.txt").write_text(stderr[-20000:])

    try:
        options = {"model": cell["model"]} if cell["harness"] == "codex" else {}
        usage = parse(stdout, invocation.final_file, **options)
    except Exception as error:  # a crashed agent still gets a result row
        usage = {"by_model": {}, "usd_reported": None, "turns": None,
                 "error": f"unreadable agent output: {error}", "final": ""}

    if timed_out and not usage.get("error"):
        usage["error"] = f"timed out after {matrix['timeout_seconds']} s"
    # Diff against the baseline commit, not HEAD: an agent that commits its
    # work must not leave an empty patch behind.
    _git(repo, "add", "-A")
    patch = _git(repo, "diff", "--cached", "--binary", "--no-color", base)
    (out / "diff.patch").write_text(patch)
    files = added = removed = 0
    for line in _git(repo, "diff", "--cached", "--numstat", base).splitlines():
        plus, minus, _ = line.split("\t", 2)
        files += 1
        added += int(plus) if plus.isdigit() else 0
        removed += int(minus) if minus.isdigit() else 0

    scored, apply_error = score.score_patch(scenario, patch, run_dir / "scored")
    if apply_error:
        scored = {"fixed": [], "regression_pass": False, "visible_pass": False,
                  "visible_tail": "", "tests": {}}
        usage["error"] = usage.get("error") or f"diff did not apply: {apply_error}"
    tokens = {kind: sum(t.get(kind, 0) for t in usage["by_model"].values())
              for kind in prices.KINDS}
    costs = {}
    for name, sheet in prices.load().items():
        value, missing = prices.cost(sheet, usage["by_model"])
        costs[name] = {"value": value, "unit": sheet["unit"], "missing": missing}
    result = {
        "run_id": run_id, "batch": batch, "scenario": scenario.name,
        "cell": cell["name"], "harness": cell["harness"], "model": cell["model"],
        "effort": cell.get("effort", ""), "prompt": prompt_name, "repeat": rep,
        "seconds": seconds, "exit_code": code, "timed_out": timed_out,
        "error": usage.get("error"), "turns": usage.get("turns"),
        "tokens": tokens, "by_model": usage["by_model"],
        "raw_usage": usage.get("raw_usage"),
        "usd_reported": usage.get("usd_reported"), "costs": costs,
        "choice": _choice(usage.get("final", "")),
        "final": usage.get("final", "")[-4000:],
        "diff": {"files": files, "added": added, "removed": removed},
        **scored,
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if not keep:
        shutil.rmtree(run_dir)
    return result


def _versions():
    found = {}
    for name in ("claude", "codex"):
        try:
            found[name] = subprocess.run([name, "--version"], capture_output=True,
                                         text=True, timeout=30).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            found[name] = None
    return found


def run_batch(scenario_name, matrix, cell_names, prompt_names, repeats,
              results_root=None, keep=False, echo=print, resume=None):
    """Run a batch. With `resume`, add the missing runs to that batch folder."""
    scenario = scenarios.load(scenario_name)
    if scenario.unprepared():
        raise SystemExit(scenario.unprepared())
    unknown = [p for p in prompt_names if p not in scenario.prompts]
    if unknown:
        raise SystemExit(f"unknown prompts: {', '.join(unknown)}")
    runs = plan(matrix, cell_names, prompt_names, repeats)
    # "-dirty" marks uncommitted rig changes, which a bare HEAD would hide.
    commit = subprocess.run(["git", "-C", str(ROOT), "describe", "--always", "--dirty"],
                            capture_output=True, text=True).stdout.strip()
    if resume:
        out_root = Path(resume)
        info = json.loads((out_root / "batch.json").read_text())
        if info["scenario"] != scenario.name:
            raise SystemExit(f"{out_root} is a batch of {info['scenario']}")
        batch = info["batch"]
        runs = [(rep, cell, prompt) for rep, cell, prompt in runs
                if not (out_root / "runs" / f"{cell['name']}.{prompt}.r{rep}"
                        / "result.json").exists()]
        info.setdefault("resumed", []).append({
            "at": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
            "cells": cell_names, "prompts": prompt_names, "repeats": repeats,
            "runs": len(runs), "rig_commit": commit or None, "versions": _versions(),
        })
        (out_root / "batch.json").write_text(json.dumps(info, indent=2) + "\n")
    else:
        stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        batch = f"{stamp}-{scenario.name}"
        out_root = Path(results_root or ROOT / "results") / batch
        out_root.mkdir(parents=True)
        (out_root / "batch.json").write_text(json.dumps({
            "batch": batch, "scenario": scenario.name, "cells": cell_names,
            "prompts": prompt_names, "repeats": repeats, "rig_commit": commit or None,
            "versions": _versions(), "matrix": matrix,
        }, indent=2) + "\n")
    signal.signal(signal.SIGTERM, _stop_on_term)
    results = []
    for number, (rep, cell, prompt) in enumerate(runs, 1):
        echo(f"[{number}/{len(runs)}] {cell['name']} {prompt} r{rep}")
        result = run_one(scenario, cell, prompt, rep, batch, matrix, out_root, keep)
        echo(f"    fixed={result['fixed'] or 'none'} regression_pass="
             f"{result['regression_pass']} seconds={result['seconds']} error={result['error']}")
        results.append(result)
    return out_root, results
