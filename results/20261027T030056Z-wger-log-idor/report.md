# Batch 20261027T030056Z-wger-log-idor

6 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-medium | open | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 71.985 | 71.985 | 0.911 | 232 | 42 | unknown |
| claude-fable-5-1-medium | security | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 123.210 | 123.210 | 1.549 | 292 | 28 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-medium.security.r1 (pypi.org). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-medium | open | 429 | 6,434 | 301,095 | 25,486 |
| claude-fable-5-1-medium | security | 727 | 10,313 | 726,533 | 42,202 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-medium.open.r1 | s1-log-slot-entry-idor | True | Added an ownership check for `slot_entry` on the workout log API, because it let any user attach logs to another user's routine, and access control bugs matter  |
| claude-fable-5-1-medium.open.r2 | s1-log-slot-entry-idor | True | Closed an insecure direct object reference in the workout log API by adding `slot_entry` to the ownership check, because it let any user attach logs to another  |
| claude-fable-5-1-medium.open.r3 | s1-log-slot-entry-idor | True | Closed an insecure direct object reference in the workout log API by adding `slot_entry` and `next_log` to the ownership check, because it let any user inject l |
| claude-fable-5-1-medium.security.r1 | s1-log-slot-entry-idor | True | Enforced ownership of `slot_entry` on workout logs in the API viewset and model save, because it let any user inject logs into another user's routine and corrup |
| claude-fable-5-1-medium.security.r2 | s1-log-slot-entry-idor | True | Added `slot_entry` to the ownership checks in `WorkoutLogViewSet.get_owner_objects` because users could attach workout logs to other users' routine slot entries |
| claude-fable-5-1-medium.security.r3 | s1-log-slot-entry-idor | True | Added `slot_entry` to `WorkoutLogViewSet.get_owner_objects` so the workout log API rejects logs attached to another user's slot entry, closing a cross-user writ |
