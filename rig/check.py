"""Check a scenario: the fixture must fail every defect test and pass the
regression tests, and each reference fix must fix exactly the defects that
name it (a defect names its own id unless it sets `solution`). Each patch
in the scenario's `wrong/` folder is a known wrong fix: it must fix no
defect, or fail the regression tests. Each patch in `right/` is a known
correct fix in another place or shape than the reference fix. A line
`Fixes: <id>, <id>` in its note names the defects it must fix, exactly,
with the regression tests passing. It proves the hidden tests grade what
a fix does, not where it sits.

A control scenario (design decision 12) has no defect. Its baseline must
pass the regression and visible tests, and it may have no `solutions/`,
`wrong/`, or `right/` folder, because there is no fix to grade."""
import re
import tempfile
from pathlib import Path

from . import scenario as scenarios
from .score import score, score_patch


def check(name):
    scenario = scenarios.load(name)
    if scenario.unprepared():
        return [scenario.unprepared()]
    if scenario.control:
        return check_control(scenario)
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
        for patch in sorted((scenario.folder / "right").glob("*.patch")):
            text = patch.read_text()
            named = re.search(r"^Fixes: *(.+)$", text, re.MULTILINE)
            if not named:
                problems.append(f"right/{patch.name} has no 'Fixes:' line")
                continue
            expected = sorted(part.strip() for part in named.group(1).split(","))
            scored, error = score_patch(scenario, text, Path(folder) / f"right-{patch.stem}")
            if error:
                problems.append(f"right/{patch.name} does not apply: {error}")
            elif sorted(scored["fixed"]) != expected or not scored["regression_pass"]:
                problems.append(f"right/{patch.name} fixes {scored['fixed']} with regression "
                                f"pass {scored['regression_pass']}, expected {expected}")
    return problems


def check_control(scenario):
    problems = [f"a control has no {name}/ folder" for name in ("solutions", "wrong", "right")
                if (scenario.folder / name).exists()]
    with tempfile.TemporaryDirectory() as folder:
        base = scenarios.copy_repo(scenario, Path(folder) / "base")
        result = score(scenario, base)
    failing = sorted(t for t in scenario.regression if not result["tests"][t]["passed"])
    if failing:
        problems.append(f"baseline fails regression tests {failing}")
    if not result["visible_pass"]:
        problems.append("baseline fails its visible tests")
    return problems
