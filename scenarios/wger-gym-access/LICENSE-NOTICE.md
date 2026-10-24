# Licence notice: wger files

The files below come from wger Workout Manager:
https://github.com/wger-project/wger.

wger is licensed under the GNU Affero General Public License, version 3
or later (GitHub reports the SPDX id `AGPL-3.0` for its `LICENSE`). The
files below keep that licence. The Apache-2.0 licence of the rest of this
repository does not apply to them.

Full licence text: https://github.com/wger-project/wger/blob/master/LICENSE.txt

## Files and their upstream source

| File in this repository | Upstream path | Upstream commit | Changed |
|---|---|---|---|
| `hidden/test_gym_config_access.py` | `wger/gym/tests/test_config.py` and `wger/gym/tests/test_admin_config.py` (parts) | `dd28603abe5b5e3b33eb61e0f3baa94b36052e87` and `d0ca31ca89be213a4c84b6793df2247fa85469b1` | yes, see below |
| `solutions/s1-gym-config-other-gym/wger/gym/views/config.py` | same path | `dd28603abe5b5e3b33eb61e0f3baa94b36052e87` | no |
| `solutions/s2-admin-config-no-permission/wger/gym/views/admin_config.py` | same path | `d0ca31ca89be213a4c84b6793df2247fa85469b1` | no |
| `hidden/test_reset_password_role.py` | `wger/gym/tests/test_user.py` (part) | `5c1817e9d56bed3c887b7dcc7b5434dd80de12a6` | yes, see below |
| `solutions/s3-reset-password-higher-role/wger/gym/views/gym.py` | same path | `5c1817e9d56bed3c887b7dcc7b5434dd80de12a6` | no |
| `solutions/s3-reset-password-higher-role/wger/gym/helpers.py` | same path | `5c1817e9d56bed3c887b7dcc7b5434dd80de12a6` | no |

The solution files are byte-identical to upstream at their fix
commits. Their git blob ids, `ad29ae716f755c12e0a9d1dd6f736a6947812195`
(`config.py`) and `00de7edfbca131710f414871d867972684215299`
(`admin_config.py`), match a fetch of upstream on 2026-10-20. The blob
ids `a911fc751977b6578a7dc1c20a72f2e26a42dd50` (`gym.py`) and
`fa669f4be032af90458ed804faf010edd7d3fab8` (`helpers.py`) match a fetch
on 2026-10-23. Each differs from the fixture commit by exactly its fix
commit's diff to that file. The s3 solution leaves out the third file of
5c1817e9, `wger/core/views/user.py`, whose hole is not scored.

## Commits

- Fix commit `d0ca31ca89be213a4c84b6793df2247fa85469b1` (2026-10-04),
  "Enforce the permission on the gym admin config edit view". Parent
  `6a90e34fce4419f4d5cafdf635e14f10c280ef11`.
- Fix commit `dd28603abe5b5e3b33eb61e0f3baa94b36052e87` (2026-10-04),
  "Compare the gym of the config in the gym config edit view". Parent
  `5c1817e9d56bed3c887b7dcc7b5434dd80de12a6`.
- Fix commit `5c1817e9d56bed3c887b7dcc7b5434dd80de12a6` (2026-10-04),
  "Check the target's role before gym admins act on an account". Parent
  `f0a8493f0b3e05d02801487e31d607d752c1e8cc`. `wger/gym/views/gym.py` and
  `wger/gym/helpers.py` are the same at the fixture commit and at this
  parent, so its reset holes are open in the fixture. Scored as s3 to s6
  from 2026-10-23.
- No published advisory names any of the three fixes on 2026-10-23.
- Fixture commit: `6a90e34fce4419f4d5cafdf635e14f10c280ef11`, the parent
  of the earlier fix. `wger/gym/views/config.py` is the same there as at
  the later fix's parent, so both holes are open and no revert patch is
  needed. `model-rig prepare wger-gym-access` fetches it from upstream. It
  is not stored in this repository.

`scenario.toml` in this folder is part of model-rig and is Apache-2.0.

## Changes from upstream in `hidden/test_reset_password_role.py`

Each change is also listed at the top of the file and marked "model-rig"
where it happens.

- The class `ResetPasswordTargetRoleTestCase` (from `test_user.py`)
  splits into one class per defect (s3, s4, s5) and one for the
  legitimate resets. Shared helpers move into a base class.
- The defect tests no longer assert a 403. They check that the target's
  password hash is unchanged and that no password the response shows
  signs the target in. A request that raises in the view counts as a
  refusal.
- The legitimate-reset tests keep the 200 and also check that the
  password changed and that the shown password signs the target in.
- Added tests, marked "model-rig addition":
  `test_manager_cannot_reset_general_manager`,
  `test_manager_cannot_reset_superuser` (s3),
  `test_general_manager_can_reset_manager` (regression), and the class
  `ResetPasswordDeactivatedRoleTestCase` (s6).

## Changes from upstream in `hidden/test_gym_config_access.py`

Each change is also listed at the top of the file and marked "model-rig"
where it happens.

- The classes `EditGymConfigOwnershipTestCase` (from `test_config.py`)
  and `EditConfigPermissionTestCase` (from `test_admin_config.py`) move
  into one file.
- `test_config_of_other_gym` and `test_owner_without_permission` no
  longer assert a 403. They check that the config is unchanged. A request
  that raises in the view counts as a refusal.
- `edit()` returns the response, not the status code, and the
  unpermitted owner's helper `strip()` is shared.
- Added tests, marked "model-rig addition":
  `test_config_of_other_gym_with_two_fields`,
  `test_config_of_other_gym_is_not_shown`,
  `test_owner_without_permission_other_value` (defect tests), and
  `test_config_of_own_gym_same_id`, `test_manager_owner_with_permission`
  (regression tests).
- `test_config_of_own_gym` stays but is not scored. It fails on the
  unfixed code, which refuses that legitimate edit.

`wrong/*.patch` are known wrong fixes that `rig check` must not score as
a success, and `right/*.patch` are correct fixes in other places that it
must score as their `Fixes:` line says. Their context lines come from the
fixture commit, under AGPL-3.0; the added lines are model-rig's.
