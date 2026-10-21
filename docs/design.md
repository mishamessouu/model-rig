# Design

Status: v0.1, 2026-10-16; network allowlist 2026-10-19. Each decision
says what would change it.

## The question

Which coding agent gives a correct fix at the lowest cost?

Single-run model comparisons often show all models picking the same easy
fix and differing only in price. That says little about real code. In
one such comparison, most of a 50x cost gap between the cheapest and the
most expensive model came from price per token (about 40x), not from
token use (about 1.2x to 1.6x). One run per model, an easy task, and no
check of the result leave the real question open: does a higher price buy
a better result on harder work?

So model-rig measures four things per run, over repeats:

1. **Choice.** Which of several planted defects the agent fixed.
2. **Correctness.** Hidden tests decide, not the agent.
3. **Breakage.** Hidden regression tests.
4. **Cost.** Tokens per model, split into input, output, cache read, and
   cache write, priced by a price sheet.

The headline number is **cost per successful fix**, not cost per run.

## Existing solutions

- **SWE-bench, Aider polyglot, Terminal-Bench**: public tasks, so models
  may have seen them in training. They measure success, not choice among
  several defects.
- **Inspect AI** with `inspect_swe`: runs Claude Code and Codex in
  sandboxes, with logs and a viewer. It bills through API keys. A good
  home if this rig grows past a few scenarios.
- **promptfoo**: suits prompt evaluations more than agent runs in a repo.

model-rig is a small script instead: held-out fixtures you can keep
private, subscription sign-ins, and the "choice" measure.

## Decisions

1. **Planted or reinjected defects, proven by a check.** Every defect has
   a hidden test that fails before a fix and a reference fix that passes
   it. `model-rig check` proves both. Changes if: a public suite adds
   private, held-out tasks with the same measures.
2. **Deterministic scoring first.** Hidden tests decide. A model judge or
   a blind human read may come later, for quality questions tests cannot
   answer. Changes if: we add design tasks with no testable behaviour.
3. **The real CLIs, headless.** The harness is part of what we measure, so
   the rig runs Claude Code and Codex, not raw API calls. Changes if: we
   want to measure the model alone, without its harness.
4. **bubblewrap, not Docker.** bwrap needs no daemon, no root, and no
   group membership, and starts in milliseconds. The network is decision
   10. Changes if: a scenario needs a service that bwrap cannot hold.
5. **Separate sign-ins.** Each run gets a copy of the rig's own sign-in
   from `~/.model-rig/`, and a refreshed token is copied back. Sharing
   your everyday sign-in could rotate its refresh token under a running
   session.
6. **Price sheets are data.** Token counts are stored per model and per
   kind, so any later price sheet can price old runs again.
7. **Real apps by bug reinjection, prepared outside the repo.** A
   scenario may name an upstream git URL, a commit, and an optional
   revert patch. `model-rig prepare` fetches the commit into
   `~/.model-rig/fixtures/<name>` and builds a venv in
   `~/.model-rig/envs/<hash of name>` from the project's own lock file, with the
   network on. The repo keeps only the scenario file, the hidden tests,
   the reference fix, and any patch. The venv is bound read-only into the
   agent sandbox and the scoring sandbox, first on `PATH`, so the agent
   runs the tests the way the scorer does, and scoring needs no network.
   Each scenario names its test command (`{tests}` becomes the test ids),
   where the hidden tests land, which visible test files the scorer
   restores, and a test timeout. Why: a planted toy app is easy to
   recognise, and a real fix gives a real defect, a real test, and a real
   reference fix. Pinning the fix's parent is preferred over a revert
   patch when the parent passes its own suite, because then nothing is
   hand-made. Changes if: a project needs a database server or a
   toolchain that a venv cannot hold (then a container image per
   scenario), or upstream history becomes unreachable (then keep a
   tarball of the fixture and record its hash).
8. **One agent, no background work, no web, in both harnesses.** Claude
   Code runs with helper agents, scheduling tools, worktree tools, and web
   tools denied, and with background tasks off. Codex runs with
   `web_search="disabled"`. Why: in an early wger batch, one Claude run
   started a background helper, then waited for a notification that never
   comes in headless mode, and ended with no change after 3.4M tokens. Web
   lookup could also find the advisory and its fix. Changes if: the CLI
   waits for background work before it exits; then helper agents can come
   back as their own cell, because they are part of the harness.
9. **One run at a time.** Runs share one sign-in copy, and a refresh
   during a parallel run could race. Changes if: each cell gets its own
   sign-in, or a batch grows too slow to run serially.
10. **No network but the provider, through a host proxy.** Every sandbox
   gets its own network namespace (`--unshare-net`), with loopback only
   and no name resolution. A real run also gets a Unix socket bound in.
   On the host, `rig/proxy.py` listens on it, accepts only `CONNECT
   host:port` to a host in `config/network.toml`, resolves the name on
   the host, and logs one JSON line per request. In the sandbox,
   `rig/netbridge.py` listens on `127.0.0.1:3128`, forwards to the
   socket, and starts the agent with the proxy variables set. This is
   the pattern of Anthropic's sandbox-runtime, in the standard library.
   Why: an agent's shell could fetch the upstream fix or the advisory,
   and a security reader asks "could it look up the CVE?" first. The log
   answers that per run. Why not the harnesses' own sandboxes: they
   differ between Claude Code and Codex, so the two would not run under
   one rule. They are also part of the harness under test, and a model
   can ask to turn some of them off. The proxy sits outside the agent's
   reach, and its log is written to the results folder, which the
   sandbox hides. The host lists come from reading the CLI binaries:
   Claude Code 2.1.302 names `api.anthropic.com` and
   `platform.claude.com` (token refresh); Codex 0.163.0 names
   `chatgpt.com`, `auth.openai.com` (token refresh), and
   `api.openai.com`. One real run per harness on 2026-10-19 confirmed the
   Claude list. Codex used only `chatgpt.com`, and its refused tries
   (`ab.chatgpt.com`, `*.oaiusercontent.com`) did not stop the run, so
   `api.openai.com` came off the list.
   Limit: the proxy cannot see inside a tunnel, so a provider's own
   server-side tools, such as web search, pass through an allowed host.
   Decision 8 still turns those tools off in each harness. Changes if: a
   CLI stops honouring `HTTPS_PROXY` for some transport (the log then
   shows nothing, and the run fails), or a scenario needs a package
   index, which then gets its own entry.
11. **Fix date against training cutoff.** A scenario from a real fix
   sets `fix_date`. A cell sets `cutoff = "YYYY-MM"` only when a primary
   source states the model's training cutoff. `result.json` records
   `fix_after_cutoff` as true, false, or null for unknown. The fix month
   itself counts as known. The report shows it per cell, and `rig run`
   warns but does not refuse. On 2026-10-19 no cell has a sourced
   cutoff: the matrix uses aliases such as `opus`, and the Claude API
   reference names no training cutoff for Claude Opus 5.5.

## Where things live

| Path | What |
|---|---|
| `rig/` | The runner, harnesses, sandbox, scorer, prices, reports |
| `scenarios/<name>/` | `scenario.toml`, `hidden/`, `solutions/`, and `repo/` or an upstream fixture |
| `config/matrix.toml` | Cells: harness, model, effort; repeats, timeout, budget |
| `config/prices.toml` | Price sheets per 1M tokens |
| `config/network.toml` | The hosts each harness may reach through the proxy |
| `results/<batch>/` | One folder per batch; see `results/README.md` |
| `~/.model-rig/` | Sign-ins, prepared fixtures and venvs, run work folders |

## What ages, what stays

Better models will clear the booking-ladder rungs. The fixtures age; add
harder rungs and new scenarios. A reinjected real fix ages faster in one
way: once the fix date is before a model's training cutoff, the model may
know the fix. Each scenario records its fix date, and each result says
whether the fix came after the model's cutoff, where that is known. The
runner, the scorer, the stored token split, and the "cost per successful
fix" measure stay. Ten times the
agents means ten times the cells, so the runner may need parallel runs
then; today it runs one at a time to keep the sign-in copy safe.

The host lists age with each CLI release, so read them again from the
logs. The harnesses' own sandboxes will improve. When both CLIs offer the
same allowlist with a log the rig can read, the proxy may go. The
namespace boundary and a log kept outside the agent's reach stay: a
stronger model is better at finding a way out, not worse.
