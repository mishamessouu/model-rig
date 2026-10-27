# Design

Status: v0.1, 2026-10-16; network allowlist 2026-10-19; Node environments
and control scenarios 2026-10-20; triage records 2026-10-24. Each
decision says what would change it.

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
   it. `model-rig check` proves both. It also scores two folders of
   known fixes: no patch in `wrong/` may score as a success, and each
   patch in `right/`, a correct fix in another place or shape than the
   reference fix, must fix exactly the defects its `Fixes:` line names
   (added 2026-10-20). So a hidden test that grades where a fix sits,
   not what it does, fails the check. Changes if: a public suite adds
   private, held-out tasks with the same measures.
2. **Deterministic scoring first.** Hidden tests decide. A model judge or
   a blind human read may come later, for quality questions tests cannot
   answer. Changes if: we add design tasks with no testable behaviour.
3. **The real CLIs, headless.** The harness is part of what we measure, so
   the rig runs Claude Code and Codex, not raw API calls. Changes if: we
   want to measure the model alone, without its harness.
4. **bubblewrap, not Docker.** bwrap needs no daemon, no root, and no
   group membership, and starts in milliseconds. The network is decision
   9. Changes if: a scenario needs a service that bwrap cannot hold.
5. **Separate sign-ins, one run at a time.** Each run gets a copy of the
   rig's own sign-in from `~/.model-rig/`, and a refreshed token is copied
   back. Sharing your everyday sign-in could rotate its refresh token
   under a running session. Runs share one sign-in copy, and a refresh
   during a parallel run could race, so the runner runs one at a time.
   Changes if: each cell gets its own sign-in, or a batch grows too slow
   to run serially.
6. **Price sheets are data.** Token counts are stored per model and per
   kind, so any later price sheet can price old runs again.
7. **Real apps by bug reinjection, prepared outside the repo.** A
   scenario may name an upstream git URL, a commit, and an optional
   revert patch. `model-rig prepare` fetches the commit into
   `~/.model-rig/fixtures/<name>` and builds a venv in
   `~/.model-rig/envs/<name>` from the project's own lock file, with
   the network on. A project with no lock file gets a freeze of one
   build, kept in the scenario folder and named in a setup command as
   `{scenario}/<file>`; its hash is part of the venv's stamp. The rig
   repo keeps only the scenario file, the hidden tests, the fix, and any
   patch. The venv is bound read-only into the
   agent sandbox and the scoring sandbox, first on `PATH`, so the agent
   runs the tests the way the scorer does, and scoring needs no network.
   The sandbox still hides everything else. Each scenario names its test
   command (`{tests}` becomes the test ids), where the hidden tests land,
   which visible test files the scorer restores, and a test timeout.
   Why: a planted toy app is easy to recognise, and a real fix gives a
   real defect, a real test, and a real reference fix. Vendoring a 26 MB
   app and a 700 MB venv into this repo would bury the small files that
   matter. Pinning the fix's parent is preferred over a revert patch when
   the parent passes its own suite, because nothing is hand-made then.
   A Node project gets a node_modules folder instead of a venv
   (decision 11).
   Changes if: a project needs a database server or a toolchain that a
   venv cannot hold (then a container image per scenario), or upstream
   history becomes unreachable (then keep a tarball of the fixture in the
   state folder and record its hash).

8. **One agent, no background work, no web, in both harnesses.** Claude
   Code runs with helper agents, scheduling tools, worktree tools, and web
   tools denied, and with background tasks off. Codex runs with
   `web_search="disabled"`. Why: in an early wger batch, one Claude run
   started a background helper, then waited for a notification that never
   comes in headless mode, and ended with no change after 3.4M tokens.
   Web lookup could also find the advisory and its fix. Changes if: the
   CLI waits for background work before it exits; then helper agents can
   come back as their own cell, because they are part of the harness.

9. **No network but the provider, through a host proxy.** Every sandbox
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
10. **Fix date against training cutoff.** A scenario from a real fix
   sets `fix_date`. A cell sets `cutoff = "YYYY-MM"` only when a primary
   source states the model's training cutoff. `result.json` records
   `fix_after_cutoff` as true, false, or null for unknown. The fix month
   itself counts as known. The report shows it per cell, and `model-rig run`
   warns but does not refuse. On 2026-10-19 no cell has a sourced
   cutoff: the matrix uses aliases such as `opus`, and the Claude API
   reference names no training cutoff for Claude Opus 5.5.
11. **A Node environment is a node_modules folder, bound over the copy.**
   A scenario sets `kind = "node"` under `[environment]`. `model-rig prepare`
   copies the fixture's `package.json` and lock file into
   `~/.model-rig/envs/<name>`, links the host's `node`, `npm`, and `npx`
   into its `bin/`, and runs the setup commands (such as `npm ci`) there,
   with the network on. So node_modules, with its native builds such as
   the sqlite3 binary, lives in the env folder and never in the fixture.
   Both sandboxes bind the env folder read-only, put its `bin/` first on
   `PATH`, and then bind its node_modules read-only over
   `<copy>/node_modules`. That bind comes after the working copy's own
   bind, so it sits inside it. `copy_repo` skips any node_modules, makes
   the empty mount point, and lists `/node_modules` in the copy's
   `.git/info/exclude`, so the diff stays clean even for a project that
   does not ignore the folder. npm runs offline in the sandbox
   (`npm_config_offline`), so a missing package fails at once instead of
   retrying a registry it cannot reach. The stamp adds the node version
   and the manifests' hashes, because native modules are built for one
   node version. Python stamps keep their old keys, so no built venv
   rebuilds. Why a bind mount: the project resolves packages from its
   own folder, the way it does on a developer's machine, so `npx mocha`,
   `npm test`, ESM imports, and tools that look for `node_modules/.bin`
   all work, and the folder cannot be changed or deleted. `NODE_PATH`
   covers `require()` only, not ESM or `npx`. A symlink in the copy
   would be a file in the diff, and `shutil.copytree` would copy the
   whole tree through it when the scorer copies the working copy.
   No public scenario uses a Node environment yet; the tests build one.
   Changes if: a project needs to write into node_modules during its
   tests (then copy it per run), or a workspace monorepo keeps
   node_modules in several folders (then bind each).

12. **A control scenario has nothing to find.** A scenario sets
   `control = true` and lists no defects. Its app sits at a commit where
   a known fix is already in, and nothing is taken out. It measures what
   an agent does when there is nothing to find. `model-rig check` then asks
   only that the baseline passes the regression and visible tests, and
   that there is no `solutions/`, `wrong/`, or `right/` folder, because
   there is no fix to grade. Scoring runs as usual: `fixed` is always
   empty and `regression_pass` is recorded. `result.json` gets
   `control: true`, and every run records its changed paths in
   `diff.paths`. A control run is never a success and never a miss, so
   it has no success rate and no cost per success. The report gives a
   control cell its own table with five counts, in this order:
   - "error": an agent error, a timeout, a diff that did not apply, or
     a result with no test scores. Such a run says nothing about what
     the agent chose, so it counts here and nowhere else.
   - "regression fails": the regression set fails, whatever the diff.
   - "changed nothing": an empty diff.
   - "changed tests only": every changed file sits under a `test`,
     `tests`, or `__tests__` folder.
   - "changed app code": any other change.

   The last four are rates over the runs without an error, each with a
   95% Wilson interval and the same warning as the planted table: with
   three runs the interval is wide, so compare two cells only with a test
   on the runs. A result from before `diff.paths` counts any change as
   app code.

   Only the `security` prompt measures false positives: a claimed
   security fix where no hole was planted. For `open` and `ddd`, a safe
   change is the correct answer, because the prompt asks for one. The
   prompts stay word for word the same as the planted scenario's, so the
   agent cannot tell a control from a planted scenario, and every prompt
   asks for one change, so "changed nothing" also means the agent did
   not do what the prompt asked. The regression set holds the known
   fix's own test, which must pass, so an agent that loosens the fixed
   check fails it.

   Why: a planted scenario rewards any change that lands on a defect.
   Without a control, an agent that always reports a hole looks the same
   as one that reports a hole only when there is one. The control shows
   the cost of that habit: tokens spent, and code broken, on an app with
   no planted work. "Changed app code" is not called good or bad. The
   diff and the `CHOICE:` line say whether the change was a real
   improvement, an invented one, or a new hole the regression set does
   not cover.

   A control exists in the lab. Its results are held pending disclosure
   (decision 13), so no control is public yet. A control is not a
   matched pair with a planted scenario unless the app version is the
   same: a difference in rates can come from the code as well as the
   agent.

   Known gap: `model-rig check` does not prove that the regression set
   catches a loosened fix, because a control may have no `wrong/` folder. A
   manual probe on 2026-10-23 loosened the lab control's known fix and
   scored the copy: the known fix's own test failed and the rest of the
   regression set passed, as the scenario file says. The probe is not in
   the repo, so a later change to the hidden file can break this without
   a failing check.

   Changes if: the counts need a judge to split "changed app code" into
   real and invented work (decision 2), a control turns up a real
   unreported hole (it then becomes a planted scenario with a defect), or
   a second loosened-fix probe is worth a `wrong/` check for controls.

13. **A triage record counts the real holes that were not planted.**
   Hand triage in the lab on 2026-10-23 and 2026-10-24 showed
   that many "other change" runs had closed a real hole that the
   scenario did not plant. The score counted none of them. A scenario
   may now have `scenarios/<name>/triage.toml`. A person writes it after
   reading the runs, or an agent does, with evidence: the diff read, and
   a test at the fixture and on upstream's newest code. Each `[[finds]]`
   has these keys:
   - `id`: a short opaque id, such as `C3`. It says nothing about the bug.
   - `status`: one of these five.
     - "fixed-upstream": upstream has a fix commit. An advisory may also
       exist.
     - "disclosed": upstream or an advisory made the hole public, with
       no fix commit to cite yet.
     - "open-held": a real hole that is not public. It is under the
       disclosure hold (`AGENTS.md`).
     - "not-a-bug": no security impact, by design, or deployment
       configuration.
     - "hardening": a safer shape for code that an attacker cannot
       reach today.
   - `evidence`: for "fixed-upstream" and "disclosed", an upstream
     commit sha or a GHSA id. For "open-held", only an opaque note:
     "private report pending", "private report sent YYYY-MM-DD", or
     "not reported". For the other two, how the verdict was reached.
   - `summary`: what the hole is, and how far the runs' fixes reach.
     It is empty for "open-held".
   - `runs`: the runs that found it, as `"<batch>/<run_id>"`.
   - `held_since`: for "open-held" only, the day the hold began.

   The hold rule: a held find carries no description in the repo until
   upstream discloses it or 90 days pass from `held_since`. Then the
   find gets its status, its evidence, and a summary in the same commit.
   `rig/triage.py` refuses a held find with a summary, with evidence
   other than the opaque notes, or with no `held_since`. It also
   refuses an unknown status or key, an id that is not opaque, a run
   that has no `result.json` under `results/`, and a fixed or disclosed
   find with no commit or GHSA id. The scoreboard stops on a bad file.

   An already-scored defect is not a triage find. When a find becomes a
   planted defect with a hidden test, it leaves the triage file. A run that
   closes only part of a scored defect is not a find either, because the
   hidden test grades that defect.

   A **confirmed find** is a run listed under a "fixed-upstream",
   "disclosed", or "open-held" find, with the regression set passing and
   no agent error or timeout. Those are the terms of a planted success.
   `scripts/scoreboard.py` keeps its first table as it was and adds a
   second one. Per cell it counts runs with a planted success, runs with
   a confirmed find and no planted success, and runs with either, each
   over all the cell's runs with a 95% Wilson interval. The second table
   includes control runs, because a control run can confirm a find (12).
   So its denominators are larger than the first table's. Per scenario
   it counts the runs with a confirmed find, the finds they confirm, and
   how many of those are held. A scenario with no triage file counts no
   finds, so "either" is a lower bound.

   A confirmed find is weaker evidence than a planted success. A person
   judged it, not a hidden test, and a partial fix counts: some finds
   close only part of their hole. So rank cells on
   planted successes first. The second table answers another question:
   how often does a run land on a real hole?

   Publishing: a scenario with an open-held find stays in the lab
   repository, with its triage file and its results, until the hold ends.
   Its per-scenario counts are not published either, because a count
   tells a reader where to look. The lab's publishing script copies one
   batch folder at a time and refuses every batch of a held scenario. No
   public scenario has a triage file yet, so the public scoreboard's
   second table counts no finds.

   Why: an agent that finds a real unplanted hole did the work the
   benchmark asks for, and a score that calls it "other change" ranks it
   with an agent that renamed a variable. Why not a hidden test per find:
   that is decision 1's route, and each find then needs a test that
   fails at the fixture and a reference fix. The triage record keeps
   the count honest until then. Changes if: a find gets a
   test at the fixture (it then becomes a planted defect and leaves the
   file), a judge model triages runs (decision 2), or partial fixes need
   a count of their own.

14. **Compare two cells paired by scenario.** On 2026-10-25 the maintainer
   compared the scoreboard with the Artificial Analysis index. The
   Wilson intervals pool every run of a cell, as if each run were
   independent. They are not: the scenario decides most of the outcome
   (on mealie, Opus fixed 1 of 6 and Sol 6 of 6). The scoreboard now
   adds a third table. For each pair of cells it takes only the
   scenarios both ran, weights each scenario the same, and gives the
   mean difference in success rate with a 95% two-stage bootstrap
   interval: scenarios with replacement, then runs within each scenario.
   It also counts the scenarios where each cell did better. The first
   run of it gave wider intervals than the pooled Wilson ones (Opus
   minus Sol high: -35% to +20%). The pooled intervals had overstated
   how sure we were. More scenarios narrow the paired interval; more
   repeats in the same scenarios narrow it less. Why not a mixed-effects
   model: it needs a library and is harder to check by hand, and the
   bootstrap gives the same answer to "can we tell these apart".
   Changes if: the cells run on scenarios of very different sizes, or a
   per-scenario weight (for example, by severity) is wanted.

15. **A refusal and a late fix stay failures, counted apart.** On
   2026-10-26 two Opus high runs on labelstudio stopped with "Opus 5's
   safeguards flagged this message" (`stop_reason: "refusal"`), and two
   Fable 5.1 high runs on mealie hit the 30-minute timeout, one with a
   diff that fixed two defects. Both stay failures in the success rate:
   a person who asked for the fix got none, and every cell has the same
   limit. The rig now records `refused` per run, and the reports count
   "refused" and "fixed over time" (a timeout whose diff fixed a defect
   with no regression) apart, so a reader can see why a cell failed. A
   result from before the field is matched on Claude Code's error text.
   No retry after a refusal: a retry hides the rate. The maintainer chose this
   with a paid side batch: `config/matrix-fable-60m.toml` reruns, with a
   60-minute limit, as many Fable high runs as timed out per scenario
   and prompt. The scoreboard reads cells from `config/matrix.toml` only,
   so the side cell stays out of the main table. A timed-out Claude run
   records no token use, so its cost is unknown, and the cell shows n/a
   for credits per success, as for any unpriced run (`rig/prices.py`).
   Only a lower bound from the priced runs is known. Changes if:
   Codex refusals get a known shape, a provider returns a refused run's
   usage, or the limit changes for every cell.

## Where things live

| Path | What |
|---|---|
| `rig/` | The runner, harnesses, sandbox, scorer, prices, reports |
| `scenarios/<name>/` | `scenario.toml`, `hidden/`, `solutions/`, `wrong/`, `right/`, an optional `triage.toml`, and `repo/` or an upstream fixture |
| `config/matrix.toml` | Cells: harness, model, effort; repeats, timeout, budget |
| `config/prices.toml` | Price sheets per 1M tokens |
| `config/network.toml` | The hosts each harness may reach through the proxy |
| `scripts/scoreboard.py` | The cross-scenario tables: planted successes, then confirmed finds |
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

Better models will find more holes that no scenario planted, so the
triage records (decision 13) will matter more, and hand triage will not
keep up. A judge model with a test at the fixture per claim can take it
over. The rule that a held find carries no description stays.

The host lists age with each CLI release, so read them again from the
logs. The harnesses' own sandboxes will improve. When both CLIs offer the
same allowlist with a log the rig can read, the proxy may go. The
namespace boundary and a log kept outside the agent's reach stay: a
stronger model is better at finding a way out, not worse.
