"""Load a scenario and make working copies of its fixture.

A fixture is either a folder in the scenario (`repo/`) or an upstream git
commit, prepared once into a cache under the rig state folder by
`python3 -m rig prepare`. A scenario may also name an environment,
prepared into the same state folder, that the agent and the scorer use:
a Python venv, or a Node `node_modules` (design decision 11).
"""
import os
import shutil
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import ROOT, STATE, sandbox

IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", ".git")
# `{tests}` in a command becomes zero or more test ids.
TESTS = "{tests}"
DEFAULT_COMMAND = ["python3", "-m", "unittest", "-q", TESTS]
# Files a Node environment copies from the fixture root before its setup
# commands run, so `npm ci` installs what the project's lock file names.
NODE_MANIFESTS = ("package.json", "package-lock.json", "npm-shrinkwrap.json", ".npmrc")
# npm in a sandbox: no registry, so fail at once instead of retrying, and
# no update check, audit, or funding call.
NODE_ENV = {"npm_config_offline": "true", "npm_config_update_notifier": "false",
            "npm_config_audit": "false", "npm_config_fund": "false"}


@dataclass
class Scenario:
    name: str
    folder: Path
    prompts: dict
    defects: list
    regression: list
    # Upstream source: {"git": url, "commit": sha, "patch": file}, or None.
    source: dict | None = None
    # Commands that fill the environment, or None for no environment.
    setup: list | None = None
    # "python" (a venv) or "node" (a node_modules folder, decision 11).
    kind: str = "python"
    command: list = field(default_factory=lambda: list(DEFAULT_COMMAND))
    # Where hidden test files land in the scoring copy.
    hidden_into: str = "hidden"
    # Test ids for the agent's own test run. Empty runs the bare command.
    visible: list = field(default_factory=list)
    # Fixture files copied over the scoring copy, so an agent cannot
    # weaken the visible tests that the regression set uses.
    pristine: list = field(default_factory=list)
    # Seconds one scoring test command may take.
    timeout: int = 120
    # "YYYY-MM-DD" of the upstream fix, for a reinjected real fix. A model
    # whose training cutoff is on or after it may know the fix.
    fix_date: str | None = None
    # A control has no defect: the app holds a known fix, and a run shows
    # whether the agent changes nothing, changes code safely, or breaks
    # something (design decision 12).
    control: bool = False

    @property
    def fixture(self):
        if self.source:
            return STATE / "fixtures" / self.name
        return self.folder / "repo"

    @property
    def env(self):
        return STATE / "envs" / self.name if self.setup is not None else None

    @property
    def hidden(self):
        return self.folder / "hidden"

    def solution(self, defect_id):
        return self.folder / "solutions" / defect_id

    def argv(self, tests):
        out = []
        for part in self.command:
            out += list(tests) if part == TESTS else [part]
        return out

    def sandbox_read(self):
        """Paths both sandboxes bind read-only for this scenario: the
        prepared environment, and its base interpreter or Node install
        when the sandbox would otherwise hide it."""
        if not self.env:
            return []
        if self.kind == "node":
            return [self.env, *node_install(self.env)]
        return [self.env, *base_interpreter(self.env)]

    def sandbox_mounts(self, copy):
        """(source, target) pairs both sandboxes bind read-only over the
        working copy `copy`: a Node environment's node_modules, so the
        project resolves its packages the way it does on a developer's
        machine, and nothing in it enters the copy or its diff."""
        if self.kind != "node" or not self.env:
            return []
        return [(self.env / "node_modules", Path(copy) / "node_modules")]

    def sandbox_env(self):
        """Variables both sandboxes set, so `python3`, or `node` and
        `npm`, are the prepared ones."""
        if not self.env:
            return {}
        if self.kind == "node":
            return {"PATH": f"{self.env}/bin:{sandbox.PATH}", **NODE_ENV}
        return {"PATH": f"{self.env}/bin:{sandbox.PATH}", "VIRTUAL_ENV": self.env}

    def missing(self):
        """What `rig prepare` still has to build, as a list of words."""
        out = []
        if self.source and not (self.fixture / ".rig-prepared").exists():
            out.append("fixture")
        if self.env and not (self.env / ".rig-prepared").exists():
            out.append("environment")
        return out

    def unprepared(self):
        """A message naming what is missing, or None when prepared."""
        if not self.missing():
            return None
        return (f"{self.name}: {' and '.join(self.missing())} not prepared. "
                f"Run: python3 -m rig prepare {self.name}")


def _outside(link, env):
    """The first path in `link`'s chain of links that is not in `env`."""
    env = Path(env)
    while link.is_symlink() and link.is_relative_to(env):
        link = link.parent / os.readlink(link)
    return link


def _masked_install(link):
    """Restore only an install, never a private folder or its parent.
    `link` is the executable the environment names, two levels below its
    install folder. The folder comes back only when it holds the real
    executable, through a link or not. A link in a shared folder, such as
    uv's ~/.local/bin/python3, brings back the one link and the folder of
    its target, never all of ~/.local."""
    masked = (*sandbox.EMPTIED, *sandbox.hidden_paths())
    private = [Path(path).resolve() for path in
               (sandbox.ROOT, sandbox.STATE, Path.home())]
    named = link.parent.parent
    real = link.resolve()
    if real.is_relative_to(named.resolve()):
        prefixes = (named, named.resolve())
    else:
        prefixes = (link, real.parent.parent)
    out = []
    for prefix in prefixes:
        if any(path.is_relative_to(prefix.resolve()) for path in private):
            continue
        if prefix not in out and any(prefix.is_relative_to(folder) for folder in masked):
            out.append(prefix)
    return out


def base_interpreter(env):
    """The Python install a venv points to, if it sits under a folder the
    sandbox masks, including the dynamic checkout, state, and home masks.
    Without it, the venv's `python3` is a broken link in the sandbox.
    Both the named folder and its resolved target are listed, because uv
    names a version folder through a link."""
    config = Path(env) / "pyvenv.cfg"
    if not config.exists():
        return []
    for line in config.read_text().splitlines():
        key, _, value = line.partition("=")
        if key.strip() == "home" and value.strip():
            home = Path(value.strip())
            link = _outside(Path(env) / "bin" / "python3", env)
            if link.parent != home:
                link = home / "python3"
            return _masked_install(link)
    return []


def node_install(env):
    """The Node install that a Node environment's `bin/node` links to, if
    it sits under any folder the sandbox masks, fixed or dynamic.
    Without it, `node` is a broken link in the sandbox. Both the install
    folder and its resolved target are listed."""
    node = Path(env) / "bin" / "node"
    if not node.is_symlink():
        return []
    return _masked_install(_outside(node, env))


def load(name):
    """Load a scenario by name, or from a folder path (the rig's tests)."""
    folder = Path(name) if Path(name).is_absolute() else ROOT / "scenarios" / name
    if not (folder / "scenario.toml").is_file():
        raise SystemExit(f"no scenario at {folder}. Run model-rig from a model-rig "
                         "checkout, or set MODEL_RIG_ROOT to one.")
    data = tomllib.loads((folder / "scenario.toml").read_text())
    prompts = {key: " ".join(text.split()) for key, text in data["prompts"].items()}
    tests = data.get("tests", {})
    control = data.get("control", False)
    defects = data.get("defects", [])
    if control and defects:
        raise SystemExit(f"{data['name']}: a control scenario has no [[defects]]")
    if not control and not defects:
        raise SystemExit(f"{data['name']}: no [[defects]]. A scenario with nothing "
                         "to find sets `control = true`.")
    return Scenario(
        data["name"], folder, prompts, defects, data["regression"]["tests"],
        source=data.get("fixture"),
        setup=data["environment"].get("setup", []) if "environment" in data else None,
        kind=data.get("environment", {}).get("kind", "python"),
        command=tests.get("command", list(DEFAULT_COMMAND)),
        hidden_into=tests.get("hidden_into", "hidden"),
        visible=tests.get("visible", []),
        pristine=tests.get("pristine", []),
        timeout=tests.get("timeout_seconds", 120),
        fix_date=str(data["fix_date"]) if data.get("fix_date") else None,
        control=control,
    )


def copy_repo(scenario, target):
    """Copy the fixture to `target` and commit it, so the diff is exact.

    A Node scenario's copy gets an empty `node_modules` folder, the mount
    point for the prepared one, and git ignores that name, so a project
    that does not ignore it itself still gets a clean diff."""
    if scenario.unprepared():
        raise SystemExit(scenario.unprepared())
    node = scenario.kind == "node"
    shutil.copytree(scenario.fixture, target, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".git", ".rig-prepared",
        *(["node_modules"] if node else [])))
    git = ["git", "-C", str(target), "-c", "user.name=rig",
           "-c", "user.email=rig@localhost"]
    subprocess.run([*git, "init", "-q", "-b", "main"], check=True)
    if node:
        (Path(target) / "node_modules").mkdir()
        exclude = Path(target) / ".git" / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a") as out:
            out.write("/node_modules\n")
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "baseline"], check=True)
    return target


def overlay(source, target):
    """Copy every file under `source` over `target`, keeping the layout."""
    for path in Path(source).rglob("*"):
        if path.is_file():
            destination = Path(target) / path.relative_to(source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
