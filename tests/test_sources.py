"""A scenario with a git-sourced fixture, a revert patch, its own test
command, and a prepared environment. Fake agents only, no network: the
upstream is a local git repository that the test builds."""
import contextlib
import io
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from rig import ROOT, STATE, check, prepare, run
from rig import scenario as scenarios

assert "model-rig-state-" in str(STATE)

MATRIX = run.load_matrix(ROOT / "tests" / "matrix-fake.toml")
MATRIX["cells"].append({"name": "fake-d1", "harness": "fake", "model": "d1-owner"})

FIXED = "def allowed(user, owner):\n    return user == owner\n"
BROKEN = "def allowed(user, owner):\n    return True\n"

# The project's own runner. The visible test needs the variable it sets,
# so a scorer that ignored the command template would fail it.
RUNNER = """\
import os
import sys
import unittest

os.environ["APP_RUNNER"] = "custom"
names = sys.argv[1:]
loader = unittest.defaultTestLoader
suite = loader.loadTestsFromNames(names) if names else loader.discover("app", top_level_dir=".")
sys.exit(0 if unittest.TextTestRunner().run(suite).wasSuccessful() else 1)
"""

# Needs the custom runner and the prepared environment's marker module.
VISIBLE = """\
import os
import unittest

import rigmarker

from app.core import allowed


class Visible(unittest.TestCase):
    def test_runner_and_environment(self):
        self.assertEqual(os.environ.get("APP_RUNNER"), "custom")
        self.assertTrue(rigmarker.OK)

    def test_self_allowed(self):
        self.assertTrue(allowed("ann", "ann"))
"""

HIDDEN = """\
import unittest

from app.core import allowed


class Owner(unittest.TestCase):
    def test_denies_other(self):
        self.assertFalse(allowed("bob", "ann"))

    def test_allows_self(self):
        self.assertTrue(allowed("ann", "ann"))
"""

# Setup runs inside the venv: it writes a module only that venv can import.
MARKER = ("python3 -c \"import pathlib, site; pathlib.Path(site.getsitepackages()[0],"
          " 'rigmarker.py').write_text('OK = True')\"")


def _git(folder, *args):
    return subprocess.run(["git", "-C", str(folder), "-c", "user.name=t",
                           "-c", "user.email=t@localhost", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def _write(root, files):
    for name, text in files.items():
        path = Path(root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def build_scenario():
    """An upstream with three commits: vulnerable, fixed, later. The
    scenario pins the fix and reverts it with a patch."""
    base = Path(tempfile.mkdtemp(prefix="model-rig-upstream-"))
    upstream = base / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "-q", "-b", "main")
    _write(upstream, {"runtests.py": RUNNER, "app/__init__.py": "",
                      "app/core.py": BROKEN, "app/tests/__init__.py": "",
                      "app/tests/test_visible.py": VISIBLE})
    _git(upstream, "add", "-A")
    _git(upstream, "commit", "-q", "-m", "vulnerable")
    _write(upstream, {"app/core.py": FIXED})
    _git(upstream, "commit", "-q", "-am", "fix")
    fix = _git(upstream, "rev-parse", "HEAD")
    revert = _git(upstream, "diff", "HEAD", "HEAD~1") + "\n"
    _write(upstream, {"README.md": "later\n"})
    _git(upstream, "add", "-A")
    _git(upstream, "commit", "-q", "-m", "later")

    folder = base / "git-scenario"
    _write(folder, {
        "revert.patch": revert,
        "hidden/test_hidden_owner.py": HIDDEN,
        "solutions/d1-owner/app/core.py": FIXED,
        "scenario.toml": textwrap.dedent(f"""\
            name = "git-scenario"
            [fixture]
            git = "{upstream}"
            commit = "{fix}"
            patch = "revert.patch"
            [environment]
            setup = ['''{MARKER}''']
            [tests]
            command = ["python3", "runtests.py", "{{tests}}"]
            hidden_into = "app/tests"
            pristine = ["app/tests/test_visible.py"]
            [prompts]
            open = "Fix it."
            [[defects]]
            id = "d1-owner"
            tests = ["app.tests.test_hidden_owner.Owner.test_denies_other"]
            [regression]
            tests = ["app.tests.test_hidden_owner.Owner.test_allows_self",
                     "app.tests.test_visible"]
            """)})
    return folder


class GitScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for folder, name in (("claude-config", ".credentials.json"),
                             ("codex-home", "auth.json")):
            Path(STATE, folder).mkdir(exist_ok=True)
            Path(STATE, folder, name).write_text("{}")
        cls.folder = build_scenario()
        cls.scenario = scenarios.load(cls.folder)
        cls.before = cls.scenario.missing()
        cls.check_before = check.check(cls.folder)
        cls.said = []
        prepare.prepare(cls.scenario, echo=cls.said.append)
        prepare.prepare(cls.scenario, echo=cls.said.append)
        results = tempfile.mkdtemp(prefix="model-rig-results-")
        _, rows = run.run_batch(cls.folder, MATRIX, ["fake-none", "fake-d1", "fake-probe"],
                                ["open"], 1, results_root=results, echo=lambda *_: None)
        cls.rows = {row["cell"]: row for row in rows}

    def test_unprepared_scenario_refuses_to_check(self):
        self.assertEqual(self.before, ["fixture", "environment"])
        self.assertIn("python3 -m rig prepare git-scenario", self.check_before[0])

    def test_fixture_is_pinned_commit_with_patch(self):
        fixture = self.scenario.fixture
        self.assertTrue(fixture.is_relative_to(STATE))
        self.assertEqual((fixture / "app" / "core.py").read_text(), BROKEN)
        self.assertFalse((fixture / "README.md").exists())
        self.assertFalse((fixture / "app" / "tests" / "test_hidden_owner.py").exists())

    def test_prepare_again_is_a_no_op(self):
        self.assertEqual(sum("current" in line for line in self.said), 2)

    def test_copy_has_no_upstream_history(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = scenarios.copy_repo(self.scenario, Path(folder) / "repo")
            log = _git(repo, "log", "--format=%s")
            self.assertEqual(log, "baseline")
            self.assertFalse((repo / ".rig-prepared").exists())

    def test_command_template(self):
        self.assertEqual(self.scenario.argv([]), ["python3", "runtests.py"])
        self.assertEqual(self.scenario.argv(["a", "b"]), ["python3", "runtests.py", "a", "b"])
        default = scenarios.load("booking-ladder")
        self.assertEqual(default.argv(["x"]), ["python3", "-m", "unittest", "-q", "x"])

    def test_scenario_is_sound(self):
        self.assertEqual(check.check(self.folder), [])

    def test_baseline_scores_nothing_fixed(self):
        row = self.rows["fake-none"]
        self.assertEqual(row["fixed"], [])
        self.assertTrue(row["visible_pass"], row["visible_tail"])
        self.assertTrue(row["regression_pass"])

    def test_reference_fix_scores(self):
        row = self.rows["fake-d1"]
        self.assertEqual(row["fixed"], ["d1-owner"])
        self.assertTrue(row["regression_pass"])
        self.assertEqual(row["diff"]["files"], 1)

    def test_sandbox_shows_environment_and_hides_the_rest(self):
        self.assertEqual(self.rows["fake-probe"]["final"],
                         f'PROBE ["{self.scenario.env}"]')

    def test_cli_prepare_reports_current(self):
        from rig.__main__ import main
        with contextlib.redirect_stdout(io.StringIO()) as said:
            self.assertEqual(main(["prepare", str(self.folder)]), 0)
        self.assertIn("environment current", said.getvalue())


class BaseInterpreterTest(unittest.TestCase):
    def write_config(self, home):
        env = Path(tempfile.mkdtemp(prefix="model-rig-venv-"))
        (env / "pyvenv.cfg").write_text(f"home = {home}\nversion = 3.12.0\n")
        return env

    def test_hidden_base_interpreter_is_bound(self):
        env = self.write_config("/srv/pythons/3.12.0/bin")
        self.assertEqual(scenarios.base_interpreter(env),
                         [Path("/srv/pythons/3.12.0")])

    def test_linked_version_folder_binds_link_and_target(self):
        root = Path(tempfile.mkdtemp(prefix="model-rig-pythons-"))
        (root / "cpython-3.12.9" / "bin").mkdir(parents=True)
        (root / "cpython-3.12").symlink_to(root / "cpython-3.12.9")
        env = self.write_config(root / "cpython-3.12" / "bin")
        self.assertEqual(scenarios.base_interpreter(env),
                         [root / "cpython-3.12", (root / "cpython-3.12.9").resolve()])

    def test_system_interpreter_needs_no_bind(self):
        self.assertEqual(scenarios.base_interpreter(self.write_config("/usr/bin")), [])


if __name__ == "__main__":
    unittest.main()
