"""Score a finished working copy against the hidden tests.

The tests run in a sandbox with no network, on a copy, so the agent's code
cannot touch the scenario. A defect counts as fixed when all its tests pass.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import sandbox
from .scenario import IGNORED

def _run(scenario, tests, cwd):
    command = sandbox.command(
        scenario.argv(tests), cwd=cwd, read=scenario.sandbox_read(), write=[cwd],
        env={"HOME": str(cwd), "PYTHONDONTWRITEBYTECODE": "1",
             **scenario.sandbox_env()},
    )
    try:
        done = subprocess.run(command, capture_output=True, text=True,
                              timeout=scenario.timeout)
    except subprocess.TimeoutExpired:
        return False, "timed out"
    tail = "\n".join((done.stdout + done.stderr).strip().splitlines()[-15:])
    return done.returncode == 0, tail


def score(scenario, repo):
    with tempfile.TemporaryDirectory(dir=Path(repo).parent) as scratch:
        copy = Path(scratch) / "repo"
        shutil.copytree(repo, copy, ignore=IGNORED)
        # The agent's own test command, before the hidden tests exist.
        visible, visible_tail = _run(scenario, scenario.visible, copy)
        for name in scenario.pristine:
            (copy / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(scenario.fixture / name, copy / name)
        # A folder the fixture lacks belongs to the hidden tests alone, so
        # anything the agent left there goes. Inside a fixture folder, the
        # hidden files land over the agent's files of the same name.
        target = copy / scenario.hidden_into
        if not (scenario.fixture / scenario.hidden_into).is_dir():
            shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(scenario.hidden, target, dirs_exist_ok=True,
                        ignore=IGNORED)
        tests = {}
        for test in sorted({t for d in scenario.defects for t in d["tests"]}
                           | set(scenario.regression)):
            passed, tail = _run(scenario, [test], copy)
            tests[test] = {"passed": passed, "tail": "" if passed else tail}
    fixed = [d["id"] for d in scenario.defects
             if all(tests[t]["passed"] for t in d["tests"])]
    regression = all(tests[t]["passed"] for t in scenario.regression)
    return {
        "fixed": fixed,
        "regression_pass": regression,
        "visible_pass": visible,
        "visible_tail": "" if visible else visible_tail,
        "tests": tests,
    }
