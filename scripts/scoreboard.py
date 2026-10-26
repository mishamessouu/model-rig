#!/usr/bin/env python3
"""Print planted-defect successes across scenarios, then confirmed finds.

    scripts/scoreboard.py [--sheet copilot] [--skip scenario,...]

For each scenario and cell it takes the newest batch that holds the cell,
so a rerun replaces an old one. The booking-ladder smoke tests are left
out.

The first table counts planted successes only, without control
scenarios. A cell shows successes of runs, both prompts together; the
last rows give each cell's total, its 95% Wilson interval, and its mean
credits per success over all its runs. A cell with an unpriced run shows
n/a, as in a batch report.

The second table (design decision 13) adds confirmed finds: real holes
the scenario did not plant, from `scenarios/<name>/triage.toml`. It also
counts control runs, because a control run can confirm a find. A scenario
with no triage file counts no finds, so "either" is a lower bound. The
per-scenario counts of a held scenario stay in the lab repo.
"""
import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rig import prices, report, triage  # noqa: E402


def newest_runs(root, cells, skip, controls):
    """(scenario, cell) -> (batch name, runs) from the newest batch that
    holds the cell. Control scenarios count only when `controls`."""
    newest = {}
    for batch in sorted((Path(root) / "results").iterdir()):
        runs = report.load(batch)
        if not runs or runs[0]["scenario"] in skip:
            continue
        if runs[0].get("control") and not controls:
            continue
        for cell in {r["cell"] for r in runs} & set(cells):
            newest[(runs[0]["scenario"], cell)] = (
                batch.name, [r for r in runs if r["cell"] == cell])
    return newest


def planted_table(newest, cells, sheet):
    """The planted-success table, as lines."""
    scenarios = sorted({s for s, _ in newest})
    shown = [c for c in cells if any((s, c) in newest for s in scenarios)]
    lines = ["| Scenario | " + " | ".join(shown) + " |",
             "|---|" + "---:|" * len(shown)]
    totals = {c: [0, 0, 0.0] for c in shown}
    for s in scenarios:
        row = []
        for c in shown:
            if (s, c) not in newest:
                row.append("")
                continue
            runs = newest[(s, c)][1]
            wins = sum(report.success(r) for r in runs)
            costs = [report.run_cost(r, sheet) for r in runs]
            totals[c][0] += wins
            totals[c][1] += len(runs)
            # One unpriced run makes the cell's cost unknown, as in a batch
            # report, not a partial sum read as the whole.
            if totals[c][2] is not None:
                totals[c][2] = None if None in costs else totals[c][2] + sum(costs)
            row.append(f"{wins}/{len(runs)}")
        lines.append(f"| {s} | " + " | ".join(row) + " |")
    lines += [
        "| **All** | " + " | ".join(f"**{w}/{n}**" for w, n, _ in totals.values()) + " |",
        "| 95% interval | " + " | ".join(
            "{:.0%} to {:.0%}".format(*report.wilson(w, n)) for w, n, _ in totals.values())
        + " |",
        "| Credits per success | " + " | ".join(
            f"{cost / w:.0f}" if w and cost is not None else "n/a"
            for w, _, cost in totals.values()) + " |",
        "",
        "Batches: " + ", ".join(sorted({b for b, _ in newest.values()})),
    ]
    return lines


def find_counts(newest, cells, finds):
    """Per cell: [runs, planted successes, confirmed finds with no planted
    success]. Per scenario: [runs, runs with a confirmed find, ids of the
    real finds those runs confirm]. `finds` maps scenario -> its finds."""
    per_cell = {c: [0, 0, 0] for c in cells}
    per_scenario = {}
    for (scenario, cell), (batch, runs) in newest.items():
        counts = per_scenario.setdefault(scenario, [0, 0, set()])
        for run in runs:
            ids = triage.confirmed(run, batch, finds.get(scenario, []))
            per_cell[cell][0] += 1
            counts[0] += 1
            if ids:
                counts[1] += 1
                counts[2].update(ids)
            if report.success(run):
                per_cell[cell][1] += 1
            elif ids:
                per_cell[cell][2] += 1
    return per_cell, per_scenario


def _rate(count, n):
    return f"{count}/{n} ({report._interval(report.wilson(count, n))})"


def finds_table(newest, cells, finds):
    """The second table and the per-scenario counts, as lines."""
    per_cell, per_scenario = find_counts(newest, cells, finds)
    shown = [c for c in cells if per_cell[c][0]]
    lines = [
        "Planted successes and confirmed finds (decision 13), control runs "
        "included. A confirmed find is a run listed under a fixed-upstream, "
        "disclosed, or open-held find in the scenario's `triage.toml`, with "
        "the regression set passing and no agent error or timeout. A person "
        "judged it, not a hidden test. A scenario with no triage file counts "
        "no finds, so \"either\" is a lower bound. Each count has a 95% "
        "Wilson interval over all the cell's runs.",
        "",
        "| Cell | Runs | Planted success | Confirmed find, no planted success | Either |",
        "|---|---:|---|---|---|",
    ]
    for c in shown:
        n, planted, found = per_cell[c]
        lines.append(f"| {c} | {n} | {_rate(planted, n)} | {_rate(found, n)} | "
                     f"{_rate(planted + found, n)} |")
    lines += [
        "",
        "| Scenario | Runs | Triaged | Runs with a confirmed find | Finds confirmed | Held |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for scenario in sorted(per_scenario):
        n, runs_found, ids = per_scenario[scenario]
        listed = finds.get(scenario, [])
        held = {f["id"] for f in listed if f["status"] == triage.HELD} & ids
        lines.append(f"| {scenario} | {n} | {'yes' if listed else 'no'} | {runs_found} | "
                     f"{len(ids)} | {len(held)} |")
    lines += ["", "Batches: " + ", ".join(sorted({b for b, _ in newest.values()}))]
    return lines


def main(argv=None, root=ROOT):
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", default="copilot")
    parser.add_argument("--skip", default="", help="scenarios to leave out, comma-separated")
    args = parser.parse_args(argv)
    skip = {"booking-ladder", *filter(None, args.skip.split(","))}
    sheet = prices.load()[args.sheet]
    cells = [c["name"] for c in
             tomllib.loads((Path(root) / "config" / "matrix.toml").read_text())["cells"]
             if not c["name"].startswith("fake")]
    lines = planted_table(newest_runs(root, cells, skip, controls=False), cells, sheet)
    every = newest_runs(root, cells, skip, controls=True)
    finds = {s: triage.load(s, root) for s in {s for s, _ in every}}
    lines += [""] + finds_table(every, cells, finds)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
