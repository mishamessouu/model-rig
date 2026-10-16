"""Load a scenario and make working copies of its fixture.

A fixture is either a folder in the scenario (`repo/`) or an upstream git
commit, prepared once into a cache under the rig state folder by
`python3 -m rig prepare`. A scenario may also name a Python environment,
prepared into the same state folder, that the agent and the scorer use.
"""
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
        """Paths both sandboxes bind read-only for this scenario."""
        return [self.env] if self.env else []

    def sandbox_env(self):
        """Variables both sandboxes set, so `python3` is the prepared one."""
        if not self.env:
            return {}
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


def load(name):
    """Load a scenario by name, or from a folder path (the rig's tests)."""
    folder = Path(name) if Path(name).is_absolute() else ROOT / "scenarios" / name
    data = tomllib.loads((folder / "scenario.toml").read_text())
    prompts = {key: " ".join(text.split()) for key, text in data["prompts"].items()}
    tests = data.get("tests", {})
    return Scenario(
        data["name"], folder, prompts, data["defects"], data["regression"]["tests"],
        source=data.get("fixture"),
        setup=data["environment"].get("setup", []) if "environment" in data else None,
        command=tests.get("command", list(DEFAULT_COMMAND)),
        hidden_into=tests.get("hidden_into", "hidden"),
        visible=tests.get("visible", []),
        pristine=tests.get("pristine", []),
        timeout=tests.get("timeout_seconds", 120),
    )


def copy_repo(scenario, target):
    """Copy the fixture to `target` and commit it, so the diff is exact."""
    if scenario.unprepared():
        raise SystemExit(scenario.unprepared())
    shutil.copytree(scenario.fixture, target, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".git", ".rig-prepared"))
    git = ["git", "-C", str(target), "-c", "user.name=rig",
           "-c", "user.email=rig@localhost"]
    subprocess.run([*git, "init", "-q", "-b", "main"], check=True)
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
