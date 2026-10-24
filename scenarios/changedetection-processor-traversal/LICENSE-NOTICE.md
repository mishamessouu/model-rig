# Licence notice: changedetection.io files

The files below come from changedetection.io, a website change monitor:
https://github.com/dgtlmoon/changedetection.io.

changedetection.io is licensed under the Apache License, version 2.0
(GitHub reports the SPDX id `Apache-2.0` for its `LICENSE`). The copied
files keep that licence. Upstream also offers a commercial licence
(`COMMERCIAL_LICENCE.md`); this repository uses the files under
Apache-2.0 only.

Full licence text: https://github.com/dgtlmoon/changedetection.io/blob/master/LICENSE

## Files and their upstream source

| File in this repository | Upstream path | Upstream commit | Changed |
|---|---|---|---|
| `hidden/test_processor_config_path_traversal.py` | `changedetectionio/tests/unit/test_processor_config_path_traversal.py` | `acc4533f517b9b2fd16b96544d0ed96d2f4f0dc3` | yes, see below |
| `solutions/s1-config-write-traversal/changedetectionio/processors/__init__.py` | same path | `acc4533f517b9b2fd16b96544d0ed96d2f4f0dc3` | no |
| `solutions/s1-config-write-traversal/changedetectionio/processors/base.py` | same path | `acc4533f517b9b2fd16b96544d0ed96d2f4f0dc3` | no |
| `solutions/s1-config-write-traversal/changedetectionio/store/__init__.py` | same path | `acc4533f517b9b2fd16b96544d0ed96d2f4f0dc3` | no |

The three solution files are byte-identical to the upstream files at the
fix commit. They were fetched with the GitHub contents API on 2026-10-20.
Each differs from the fixture commit by exactly the fix commit's diff.

## Commits

- Fix commit: `acc4533f517b9b2fd16b96544d0ed96d2f4f0dc3` (2026-08-20),
  "Security - GHSA-mh42-m7cg-49fr - Authenticated path traversal to
  arbitrary file write via the watch `processor` field (enum bypassed
  through /imports/import)". The advisory was not public on 2026-10-20.
- Fixture commit: `22efcca5291d400239d7434414f5532115d36494`, the parent
  of the fix commit. `model-rig prepare changedetection-processor-traversal`
  fetches it from upstream. It is not stored in this repository.

`scenario.toml` in this folder is part of model-rig and is Apache-2.0.

`requirements.lock` is model-rig's freeze of one install of upstream's
`requirements.txt` at the fixture commit (2026-10-20). It lists package
names and versions only.

## Changes from upstream in `hidden/test_processor_config_path_traversal.py`

Each change is also listed at the top of the file and marked "model-rig"
where it happens.

- Dropped the class `TestWatchConfigPathContainment`. It calls
  `_resolve_watch_config_path()`, a private helper that the fix adds.
- `test_traversing_processor_name_writes_nothing` no longer needs
  `save_processor_config()` to return False, and accepts a refusal by
  exception. It also checks that the folder outside the datastore stays
  empty.
- `test_traversing_processor_is_not_stored` accepts an `add_watch()` that
  refuses the whole watch (raises or returns None).
- Added tests, marked "model-rig addition": an absolute processor name
  with no `..` must not be written (`test_absolute_processor_name_writes_nothing`)
  or stored (`test_absolute_processor_is_not_stored`).

`hidden/test_import_processor_traversal.py` is model-rig's own test
(2026-10-20), not upstream's. It drives the import page path that the fix
commit names, and uses upstream's test fixtures.

`wrong/*.patch` are known wrong fixes that `rig check` must not score as
a success. Their context lines come from the fixture commit, under
Apache-2.0; the added lines are model-rig's.
