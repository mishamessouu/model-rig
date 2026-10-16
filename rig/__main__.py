"""Command line. `model-rig` and `python3 -m rig` are the same program.

    model-rig prepare wger-log-idor
    model-rig check booking-ladder
    model-rig run booking-ladder --cells claude-opus-medium --prompts open --repeats 1 --yes
    model-rig rescore results/<batch>
    model-rig report results/<batch>
"""
import argparse
import os
import sys
from pathlib import Path

from . import check, prepare, report, rescore, run
from . import scenario as scenarios


def main(argv=None):
    prog = "model-rig" if os.path.basename(sys.argv[0]) == "model-rig" else "python3 -m rig"
    parser = argparse.ArgumentParser(
        prog=prog, description="Run coding agents on planted-defect scenarios and score them.")
    commands = parser.add_subparsers(dest="command", required=True)
    preparing = commands.add_parser(
        "prepare", help="fetch a scenario's fixture and build its environment (network)")
    preparing.add_argument("scenario")
    checking = commands.add_parser("check", help="validate a scenario")
    checking.add_argument("scenario")
    running = commands.add_parser("run", help="run a batch")
    running.add_argument("scenario")
    running.add_argument("--matrix")
    running.add_argument("--cells", required=True, help="comma-separated cell names")
    running.add_argument("--prompts", required=True, help="comma-separated prompt names")
    running.add_argument("--repeats", type=int)
    running.add_argument("--keep", action="store_true", help="keep work folders")
    running.add_argument("--resume", help="add the missing runs to this batch folder")
    running.add_argument("--yes", action="store_true",
                         help="confirm that real agent runs may spend usage")
    rescoring = commands.add_parser("rescore", help="score a batch's saved diffs again")
    rescoring.add_argument("batch")
    reporting = commands.add_parser("report", help="summarise a batch")
    reporting.add_argument("batch")
    reporting.add_argument("--sheet", default="copilot")
    args = parser.parse_args(argv)

    if args.command == "prepare":
        prepare.prepare(scenarios.load(args.scenario))
        return 0
    if args.command == "check":
        problems = check.check(args.scenario)
        for problem in problems:
            print(f"FAIL {problem}")
        print("scenario OK" if not problems else f"{len(problems)} problems")
        return 1 if problems else 0
    if args.command == "run":
        matrix = run.load_matrix(args.matrix)
        cells = args.cells.split(",")
        prompts = args.prompts.split(",")
        repeats = args.repeats or matrix["repeats"]
        planned = run.plan(matrix, cells, prompts, repeats)
        real = [c for _, c, _ in planned if c["harness"] != "fake"]
        print(f"{len(planned)} runs: {len(cells)} cells x {len(prompts)} prompts x {repeats} repeats")
        if real and not args.yes:
            print("These runs call real models and spend usage. Add --yes to start.")
            return 2
        out_root, _ = run.run_batch(args.scenario, matrix, cells, prompts, repeats,
                                    keep=args.keep, resume=args.resume)
        (out_root / "report.md").write_text(report.markdown(out_root))
        print(f"report: {out_root / 'report.md'}")
        return 0
    if args.command == "rescore":
        changed = rescore.rescore(Path(args.batch))
        (Path(args.batch) / "report.md").write_text(report.markdown(Path(args.batch)))
        print(f"{changed} runs changed score. report: {Path(args.batch) / 'report.md'}")
        return 0
    if args.command == "report":
        text = report.markdown(Path(args.batch), args.sheet)
        (Path(args.batch) / "report.md").write_text(text)
        print(text)
        return 0


if __name__ == "__main__":
    sys.exit(main())
