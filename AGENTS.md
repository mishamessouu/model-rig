# AGENTS.md

Instructions for coding agents working on this repository.

model-rig runs coding agents on planted-defect scenarios and scores what
they chose, whether the fix works, what they broke, and what it cost.
Read `README.md`, then `docs/design.md`, before you change behaviour.

## Test

Run before every commit. The tests use a fake agent and make no model call.

    python3 -m unittest -v tests.test_rig tests.test_sources
    python3 -m rig check booking-ladder

## Rules

- Never run a paid or quota-spending model run (`rig run ... --yes` with a
  real cell) without the repository owner's approval in the current
  conversation. Fake cells in `tests/matrix-fake.toml` are free.
- `scenarios/*/hidden/` and `scenarios/*/solutions/` never enter an agent
  sandbox. Do not paste them into a prompt, a fixture, or an issue. A
  model that saw them is contaminated for that scenario.
- A new or changed scenario must pass `python3 -m rig check <name>`. A
  scenario with an upstream fixture needs `python3 -m rig prepare <name>`
  first. Commit only its small files, never the fixture or the venv.
- Do not edit `results/`. Results are evidence.
- Model and effort are configuration in `config/matrix.toml`, not code.
- The hosts an agent may reach are in `config/network.toml`. Widen them
  only with a reason from a run's `network.jsonl`.
- Standard library only. No new runtime dependency.
- No secrets in the repo. Sign-ins live in `~/.model-rig/`.

## Style

Short sentences. Active voice. No em dashes.
