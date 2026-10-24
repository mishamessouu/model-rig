"""Run a batch: every repeat of every cell on every prompt, one at a time."""
import contextlib
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

from . import ROOT, STATE, prices, proxy, sandbox, score
from . import scenario as scenarios
from .harness import HARNESSES


def load_matrix(path=None):
    """Load the cells. A cell without `hosts` gets its harness's list from
    config/network.toml, so batch.json records what each cell could reach."""
    matrix = tomllib.loads(Path(path or ROOT / "config" / "matrix.toml").read_text())
    network = tomllib.loads((ROOT / "config" / "network.toml").read_text())
    for cell in matrix["cells"]:
        cell.setdefault("hosts", list(network["hosts"].get(cell["harness"], [])))
    return matrix


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


def fix_after_cutoff(fix_date, cutoff):
    """True when the fix is later than the model's training cutoff, so the
    model cannot have learned it. False when the fix falls in or before the
    cutoff month. None when either date is unknown. Both compare by month,
    because cutoffs are stated by month."""
    if not fix_date or not cutoff:
        return None
    return str(fix_date)[:7] > str(cutoff)[:7]


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
    out = out_root / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    # The network log goes to the results folder, which the sandbox
    # hides, so the agent cannot edit it. A run with no hosts leaves it empty.
    network_log = out / "network.jsonl"
    network_log.write_text("")
    with contextlib.ExitStack() as stack:
        socket_path = None
        if invocation.hosts:
            # Stops on any way out of this block: a timeout, a stop, an error.
            socket_path = stack.enter_context(
                proxy.serve(invocation.hosts, network_log)).socket
        # The scenario's prepared environment is bound read-only and comes
        # first on PATH, so the agent runs the tests the way the scorer does.
        # A Node environment's node_modules is bound over the working copy.
        command = sandbox.command(invocation.argv, cwd=repo,
                                  read=[*invocation.read, *scenario.sandbox_read()],
                                  write=[run_dir],
                                  mounts=scenario.sandbox_mounts(repo),
                                  env={**scenario.sandbox_env(), **invocation.env},
                                  proxy=socket_path)
        started = time.time()
        timed_out, code = False, None
        # Own process group, so a stop or a timeout ends the whole sandbox:
        # bwrap's --die-with-parent covers its child, not bwrap itself.
        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            agent_out, agent_err = process.communicate(timeout=matrix["timeout_seconds"])
            stdout, stderr, code = _text(agent_out), _text(agent_err), process.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_group(process)
            agent_out, agent_err = process.communicate()
            stdout, stderr = _text(agent_out), _text(agent_err)
        except BaseException:
            _kill_group(process)
            _restore_sign_in(snapshots)
            shutil.rmtree(run_dir, ignore_errors=True)
            raise
    seconds = round(time.time() - started, 1)
    _restore_sign_in(snapshots)
    for _, local in invocation.auth:
        local.unlink(missing_ok=True)

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
    # Each changed path, a rename as two, so the report can tell a change
    # to test files only from a change to app code (decision 12).
    paths = [p for p in _git(repo, "diff", "--cached", "--name-only", "--no-renames",
                             "-z", base).split("\0") if p]

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
        "diff": {"files": files, "added": added, "removed": removed, "paths": paths},
        "network": proxy.summary(network_log),
        "fix_after_cutoff": fix_after_cutoff(scenario.fix_date, cell.get("cutoff")),
        # A control run is never a success or a miss (decision 12).
        "control": scenario.control,
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


def new_batch_dir(results_root, scenario_name, now=None, wait=time.sleep):
    """Make and return a new batch folder named by the UTC second.

    Two queues that start in the same second would get the same name.
    The second one waits a second and takes the next name."""
    now = now or (lambda: datetime.datetime.now(datetime.UTC))
    results_root.mkdir(parents=True, exist_ok=True)
    while True:
        out_root = results_root / f"{now().strftime('%Y%m%dT%H%M%SZ')}-{scenario_name}"
        try:
            out_root.mkdir()
            return out_root
        except FileExistsError:
            wait(1)


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
        out_root = new_batch_dir(Path(results_root or ROOT / "results"), scenario.name)
        batch = out_root.name
        (out_root / "batch.json").write_text(json.dumps({
            "batch": batch, "scenario": scenario.name, "cells": cell_names,
            "prompts": prompt_names, "repeats": repeats, "rig_commit": commit or None,
            "versions": _versions(), "matrix": matrix,
        }, indent=2) + "\n")
    for name in dict.fromkeys(cell["name"] for _, cell, _ in runs):
        cell = next(c for c in matrix["cells"] if c["name"] == name)
        if fix_after_cutoff(scenario.fix_date, cell.get("cutoff")) is False:
            echo(f"WARNING: {name} has training cutoff {cell['cutoff']}, on or after "
                 f"the {scenario.name} fix of {scenario.fix_date}. It may know the fix.")
    signal.signal(signal.SIGTERM, _stop_on_term)
    results = []
    for number, (rep, cell, prompt) in enumerate(runs, 1):
        echo(f"[{number}/{len(runs)}] {cell['name']} {prompt} r{rep}")
        result = run_one(scenario, cell, prompt, rep, batch, matrix, out_root, keep)
        echo(f"    fixed={result['fixed'] or 'none'} regression_pass="
             f"{result['regression_pass']} seconds={result['seconds']} error={result['error']}")
        results.append(result)
    return out_root, results
