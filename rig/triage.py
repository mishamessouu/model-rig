"""Load and check a scenario's triage record (design decision 13).

`scenarios/<name>/triage.toml` lists the real holes that runs found and
the scenario did not plant. A person, or an agent with evidence, writes it
after reading the runs. Each `[[finds]]` names the runs that found it, as
"<batch>/<run_id>", so the scoreboard can count them.

An open-held find carries no description: its summary is empty and its
evidence is an opaque note, until upstream discloses it or 90 days pass.
"""
import re
import tomllib
from pathlib import Path

from . import ROOT

FIXED, DISCLOSED, HELD = "fixed-upstream", "disclosed", "open-held"
NOT_A_BUG, HARDENING = "not-a-bug", "hardening"
STATUSES = (FIXED, DISCLOSED, HELD, NOT_A_BUG, HARDENING)
# A find with one of these statuses is a real hole. A run listed under it
# that kept the regression set passing is a confirmed find.
REAL = (FIXED, DISCLOSED, HELD)
KEYS = {"id", "status", "evidence", "summary", "runs", "held_since"}
# A short opaque id, such as "C3", so the id itself says nothing.
ID = re.compile(r"^[A-Z]{1,3}[0-9]{1,3}$")
# An upstream commit or an advisory id.
UPSTREAM = re.compile(r"\b[0-9a-f]{7,40}\b|\bGHSA(-[23456789cfghjmpqrvwx]{4}){3}\b")
# The only evidence an open-held find may carry: no words about the bug.
OPAQUE = re.compile(r"^(private report pending|private report sent \d{4}-\d{2}-\d{2}|not reported)$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def problems(name, root=ROOT):
    """Every problem in `scenarios/<name>/triage.toml`, as a list of
    messages. A scenario with no triage file has none."""
    path = Path(root) / "scenarios" / name / "triage.toml"
    if not path.is_file():
        return []
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        return [f"{path}: {error}"]
    out = []
    unknown = set(data) - {"finds"}
    if unknown:
        out.append(f"unknown top-level keys {sorted(unknown)}")
    seen = set()
    for number, find in enumerate(data.get("finds", []), 1):
        where = f"find {find.get('id', number)}"
        extra = set(find) - KEYS
        if extra:
            out.append(f"{where}: unknown keys {sorted(extra)}")
        missing = {"id", "status", "evidence", "summary", "runs"} - set(find)
        if missing:
            out.append(f"{where}: missing keys {sorted(missing)}")
            continue
        if not isinstance(find["id"], str) or not ID.match(find["id"]):
            out.append(f"{where}: id must be short and opaque, like 'C3'")
        if find["id"] in seen:
            out.append(f"{where}: id used twice")
        seen.add(find["id"])
        status, evidence, summary = find["status"], find["evidence"], find["summary"]
        if status not in STATUSES:
            out.append(f"{where}: status {status!r} is not one of {', '.join(STATUSES)}")
        if status == HELD:
            if summary:
                out.append(f"{where}: an open-held find has an empty summary "
                           "until it is disclosed or 90 days pass")
            if not OPAQUE.match(str(evidence)):
                out.append(f"{where}: an open-held find's evidence is an opaque note "
                           "('private report pending', 'private report sent "
                           "YYYY-MM-DD', or 'not reported')")
            if not DATE.match(str(find.get("held_since", ""))):
                out.append(f"{where}: an open-held find needs held_since = \"YYYY-MM-DD\"")
        else:
            if "held_since" in find:
                out.append(f"{where}: only an open-held find has held_since")
            if not summary:
                out.append(f"{where}: a {status} find needs a summary")
        if status in (FIXED, DISCLOSED) and not UPSTREAM.search(str(evidence)):
            out.append(f"{where}: a {status} find's evidence names an upstream "
                       "commit or a GHSA id")
        runs = find["runs"]
        if not runs:
            out.append(f"{where}: lists no runs")
        if len(set(runs)) != len(runs):
            out.append(f"{where}: lists a run twice")
        for run in runs:
            batch, _, run_id = str(run).partition("/")
            if not batch.endswith("-" + name) or not run_id:
                out.append(f"{where}: {run!r} is not '<batch>/<run_id>' of {name}")
            elif not (Path(root) / "results" / batch / "runs" / run_id / "result.json").is_file():
                out.append(f"{where}: no result for run {run}")
    return out


def load(name, root=ROOT):
    """The finds of a scenario, or [] when it has no triage file. Exits
    with every problem when the file is not valid, so a count never rests
    on a bad record."""
    found = problems(name, root)
    if found:
        raise SystemExit(f"{name}/triage.toml:\n  " + "\n  ".join(found))
    path = Path(root) / "scenarios" / name / "triage.toml"
    return tomllib.loads(path.read_text()).get("finds", []) if path.is_file() else []


def real_finds(finds):
    """"<batch>/<run_id>" -> ids of the real finds that list the run."""
    out = {}
    for find in finds:
        if find["status"] in REAL:
            for run in find["runs"]:
                out.setdefault(run, []).append(find["id"])
    return out


def confirmed(result, batch, finds):
    """Ids of the real finds a run confirms: the run is listed under them,
    it kept the regression set passing, and it ended without an agent
    error or a timeout, the same terms as a planted success."""
    if result["error"] or result.get("timed_out") or not result["regression_pass"]:
        return []
    return real_finds(finds).get(f"{batch}/{result['run_id']}", [])
