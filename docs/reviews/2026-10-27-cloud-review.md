# Cloud review, 2026-10-27

A review of the changes since 2026-10-25 and of the publish path. No
model ran. Every check used the fake agent, a local bwrap sandbox, or
the stored `result.json` files.

- Commit reviewed: `093eab2` ("Publish the high-effort, Fable 5.1, and
  first Terra batches"), `origin/main`.
- Commits in scope: `e1db75a`, `986f17c`, `ed1d41e` (merge), `093eab2`.
- Line numbers below refer to `093eab2`.

## Test runs

    python3 -m unittest -v tests.test_rig tests.test_sources
    python3 -m rig check booking-ladder

| When | Result |
|---|---|
| Before, without bwrap | `Ran 62 tests`, `FAILED (errors=40)`: "bubblewrap (bwrap) is not installed" |
| Before, with bwrap installed | `Ran 91 tests`, `OK`; `scenario OK` |
| After | `Ran 93 tests`, `OK`; `scenario OK` |

## Findings

| # | Where | Severity | Status |
|---|---|---|---|
| 1 | `rig/scenario.py:130-171` | major | fixed |
| 2 | `docs/design.md:354-356` | minor | fixed |
| 3 | `README.md:75-77` | minor | fixed |
| 4 | `results/*/runs/claude-fable-5-1-*` | minor | not fixed, needs the owner |
| 5 | `scripts/publish-results.py`, HOLDS | not reviewable | not in this repo |

### 1. A runtime link in a shared folder restores that whole folder

`base_interpreter` and `node_install` took the folder two levels above
the executable the environment names, and bound it into the sandbox
when it sat under a masked folder. They never checked that this folder
is the runtime install.

Failure scenario: `python3` on PATH is a link in `~/.local/bin`, as with
uv's default executable links. `rig prepare` runs `python3 -m venv`, so
the venv records `home = ~/.local/bin`. The rig then restores all of
`~/.local`. A sandboxed `cat ~/.local/share/keyrings/login.txt` printed
the file. The same holds for `node` linked from `~/.local/bin`. The
sandbox docstring says an agent "cannot read ... the person's files".
`~/.local/share` holds app data and some tools' credentials.

Fix: `_masked_install` now takes the executable the environment names.
It restores the named folder only when the real executable sits inside
it, directly or through a link (uv and nvm installs). Otherwise it
restores the one link and the install folder of its target. Tests: the
two startup tests in `RuntimeRestoreTest` now use a shared folder with
a link and a private marker. They fail before the fix (six subtests:
the whole folder came back) and pass after. Two new tests keep a uv or
nvm style install restored whole.

Residual: a runtime built with `--prefix=$HOME/.local` holds its real
executable in `~/.local/bin`, so all of `~/.local` still comes back. A
fix would restore only `bin/<exe>` and the runtime's `lib` folders. I
did not build it.

### 2. Decision 15 says a timed-out run costs zero

`docs/design.md:354-356` says the scoreboard "counts it as zero; that
understates the cost of a slow cell." The code does not.
`prices.cost` returns None for a run with no usage, and the scoreboard
then shows n/a for the cell. The README shows n/a for both Fable cells.
Fix: the decision now says the cost is unknown, the cell shows n/a, and
only a lower bound from the priced runs is known.

### 3. The README gives the wrong reason for Fable medium's n/a

The README said Fable shows n/a because a run that "stops with an agent
error records no tokens". No Fable medium run timed out. Its three
refused labelstudio runs recorded tokens, and each also used
`claude-opus-5`, which the sheet does not list. One Fable high wger run
(`claude-fable-5-1-high.open.r2`) also used `claude-opus-5`. Fix: the
README now names both causes. The lower bounds stay true: the priced
parts give about 119 credits per success at medium and 192 at high.

### 4. Fable runs also used Opus 5 (not fixed)

The three refused Fable medium runs report usage for `claude-opus-5`,
and their error reads "Opus 5's safeguards flagged this message". So a
second model took part in those runs. The 2026-10-25 review raised the
same thing for one Opus run (its finding 4). Whether such a run belongs
to its cell, and what `claude-opus-5` costs, needs the owner.

### 5. The publish path is not in this repo

The task named `scripts/publish-results.py` and HOLDS. Neither exists in
this repository. Commit `093eab2` says the batches were "copied with
the lab's scripts/publish-results.py". So I could not review the
script or its hold list. Nothing in this repository checks a batch
against the disclosure hold before it lands in `results/`.

I checked what was published instead. Over the 13 new batches (705
files, agent logs unzipped):

- No API key, token, JWT, or private key pattern. The only `Bearer`
  value is `sk-decoy-provider-key`, a decoy.
- No home path with a user name. Paths show as `~/.model-rig/...`.
- No email but test fixtures (`test@example.com` and similar).
- `hidden/test_defects.py` shows only in booking-ladder scoring output,
  a toy scenario, after the run.
- Every batch is for a scenario in `scenarios/`. No held scenario name.
- Nine runs changed code with no planted fix. Each touched the file of
  the planted hole or only a test, so I read them as partial fixes, not
  new holes. A person should still triage them (decision 13).

## Claims checked and found to follow from the data

- The README results table matches `python3 scripts/scoreboard.py --skip
  wger-gym-access` output, row for row.
- 82 of 372 runs missed: 62 other change, 11 fixed but broke the
  regression set, 4 broke it with no fix, 3 refused, 2 timed out.
- The paired values in the README: Sonnet high minus Sonnet medium
  +23% (0% to +50%), minus Opus high +20% (0% to +50%), and Opus high
  minus Opus medium +3% (-13% to +20%).
- No cell did better than Sonnet 5.5 high on any shared scenario.
- No two batches hold the same scenario and cell, so "newest batch per
  cell" drops no runs today.

## Refuted candidates

- The bootstrap percentile indexes 50 and 1949 of 2000 draws are
  symmetric. Not an off-by-one.
- An upper bound of exactly +0% reads "not separable". That is right for
  a percentile interval that holds zero, and the README says each
  interval touches zero.
- `rig/rescore.py` could drop the new `refused` key. `report.refused`
  also matches the error text, so the count holds.

## Not verified

- `scripts/publish-results.py` and its hold list (finding 5).
- `config/matrix-fable-60m.toml`, named in decision 15, is not in this
  repo. I could not check that its cell name differs from the main
  cells, as the scoreboard needs.
- A real Claude Code or Codex start under the fixed restore. Tests use
  the fake agent and system binaries.
- The new prices for Terra, Fable 5.1, and Haiku 5.5 against their
  sources.
