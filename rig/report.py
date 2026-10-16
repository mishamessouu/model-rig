"""Summarise a batch folder as Markdown: one row per cell and prompt."""
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def _mean(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def _fmt(value, digits=0):
    if value is None:
        return "n/a"
    return f"{value:,.{digits}f}"


def _pick(result):
    """The planted defects a run fixed, or what else it did."""
    if result["fixed"]:
        return "+".join(result["fixed"])
    return "other change" if result["diff"]["files"] else "no change"


def load(batch_dir):
    return [json.loads(p.read_text())
            for p in sorted(Path(batch_dir).glob("runs/*/result.json"))]


def summarise(results, sheet="copilot"):
    groups = defaultdict(list)
    for result in results:
        groups[(result["cell"], result["prompt"])].append(result)
    rows = []
    for (cell, prompt), runs in sorted(groups.items()):
        picks = Counter(_pick(r) for r in runs)
        good = [r for r in runs if r["fixed"] and r["regression_pass"] and not r["error"]]
        cost = [r["costs"].get(sheet, {}).get("value") for r in runs]
        total_cost = sum(cost) if None not in cost else None
        rows.append({
            "cell": cell, "prompt": prompt, "n": len(runs),
            "picks": ", ".join(f"{k} x{v}" for k, v in picks.most_common()),
            "success": len(good),
            "regressions": sum(1 for r in runs if not r["regression_pass"]),
            "errors": sum(1 for r in runs if r["error"] or r["timed_out"]),
            **{f"mean_{k}": _mean([r["tokens"][k] for r in runs])
               for k in ("input", "output", "cache_read", "cache_write")},
            "mean_cost": _mean(cost),
            "cost_per_success": total_cost / len(good) if good and total_cost is not None else None,
            "mean_usd_reported": _mean([r["usd_reported"] for r in runs]),
            "mean_seconds": _mean([r["seconds"] for r in runs]),
            "mean_lines": _mean([r["diff"]["added"] + r["diff"]["removed"] for r in runs]),
        })
    return rows


def markdown(batch_dir, sheet="copilot"):
    results = load(batch_dir)
    rows = summarise(results, sheet)
    unit = next((r["costs"][sheet]["unit"] for r in results if sheet in r["costs"]), sheet)
    lines = [
        f"# Batch {Path(batch_dir).name}", "",
        f"{len(results)} runs. Success means at least one planted defect fixed, "
        "no regression, and no agent error. Cost uses the "
        f"`{sheet}` price sheet, in {unit}.", "",
        "| Cell | Prompt | n | Picks | Success | Regressions | Errors | "
        f"Mean {unit} | {unit} per success | Mean reported USD | Mean s | Mean lines changed |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['cell']} | {r['prompt']} | {r['n']} | {r['picks']} | "
            f"{r['success']}/{r['n']} | {r['regressions']} | {r['errors']} | "
            f"{_fmt(r['mean_cost'], 3)} | {_fmt(r['cost_per_success'], 3)} | "
            f"{_fmt(r['mean_usd_reported'], 3)} | {_fmt(r['mean_seconds'])} | "
            f"{_fmt(r['mean_lines'])} |")
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
