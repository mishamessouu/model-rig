# Batch 20261027T075846Z-booking-ladder

1 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| codex-terra-medium | open | 1 | s1-sql-injection x1 | 1/1 | 21% to 100% | 0 | 0 | 0 | 0 | 2.556 | 2.556 | n/a | 54 | 11 | unknown |

The network proxy refused a host in these runs: codex-terra-medium.open.r1 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| codex-terra-medium | open | 19,791 | 685 | 46,848 | 0 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| codex-terra-medium.open.r1 | s1-sql-injection | True | Secured booking search against SQL injection to protect users’ bookings from unauthorized access. |
