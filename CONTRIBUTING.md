# Contributing

Thank you for helping. Issues and pull requests are welcome, especially
new scenarios, harness support for another agent CLI, and price sheets.

## Before you start

- Open an issue first for anything larger than a small fix, so we can
  agree on the approach.
- For a new scenario, read [`docs/adding-a-scenario.md`](docs/adding-a-scenario.md)
  and use the "New scenario" issue template.

## Set up

Install the command in editable mode.

    pip install -e .

Run the rig's own tests. They use a fake agent and make no model call.

    python3 -m unittest -v tests.test_rig tests.test_sources

Check the demo scenario.

    model-rig check booking-ladder

The tests need `bwrap`, git, Node.js with npm, and Python 3.11 or later.
They do not need a prepared fixture, the network, or a sign-in.

## Rules

- **Hidden tests and reference fixes never enter an agent sandbox.** Do
  not paste `scenarios/*/hidden/` or `scenarios/*/solutions/` into a
  prompt, an issue, or a chat with a model you plan to test.
- **A new scenario passes `model-rig check <name>`** before any run. Say
  in the pull request that it does, and paste the output.
- **Results are evidence.** Do not edit files under `results/` by hand.
  `model-rig rescore` keeps the old score in `previous_scores`.
- **Model and effort are configuration.** Change `config/matrix.toml`,
  not code, to add a cell.
- **No secrets.** Sign-ins live in `~/.model-rig/`, outside the repo.
- **Third-party files keep their licence.** Add a `LICENSE-NOTICE.md`
  next to them with the upstream URL and commit, and name them in
  `NOTICE`.
- **Report unfixed holes privately.** A run can find a real hole that
  upstream has not fixed. Report it to upstream privately, and do not
  describe it in a public issue or pull request until upstream has
  answered or 90 days have passed.
- **Real runs cost money or quota.** Fake cells in
  `tests/matrix-fake.toml` are free; use them to test the pipeline.

## Style

- Python standard library only, no runtime dependencies.
- Short sentences, active voice, and no em dashes in docs and comments.
- A pull request that changes behaviour adds or changes a test.
- Commit subjects are imperative and under 70 characters. The body says
  why.

## Licence

By contributing, you agree that your contribution is licensed under
Apache-2.0, the licence of this repository, except for third-party files
that keep their own licence as above.
