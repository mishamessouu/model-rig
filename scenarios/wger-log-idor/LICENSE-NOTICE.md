# Licence notice: wger files

The files below come from wger, a free workout and nutrition manager:
https://github.com/wger-project/wger.

wger is licensed under the GNU Affero General Public License, version 3
(GitHub reports the SPDX id `AGPL-3.0` for its `LICENSE.txt`). Each copied
file carries the upstream header, which says "either version 3 of the
License, or (at your option) any later version", so these files are
AGPL-3.0-or-later. They keep that licence. The Apache-2.0 licence of the
rest of this repository does not apply to them.

Full licence text: https://github.com/wger-project/wger/blob/master/LICENSE.txt

## Files and their upstream source

All four files are byte-identical to the upstream files at the fix commit.
This was checked against the GitHub contents API on 2026-10-16.

| File in this repository | Upstream path | Upstream commit |
|---|---|---|
| `hidden/test_api_ownership_checks.py` | `wger/manager/tests/test_api_ownership_checks.py` | `b29cf178651bbcc243d21673932e32bd42017893` |
| `solutions/s1-log-slot-entry-idor/wger/manager/api/views.py` | `wger/manager/api/views.py` | `b29cf178651bbcc243d21673932e32bd42017893` |
| `solutions/s1-log-slot-entry-idor/wger/manager/models/log.py` | `wger/manager/models/log.py` | `b29cf178651bbcc243d21673932e32bd42017893` |
| `solutions/s1-log-slot-entry-idor/wger/manager/models/slot_entry.py` | `wger/manager/models/slot_entry.py` | `b29cf178651bbcc243d21673932e32bd42017893` |

## Commits

- Fix commit: `b29cf178651bbcc243d21673932e32bd42017893` (2026-05-08),
  "Check slot_entry, next_log and day ownership on workout log/session
  APIs". Advisory GHSA-rjpf-7pf5-q54x, CVE-2026-46438.
- Fixture commit: `67fbf067a60d341cc5c6227257e3013ec31220e0`, the parent
  of the fix commit. `model-rig prepare wger-log-idor` fetches it from
  upstream. It is not stored in this repository.

`scenario.toml` in this folder is part of model-rig and is Apache-2.0.
