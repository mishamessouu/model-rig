"""Prepare a scenario on the host, with network: fetch its upstream fixture
and build its environment (a Python venv or a Node node_modules) under
the rig state folder.

Each part gets a `.rig-prepared` stamp that names its inputs, written
last. A matching stamp skips the part; a changed input builds it again.
The fixture is built in a side folder and renamed into place. The venv is
built at its final path, because a venv writes that path into its scripts.
A setup command may name a file in the scenario folder as
`{scenario}/<file>`, such as a lock file the scenario keeps. The stamp
holds that file's hash, so a changed lock builds the venv again. A Node
stamp also holds the node version and the fixture's package manifests.
"""
import functools
import hashlib
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

from . import sandbox
from . import scenario as scenarios

# Flush, so messages keep their place among the subprocess output.
say = functools.partial(print, flush=True)
# In a setup command, this becomes the scenario folder.
SCENARIO = "{scenario}"


def _stamp(scenario, part):
    inputs = {"part": part}
    if part == "fixture":
        inputs.update(git=scenario.source["git"], commit=scenario.source["commit"])
        patch = scenario.source.get("patch")
        if patch:
            inputs["patch"] = hashlib.sha256(
                (scenario.folder / patch).read_bytes()).hexdigest()
    else:
        inputs["setup"] = scenario.setup
        if scenario.source:
            inputs["commit"] = scenario.source["commit"]
        named = sorted({part[len(SCENARIO) + 1:] for line in scenario.setup
                        for part in shlex.split(line)
                        if part.startswith(SCENARIO + "/")})
        if named:
            inputs["files"] = {name: hashlib.sha256(
                (scenario.folder / name).read_bytes()).hexdigest() for name in named}
        if scenario.kind == "node":
            # Only Node stamps get these keys, so a Python venv's stamp,
            # and the venvs already built, stay as they were.
            inputs["kind"] = "node"
            inputs["node"] = _node_version()
            inputs["manifests"] = {name: hashlib.sha256(
                (scenario.fixture / name).read_bytes()).hexdigest()
                for name in scenarios.NODE_MANIFESTS
                if (scenario.fixture / name).is_file()}
    return json.dumps(inputs, sort_keys=True) + "\n"


def _current(folder, stamp):
    marker = folder / ".rig-prepared"
    return marker.exists() and marker.read_text() == stamp


def _fresh(folder):
    building = folder.with_name(folder.name + ".building")
    shutil.rmtree(building, ignore_errors=True)
    building.parent.mkdir(parents=True, exist_ok=True)
    return building


def _publish(building, folder, stamp):
    (building / ".rig-prepared").write_text(stamp)
    shutil.rmtree(folder, ignore_errors=True)
    os.replace(building, folder)


def fixture(scenario, echo=say):
    folder, stamp = scenario.fixture, _stamp(scenario, "fixture")
    if _current(folder, stamp):
        echo(f"fixture current: {folder}")
        return folder
    building = _fresh(folder)
    source = scenario.source
    git = ["git", "-C", str(building)]
    building.mkdir()
    subprocess.run([*git, "init", "-q"], check=True)
    echo(f"fetching {source['git']} at {source['commit']}")
    subprocess.run([*git, "fetch", "-q", "--depth", "1", source["git"],
                    source["commit"]], check=True)
    subprocess.run([*git, "-c", "advice.detachedHead=false", "checkout", "-q",
                    "FETCH_HEAD"], check=True)
    if source.get("patch"):
        patch = (scenario.folder / source["patch"]).resolve()
        subprocess.run([*git, "apply", "--whitespace=nowarn", str(patch)], check=True)
    _publish(building, folder, stamp)
    echo(f"fixture ready: {folder}")
    return folder


def _node():
    """The host's `node`, resolved, or an error that says what to do."""
    found = shutil.which("node")
    if found is None:
        raise SystemExit("node is not installed. A Node scenario needs it on PATH.")
    return Path(found).resolve()


def _node_version():
    return subprocess.run([str(_node()), "--version"], capture_output=True,
                          text=True, check=True).stdout.strip()


def _node_folder(scenario, folder):
    """A Node environment: `bin/` links to the host's node, npm, and npx,
    and the fixture's package manifests sit next to the coming
    node_modules. The setup commands (such as `npm ci`) run here."""
    node = _node()
    (folder / "bin").mkdir(parents=True)
    for name in ("node", "npm", "npx"):
        tool = node.parent / name
        if tool.exists():
            (folder / "bin" / name).symlink_to(tool)
    for name in scenarios.NODE_MANIFESTS:
        if (scenario.fixture / name).is_file():
            shutil.copy2(scenario.fixture / name, folder / name)


def environment(scenario, echo=say):
    """A venv, or a Node environment (decision 11). A venv's setup commands
    run in the fixture, with the venv first on PATH, so `pip` and `uv`
    mean the venv's own tools. A Node environment's run in its own folder,
    so node_modules lands there and never in the fixture."""
    folder, stamp = scenario.env, _stamp(scenario, "environment")
    if _current(folder, stamp):
        echo(f"environment current: {folder}")
        return folder
    # Build at the final path, because a venv writes its own path into its
    # scripts. The stamp comes last, so a failed build never reads as done.
    shutil.rmtree(folder, ignore_errors=True)
    folder.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PATH": f"{folder}/bin:{os.environ.get('PATH', sandbox.PATH)}"}
    if scenario.kind == "node":
        _node_folder(scenario, folder)
        cwd = folder
    else:
        subprocess.run(["python3", "-m", "venv", str(folder)], check=True)
        env.update(VIRTUAL_ENV=str(folder), UV_PROJECT_ENVIRONMENT=str(folder))
        cwd = scenario.fixture
    for line in scenario.setup:
        echo(f"setup: {line}")
        argv = [part.replace(SCENARIO, str(scenario.folder))
                for part in shlex.split(line)]
        argv[0] = shutil.which(argv[0], path=env["PATH"]) or argv[0]
        subprocess.run(argv, cwd=cwd, env=env, check=True)
    (folder / ".rig-prepared").write_text(stamp)
    echo(f"environment ready: {folder}")
    return folder


def prepare(scenario, echo=say):
    if not scenario.source and scenario.env is None:
        echo(f"{scenario.name}: nothing to prepare")
        return
    if scenario.source:
        fixture(scenario, echo)
    if scenario.env is not None:
        environment(scenario, echo)
