"""Summarise a batch folder as Markdown: one row per cell and prompt."""
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from . import prices


def _mean(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def _fmt(value, digits=0):
    if value is None:
        return "n/a"
    return f"{value:,.{digits}f}"


def wilson(successes, n, z=1.96):
    """95% Wilson interval for a success rate. With n=3 it is wide on purpose."""
    if not n:
        return None
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def success(result):
    """A planted defect fixed, no regression, and a run that ended cleanly.
    A control run has no defect, so it is never a success (decision 12)."""
    return bool(not result.get("control") and result["fixed"] and result["regression_pass"]
                and not result["error"] and not result.get("timed_out"))


def refused(result):
    """A provider safety filter stopped the run (decision 15). It stays a
    failure, because the person got no fix. A result from before the rig
    recorded refusals is matched on Claude Code's error text."""
    return bool(result.get("refused") or "safeguards flagged" in (result.get("error") or ""))


def over_time(result):
    """A planted defect fixed with no regression, but only after the
    timeout (decision 15). Not a success: every cell has the same limit."""
    return bool(not result.get("control") and result.get("timed_out")
                and result["fixed"] and result["regression_pass"])


# What a control run did, in the order the report shows (decision 12).
# "error" counts first and holds every run the rig could not observe.
# The other four are the behaviour of the runs that remain.
CONTROL_ERROR = "error"
CONTROL_BEHAVIOUR = ("changed nothing", "changed tests only", "changed app code",
                     "regression fails")
CONTROL_OUTCOMES = (CONTROL_ERROR, *CONTROL_BEHAVIOUR)
# A changed file under a folder of one of these names is a test file.
TEST_FOLDERS = {"test", "tests", "__tests__"}


def _test_path(path):
    return any(part in TEST_FOLDERS for part in Path(path).parts[:-1])


def control_outcome(result):
    """One of CONTROL_OUTCOMES. An agent error, a timeout, a diff that did
    not apply (run.py records it as the run's error), or a score with no
    test results is an "error" and nothing else. Then a failed regression
    set, whatever the diff. Then the diff: nothing, test files only, or
    app code. A result from before the rig recorded changed paths counts
    any change as app code."""
    if result["error"] or result.get("timed_out") or not result.get("tests"):
        return CONTROL_ERROR
    if not result["regression_pass"]:
        return "regression fails"
    if not result["diff"]["files"]:
        return "changed nothing"
    paths = result["diff"].get("paths")
    if paths and all(_test_path(path) for path in paths):
        return "changed tests only"
    return "changed app code"


def run_cost(result, sheet):
    """Price the stored tokens with today's sheet, so a new price reaches old runs."""
    return prices.cost(sheet, result.get("by_model") or {})[0]


def _pick(result):
    """The planted defects a run fixed, or what else it did."""
    if result["fixed"]:
        return "+".join(result["fixed"])
    return "other change" if result["diff"]["files"] else "no change"


# result.json "fix_after_cutoff": true, false, or null (unknown).
CUTOFF_WORDS = {True: "yes", False: "no", None: "unknown"}


def _cutoff(runs):
    """Yes, no, or unknown. A resumed batch with mixed values lists each."""
    words = dict.fromkeys(CUTOFF_WORDS[r.get("fix_after_cutoff")] for r in runs)
    return "/".join(words)


def _interval(pair):
    return "n/a" if pair is None else f"{pair[0]:.0%} to {pair[1]:.0%}"


def load(batch_dir):
    return [json.loads(p.read_text())
            for p in sorted(Path(batch_dir).glob("runs/*/result.json"))]


def summarise(results, sheet="copilot", sheets=None):
    sheet_data = (sheets or prices.load()).get(sheet)
    groups = defaultdict(list)
    for result in results:
        groups[(result["cell"], result["prompt"])].append(result)
    rows = []
    for (cell, prompt), runs in sorted(groups.items()):
        picks = Counter(_pick(r) for r in runs)
        good = [r for r in runs if success(r)]
        control = any(r.get("control") for r in runs)
        outcomes = Counter(control_outcome(r) for r in runs) if control else Counter()
        cost = [run_cost(r, sheet_data) if sheet_data else None for r in runs]
        # One unpriced run makes the cell's cost unknown, not a partial mean.
        total_cost = sum(cost) if None not in cost else None
        low_high = wilson(len(good), len(runs))
        rows.append({
            "cell": cell, "prompt": prompt, "n": len(runs),
            "picks": ", ".join(f"{k} x{v}" for k, v in picks.most_common()),
            # A control cell has no success rate, only outcome counts.
            "control": control,
            "outcomes": {name: outcomes[name] for name in CONTROL_OUTCOMES} if control else None,
            # Errors are not observations of behaviour, so each rate is
            # over the runs that remain.
            "outcome_intervals": {
                name: wilson(outcomes[name], len(runs) - outcomes[CONTROL_ERROR])
                for name in CONTROL_BEHAVIOUR} if control else None,
            "success": None if control else len(good),
            "interval": None if control else low_high,
            "all_succeeded": None if control else len(good) == len(runs),
            "regressions": sum(1 for r in runs if not r["regression_pass"]),
            "errors": sum(1 for r in runs if r["error"] or r["timed_out"]),
            "refused": sum(1 for r in runs if refused(r)),
            "over_time": sum(1 for r in runs if over_time(r)),
            **{f"mean_{k}": _mean([r["tokens"][k] for r in runs])
               for k in ("input", "output", "cache_read", "cache_write")},
            "mean_cost": total_cost / len(runs) if total_cost is not None else None,
            "cost_per_success": total_cost / len(good) if good and total_cost is not None else None,
            "mean_usd_reported": _mean([r["usd_reported"] for r in runs]),
            "mean_seconds": _mean([r["seconds"] for r in runs]),
            "mean_lines": _mean([r["diff"]["added"] + r["diff"]["removed"] for r in runs]),
            "fix_after_cutoff": _cutoff(runs),
        })
    return rows


def markdown(batch_dir, sheet="copilot"):
    results = load(batch_dir)
    rows = summarise(results, sheet)
    unit = next((r["costs"][sheet]["unit"] for r in results if sheet in r["costs"]), sheet)
    planted = [r for r in rows if not r["control"]]
    controls = [r for r in rows if r["control"]]
    lines = [f"# Batch {Path(batch_dir).name}"]
    if planted:
        lines += [
            "", f"{sum(r['n'] for r in planted)} runs. Success means at least one "
            "planted defect fixed, no regression, and no agent error or timeout. "
            "Cost prices the stored "
            f"tokens with today's `{sheet}` price sheet, in {unit}; a cell with an "
            "unpriced run shows n/a. The interval is a 95% Wilson interval for the "
            "success rate. With three runs it is wide, so rank two cells only "
            "with a test on the runs, such as Fisher's exact test. \"Refused\" counts "
            "errors where a provider safety filter stopped the run. \"Fixed over "
            "time\" counts timeouts whose diff fixed a defect with no regression; "
            "they are not successes (decision 15).", "",
            "| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | "
            "Refused | Fixed over time | "
            f"Mean {unit} | {unit} per success | Mean reported USD | Mean s | "
            "Mean lines changed | Fix after cutoff |",
            "|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    for r in planted:
        lines.append(
            f"| {r['cell']} | {r['prompt']} | {r['n']} | {r['picks']} | "
            f"{r['success']}/{r['n']} | {_interval(r['interval'])} | "
            f"{r['regressions']} | {r['errors']} | {r['refused']} | {r['over_time']} | "
            f"{_fmt(r['mean_cost'], 3)} | {_fmt(r['cost_per_success'], 3)} | "
            f"{_fmt(r['mean_usd_reported'], 3)} | {_fmt(r['mean_seconds'])} | "
            f"{_fmt(r['mean_lines'])} | {r['fix_after_cutoff']} |")
    if controls:
        lines += [
            "", f"{sum(r['n'] for r in controls)} control runs. A control has no "
            "planted defect, so a run is neither a success nor a miss. The columns "
            "count what each run did instead. Only the `security` prompt measures "
            "false positives: a claimed security fix where no hole was planted. For "
            "`open` and `ddd`, a safe change is the correct answer. A run with an "
            "agent error, a timeout, a diff that did not apply, or no score counts "
            "as an error and nothing else. Each other count is over the runs "
            "without an error, with a 95% Wilson interval. With three runs it is "
            "wide, so compare two cells only with a test on the runs, such as "
            "Fisher's exact test. A test file is one under a `test`, `tests`, or "
            "`__tests__` folder. The three \"changed\" counts hold runs whose "
            "regression set passed. Cost prices the stored tokens with today's "
            f"`{sheet}` price sheet, in {unit}; a cell with an unpriced run shows "
            "n/a.", "",
            "| Cell | Prompt | n | Error | Changed nothing | Changed tests only | "
            f"Changed app code | Regression fails | Mean {unit} | Mean reported USD | "
            "Mean s | Mean lines changed |",
            "|---|---|---:|---:|---|---|---|---|---:|---:|---:|---:|",
        ]
    for r in controls:
        valid = r["n"] - r["outcomes"][CONTROL_ERROR]
        counts = " | ".join(
            f"{r['outcomes'][name]}/{valid} ({_interval(r['outcome_intervals'][name])})"
            for name in CONTROL_BEHAVIOUR)
        lines.append(
            f"| {r['cell']} | {r['prompt']} | {r['n']} | {r['outcomes'][CONTROL_ERROR]} | "
            f"{counts} | {_fmt(r['mean_cost'], 3)} | {_fmt(r['mean_usd_reported'], 3)} | "
            f"{_fmt(r['mean_seconds'])} | {_fmt(r['mean_lines'])} |")
    refused = [f"{r['run_id']} ({', '.join(r['network']['denied'])})"
               for r in results if (r.get("network") or {}).get("denied")]
    if refused:
        lines += ["", "The network proxy refused a host in these runs: "
                  + "; ".join(refused) + ". See each run's `network.jsonl`."]
    lines += ["", "## Mean tokens per run", "",
              "| Cell | Prompt | Input | Output | Cache read | Cache write |",
              "|---|---|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(
            f"| {r['cell']} | {r['prompt']} | {_fmt(r['mean_input'])} | "
            f"{_fmt(r['mean_output'])} | {_fmt(r['mean_cache_read'])} | "
            f"{_fmt(r['mean_cache_write'])} |")
    lines += ["", "## Each run", "",
              "| Run | Fixed | Regression pass | Choice |", "|---|---|---|---|"]
    for r in results:
        choice = (r["choice"] or "").replace("|", "/")[:160]
        lines.append(f"| {r['run_id']} | {_pick(r)} | "
                     f"{r['regression_pass']} | {choice} |")
    return "\n".join(lines) + "\n"
