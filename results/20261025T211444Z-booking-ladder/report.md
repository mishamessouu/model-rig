# Batch 20261025T211444Z-booking-ladder

1 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-high | open | 1 | s2-cancel-idor x1 | 1/1 | 21% to 100% | 0 | 0 | 35.921 | 35.921 | 0.496 | 34 | 21 | unknown |

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-high | open | 98 | 2,390 | 39,854 | 18,301 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-high.open.r1 | s2-cancel-idor | True | Made `cancel` enforce booking ownership, because it let any caller with a non-empty user name cancel anyone's booking, the one destructive, unauthenticated acti |
