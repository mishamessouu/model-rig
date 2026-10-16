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
First batch running; results land here.
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

       model-rig run wger-log-idor --cells claude-opus-medium,claude-sonnet-medium,codex-sol-high,codex-luna-medium --prompts open,ddd,security --yes

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
 |  a time      | <------------- | headless, network on   |
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
  socket. Only the run folder is writable. A prepared venv is bound
  read-only and comes first on `PATH`.
- **Scorer.** Copies the agent's result, restores the visible test files
  the regression set uses, adds the hidden tests, and runs each test id
  in a sandbox with no network.
- **Price sheets.** `config/prices.toml` prices the stored token counts.
  The included sheet is GitHub Copilot credits per 1M tokens, as listed
  in the Copilot model picker on 2026-10-16. Add a sheet and run
  `model-rig report --sheet <name>` to price old runs again.

Design decisions and their reasons: [`docs/design.md`](docs/design.md).

## Scenarios

| Scenario | App | Defects | Notes |
|---|---|---|---|
| `booking-ladder` | Small room booking service in this repo, stdlib Python | 4 planted: a decoy bug, a domain-model bug, SQL injection, a cancel IDOR | A toy demo. Its hidden tests are public, so it is not a held-out test. |
| `wger-log-idor` | [wger](https://github.com/wger-project/wger) at commit `67fbf06`, Django and DRF, about 36k lines | 3 missing owner checks from one real fix | Real advisory GHSA-rjpf-7pf5-q54x, fix `b29cf17` (2026-05-08), reverted by pinning its parent. About 1,400 visible tests. |

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

## Limitations

- **Linux only.** The sandbox is bubblewrap.
- **Small n.** Three repeats per cell is enough to see a choice pattern,
  not to rank close models. Read the per-run table, not only the means.
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

Apache-2.0, see [`LICENSE`](LICENSE). The wger test and reference fix
files under `scenarios/wger-log-idor/` stay AGPL-3.0-or-later; see
[`NOTICE`](NOTICE) and
[`scenarios/wger-log-idor/LICENSE-NOTICE.md`](scenarios/wger-log-idor/LICENSE-NOTICE.md).

## Citation

If you use model-rig, cite it with [`CITATION.cff`](CITATION.cff).
GitHub shows a "Cite this repository" button for it.
