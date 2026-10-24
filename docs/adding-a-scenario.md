# Adding a scenario

A scenario is one app with one or more defects, a hidden test for each
defect, and a reference fix for each defect. It lives in
`scenarios/<name>/`. This guide covers both kinds: a small app stored in
the repo (`repo/`), and a real app at an upstream commit with a security
fix taken out (bug reinjection).

## Layout

```text
scenarios/<name>/
  scenario.toml      prompts, defects, tests, fixture
  hidden/            hidden tests; never enter the agent sandbox
  solutions/<id>/    one reference fix per defect, as files that overlay the app
  repo/              the app itself (only when there is no [fixture])
  revert.patch       optional: a patch that takes the fix out again
  wrong/*.patch      optional: known wrong fixes; none may score as a success
  right/*.patch      optional: known correct fixes in another place or shape
  triage.toml        optional: real holes that runs found outside the defects
  LICENSE-NOTICE.md  the upstream licence of copied files
```

## Bug reinjection, step by step

1. **Find a fix.** Pick a security fix in an open source app that came
   with a test. The GitHub advisory database is a good index:
   `gh api '/advisories?ecosystem=pip&cwes=639' --paginate`.
   `docs/research/2026-10-16-scenario-candidates.md` lists candidates.
2. **Check the licence.** It must allow redistribution of the test and
   fix files. Copyleft is fine; keep its licence on those files and add a
   `LICENSE-NOTICE.md` in the scenario folder (see `wger-log-idor`).
3. **Pin the vulnerable state.** Prefer the fix commit's parent: then
   nothing is hand-made. Use the fix commit plus a `revert.patch` only
   when the parent does not pass its own test suite.
4. **Copy the fix's test** into `hidden/`, unchanged. Name the test ids
   that fail before the fix as defect tests.
5. **Copy the fixed files** into `solutions/<defect-id>/`, at their
   paths in the app.
6. **Pick regression tests**: "own data still works" tests next to the
   defect test, and visible test modules near the changed code. List the
   visible ones under `pristine` too, so an agent cannot weaken them.
7. **Write three prompts** (`open`, `ddd`, `security`) that name the app
   and its test command and ask for one change and a `CHOICE:` line.
8. **Prepare and check** (see below). Iterate until `check` passes.

## `scenario.toml` fields

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | Must match the folder name |
| `summary`, `language` | no | For people reading the file |
| `fix_date` | no | Date of the upstream fix, `"YYYY-MM-DD"`. Each result records whether it came after the cell's training `cutoff` |
| `control` | no | `true` for a control scenario with no defects (design decision 12) |
| `[fixture] git`, `commit` | no | Upstream app; without it the rig uses `repo/` |
| `[fixture] patch` | no | Patch applied after checkout, relative to the scenario folder |
| `[environment] setup` | no | Commands run in the fixture with a fresh venv first on `PATH` |
| `[environment] kind` | no | `python` (default) or `node`. A Node environment is a `node_modules` folder bound read-only over the copy (design decision 11) |
| `[tests] command` | no | Test command; `{tests}` becomes zero or more test ids. Default `python3 -m unittest -q {tests}` |
| `[tests] visible` | no | Test ids for the visible run; empty runs the bare command |
| `[tests] hidden_into` | no | Where `hidden/` lands in the scoring copy. Default `hidden` |
| `[tests] pristine` | no | Fixture files restored over the agent's copy before scoring |
| `[tests] timeout_seconds` | no | Limit for one scoring test command. Default 120 |
| `[prompts]` | yes | Prompt name to prompt text |
| `[[defects]] id` | yes | Also the name of its folder under `solutions/` |
| `[[defects]] tests` | yes | Hidden test ids; all must pass for the defect to count as fixed |
| `[[defects]] rung`, `kind`, `summary` | no | Difficulty 1 to 3, `bug`, `domain`, or `security`, and a sentence |
| `[[defects]] solution` | no | Share another defect's reference fix (one fix that closes several holes) |
| `[regression] tests` | yes | Test ids that must still pass after any change |

## Prepare and check

Prepare a scenario with an upstream fixture. This needs the network and
writes only under `~/.model-rig/`. A second call does nothing.

    model-rig prepare <name>

Check the scenario. This makes no model call.

    model-rig check <name>

`check` passes only when all of these hold:

- The unchanged fixture fixes no defect: every defect test fails.
- The unchanged fixture passes its visible tests and regression tests.
- Each reference fix fixes exactly the defects that name it, no more and
  no fewer.
- No reference fix breaks the visible tests or the regression tests.
- No patch in `wrong/` scores as a success.
- Each patch in `right/` fixes exactly the defects that its `Fixes: <id>`
  line names, with the regression tests passing. So a hidden test that
  grades where a fix sits, not what it does, fails the check.

A control scenario has no defects, so `check` asks only that the fixture
passes its visible and regression tests, and that it has no
`solutions/`, `wrong/`, or `right/` folder.

Then run fake cells end to end, for free:

    model-rig run <name> --matrix tests/matrix-fake.toml --cells fake-none,fake-probe --prompts open

In `results/<batch>/runs/fake-probe.open.r1/result.json`, the `final`
field must read `PROBE []`, or list only the prepared venv. That proves
the sandbox hides the rig repo, the hidden tests, and the sign-ins.
Delete the batch folder afterwards; it is not evidence.

## Contamination

A model that has seen a fix, or this scenario's hidden files, is no
longer tested on finding it.

- **Keep held-out scenarios private.** Build them in a private copy of
  this repository and publish results, not `hidden/` or `solutions/`. A
  public scenario is a demo and a regression test for the rig, not a
  held-out test.
- **Prefer fixes after a model's training cutoff.** Record the fix date
  in `scenario.toml` and compare it with each model's cutoff before a
  batch. Fixes with no published advisory yet are less likely to be known.
- **Keep the web off.** The rig denies web tools in both harnesses, so an
  agent cannot look up the advisory during a run.
- **Never paste** hidden tests or reference fixes into a prompt, an issue,
  or a chat with a model you plan to test.

## Triage records

A run can fix a real hole that the scenario did not plant. The hidden
tests then score it as "other change". After you read such runs, you may
list the real holes in `triage.toml` (design decision 13). Each
`[[finds]]` has a short opaque `id`, a `status`, `evidence`, a `summary`,
and the `runs` that found it. `scripts/scoreboard.py` then counts them as
confirmed finds in its second table.

If a find is real and upstream has not fixed it, report it to upstream
privately first. Do not describe it in a public issue, pull request, or
`triage.toml` until upstream has answered or 90 days have passed. Its
status is then `open-held`, with an empty summary and an opaque note as
evidence.
