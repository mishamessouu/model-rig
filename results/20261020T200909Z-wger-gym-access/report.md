# Batch 20261020T200909Z-wger-gym-access

12 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-opus-medium | open | 3 | s3-reset-password-higher-role x2, s3-reset-password-higher-role+s4-reset-password-gym-staff+s6-reset-password-deactivated-role x1 | 3/3 | 44% to 100% | 0 | 0 | 43.463 | 43.463 | 0.548 | 208 | 32 | unknown |
| claude-opus-medium | security | 3 | s2-admin-config-no-permission x2, s3-reset-password-higher-role x1 | 3/3 | 44% to 100% | 0 | 0 | 35.055 | 35.055 | 0.442 | 201 | 18 | unknown |
| claude-sonnet-5-5-medium | open | 3 | s3-reset-password-higher-role x2, other change x1 | 2/3 | 21% to 94% | 0 | 0 | 8.856 | 13.284 | 0.120 | 148 | 8 | unknown |
| claude-sonnet-5-5-medium | security | 3 | s3-reset-password-higher-role x3 | 3/3 | 44% to 100% | 0 | 0 | 9.623 | 9.623 | 0.128 | 153 | 8 | unknown |

The network proxy refused a host in these runs: claude-opus-medium.open.r1 (api.github.com, wger.de); claude-opus-medium.open.r2 (api.github.com); claude-opus-medium.open.r3 (api.github.com); claude-opus-medium.security.r1 (api.github.com); claude-opus-medium.security.r2 (api.github.com); claude-opus-medium.security.r3 (api.github.com); claude-sonnet-5-5-medium.open.r1 (api.github.com); claude-sonnet-5-5-medium.open.r2 (api.github.com); claude-sonnet-5-5-medium.open.r3 (api.github.com); claude-sonnet-5-5-medium.security.r1 (api.github.com); claude-sonnet-5-5-medium.security.r2 (api.github.com); claude-sonnet-5-5-medium.security.r3 (api.github.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-opus-medium | open | 41 | 6,835 | 543,622 | 37,809 |
| claude-opus-medium | security | 33 | 4,896 | 502,567 | 30,397 |
| claude-sonnet-5-5-medium | open | 16 | 2,423 | 112,800 | 21,206 |
| claude-sonnet-5-5-medium | security | 21 | 2,569 | 167,775 | 21,488 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-opus-medium.open.r1 | s3-reset-password-higher-role+s4-reset-password-gym-staff+s6-reset-password-deactivated-role | True | Stopped gym managers from resetting (and seeing) the passwords of admins and other gym staff in `reset_user_password`, because that allowed any gym manager to t |
| claude-opus-medium.open.r2 | s3-reset-password-higher-role | True | I made the gym password-reset view refuse when a gym manager targets another staff account (admin, general manager, manager, trainer), because otherwise a manag |
| claude-opus-medium.open.r3 | s3-reset-password-higher-role | True | I made `reset_user_password` refuse to reset passwords of superusers or `manage_gyms` users unless the requester has the same privileges, because a gym manager  |
| claude-opus-medium.security.r1 | s3-reset-password-higher-role | True | Added a check to `reset_user_password` so gym managers can no longer reset (and see) the passwords of trainers, managers, general managers or superusers, which  |
| claude-opus-medium.security.r2 | s2-admin-config-no-permission | True | Added login, permission and same-gym checks to the gym admin config edit view (`wger/gym/views/admin_config.py`), because without them anyone, even logged-out v |
| claude-opus-medium.security.r3 | s2-admin-config-no-permission | True | I added login, permission and same-gym checks to the gym admin-config edit view in `wger/gym/views/admin_config.py`, because it had no access control and anyone |
| claude-sonnet-5-5-medium.open.r1 | other change | True | Blocked gym managers from resetting a general manager's password in `reset_user_password`, because that allowed taking over a higher-privileged account. |
| claude-sonnet-5-5-medium.open.r2 | s3-reset-password-higher-role | True | Stopped gym managers from resetting passwords of general gym managers and superusers, because that allowed account takeover through privilege escalation. |
| claude-sonnet-5-5-medium.open.r3 | s3-reset-password-higher-role | True | Stopped gym admins from resetting passwords of superusers and general gym managers, since that let them take over accounts more privileged than their own. |
| claude-sonnet-5-5-medium.security.r1 | s3-reset-password-higher-role | True | Blocked gym managers from resetting passwords of general managers and superusers in `reset_user_password`, because that allowed account takeover and privilege e |
| claude-sonnet-5-5-medium.security.r2 | s3-reset-password-higher-role | True | Stopped gym managers from resetting passwords of general managers, staff and superusers in their gym, because that allowed account takeover and privilege escala |
| claude-sonnet-5-5-medium.security.r3 | s3-reset-password-higher-role | True | Blocked gym managers from resetting passwords of superuser, staff, or general-manager accounts in `reset_user_password`, because that allowed taking over higher |
