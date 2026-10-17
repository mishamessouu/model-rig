# Batch 20261016T205957Z-wger-log-idor

44 runs. Success means at least one planted defect fixed, no regression, and no agent error. Cost uses the `copilot` price sheet, in credits.

| Cell | Prompt | n | Picks | Success | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-opus-medium | open | 3 | s1-log-slot-entry-idor x2, s1-log-slot-entry-idor+s3-log-next-log-idor x1 | 3/3 | 0 | 0 | 37.888 | 37.888 | 0.473 | 228 | 23 |
| claude-opus-medium | security | 3 | s1-log-slot-entry-idor x3 | 3/3 | 0 | 0 | 63.935 | 63.935 | 0.775 | 223 | 2 |
| claude-sonnet-medium | open | 1 | other change x1 | 0/1 | 0 | 0 | n/a | n/a | 1.037 | 342 | 16 |
| claude-sonnet-medium | security | 1 | s2-session-day-idor x1 | 1/1 | 0 | 0 | n/a | n/a | 1.805 | 563 | 2 |
| codex-luna-high | ddd | 3 | other change x3 | 0/3 | 0 | 0 | 1.129 | n/a | n/a | 114 | 36 |
| codex-luna-high | open | 3 | other change x2, s1-log-slot-entry-idor x1 | 1/3 | 0 | 0 | 1.374 | 4.123 | n/a | 119 | 8 |
| codex-luna-high | security | 3 | other change x2, s1-log-slot-entry-idor x1 | 1/3 | 0 | 0 | 2.816 | 8.447 | n/a | 175 | 40 |
| codex-luna-medium | ddd | 3 | other change x3 | 0/3 | 0 | 0 | 0.953 | n/a | n/a | 115 | 18 |
| codex-luna-medium | open | 3 | other change x3 | 0/3 | 0 | 0 | 1.104 | n/a | n/a | 113 | 7 |
| codex-luna-medium | security | 3 | other change x2, s1-log-slot-entry-idor x1 | 1/3 | 0 | 0 | 1.078 | 3.233 | n/a | 105 | 6 |
| codex-sol-high | ddd | 3 | other change x3 | 0/3 | 0 | 0 | 28.701 | n/a | n/a | 213 | 106 |
| codex-sol-high | open | 3 | s1-log-slot-entry-idor x2, other change x1 | 2/3 | 0 | 0 | 20.205 | 30.308 | n/a | 147 | 54 |
| codex-sol-high | security | 3 | s1-log-slot-entry-idor x2, other change x1 | 2/3 | 0 | 0 | 29.469 | 44.204 | n/a | 188 | 18 |
| codex-sol-medium | ddd | 3 | other change x3 | 0/3 | 0 | 0 | 18.932 | n/a | n/a | 165 | 84 |
| codex-sol-medium | open | 3 | other change x2, s1-log-slot-entry-idor x1 | 1/3 | 0 | 0 | 18.540 | 55.619 | n/a | 142 | 38 |
| codex-sol-medium | security | 3 | s1-log-slot-entry-idor x3 | 3/3 | 0 | 0 | 22.253 | 22.253 | n/a | 173 | 48 |

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-opus-medium | open | 45 | 5,887 | 517,538 | 31,488 |
| claude-opus-medium | security | 73 | 8,809 | 1,182,225 | 45,284 |
| claude-sonnet-medium | open | 118 | 17,141 | 2,771,727 | 77,794 |
| claude-sonnet-medium | security | 152 | 31,640 | 5,163,667 | 113,930 |
| codex-luna-high | ddd | 33,533 | 3,631 | 612,352 | 0 |
| codex-luna-high | open | 35,180 | 4,012 | 822,016 | 0 |
| codex-luna-high | security | 58,981 | 6,714 | 1,890,176 | 0 |
| codex-luna-medium | ddd | 30,616 | 2,265 | 533,760 | 0 |
| codex-luna-medium | open | 38,863 | 2,740 | 577,920 | 0 |
| codex-luna-medium | security | 36,801 | 2,183 | 600,619 | 0 |
| codex-sol-high | ddd | 59,822 | 5,958 | 1,077,845 | 0 |
| codex-sol-high | open | 50,110 | 3,429 | 675,413 | 0 |
| codex-sol-high | security | 69,276 | 4,666 | 1,094,827 | 0 |
| codex-sol-medium | ddd | 41,223 | 3,812 | 687,531 | 0 |
| codex-sol-medium | open | 44,316 | 2,962 | 671,488 | 0 |
| codex-sol-medium | security | 51,053 | 3,290 | 875,179 | 0 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-opus-medium.open.r1 | s1-log-slot-entry-idor | True | I added an ownership check on `slot_entry` in `WorkoutLogViewSet` because without it any user could attach logs to another user's routine and change that user's |
| claude-opus-medium.open.r2 | s1-log-slot-entry-idor+s3-log-next-log-idor | True | I made `WorkoutLogViewSet` check ownership of `slot_entry` and `next_log`, so users can no longer attach logs to another user's exercise entries and change that |
| claude-opus-medium.open.r3 | s1-log-slot-entry-idor | True | Added `slot_entry` to the workout log API's ownership checks so users can no longer attach logs to other users' slot entries and change their routine progressio |
| claude-opus-medium.security.r1 | s1-log-slot-entry-idor | True | I added an ownership check on `slot_entry` in `WorkoutLogViewSet` so users can't attach logs to another user's slot entries and change the progression targets i |
| claude-opus-medium.security.r2 | s1-log-slot-entry-idor | True | Added a `slot_entry` ownership check to the workout log API (`WorkoutLogViewSet.get_owner_objects`) so users can no longer attach logs to another user's routine |
| claude-opus-medium.security.r3 | s1-log-slot-entry-idor | True | Added `slot_entry` to the ownership check in `WorkoutLogViewSet`, so users can no longer attach workout logs to another user's slot entries (an IDOR that corrup |
| claude-sonnet-medium.open.r1 | other change | True | Fixed an N+1 query bug in `UserDetailView.get_context_data` (wger/core/views/user.py) where it issued a separate `WorkoutLog` query per routine on the trainer/m |
| claude-sonnet-medium.security.r1 | s2-session-day-idor | True | Added `(Day, 'day')` to `WorkoutSessionViewSet.get_owner_objects()` in `wger/manager/api/views.py:279` so workout-session create/update requests are rejected if |
| codex-luna-high.ddd.r1 | other change | True | Fixed the until-failure workout-log rule so it uses the named domain constant and actually persists one repetition. |
| codex-luna-high.ddd.r2 | other change | True | Enforced serving unit ownership in shared meal item behavior because mismatched units can produce incorrect nutrition totals. |
| codex-luna-high.ddd.r3 | other change | True | Centralized the routine date range rule in the Routine model so every save path enforces the same invariant. |
| codex-luna-high.open.r1 | other change | True | Made `is_temporary` read-only to protect the account trustworthiness rule. |
| codex-luna-high.open.r2 | s1-log-slot-entry-idor | True | Checked slot entry ownership when creating or updating workout logs to prevent cross-user references to private routines. |
| codex-luna-high.open.r3 | other change | True | Secured proxy login redirects against external destinations because an untrusted `next` URL could send authenticated users to a malicious site. |
| codex-luna-high.security.r1 | other change | True | Require POST for trainer impersonation to prevent cross-site session switching. |
| codex-luna-high.security.r2 | s1-log-slot-entry-idor | True | Added slot ownership validation to prevent cross-user workout log references from affecting another user’s routine. |
| codex-luna-high.security.r3 | other change | True | Block inactive users in the auth proxy backend to prevent deactivated accounts from logging in or retaining access through existing sessions. |
| codex-luna-medium.ddd.r1 | other change | True | Use each nutrition plan’s calorie goal for its approximation because that is the goal the plan stores. |
| codex-luna-medium.ddd.r2 | other change | True | Enforced the rest day rule when saving slots because the existing day save rule could be bypassed by adding slots afterward. |
| codex-luna-medium.ddd.r3 | other change | True | Centralized nutritional value aggregation in `NutritionalValues` so meals and plans share one domain operation. |
| codex-luna-medium.open.r1 | other change | True | Return 404 for missing related objects to make API errors predictable and avoid server errors. |
| codex-luna-medium.open.r2 | other change | True | Return a 404 for nonexistent related-object IDs in owner checks, so invalid references do not become server errors. |
| codex-luna-medium.open.r3 | other change | True | Tightened API path detection because accidental substring matches could disrupt guest-user creation on unrelated routes. |
| codex-luna-medium.security.r1 | other change | True | Reject nonexistent related IDs in owner checks so invalid references fail cleanly instead of causing server errors. |
| codex-luna-medium.security.r2 | other change | True | Restricted proxy login redirects to the current host to prevent redirecting authenticated users to attacker controlled sites. |
| codex-luna-medium.security.r3 | s1-log-slot-entry-idor | True | Checked workout log slot ownership to prevent users from attaching logs to another account’s routine. |
| codex-sol-high.ddd.r1 | other change | True | Made Routine own its date bounds so the existing business rule also applies outside the API. |
| codex-sol-high.ddd.r2 | other change | True | Moved routine date validation into `Routine` so API calls and model saves share one rule enforcing ordered dates and the 120-day limit. |
| codex-sol-high.ddd.r3 | other change | True | Moved progression requirement validation into `ConfigRequirements`, with the API delegating to it, so domain calculations and API requests enforce the same busi |
| codex-sol-high.open.r1 | other change | True | Check ownership before serving cached workout history, because private training data must remain protected after access changes. |
| codex-sol-high.open.r2 | s1-log-slot-entry-idor | True | Require ownership of linked exercise slots to prevent users from attaching logs to someone else’s training plan. |
| codex-sol-high.open.r3 | s1-log-slot-entry-idor | True | Enforced exercise-slot ownership to prevent users from injecting logs into another user’s workout progression. |
| codex-sol-high.security.r1 | s1-log-slot-entry-idor | True | Added slot-entry ownership validation to prevent cross-user manipulation of workout progression. |
| codex-sol-high.security.r2 | s1-log-slot-entry-idor | True | Added ownership validation for workout-log `slot_entry` references to prevent users from manipulating another user’s training progression. |
| codex-sol-high.security.r3 | other change | True | Enforced permissions before routine cache reads because cached data remained accessible after owners made routines private. |
| codex-sol-medium.ddd.r1 | other change | True | Enforced slot-entry ownership in WorkoutLog to prevent cross-user logs from contaminating routine progression. |
| codex-sol-medium.ddd.r2 | other change | True | Centralized routine date rules in the domain model so validation is available beyond the API. |
| codex-sol-medium.ddd.r3 | other change | True | Centralized routine date bounds in the domain model so model validation and the API share one business rule. |
| codex-sol-medium.open.r1 | other change | True | Check ownership before serving cached workout history to prevent unauthorized access to private training data. |
| codex-sol-medium.open.r2 | other change | True | Enforce ownership before serving cached workout history so cached responses cannot bypass privacy checks. |
| codex-sol-medium.open.r3 | s1-log-slot-entry-idor | True | Prevented users from attaching workout logs to another user’s exercise slot, closing a missing ownership check. |
| codex-sol-medium.security.r1 | s1-log-slot-entry-idor | True | Added `slot_entry` ownership validation to prevent cross-user workout-log injection. |
| codex-sol-medium.security.r2 | s1-log-slot-entry-idor | True | Added ownership validation for workout-log slot entries to prevent cross-user progression tampering. |
| codex-sol-medium.security.r3 | s1-log-slot-entry-idor | True | Added ownership validation for workout-log `slot_entry` links to prevent users from poisoning another user’s training progression. |
