"""Check a scenario: the fixture must fail every defect test and pass the
regression tests, and each reference fix must fix exactly the defects that
name it (a defect names its own id unless it sets `solution`)."""
import tempfile
from pathlib import Path

from . import scenario as scenarios
from .score import score


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
    return problems
