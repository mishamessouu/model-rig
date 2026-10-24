# Licence notice: InvenTree files

The files below come from InvenTree, an inventory management system:
https://github.com/inventree/InvenTree.

InvenTree is licensed under the MIT License (GitHub reports the SPDX id
`MIT` for its `LICENSE`), "Copyright (c) 2017 - InvenTree Developers".
The copied files keep that licence and its notice.

Full licence text: https://github.com/inventree/InvenTree/blob/master/LICENSE

## Files and their upstream source

| File in this repository | Upstream path | Upstream commit | Changed |
|---|---|---|---|
| `solutions/s1-attachment-list-read/src/backend/InvenTree/common/api.py` | same path | `528bb085d7ccde10d76a8c78580d4659cabbe45c` | no |
| `hidden/test_attachment_access.py` | `src/backend/InvenTree/common/test_api.py` (one test) | `528bb085d7ccde10d76a8c78580d4659cabbe45c` | yes, see below |

The solution file is byte-identical to upstream at the fix commit. Its git
blob id, `792b7dd79fa21f9e0f007269e159f382cb45684c`, matches `git
rev-parse` on the fix commit, fetched from upstream with git on
2026-10-20. It differs from the fixture commit by exactly the fix
commit's diff to that file.

## Commits

- Fix commit: `528bb085d7ccde10d76a8c78580d4659cabbe45c` (2026-08-23),
  "User permissions check for Attachment API (#12689)". No advisory was
  found on 2026-10-20.
- Fixture commit: `f16fb36b08f3e8dad5bead6966a819756b05b51a`, the parent
  of the fix commit. `model-rig prepare inventree-attachment-access`
  fetches it from upstream. It is not stored in this repository.

`scenario.toml` in this folder is part of model-rig and is Apache-2.0.

## Changes from upstream in `hidden/test_attachment_access.py`

- `test_attachment_read_permissions`, the test the fix added to
  `common/test_api.py`, is copied into a class of its own,
  `UpstreamAttachmentReadPermissionsTest`, with its body unchanged. It is
  not scored: it asserts 403 on a denied detail read, so a correct fix
  that answers 404 would fail it.
- Everything else in the file is model-rig's own (2026-10-20): the defect
  tests for the list and the detail view. They send the same requests as
  the upstream test, plus filtered, paginated, and search list requests,
  and check only that no attachment row, comment, or link leaks. A
  refusal by any status or by an exception passes.

`hidden/test_attachment_regression.py` is model-rig's own (2026-10-20). It
holds the allowed half of the upstream test, and it imports upstream's
visible attachment test classes from the fixture's `common/test_api.py`,
`common/tests.py`, and `part/test_api.py` without copying them.

`wrong/*.patch` are known wrong fixes that `rig check` must not score as
a success, and `right/*.patch` are correct fixes in another place or
shape. Their context lines come from `src/backend/InvenTree/common/api.py`
at the fixture commit, under MIT; the added lines are model-rig's.
