# Licence notice: MLflow files

The files below come from MLflow, an open source platform for the
machine learning lifecycle: https://github.com/mlflow/mlflow.

MLflow is licensed under the Apache License, version 2.0 (GitHub reports
the SPDX id `Apache-2.0` for its `LICENSE.txt`). The copied files keep
that licence. Upstream keeps no `NOTICE` file; its `LICENSE.txt` starts
with "Copyright 2018 Databricks, Inc. All rights reserved."

Full licence text: https://github.com/mlflow/mlflow/blob/master/LICENSE.txt

## Files and their upstream source

| File in this repository | Upstream path | Upstream commit | Changed |
|---|---|---|---|
| `hidden/test_graphql_model_version_permissions.py` | `tests/server/auth/test_auth.py` and `tests/server/auth/test_client_workspace.py` (parts) | `395db9deef3d7487511eed8df85f77aedd799de1` | yes, see below |
| `solutions/s1-nested-run-model-versions/mlflow/server/auth/__init__.py` | `mlflow/server/auth/__init__.py` | `395db9deef3d7487511eed8df85f77aedd799de1` | no |

The solution file is byte-identical to the upstream file at the fix
commit. Its git blob id, `1af20e8`, matched the GitHub contents API on
2026-10-20. It differs from the fixture commit by exactly the fix
commit's change to that file (27 lines added, 3 removed).

## Commits

- Fix commit: `395db9deef3d7487511eed8df85f77aedd799de1` (2026-09-16),
  "Filter nested `run.modelVersions` GraphQL field by registered-model
  permission (GHSA-f253-vggg-rwh8) (#25905)". The advisory was not
  public on 2026-10-20.
- Fixture commit: `08dfbc936c6c4f1e2585b554d69c094cb0f63c68`, the parent
  of the fix commit. `python3 -m rig prepare mlflow-graphql-permission`
  fetches it from upstream. It is not stored in this repository.

`scenario.toml` in this folder is part of model-rig.

## Changes from upstream in `hidden/test_graphql_model_version_permissions.py`

Each change is also listed at the top of the file and marked "model-rig"
where it happens.

- The file collects four upstream tests from two upstream modules. It
  imports the fixtures and helpers it needs from those two modules
  (`client`, `_graphql_query`, `workspace_setup`, and others), which the
  scorer restores from the fixture.
- `test_graphql_nested_run_model_versions_filtered_by_model_permission`
  and `test_nested_run_model_versions_use_requested_workspace_grants` are
  upstream's text, unchanged. So is the helper
  `_graphql_get_run_model_versions`.
- `test_graphql_search_model_versions_judges_prompts_by_prompt_grants` is
  split in two. `..._model_grant_does_not_reveal_prompt` keeps the
  wildcard registered-model reader, and first checks that the admin
  sees the prompt version (model-rig addition), so the empty list it
  then expects comes from the filter, not from the query.
  `..._prompt_grant_reveals_prompt` keeps the prompt reader.
- Added tests, each marked "model-rig addition": a reader with READ on
  every model, a wildcard reader, and the admin each see every nested
  version through `mlflowGetRun` and `mlflowSearchRuns`; a grant made
  between two requests shows in the second.

`wrong/*.patch` are known wrong fixes that `rig check` must not score as
a success. Their context lines come from MLflow at the fixture commit,
under Apache-2.0; the added lines are model-rig's.
