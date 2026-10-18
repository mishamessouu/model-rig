"""Score the saved diffs of a batch again, with no model call.

Use it after a scenario gains defects or its tests change. Each run's
`diff.patch` goes onto a fresh copy of the fixture, and the scorer runs as
it would after a real run. The old score stays in `previous_scores`.
"""
import datetime
import json
import tempfile
from pathlib import Path

from . import scenario as scenarios
from .score import score_patch

FIELDS = ("fixed", "regression_pass", "visible_pass", "visible_tail", "tests")


def rescore(batch_dir, echo=print):
    batch_dir = Path(batch_dir)
    name = json.loads((batch_dir / "batch.json").read_text())["scenario"]
    scenario = scenarios.load(name)
    if scenario.unprepared():
        raise SystemExit(scenario.unprepared())
    changed = 0
    for path in sorted(batch_dir.glob("runs/*/result.json")):
        result = json.loads(path.read_text())
        patch = path.parent / "diff.patch"
        with tempfile.TemporaryDirectory() as folder:
            new, error = score_patch(scenario, patch.read_text(), folder)
        if error:
            echo(f"{result['run_id']}: patch did not apply, kept old score: {error[:200]}")
            continue
        old = {key: result.get(key) for key in FIELDS}
        if any(old[key] != new[key] for key in ("fixed", "regression_pass", "visible_pass")):
            changed += 1
            echo(f"{result['run_id']}: {old['fixed']} -> {new['fixed']}")
        stamp = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
        result.setdefault("previous_scores", []).append({"until": stamp, **old})
        result.update(new)
        path.write_text(json.dumps(result, indent=2) + "\n")
    return changed
