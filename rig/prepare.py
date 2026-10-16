"""Prepare a scenario on the host, with network: fetch its upstream fixture
and build its Python environment under the rig state folder.

Each part gets a `.rig-prepared` stamp that names its inputs, written
last. A matching stamp skips the part; a changed input builds it again.
The fixture is built in a side folder and renamed into place. The venv is
built at its final path, because a venv writes that path into its scripts.
"""
import functools
import hashlib
import json
import os
import shlex
import shutil
import subprocess
from . import sandbox

# Flush, so messages keep their place among the subprocess output.
say = functools.partial(print, flush=True)


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


def environment(scenario, echo=say):
    """A venv. Its setup commands run in the fixture, with the venv first
    on PATH, so `pip` and `uv` mean the venv's own tools."""
    folder, stamp = scenario.env, _stamp(scenario, "environment")
    if _current(folder, stamp):
        echo(f"environment current: {folder}")
        return folder
    # Build at the final path, because a venv writes its own path into its
    # scripts. The stamp comes last, so a failed build never reads as done.
    shutil.rmtree(folder, ignore_errors=True)
    folder.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["python3", "-m", "venv", str(folder)], check=True)
    env = {**os.environ, "VIRTUAL_ENV": str(folder),
           "UV_PROJECT_ENVIRONMENT": str(folder),
           "PATH": f"{folder}/bin:{os.environ.get('PATH', sandbox.PATH)}"}
    for line in scenario.setup:
        echo(f"setup: {line}")
        argv = shlex.split(line)
        argv[0] = shutil.which(argv[0], path=env["PATH"]) or argv[0]
        subprocess.run(argv, cwd=scenario.fixture, env=env, check=True)
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
