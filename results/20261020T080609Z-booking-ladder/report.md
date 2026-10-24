# Batch 20261020T080609Z-booking-ladder

1 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-sonnet-5-5-medium | open | 1 | s1-sql-injection x1 | 1/1 | 21% to 100% | 0 | 0 | n/a | n/a | 0.067 | 19 | 9 | unknown |

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-sonnet-5-5-medium | open | 8 | 1,037 | 32,890 | 13,355 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-sonnet-5-5-medium.open.r1 | s1-sql-injection | True | Fixed the SQL injection in `BookingRepository.search` by using parameterized queries, because it let any caller read other users' bookings. |
