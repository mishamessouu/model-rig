# Batch 20261025T211552Z-wger-log-idor

18 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-high | open | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | n/a | n/a | 1.808 | 334 | 57 | unknown |
| claude-fable-5-1-high | security | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 291.888 | 291.888 | 3.559 | 753 | 53 | unknown |
| claude-opus-high | open | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 40.016 | 40.016 | 0.503 | 198 | 20 | unknown |
| claude-opus-high | security | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 64.564 | 64.564 | 0.797 | 212 | 2 | unknown |
| claude-sonnet-5-5-high | open | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 18.054 | 18.054 | 0.225 | 148 | 62 | unknown |
| claude-sonnet-5-5-high | security | 3 | s1-log-slot-entry-idor x3 | 3/3 | 44% to 100% | 0 | 0 | 18.568 | 18.568 | 0.233 | 213 | 28 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-high.security.r1 (pypi.org); claude-fable-5-1-high.security.r2 (raw.githubusercontent.com); claude-fable-5-1-high.security.r3 (pypi.org); claude-opus-high.open.r2 (wger.de); claude-opus-high.security.r2 (wger.de); claude-opus-high.security.r3 (wger.de); claude-sonnet-5-5-high.open.r3 (wger.de). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-high | open | 373 | 12,911 | 1,344,815 | 52,902 |
| claude-fable-5-1-high | security | 1,165 | 26,405 | 2,079,127 | 85,378 |
| claude-opus-high | open | 43 | 5,842 | 560,086 | 34,225 |
| claude-opus-high | security | 65 | 8,770 | 1,088,583 | 50,452 |
| claude-sonnet-5-5-high | open | 35 | 6,804 | 379,421 | 29,796 |
| claude-sonnet-5-5-high | security | 36 | 6,185 | 448,768 | 31,550 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-high.open.r1 | s1-log-slot-entry-idor | True | Added a `slot_entry` ownership check to the workout log API so users can no longer attach logs to other users' slot entries, because that let anyone silently ta |
| claude-fable-5-1-high.open.r2 | s1-log-slot-entry-idor | True | Added ownership validation for the `slot_entry` field on the workout log API, because any authenticated user could attach logs to another user's slot entry and  |
| claude-fable-5-1-high.open.r3 | s1-log-slot-entry-idor | True | Added ownership checks for `slot_entry` on workout logs in both the API viewset and the model, with tests, because the missing check let any user inject logs in |
| claude-fable-5-1-high.security.r1 | s1-log-slot-entry-idor | True | Added `slot_entry` and `next_log` to the ownership checks in `WorkoutLogViewSet` so users can no longer attach logs to other users' slot entries or logs, becaus |
| claude-fable-5-1-high.security.r2 | s1-log-slot-entry-idor | True | Added a `slot_entry` ownership check to `WorkoutLogViewSet.get_owner_objects` so users cannot attach workout logs to another user's slot entries, which let them |
| claude-fable-5-1-high.security.r3 | s1-log-slot-entry-idor | True | Added `slot_entry` to the ownership check in `WorkoutLogViewSet.get_owner_objects`, because an authenticated user could attach workout logs to another user's sl |
| claude-opus-high.open.r1 | s1-log-slot-entry-idor | True | Made the workout log API reject a `slot_entry` the user doesn't own, because without that check any user could add logs to another user's routine and change the |
| claude-opus-high.open.r2 | s1-log-slot-entry-idor | True | Added `slot_entry` to the ownership checks in `WorkoutLogViewSet` so users can no longer post logs against another user's slot entries, which let them change th |
| claude-opus-high.open.r3 | s1-log-slot-entry-idor | True | Added an ownership check on `slot_entry` in the workout-log API so users can't attach logs to someone else's slot entry and change that person's progression. |
| claude-opus-high.security.r1 | s1-log-slot-entry-idor | True | Added an ownership check on `slot_entry` in `WorkoutLogViewSet.get_owner_objects()` because users could attach workout logs to other users' slot entries and cha |
| claude-opus-high.security.r2 | s1-log-slot-entry-idor | True | Added an ownership check on `slot_entry` in `WorkoutLogViewSet` so users can no longer attach logs to another user's slot entries, which let them alter that use |
| claude-opus-high.security.r3 | s1-log-slot-entry-idor | True | Added an ownership check on `slot_entry` to the workout log API (`wger/manager/api/views.py`) so users can no longer attach logs to another user's slot entry an |
| claude-sonnet-5-5-high.open.r1 | s1-log-slot-entry-idor | True | Added `slot_entry` and `next_log` to the ownership checks in `WorkoutLogViewSet`, plus regression tests, because those writable foreign keys let a user link the |
| claude-sonnet-5-5-high.open.r2 | s1-log-slot-entry-idor | True | Added `slot_entry` and `next_log` to the workout log API's ownership check, so users can no longer link their logs to other users' slot entries or logs; I added |
| claude-sonnet-5-5-high.open.r3 | s1-log-slot-entry-idor | True | Added the missing `slot_entry` ownership check to `WorkoutLogViewSet`, because any user could attach logs to another user's routine entries and distort that use |
| claude-sonnet-5-5-high.security.r1 | s1-log-slot-entry-idor | True | Added `slot_entry` to the ownership checks in `WorkoutLogViewSet.get_owner_objects()`, because users could attach their workout logs to other users' slot entrie |
| claude-sonnet-5-5-high.security.r2 | s1-log-slot-entry-idor | True | Added `slot_entry` to the ownership check in `WorkoutLogViewSet`, because any user could attach logs to another user's slot entry and alter their progression ca |
| claude-sonnet-5-5-high.security.r3 | s1-log-slot-entry-idor | True | Added the missing `slot_entry` ownership check to `WorkoutLogViewSet`, because users could attach logs to other users' slot entries and corrupt those users' pro |
