# Licence notice: Label Studio files

The files below come from Label Studio, an open source data labeling
tool: https://github.com/HumanSignal/label-studio.

Label Studio is licensed under the Apache License, version 2.0 (GitHub
reports the SPDX id `Apache-2.0`). The rest of this repository is also
Apache-2.0. Upstream's `NOTICE` file reads, in full:

    Label Studio (TM)
    Copyright (c) 2019-2021  Heartex, Inc. All Rights Reserved.
    Source code in this repository is licensed under the Apache License
    Version 2.0, Please see LICENSE for more information.

Full licence text: https://github.com/HumanSignal/label-studio/blob/develop/LICENSE

## Files and their upstream source

| File in this repository | Upstream path | Upstream commit | Changed |
|---|---|---|---|
| `hidden/test_inline_query_traversal.py` | `label_studio/tests/data_manager/test_inline_query_traversal.py` | `7e2f696403da6802b82171abd299fd39c5ef2b37` | yes, see below |
| `solutions/s1-inline-filter-traversal/label_studio/data_manager/prepare_params.py` | `label_studio/data_manager/prepare_params.py` | `7e2f696403da6802b82171abd299fd39c5ef2b37` | no |

The solution file is byte-identical to the upstream file at the fix
commit. Its git blob id, `520903c`, matched the GitHub contents API on
2026-10-20.

## Commits

- Fix commit: `7e2f696403da6802b82171abd299fd39c5ef2b37` (2026-09-01),
  "Merge commit from fork". Advisories GHSA-9q39-f8w9-75wm (filters) and
  GHSA-xw23-r93p-26jm (ordering), both a bypass of the CVE-2023-47117
  fix, patched in 1.23.1.
- Fixture commit: `57ec9153aa0e155815c274297ecca2a23bba3f0e`, the parent
  of the fix commit. `python3 -m rig prepare labelstudio-orm-traversal`
  fetches it from upstream. It is not stored in this repository.

`scenario.toml` in this folder is part of model-rig.

## Changes from upstream in `hidden/test_inline_query_traversal.py`

- A comment at the top names the source and lists these changes.
- The five "blocked" tests accept 400 or 403 (`REFUSED`) instead of 400
  only.
- Added tests, each marked "model-rig addition": a filter with the
  `contains` operator; a filter in a POST body to the data manager
  actions API (`delete_tasks`), which also checks that the task was not
  deleted; an ordering stored in a View through the View API.

`wrong/*.patch` are known wrong fixes that `rig check` must not score as
a success. Their context lines come from Label Studio at the fixture
commit, under Apache-2.0; the added lines are model-rig's.
