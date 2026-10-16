# How public benchmark repositories present themselves

Date: 2026-10-16. Method: read each README, top-level file list, and
`.github/` folder through the GitHub API, and the Aider leaderboard page,
to pick the patterns that fit a small, stdlib-only rig.

## What each one does

- **SWE-bench**: a centred hero with links, then shield badges (Python
  version, licence, PyPI). Sections: News, Overview, Set Up, Usage,
  Downloads, Contributions, Citation and licence (BibTeX). Has
  `.github/ISSUE_TEMPLATE` (bug, feature, question), a PR template,
  workflows, `CHANGELOG.md`, `pyproject.toml`, and a docs site.
- **Aider benchmark**: `benchmark/README.md` puts Background first, then
  Usage, Setup, Running, the report, and a "Limitations, notes" section.
  The leaderboard table ranks by percent correct and shows cost, the
  command to reproduce, edit format, and the run date per row.
- **Terminal-Bench**: one-line pitch, badges, Quickstart with
  `uv tool install` or `pip install`, then Core Components (dataset of
  tasks, execution harness), how to add tasks, Citing Us.
- **inspect_evals (UK AISI)**: Quick start at the top, then About, Getting
  started, Usage. Ships `CONTRIBUTING.md`, `AGENTS.md`, `NOTICE`,
  `third-party-licenses/`, an evaluation checklist, ADRs, issue and PR
  templates, and many CI workflows.
- **LiveCodeBench**: Introduction, Installation, Evaluation, Results,
  Citation. Its pitch is contamination: problems are dated, and a model
  is scored only on problems released after its training cutoff.
- **CVE-Bench**: Overview, Set-up, Usage, Prompts, an example, Citation.
  Real CVEs in real web apps, the closest neighbour in subject.
- **METR task standard**: sections on hiding information from the agent
  and on what the standard deliberately avoids defining.

## Patterns applied here

1. A one-line pitch that states the question, then badges (licence,
   Python, CI). No logo, no news section, because there is no history yet.
2. Results near the top, between fixed markers, so a script or a person
   can replace the table without touching the rest.
3. A Quickstart with requirements first, numbered steps, and the cost of
   each step, because some steps spend subscription usage.
4. "How it works" with the four parts (scenario, cell, sandbox, scorer)
   and a small diagram, following Terminal-Bench's "Core Components".
5. An "Add your own scenario" guide in its own file, as Terminal-Bench and
   inspect_evals do, with a contamination section after LiveCodeBench.
6. Fairness rules and Limitations as their own sections, after Aider's
   "Limitations, notes" and METR's "hiding information" section.
7. `CONTRIBUTING.md`, a short `AGENTS.md`, issue templates (bug, new
   scenario), and a PR template, as in inspect_evals and SWE-bench.
8. `NOTICE` plus a per-scenario licence notice for third-party files,
   after inspect_evals' `NOTICE` and `third-party-licenses/`.
9. `CITATION.cff` instead of a BibTeX block only: GitHub renders a
   "Cite this repository" button from it, and it converts to BibTeX.

## Not applied

- A docs site (SWE-bench, Terminal-Bench): too much for two scenarios.
- A leaderboard site (Aider, Terminal-Bench): no results are published yet.
- PyPI release and badge: the package needs a checkout for its scenarios.

## CI note

Ubuntu 24.04 sets `kernel.apparmor_restrict_unprivileged_userns=1`, so
`bwrap` fails with "setting up uid map: Permission denied" unless an
AppArmor profile grants it user namespaces. On a throwaway CI runner the
simple fix is `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0`.
On a workstation, a scoped profile for `/usr/bin/bwrap` is safer.

## Sources

- https://github.com/SWE-bench/SWE-bench
- https://github.com/Aider-AI/aider/tree/main/benchmark
- https://aider.chat/docs/leaderboards/
- https://github.com/laude-institute/terminal-bench
- https://github.com/UKGovernmentBEIS/inspect_evals
- https://github.com/LiveCodeBench/LiveCodeBench
- https://github.com/uiuc-kang-lab/cve-bench
- https://github.com/METR/task-standard
- https://etbe.coker.com.au/2024/04/24/ubuntu-24-04-bubblewrap/
- https://github.com/openai/codex/issues/15057
