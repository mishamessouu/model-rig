# Cloud review, 2026-10-25

A review of model-rig as a benchmark method: scoring, contamination,
the statistics in the reports, and whether the published results follow
from the data in `results/`. No model ran. Every check used the fake
agent or the stored `result.json` files.

- Commit reviewed: `5113bf6` ("Update the scenario table for the new
  public batches"), `origin/main`.
- Line numbers below refer to that commit.

## Test runs

    python3 -m unittest -v tests.test_rig tests.test_sources
    python3 -m rig check booking-ladder

| When | Result |
|---|---|
| Before, without bwrap | `Ran 50 tests`, `FAILED (errors=16)`: "bubblewrap (bwrap) is not installed" |
| Before, with bwrap installed | `Ran 79 tests`, `OK`; `scenario OK` |
| Before, checkout copied to `/root` | `test_sandbox_hides_rig_sign_in_and_sockets` fails (finding 1) |
| After | `Ran 83 tests`, `OK`; `scenario OK`. Also `OK` with the checkout under `/root`. |

## Findings

| # | Where | Severity | Status |
|---|---|---|---|
| 1 | `rig/sandbox.py:17`, `rig/sandbox.py:41-45` | blocker | fixed |
| 2 | `scripts/scoreboard.py:62`, `README.md:37`, `README.md:79` | major | fixed |
| 3 | `README.md:73-81` | major | fixed |
| 4 | `results/20261020T101406Z-labelstudio-orm-traversal/runs/claude-opus-medium.open.r2` | minor | not fixed, needs the owner |
| 5 | `scripts/scoreboard.py:47-78`, `README.md:54-61` | minor | not fixed, now named in the README |
| 6 | `tests/test_rig.py`, `tests/test_sources.py` | minor | not fixed |

### 1. The sandbox shows the state folder and the rig repo outside `/home`

`EMPTIED` lists `/home`, `/tmp`, and a few data folders. It does not list
`/root`, `/opt`, or any other place, and the rig's own folders were never
hidden by name. When the rig runs as root, `STATE` is
`/root/.model-rig`, and the agent sandbox can read it. The same holds
for a checkout under `/root`, `/opt`, or `/workspace`.

Failure scenario: as root, with `MODEL_RIG_HOME=/root/demo/state` and
`MODEL_RIG_ROOT=/root/demo/repo`, a sandboxed `cat` printed a dummy
`claude-config/.credentials.json` and a file under
`scenarios/x/hidden/`. So an agent could read the sign-in masters, the
hidden tests and reference fixes (AGENTS.md: they "never enter an agent
sandbox"), other agents' diffs under `results/`, and the work folders of
a concurrent batch, whose scoring copy holds the hidden tests. The repo's
own probe test fails when the checkout sits under `/root`.

Fix: `sandbox.hidden_paths()` names the rig checkout, the state folder,
and home, unless an emptied folder already holds them. `command()` puts
a tmpfs on each before any bind, so the run's own folders (the run
folder, the venv) come back. Tests: `SandboxHideTest`, three tests. The
integration test runs only when home is outside the emptied folders, as
for root.

### 2. The scoreboard prices an unpriced run at zero

`planted_table` summed `report.run_cost(r, sheet) or 0`. `run_cost`
returns None for a whole run when one model in it is not on the sheet.
So the run's priced tokens also counted as zero. `rig/report.py:116`
states the repo's rule: "One unpriced run makes the cell's cost unknown,
not a partial mean."

Failure scenario: `claude-opus-medium.open.r2` in the labelstudio batch
used `claude-opus-5-5` and `claude-opus-5`. The sheet lists only the
first, so the run counted 0 credits and the README showed 46 credits per
success for Opus. The run's priced part alone is 22.1 credits.

Fix: a cell with an unpriced run shows n/a, as in a batch report. Test:
`ScoreboardTest.test_one_unpriced_run_makes_the_cell_cost_unknown`
showed `5` before and `n/a` after. The README table now shows n/a for
Opus and a note: at least 46 credits per success from the priced runs.

### 3. Separability argued from overlapping intervals

The README said five cells "are not separable: their intervals overlap."
Overlapping 95% intervals do not show that two rates are equal. On the
published totals, Fisher's exact test gives p = 0.024 for Astra medium
(34 of 36) against Sonnet 5.5 (26 of 36). That pair is separable at 0.05
without a correction. The README's own batch text says to rank cells
"only with a test on the runs, such as Fisher's exact test."

Check: over the 15 pairs of the six full cells, with a Holm correction,
the Astra and Sonnet pair has p = 0.24, and every pair with Luna medium
has p below 0.0001. So the conclusion holds, but only with the test and
the correction. Fix: the README now states the test, the correction, the
closest pair, and that the test treats runs as independent and pools
scenarios. The "expensive cells bought no measurable gain" bullet now
says Astra and Sonnet come closest.

### 4. One Opus run also used a second model (not fixed)

The run in finding 2 reports usage for `claude-opus-5` as well as
`claude-opus-5-5`, about two thirds of its tokens. It scored a success,
and that success counts for the Opus 5.5 cell. The rig records the
usage but does not flag a run that used a model other than its cell's.
Whether such a run belongs to the cell, and what `claude-opus-5` costs,
needs the owner and a primary price source. I did not add a price.

### 5. Pooled totals mix scenario weights and prompts (not fixed)

The "All" row and its Wilson interval pool runs across scenarios as one
binomial. Success varies a lot by scenario (mealie: Opus 1 of 6, Sol 6
of 6), so the pooled interval is narrower than the scenario-to-scenario
spread warrants. The four Sol and Luna cells also carry three `ddd` runs
on wger, which the 36-run cells lack. The README says both facts. A
stratified or per-scenario test would be the stronger comparison. The
README now says the pooled test is rough.

### 6. The test suite errors without bwrap (not fixed)

Without `bwrap`, 16 tests error in `setUpClass` or mid-test with a
RuntimeError. The README lists bwrap as a requirement and CI installs
it, so this is a setup step, not a defect. A skip with the reason would
read better.

## Claims checked and found to follow from the data

- 240 runs in the cross-scenario table, and every cell count in it.
- Every Wilson interval in the README, including 61% to 100% for 6 of 6
  and 30% to 90% for 4 of 6.
- 68 misses: 57 changed something other than a planted hole with the
  regression set passing, and 11 broke the regression set, 7 of them
  with a planted fix. No agent error or timeout.
- The wger-log-idor table: every success count, interval, mean token
  count, mean credits, and credits per success.
- The wger Fisher values: p = 1.0 and 0.45 for Opus against Astra and
  Sol, and p = 0.015 for Opus against Luna medium.
- Mealie: 4 of the 6 Opus runs broke the regression set.

## Refuted candidates

- A defect with an empty test list would always count as fixed.
  `rig check` refuses it, because the baseline then "already passes" it.
- A hidden folder that also exists in the fixture keeps the agent's
  extra files. That is documented in `rig/score.py:39-41`.
- Codex tokens: cached input moves out of `input`, and the sheet prices
  it as cache read. Correct for the OpenAI usage format.

## Runtime restore follow-up

The new dynamic masks also hide Python and Node installs. Both restore
helpers now check `EMPTIED` and `sandbox.hidden_paths()`. They restore
the named install and its resolved target. They reject an install that
contains the checkout, state folder, or home, including through a link.
This preserves decisions 7 and 11 without restoring private parents.

`RuntimeRestoreTest` starts Python and Node under each dynamic mask.
It checks that private markers stay hidden and the environment stays
visible. Both startup tests fail with the original helpers, with six
failed subtests. All four new tests pass with the fix.

The follow-up checks use no real model. Run the full suite with
`python3 -m unittest tests.test_rig tests.test_sources`: `Ran 87 tests`,
`OK (skipped=1)`. The skipped test requires home outside `EMPTIED`.
Run `python3 -m rig check booking-ladder`: `scenario OK`.
The outside-home reproduction shows Python exits `0,0,0` and hidden
private markers. Its original assertion expects the old `0,1,0`
failure and therefore fails. A copy expecting `0,0,0` passes.

The fix and regression tests are complete. Integration can continue on
this branch. Real harness startup remains unverified, as described below.

## Not verified

- No real model ran, and no upstream fixture was prepared, so the
  sandbox fix is tested with the fake agent only. A real Claude Code or
  Codex install under a hidden home may need its support files bound in.
  That was already true for a user under `/home`.
- Whether an editable install of the project in a prepared venv (for
  example labelstudio's `uv sync` without `--no-install-project`) points
  the agent at a copy outside its working copy.
- The price sheet values against GitHub's page.
- The triage records and held scenarios, which are not in this repo.
