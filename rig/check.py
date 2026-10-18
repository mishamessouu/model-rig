"""Check a scenario: the fixture must fail every defect test and pass the
regression tests, and each reference fix must fix exactly the defects that
name it (a defect names its own id unless it sets `solution`). Each patch
in the scenario's `wrong/` folder is a known wrong fix: it must fix no
defect, or fail the regression tests."""
import tempfile
from pathlib import Path

from . import scenario as scenarios
from .score import score, score_patch


def check(name):
    scenario = scenarios.load(name)
    if scenario.unprepared():
        return [scenario.unprepared()]
    problems = []
    with tempfile.TemporaryDirectory() as folder:
        base = scenarios.copy_repo(scenario, Path(folder) / "base")
        result = score(scenario, base)
        if result["fixed"]:
            problems.append(f"baseline already passes {result['fixed']}")
        # Each test, not only each defect: a test that passes on the
        # unfixed code measures nothing.
        passing = sorted(t for d in scenario.defects for t in d["tests"]
                         if result["tests"][t]["passed"])
        if passing:
            problems.append(f"baseline already passes defect tests {passing}")
        if not result["regression_pass"] or not result["visible_pass"]:
            problems.append("baseline fails its regression or visible tests")
        covers = {}
        for defect in scenario.defects:
            covers.setdefault(defect.get("solution", defect["id"]), []).append(defect["id"])
        for name, ids in covers.items():
            solution = scenario.solution(name)
            if not solution.is_dir():
                problems.append(f"{name}: no reference fix")
                continue
            repo = scenarios.copy_repo(scenario, Path(folder) / name)
            scenarios.overlay(solution, repo)
            fixed = score(scenario, repo)
            if sorted(fixed["fixed"]) != sorted(ids):
                problems.append(f"{name}: reference fix fixes {fixed['fixed']}, expected {ids}")
            if not fixed["regression_pass"] or not fixed["visible_pass"]:
                problems.append(f"{name}: reference fix breaks regression tests")
        for patch in sorted((scenario.folder / "wrong").glob("*.patch")):
            scored, error = score_patch(scenario, patch.read_text(),
                                        Path(folder) / f"wrong-{patch.stem}")
            if error:
                problems.append(f"wrong/{patch.name} does not apply: {error}")
            elif scored["fixed"] and scored["regression_pass"]:
                problems.append(f"wrong/{patch.name} scores as a success: {scored['fixed']}")
    return problems
