# Batch 20261020T080644Z-wger-log-idor

6 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-sonnet-5-5-medium | open | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 7.220 | 7.220 | 0.095 | 185 | 7 | unknown |
| claude-sonnet-5-5-medium | security | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 10.023 | 10.023 | 0.128 | 191 | 4 | unknown |

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-sonnet-5-5-medium | open | 18 | 2,136 | 130,717 | 15,090 |
| claude-sonnet-5-5-medium | security | 26 | 3,279 | 214,645 | 18,371 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-sonnet-5-5-medium.open.r1 | s1-log-slot-entry-idor | True | Added `slot_entry` and `next_log` to the ownership checks in `WorkoutLogViewSet`, so users can't link their workout logs to other users' slot entries or logs (a |
| claude-sonnet-5-5-medium.open.r2 | s1-log-slot-entry-idor | True | Added `slot_entry` and `next_log` to the ownership checks in `WorkoutLogViewSet`, because those foreign keys were writable on the log API without checking that  |
| claude-sonnet-5-5-medium.open.r3 | s1-log-slot-entry-idor | True | Added `slot_entry` to the ownership checks in `WorkoutLogViewSet`, so users can't attach their workout logs to another user's slot entries. |
| claude-sonnet-5-5-medium.security.r1 | s1-log-slot-entry-idor | True | Added a `slot_entry` ownership check to `WorkoutLogViewSet` in `wger/manager/api/views.py`, so users can't create or update workout logs that reference another  |
| claude-sonnet-5-5-medium.security.r2 | s1-log-slot-entry-idor | True | Added `slot_entry` and `next_log` to `WorkoutLogViewSet.get_owner_objects()` so users can't link their workout logs to other users' slot entries or logs. |
| claude-sonnet-5-5-medium.security.r3 | s1-log-slot-entry-idor | True | Added an ownership check on `slot_entry` in the workout log API (replacing the dead `session` check), so users can't attach logs to other users' slot entries. |
