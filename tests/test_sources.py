"""A scenario with a git-sourced fixture, a revert patch, its own test
command, and a prepared environment, as a Python venv and as a Node
node_modules. Fake agents only, no network: the upstream is a local git
repository that the test builds, and the Node package a local tarball."""
import contextlib
import dataclasses
import io
import json
import subprocess
import tarfile
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from rig import ROOT, STATE, check, prepare, run, sandbox
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

# Setup runs inside the venv: it copies a module from the scenario folder
# (named through `{scenario}`) to where only that venv can import it.
MARKER = ("python3 -c \"import shutil, site, sys; shutil.copy(sys.argv[1],"
          " site.getsitepackages()[0])\" {scenario}/env/rigmarker.py")


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
        "env/rigmarker.py": "OK = True\n",
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

    def test_setup_file_change_builds_again(self):
        marker = self.folder / "env" / "rigmarker.py"
        before = prepare._stamp(self.scenario, "environment")
        self.assertIn("env/rigmarker.py", before)
        marker.write_text("OK = True  # changed\n")
        try:
            self.assertNotEqual(prepare._stamp(self.scenario, "environment"), before)
        finally:
            marker.write_text("OK = True\n")

    def test_cli_prepare_reports_current(self):
        from rig.__main__ import main
        with contextlib.redirect_stdout(io.StringIO()) as said:
            self.assertEqual(main(["prepare", str(self.folder)]), 0)
        self.assertIn("environment current", said.getvalue())


# --- A Node scenario (decision 11) ------------------------------------------

NODE_FIXED = "exports.allowed = (user, owner) => user === owner\n"
NODE_BROKEN = "exports.allowed = (user, owner) => true\n"

# A package the environment installs from a local tarball, so the test
# needs no registry. Its bin is the project's test runner, reached through
# `npx` the way a project reaches mocha. It runs `node --test` with a
# variable that the visible test needs, so a scorer that ignored the
# command template would fail it.
RIGTOOLS = {
    "package.json": '{"name": "rigtools", "version": "1.0.0", "main": "index.js",'
                    ' "bin": {"rigtools": "bin/rigtools.js"}}\n',
    "index.js": "exports.OK = true\n",
    "bin/rigtools.js": """\
#!/usr/bin/env node
const { spawnSync } = require('node:child_process')
const done = spawnSync('node', ['--test', ...process.argv.slice(2)], {
  stdio: 'inherit', env: { ...process.env, APP_RUNNER: 'custom' }
})
process.exit(done.status === null ? 1 : done.status)
""",
}

# The package must resolve from the working copy's own node_modules, the
# way the project resolves it outside the rig, not through NODE_PATH.
NODE_VISIBLE = """\
const test = require('node:test')
const assert = require('node:assert')
const path = require('node:path')
const rigtools = require('rigtools')
const { allowed } = require('../app/core')

test('runner and environment', () => {
  assert.equal(process.env.APP_RUNNER, 'custom')
  assert.equal(rigtools.OK, true)
  assert.ok(require.resolve('rigtools').startsWith(path.join(process.cwd(), 'node_modules')))
})

test('self allowed', () => assert.equal(allowed('ann', 'ann'), true))
"""

NODE_HIDDEN_DENY = """\
const test = require('node:test')
const assert = require('node:assert')
const { allowed } = require('../app/core')

test('denies other', () => assert.equal(allowed('bob', 'ann'), false))
"""

NODE_HIDDEN_SELF = """\
const test = require('node:test')
const assert = require('node:assert')
const { allowed } = require('../app/core')

test('allows self', () => assert.equal(allowed('ann', 'ann'), true))
"""


def _npm_tarball(path, files):
    """An npm package tarball: a gzipped tar with every file under package/."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w:gz") as tar:
        for name, text in files.items():
            data = text.encode()
            info = tarfile.TarInfo(f"package/{name}")
            info.size, info.mode = len(data), 0o755 if name.startswith("bin/") else 0o644
            tar.addfile(info, io.BytesIO(data))


def build_node_scenario():
    """An upstream Node project with two commits, vulnerable then fixed.
    The scenario pins the vulnerable one, as the real scenarios do."""
    base = Path(tempfile.mkdtemp(prefix="model-rig-node-upstream-"))
    upstream = base / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "-q", "-b", "main")
    _write(upstream, {"package.json": '{"name": "nodeapp", "version": "1.0.0",'
                                      ' "private": true}\n',
                      "app/core.js": NODE_BROKEN,
                      "test/visible.test.js": NODE_VISIBLE})
    _git(upstream, "add", "-A")
    _git(upstream, "commit", "-q", "-m", "vulnerable")
    vulnerable = _git(upstream, "rev-parse", "HEAD")
    _write(upstream, {"app/core.js": NODE_FIXED})
    _git(upstream, "commit", "-q", "-am", "fix")

    folder = base / "node-scenario"
    _npm_tarball(folder / "env" / "rigtools-1.0.0.tgz", RIGTOOLS)
    _write(folder, {
        "hidden/hidden_deny.test.js": NODE_HIDDEN_DENY,
        "hidden/hidden_self.test.js": NODE_HIDDEN_SELF,
        "solutions/d1-owner/app/core.js": NODE_FIXED,
        "scenario.toml": textwrap.dedent(f"""\
            name = "node-scenario"
            [fixture]
            git = "{upstream}"
            commit = "{vulnerable}"
            [environment]
            kind = "node"
            setup = ["npm install --no-save --offline --no-audit --no-fund --loglevel=error {{scenario}}/env/rigtools-1.0.0.tgz"]
            [tests]
            command = ["npx", "rigtools", "{{tests}}"]
            hidden_into = "test"
            pristine = ["test/visible.test.js"]
            [prompts]
            open = "Fix it."
            [[defects]]
            id = "d1-owner"
            tests = ["test/hidden_deny.test.js"]
            [regression]
            tests = ["test/hidden_self.test.js", "test/visible.test.js"]
            """)})
    return folder


class NodeScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for folder, name in (("claude-config", ".credentials.json"),
                             ("codex-home", "auth.json")):
            Path(STATE, folder).mkdir(exist_ok=True)
            Path(STATE, folder, name).write_text("{}")
        cls.folder = build_node_scenario()
        cls.scenario = scenarios.load(cls.folder)
        cls.said = []
        prepare.prepare(cls.scenario, echo=cls.said.append)
        prepare.prepare(cls.scenario, echo=cls.said.append)
        results = tempfile.mkdtemp(prefix="model-rig-results-")
        cls.out, rows = run.run_batch(cls.folder, MATRIX, ["fake-none", "fake-d1", "fake-probe"],
                                      ["open"], 1, results_root=results, echo=lambda *_: None)
        cls.rows = {row["cell"]: row for row in rows}

    def test_node_modules_lives_in_the_environment(self):
        self.assertEqual(self.scenario.kind, "node")
        self.assertTrue((self.scenario.env / "node_modules" / "rigtools" / "index.js").is_file())
        self.assertFalse((self.scenario.fixture / "node_modules").exists())
        self.assertEqual(sum("current" in line for line in self.said), 2)

    def test_scenario_is_sound(self):
        self.assertEqual(check.check(self.folder), [])

    def test_baseline_scores_nothing_fixed(self):
        row = self.rows["fake-none"]
        self.assertEqual(row["fixed"], [])
        self.assertTrue(row["visible_pass"], row["visible_tail"])
        self.assertTrue(row["regression_pass"])
        self.assertEqual(row["diff"]["files"], 0)

    def test_reference_fix_scores_and_diff_holds_only_the_fix(self):
        row = self.rows["fake-d1"]
        self.assertEqual(row["fixed"], ["d1-owner"])
        self.assertTrue(row["regression_pass"])
        self.assertEqual(row["diff"]["files"], 1)
        patch = (self.out / "runs" / "fake-d1.open.r1" / "diff.patch").read_text()
        self.assertIn("app/core.js", patch)
        self.assertNotIn("node_modules", patch)

    def test_sandbox_shows_environment_and_hides_the_rest(self):
        # The agent's copy holds the environment's node_modules.
        seen = json.loads(self.rows["fake-probe"]["final"][len("PROBE "):])
        self.assertEqual(len(seen), 2, seen)
        self.assertEqual(seen[0], str(self.scenario.env))
        self.assertTrue(seen[1].endswith("/fake-probe.open.r1/repo/node_modules/.package-lock.json"),
                        seen[1])

    def test_copy_resolves_read_only_node_modules_and_stays_clean(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = scenarios.copy_repo(self.scenario, Path(folder) / "repo")
            self.assertEqual(list((repo / "node_modules").iterdir()), [])
            script = ("let wrote; try { require('fs').writeFileSync('node_modules/x', '');"
                      " wrote = 'yes' } catch (e) { wrote = e.code }"
                      " console.log(JSON.stringify({resolved: require.resolve('rigtools'),"
                      " wrote, node: process.execPath}))")
            command = sandbox.command(
                ["node", "-e", script], cwd=repo, read=self.scenario.sandbox_read(),
                write=[repo], mounts=self.scenario.sandbox_mounts(repo),
                env=self.scenario.sandbox_env())
            done = subprocess.run(command, capture_output=True, text=True, check=True)
            seen = json.loads(done.stdout)
            self.assertEqual(seen["resolved"], str(repo / "node_modules" / "rigtools" / "index.js"))
            self.assertEqual(seen["wrote"], "EROFS")
            # The mount leaves nothing behind for git or the diff.
            self.assertEqual(list((repo / "node_modules").iterdir()), [])
            self.assertEqual(_git(repo, "status", "--porcelain"), "")

    def test_python_stamp_has_no_node_keys(self):
        # Built venvs keep their stamps, so the Node kind rebuilds none.
        python = dataclasses.replace(self.scenario, kind="python")
        stamp = json.loads(prepare._stamp(python, "environment"))
        self.assertEqual(sorted(stamp), ["commit", "files", "part", "setup"])

    def test_node_version_change_builds_again(self):
        before = prepare._stamp(self.scenario, "environment")
        with mock.patch("rig.prepare._node_version", return_value="v0.0.0"):
            self.assertNotEqual(prepare._stamp(self.scenario, "environment"), before)


class NodeInstallTest(unittest.TestCase):
    def env_with_node(self, target):
        env = Path(tempfile.mkdtemp(prefix="model-rig-nodeenv-"))
        (env / "bin").mkdir()
        (env / "bin" / "node").symlink_to(target)
        return env

    def test_hidden_node_install_is_bound(self):
        env = self.env_with_node("/home/someone/.nvm/versions/node/v24.0.0/bin/node")
        self.assertEqual(scenarios.node_install(env),
                         [Path("/home/someone/.nvm/versions/node/v24.0.0")])

    def test_system_node_needs_no_bind(self):
        self.assertEqual(scenarios.node_install(self.env_with_node("/usr/local/bin/node")), [])


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
