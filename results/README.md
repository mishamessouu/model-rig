# Results

Each batch gets one folder here, named `<UTC time>-<scenario>`, for
example `20261016T173617Z-booking-ladder`. `model-rig run` writes it.
Results are evidence: do not edit them by hand. `model-rig rescore` and
`model-rig report` are the only tools that change a batch folder.

## Layout of a batch folder

```text
<batch>/
  batch.json                 what was asked for
  report.md                  the summary tables
  runs/<cell>.<prompt>.r<n>/
    result.json              the score, tokens, and cost of one run
    diff.patch               the agent's change, as a git diff
    agent-log.jsonl.gz       the agent's full output stream, gzipped
    agent-stderr.txt         the last 20,000 characters of stderr
```

### `batch.json`

The scenario, cells, prompts, and repeats; the full matrix used; the
rig's git commit (`rig_commit`); and the Claude Code and Codex versions.

### `runs/<id>/result.json`

| Field | Meaning |
|---|---|
| `run_id`, `cell`, `harness`, `model`, `effort`, `prompt`, `repeat` | Which run this is |
| `fixed` | Defect ids whose hidden tests all pass |
| `regression_pass` | All regression tests pass |
| `visible_pass`, `visible_tail` | The agent's own test command passes; output tail when it fails |
| `tests` | Pass or fail per hidden test id, with an output tail on failure |
| `tokens` | Totals of `input`, `output`, `cache_read`, `cache_write` |
| `by_model` | The same four counts per model id the harness reported |
| `raw_usage` | Usage as the CLI reported it, before normalising |
| `costs` | Per price sheet: `value`, `unit`, and `missing` model ids |
| `usd_reported` | The cost the CLI itself reported, if any |
| `choice` | The agent's last `CHOICE:` line |
| `final` | The last 4,000 characters of the agent's answer |
| `diff` | Files changed, lines added, lines removed |
| `seconds`, `exit_code`, `timed_out`, `error`, `turns` | How the run ended |
| `previous_scores` | Earlier scores, kept by `model-rig rescore` |

A cost of `null` means the price sheet does not list one of the models;
`missing` names it. A partial sum never stands in for the whole cost.

### `report.md`

One row per cell and prompt: what the runs picked, successes, regressions,
errors, mean cost, cost per success, mean time, and mean lines changed.
Then mean tokens per run, and one line per run with its `CHOICE:`.
Success means at least one defect fixed, no regression, and no agent error.

Rebuild it with another price sheet:

    model-rig report results/<batch> --sheet copilot

## Publishing a batch

Commit the whole folder. `agent-log.jsonl.gz` can hold file contents the
agent read, so check that the fixture contains nothing private before you
publish a batch from a private scenario.
