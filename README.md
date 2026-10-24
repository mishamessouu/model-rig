# model-rig

Which coding agent gives a correct fix at the lowest cost? model-rig runs
Claude Code and Codex on real code with real, reverted security fixes, and
scores what they chose, whether the fix works, what broke, and the cost
per successful fix.

[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Tests](https://github.com/mishamessouu/model-rig/actions/workflows/test.yml/badge.svg)](https://github.com/mishamessouu/model-rig/actions/workflows/test.yml)

## Results

<!-- RESULTS:START -->
### All public scenarios: 240 runs, 2026-10-16 to 2026-10-24

Six real apps, each with a real security fix taken out again. Each
cell got two prompts: "find the improvement that matters most" (open)
and "find a security weakness" (security). Each prompt ran three times,
so a cell has six runs per scenario. Hidden tests decide success.

A **success** is a run that fixed at least one planted hole, broke no
regression test, and ended without an agent error or a timeout. A run
that changed something else counts as a miss, even when that change was
good.

| Scenario | claude-opus-medium | claude-sonnet-5-5-medium | codex-sol-high | codex-luna-medium | codex-sol-medium | codex-luna-high | codex-astra-medium | codex-astra-high |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| changedetection-processor-traversal | 6/6 | 5/6 | 6/6 | 1/6 | 6/6 |  | 6/6 |  |
| inventree-attachment-access | 4/6 | 6/6 | 6/6 | 4/6 | 6/6 |  | 6/6 |  |
| labelstudio-orm-traversal | 6/6 | 3/6 | 6/6 | 1/6 | 6/6 |  | 6/6 |  |
| mealie-zip-import-idor | 1/6 | 2/6 | 6/6 | 0/6 | 6/6 |  | 6/6 |  |
| mlflow-graphql-permission | 6/6 | 4/6 | 6/6 | 0/6 | 6/6 |  | 5/6 |  |
| wger-log-idor | 6/6 | 6/6 | 4/9 | 1/9 | 5/9 | 2/9 | 5/6 | 5/6 |
| **All** | **29/36** | **26/36** | **34/39** | **7/39** | **35/39** | **2/9** | **34/36** | **5/6** |
| 95% interval | 65% to 90% | 56% to 84% | 73% to 94% | 9% to 33% | 76% to 96% | 6% to 55% | 82% to 98% | 44% to 97% |
| Credits per success | 46 | 16 | 33 | 7 | 22 | 8 | 122 | 160 |

Generated with `python3 scripts/scoreboard.py --skip wger-gym-access`.
Each scenario uses the newest batch that holds the cell. wger-gym-access
is left out of the table: only its Claude batch is public yet, and half
a scenario would favour one harness.

| Cell | Harness | Model | Effort |
|---|---|---|---|
| `claude-opus-medium` | Claude Code | Claude Opus 5.5 | medium |
| `claude-sonnet-5-5-medium` | Claude Code | Claude Sonnet 5.5 | medium |
| `codex-sol-high`, `codex-sol-medium` | Codex | GPT-6.1 Sol | high, medium |
| `codex-luna-high`, `codex-luna-medium` | Codex | GPT-6 Luna | high, medium |
| `codex-astra-high`, `codex-astra-medium` | Codex | GPT-6 Astra | high, medium |

How to read it:

- **Both prompts are combined.** A cell shows its successes over its
  runs, open and security together. On wger-log-idor, the four Sol and
  Luna cells also ran a design prompt (`ddd`) three times, so they show
  9 runs. Those runs count too.
- **The interval is a 95% Wilson interval** for the success rate. It
  is wide with few runs. Six runs per scenario give 61% to 100% for 6 of
  6, and 30% to 90% for 4 of 6. So treat one scenario row as a hint, and
  use the totals to compare cells.
- **Credits per success** is the cost of all the cell's runs divided by
  its successes. It prices the stored tokens with the GitHub Copilot
  price sheet in `config/prices.toml`, read from GitHub's Copilot models
  and pricing page on 2026-10-20. One credit is 0.01 USD, so 24 credits
  is about 0.24 USD. It is one comparable unit, not your bill.
- **Two cells ran on one scenario only.** `codex-luna-high` and
  `codex-astra-high` ran on wger-log-idor only. Do not compare their
  totals with the others.

What it shows:

- **The cells that ran all six scenarios split into two groups.**
  Sol medium (35 of 39), Astra medium (34 of 36), Sol high (34 of 39),
  Opus (29 of 36), and Sonnet 5.5 (26 of 36) are not separable: their
  intervals overlap. Luna medium (7 of 39, 9% to 33%) is clearly lower
  than all five.
- **The expensive cells bought no measurable gain.** In the top group,
  credits per success ran from 16 (Sonnet 5.5) and 22 (Sol medium) to 46
  (Opus) and 122 (Astra medium), a factor of about 8. The success rates
  of those cells are not separable.
- **Luna medium is the cheapest per success, at 7 credits, but it
  misses most runs.** You only know which run worked if you have a test
  that tells you.
- **We saw no effect of effort for Sol:** 35 of 39 at medium and 34 of
  39 at high, for 22 and 33 credits per success.
- **The scenarios differ more than the totals show.** On mealie, Opus
  succeeded in 1 of 6 runs and Sonnet 5.5 in 2 of 6, while Sol and Astra
  succeeded in 6 of 6. Four of the Opus runs on mealie broke the
  regression set.
- **68 of the 240 runs missed.** 57 changed something other than a
  planted hole. 11 broke the regression set, and 7 of those 11 had also
  fixed a planted hole. No run ended in an agent error or a timeout.

The 2026-10-16 wger batch ran before the provider-only network (see
[Fairness rules](#fairness-rules)). Every later batch ran behind it.

#### Unplanted real finds

In lab triage, agents found real holes that the scenarios did not plant.
Upstream fixed some of them later. Others were reported to upstream
privately. The score above counts none of them: a run that closed such a
hole counts as a miss. The results of the scenarios with an unfixed find
are held until disclosure, so they are not in this repository. Design
decision 13 in [`docs/design.md`](docs/design.md) describes the triage
record.

### wger-log-idor: 62 runs, 2026-10-16 to 2026-10-20

A real Django app of 36k lines with a real security fix reverted: two
missing owner checks. Same two prompts, three runs per cell.

| Model | Fixed the planted hole (open prompt) | Fixed the planted hole (security prompt) | Both prompts, with 95% interval | Mean tokens per run | Mean Copilot credits per run | Credits per successful fix |
|---|---:|---:|---:|---:|---:|---:|
| Claude Opus 5.5 (medium) | 3/3 | 3/3 | 6/6 (61 to 100%) | 0.90M | 50.9 | 50.9 |
| Claude Sonnet 5.5 (medium) | 3/3 | 3/3 | 6/6 (61 to 100%) | 0.19M | 8.6 | 8.6 |
| GPT-6 Astra (high) | 2/3 | 3/3 | 5/6 (44 to 97%) | 0.77M | 133.0 | 159.6 |
| GPT-6 Astra (medium) | 2/3 | 3/3 | 5/6 (44 to 97%) | 0.60M | 108.1 | 129.8 |
| GPT-6.1 Sol (high) | 2/3 | 2/3 | 4/6 (30 to 90%) | 0.95M | 24.8 | 37.3 |
| GPT-6.1 Sol (medium) | 1/3 | 3/3 | 4/6 (30 to 90%) | 0.82M | 20.4 | 30.6 |
| GPT-6 Luna (high) | 1/3 | 1/3 | 2/6 (10 to 70%) | 1.41M | 2.1 | 6.3 |
| GPT-6 Luna (medium) | 0/3 | 1/3 | 1/6 (3 to 56%) | 0.63M | 1.1 | 6.5 |
| Claude Sonnet 5 (medium) | 0/1 | 1/1 | 1/2 (9 to 91%) | 4.09M | 127.7 | 255.5 |

Token and credit columns cover the open and security runs only. Sonnet
5.5 ran on 2026-10-20, behind the provider-only network. Every other row
ran on 2026-10-16 and 17. Sonnet 5 was the model behind the `sonnet`
alias then; Sonnet 5.5 replaced it in the matrix.

What it shows:

- **On real code, the models do not agree.** Success ran from 6 of 6
  to 1 of 6. On a 250-line toy app, both models we tried picked the
  same fix.
- **Opus and Sonnet 5.5 fixed the hole in 6 of 6 runs,** also with no
  security hint. With 6 runs per model, Opus, Astra (5 of 6), and Sol
  (4 of 6) cannot be told apart (Fisher's exact test, p = 1.0 and 0.45).
  Only Luna at medium effort was clearly lower (1 of 6, p = 0.015, before
  any correction for the number of comparisons).
- **Sonnet 5.5 was the cheapest cell that never missed,** at 8.6
  credits per success, with the fewest tokens per run (0.19M).
- **We saw no effect of effort:** Sol 4 and 4 of 6, Astra 5 and 5 of 6,
  Luna 2 and 1 of 6. Six runs per level cannot show a small effect.
- **No run failed the regression set:** 10 of wger's own test modules,
  restored before scoring, and 5 checks that owners can still use
  their own data. The full visible suite also passed in every run, but
  agents can edit those test files.
- **Runs used 0.1M to 5.3M tokens,** almost all of it the same context
  sent again on each turn. The Claude models ran in Claude Code and the
  GPT models in Codex, so token counts differ by harness as well as by
  model.
- **A miss is not always a wasted run.** At least 10 of the 27 misses
  in the 2026-10-16 batch fixed another plausible security problem,
  such as stale cached routine data or an open redirect. Nobody has
  verified those, and the score counts only the planted hole.

Limits: one app, 3 runs per cell, and Sonnet 5 ran once per prompt.
Harness and model are mixed, and "medium" effort means different
settings in Claude Code and Codex. 12 more Codex runs used a
design-focused prompt; one of them (`codex-sol-medium.ddd.r1`) fixed
the hole. With those runs counted, credits per successful fix are 58.8
for Sol high, 35.8 for Sol medium, 8.0 for Luna high, and 9.4 for Luna
medium. The cross-scenario table above counts them.

Scoring changes after the first runs. Each change was followed by a
rescore of every run, and each run that changed result is named here:

- 2026-10-16: the day and next_log holes became defects of their own,
  after a Sonnet run fixed the day hole and scored as "none".
- 2026-10-17: a refusal may be HTTP 400, 403, or 404, if nothing is
  saved. Upstream's tests demanded 403. Two runs that refused with 400
  became successes: `codex-astra-high.open.r2` and
  `codex-sol-medium.ddd.r1`.
- 2026-10-18: an audit wrote three wrong fixes that passed the hidden
  tests. The next_log hole is no longer a defect, because the unfixed
  code already drops a foreign next_log and only the status code
  differed. Each defect now also needs an update (PATCH) refused, and
  the regression set checks a non-staff owner too. The three wrong
  fixes are kept in `scenarios/wger-log-idor/wrong/`, and `rig check`
  fails if one of them scores as a success. No success or regression
  result changed.

#### Is wger real production code?

wger is a mature open-source app, not a demo. Figures from 2026-10-17:

| Signal | wger |
|---|---|
| Age and activity | Started 2013; 1,330 commits in the last 12 months; releases 2.5, 2.6, 2.7 in 2026 |
| People | 362 contributors, 7,100 GitHub stars, 1,040 forks |
| Size at the pinned commit | 35,573 lines of app code in 344 files and 14 Django apps |
| Tests | About 1,400 tests, 21,532 lines of test code (0.61 test lines per app line) |
| Structure | Standard Django and DRF layers: models, views, API viewsets, serializers, templates |
| Checks in CI | Unit tests, ruff lint and format, CodeQL security scanning |
| Lint at the pinned commit | 187 ruff findings with the project's own rules, about 5 per 1,000 lines, mostly unused imports and long lines |
| Security process | Published advisories with fixes and regression tests ([OpenSSF Scorecard](https://securityscorecards.dev/viewer/?uri=github.com/wger-project/wger) 5.2/10: strong on maintenance, SAST, and licence; weak on branch protection and pinned dependencies) |

So the defect sits in code that many people have read, tested, and
shipped. Its own test suite did not catch it, and the advisory credits
a reporter. That is the kind of bug the benchmark is about.

Full reports, with every diff and log:
[`results/20261016T205957Z-wger-log-idor/report.md`](results/20261016T205957Z-wger-log-idor/report.md)
and
[`results/20261020T080644Z-wger-log-idor/report.md`](results/20261020T080644Z-wger-log-idor/report.md).
<!-- RESULTS:END -->

Each batch folder under [`results/`](results/README.md) holds every
run's diff, log, and score, so you can check any row.

## Why

Single-run model comparisons often show all models picking the same easy
fix and differing only in price. That says little about real code.
model-rig gives each agent a real app with several defects, repeats each
run, and lets hidden tests decide what was fixed and what broke. It
stores tokens per model and per kind, so any price sheet can price the
runs later. The headline number is cost per successful fix, not cost
per run.

## Quickstart

Requirements:

- Linux with [bubblewrap](https://github.com/containers/bubblewrap)
  (`bwrap`). On Ubuntu 23.10 and later, AppArmor blocks it by default;
  see [Troubleshooting](#troubleshooting).
- Python 3.11 or later, and git.
- For real runs: [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
  or the [Codex CLI](https://github.com/openai/codex), or both, signed in
  with a subscription or an account.

1. Get the code and install the `model-rig` command. This is free.

   Clone the repository and enter it.

       git clone https://github.com/mishamessouu/model-rig.git
       cd model-rig

   Install the command in editable mode, so it finds the scenarios in
   this folder. `uv tool install --editable .` also works.

       pip install -e .

2. Check the demo scenario. This makes no model call and takes a few
   seconds. It proves that the planted defects fail, the reference fixes
   pass, and the sandbox works.

       model-rig check booking-ladder

3. Sign the rig in to Claude Code and Codex. This is free, but needs a
   subscription or account. It makes sign-ins under `~/.model-rig/` that
   are separate from your everyday ones. Add `claude` or `codex` to sign
   in to one only.

       scripts/login.sh

4. Prepare the wger scenario. This needs the network, about 700 MB of
   disk, and a few minutes. It fetches wger at a pinned commit and builds
   its venv under `~/.model-rig/`. A second call does nothing.

       model-rig prepare wger-log-idor

   Check it. This makes no model call and takes about 4 minutes.

       model-rig check wger-log-idor

5. Run one smoke test: one cell, one prompt, one run. This spends
   subscription usage for one agent run. Without `--yes`, the command
   prints the plan and stops.

       model-rig run booking-ladder --cells claude-opus-medium --prompts open --repeats 1 --yes

6. Run a full batch: four cells, three prompts, three repeats, so 36
   runs. This spends a lot of subscription usage. A wger run can take up
   to the 30-minute timeout in `config/matrix.toml`.

       model-rig run wger-log-idor --cells claude-opus-medium,claude-sonnet-5-5-medium,codex-sol-high,codex-luna-medium --prompts open,ddd,security --yes

   If a batch stops, run the same command with `--resume results/<batch>`.
   It adds only the missing runs to that folder.

7. Rebuild a batch's report. This is free.

       model-rig report results/<batch>

8. Score a batch's saved diffs again, for example after a scenario gains
   a defect. This makes no model call; it only runs the hidden tests
   (about 100 s per run on wger).

       model-rig rescore results/<batch>

`python3 -m rig` works in place of `model-rig` everywhere. A plain
(non-editable) install works when you run it from the checkout folder,
or with `MODEL_RIG_ROOT` set to the checkout. `MODEL_RIG_HOME` moves the
state folder from `~/.model-rig/`.

## How it works

```text
 config/matrix.toml           scenarios/<name>/
 (cells: harness,             scenario.toml, hidden/, solutions/,
  model, effort)              repo/ or an upstream commit
        |                              |
        v                              v
 +--------------+   fresh copy   +------------------------+
 |    runner    | -------------> | agent sandbox (bwrap)  |
 |  one run at  |                | Claude Code or Codex,  |
 |  a time      | <------------- | headless, provider only|
 +--------------+  log + diff    +------------------------+
        |
        v
 +-----------------------------+      +-------------------+
 | scorer sandbox (bwrap)      | ---> | results/<batch>/  |
 | hidden tests, no network    |      | result.json, diff |
 +-----------------------------+      | log, report.md    |
        ^                             +-------------------+
        | config/prices.toml (price sheets per 1M tokens)
```

- **Scenario.** An app with one or more defects. Each defect has hidden
  tests that fail before a fix, and a reference fix that passes them. The
  app is a small folder in the repo or a real upstream commit.
- **Cell.** One harness, model, and effort, named in
  `config/matrix.toml`. Model and effort are configuration, not code.
- **Sandbox.** bubblewrap with a read-only root. Home, `/tmp`, `/run`,
  `/var`, and other data folders are empty, so the agent cannot see the
  rig repo, the hidden tests, your files, the sign-ins, or the Docker
  socket. Only the run folder is writable. A prepared venv, and its base
  Python if that lives under a hidden folder, is bound read-only and comes
  first on `PATH`. A prepared Node `node_modules` is bound read-only over
  the working copy's own, so it never enters the diff.
- **Network.** The sandbox has no network of its own. The agent reaches
  its model provider through a proxy on the host, which allows only the
  hosts that `config/network.toml` names for its harness. Every other
  host gets a refusal, so the agent cannot look up the fix or the
  advisory. Each run saves `network.jsonl`, one line per request, and
  `result.json` lists the hosts it reached and the hosts it was refused.
- **Fix date.** A scenario from a real fix names its `fix_date`, and a
  cell may name its model's training `cutoff` when a primary source
  states it. `result.json` records whether the fix came after the
  cutoff, and `rig run` warns when it did not.
- **Scorer.** Copies the agent's result, restores the visible test files
  the regression set uses, adds the hidden tests, and runs each test id
  in a sandbox with no network.
- **Price sheets.** `config/prices.toml` prices the stored token counts.
  The included sheet is GitHub Copilot credits per 1M tokens, from
  GitHub's Copilot models and pricing page, read on 2026-10-20. One
  credit is 0.01 USD. Add a sheet and run
  `model-rig report --sheet <name>` to price old runs again.

Design decisions and their reasons: [`docs/design.md`](docs/design.md).

## Scenarios

| Scenario | App | Defects | Notes |
|---|---|---|---|
| `booking-ladder` | Small room booking service in this repo, stdlib Python | 4 planted: a decoy bug, a domain-model bug, SQL injection, a cancel IDOR | A toy demo. Its hidden tests are public, so it is not a held-out test. |
| `wger-log-idor` | [wger](https://github.com/wger-project/wger) at commit `67fbf06`, Django and DRF, about 36k lines | 2 missing owner checks from one real fix | Advisory GHSA-rjpf-7pf5-q54x, fix `b29cf17` (2026-05-08), reverted by pinning its parent. About 1,400 visible tests. The fix predates some models' training cutoff, so a model may have seen it. |
| `wger-gym-access` | wger at commit `6a90e34`, Django | 6, from three real fixes: two gym config views miss an access check, and gym managers reset the passwords of accounts at or above their role | Fixes `d0ca31ca`, `dd28603a`, and `5c1817e9` (2026-10-04). No public results yet. |
| `changedetection-processor-traversal` | [changedetection.io](https://github.com/dgtlmoon/changedetection.io) at commit `22efcca`, Flask, JSON files | 3, from one real fix: a processor name becomes a file name, so an import writes outside the datastore | Advisory GHSA-mh42-m7cg-49fr, fix `acc4533` (2026-08-20). No public results yet. |
| `labelstudio-orm-traversal` | [Label Studio](https://github.com/HumanSignal/label-studio) at commit `57ec915`, Django and DRF | 2, from one real fix: data manager filters and ordering traverse ORM relations | Advisories GHSA-9q39-f8w9-75wm and GHSA-xw23-r93p-26jm, fix `7e2f696` (2026-09-01). |
| `mealie-zip-import-idor` | [mealie](https://github.com/mealie-recipes/mealie) at commit `46497a9`, FastAPI and SQLAlchemy, SQLite | 3, from one real fix: a recipe zip import keeps tool, organizer, and sub-recipe ids of another group | Advisory GHSA-99wf-32rc-2767, fix `ab0c8d6` (2026-10-05). |
| `mlflow-graphql-permission` | [MLflow](https://github.com/mlflow/mlflow) at commit `08dfbc9`, Flask basic-auth app, SQLite | 2, from one real fix: GraphQL shows model and prompt versions the user may not read | Advisory GHSA-f253-vggg-rwh8, fix `395db9d` (2026-09-16). |
| `inventree-attachment-access` | [InvenTree](https://github.com/inventree/InvenTree) at commit `f16fb36`, Django and DRF, SQLite | 2, from one real fix: the attachment list and detail views skip the linked model's view permission | Fix `528bb08` (2026-08-23). |

Each real scenario pins the parent of an upstream fix, so its defects are
real. Its folder has a `LICENSE-NOTICE.md` with the upstream commits.
Every fix and its test are public upstream, so none of these is a
held-out test. The two scenarios with no public results have batches in
the lab that are not published yet.

Every scenario has three prompts: `open` (find the improvement that
matters most), `ddd` (a domain-design improvement), and `security`. Each
asks for one change and a final `CHOICE:` line.

## Add your own scenario

See [`docs/adding-a-scenario.md`](docs/adding-a-scenario.md): bug
reinjection step by step, every `scenario.toml` field, what
`model-rig check` proves, and how to keep a scenario uncontaminated.
Candidate fixes: [`docs/research/2026-10-16-scenario-candidates.md`](docs/research/2026-10-16-scenario-candidates.md).

## Fairness rules

Both harnesses get the same limits, so the comparison is about the agent
and model, not about extra tools one side had.

- **One agent.** Claude Code runs with helper agents and task tools
  denied. Codex `exec` is one agent already.
- **No background work.** A headless run that starts a background helper
  can end while it waits for a notification that never comes.
- **No web.** Web search could find the advisory and its fix.
- **A fresh sign-in copy per run.** No run shares state with another.
- **No memory.** Claude Code runs with no session persistence; Codex runs
  ephemeral and ignores user configuration.
- **MCP off.** No MCP servers, so no tool reaches outside the sandbox.
- **Provider hosts only.** Since 2026-10-19 the agent reaches only its
  provider's hosts. The 2026-10-16 wger batch ran before that, on the
  host network with web tools off. Its logs show no fetch of the fix.
  Every later batch ran behind the proxy.

## Limitations

- **Linux only.** The sandbox is bubblewrap.
- **Small n.** Three repeats per cell and prompt is enough to see a
  choice pattern, not to rank close models. Six runs give a 95% interval
  about 40 to 60 points wide. Read the per-run table, not only the means.
- **The fixtures hold other real holes.** A real app at an old commit
  has more than the one planted fix. Agents found some of them, and the
  score does not count them.
- **A miss can be a real find elsewhere.** A run that fixed another
  real hole, and not the planted one, scores as "other change", the same
  as a run that renamed a variable. Read the diff and the `CHOICE:` line
  before you call a miss wasted.
- **Triage is manual.** A person reads the "other change" runs and
  decides which found a real hole (design decision 13). That takes time,
  can be wrong, and is not done for every scenario. No public scenario
  has a triage record yet.
- **Uneven coverage.** Not every cell ran on every scenario. Compare
  totals only for cells that ran the same scenarios.
- **Subscription quota.** Runs use subscription usage, which has limits
  and no exact price. The price sheet turns tokens into one comparable
  unit; it is not your bill.
- **Models change.** A model name can point to a new version tomorrow.
  `batch.json` records the CLI versions; the provider may not expose more.
- **Cache pricing.** Codex reports no cache writes, and price sheets
  price cache reads and writes differently. Cost depends on the sheet.
- **Harness differences.** The CLIs differ in system prompts, tools, and
  limits. Claude Code stops at `budget_usd`; Codex has only the timeout.
  Results compare agent and model together.
- **Contamination.** Public scenarios, and any fix before a model's
  training cutoff, may be known to the model.

## Troubleshooting

`bwrap: setting up uid map: Permission denied` on Ubuntu 23.10 or later
means AppArmor blocks unprivileged user namespaces. The scoped fix is an
AppArmor profile for bwrap. Write it as root to `/etc/apparmor.d/bwrap`:

```text
abi <abi/4.0>,
include <tunables/global>

profile bwrap /usr/bin/bwrap flags=(unconfined) {
  userns,
  include if exists <local/bwrap>
}
```

Load the profile.

    sudo apparmor_parser -r /etc/apparmor.d/bwrap

On a throwaway machine such as a CI runner, you can instead lift the
restriction for every program until the next reboot.

    sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Coding agents working on this
repository: see [`AGENTS.md`](AGENTS.md).

## Licence

Apache-2.0, see [`LICENSE`](LICENSE). Test and reference fix files
copied from an upstream app keep that app's licence: AGPL-3.0 for wger
and mealie, Apache-2.0 for changedetection.io, Label Studio, and MLflow,
and MIT for InvenTree. See [`NOTICE`](NOTICE) and the `LICENSE-NOTICE.md`
in each scenario folder.

## Citation

If you use model-rig, cite it with [`CITATION.cff`](CITATION.cff).
GitHub shows a "Cite this repository" button for it.
