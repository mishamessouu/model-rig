# Batch 20261020T101406Z-labelstudio-orm-traversal

12 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-opus-medium | open | 3 | s2-ordering-traversal x2, s1-inline-filter-traversal+s2-ordering-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | n/a | n/a | 0.625 | 198 | 60 | unknown |
| claude-opus-medium | security | 3 | s1-inline-filter-traversal+s2-ordering-traversal x2, s1-inline-filter-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 40.660 | 40.660 | 0.509 | 168 | 7 | unknown |
| claude-sonnet-5-5-medium | open | 3 | other change x2, s1-inline-filter-traversal+s2-ordering-traversal x1 | 0/3 | 0% to 56% | 2 | 0 | 7.684 | n/a | 0.100 | 154 | 12 | unknown |
| claude-sonnet-5-5-medium | security | 3 | s2-ordering-traversal x3 | 3/3 | 44% to 100% | 0 | 0 | 10.697 | 10.697 | 0.142 | 113 | 6 | unknown |

The network proxy refused a host in these runs: claude-opus-medium.open.r1 (pypi.org); claude-opus-medium.open.r2 (pypi.org); claude-opus-medium.open.r3 (pypi.org); claude-opus-medium.security.r1 (pypi.org); claude-opus-medium.security.r2 (pypi.org); claude-opus-medium.security.r3 (pypi.org); claude-sonnet-5-5-medium.open.r1 (pypi.org); claude-sonnet-5-5-medium.open.r2 (pypi.org); claude-sonnet-5-5-medium.open.r3 (pypi.org); claude-sonnet-5-5-medium.security.r1 (pypi.org); claude-sonnet-5-5-medium.security.r2 (pypi.org); claude-sonnet-5-5-medium.security.r3 (pypi.org). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-opus-medium | open | 38 | 6,139 | 474,269 | 40,776 |
| claude-opus-medium | security | 39 | 6,865 | 493,976 | 34,070 |
| claude-sonnet-5-5-medium | open | 16 | 2,607 | 116,500 | 15,637 |
| claude-sonnet-5-5-medium | security | 22 | 2,835 | 206,372 | 23,172 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-opus-medium.open.r1 | s2-ordering-traversal | True | Added a check to Data Manager sorting (`apply_ordering`) that blocks following links into related models, because sort fields were never checked and could be us |
| claude-opus-medium.open.r2 | s2-ordering-traversal | True | Added foreign-key traversal validation to Data Manager ordering columns in `apply_ordering`, because filters were already hardened against ORM relation-walking  |
| claude-opus-medium.open.r3 | s1-inline-filter-traversal+s2-ordering-traversal | True | Enforced the `__` foreign-key guard inside `apply_filters`/`apply_ordering` because ad-hoc `query` filters and sorting skipped the serializer check, which let a |
| claude-opus-medium.security.r1 | s1-inline-filter-traversal | True | Added the `FilterSerializer.validate_column` check to `apply_filters` so ad-hoc `?query=`/body filters can no longer follow links like `updated_by__password` to |
| claude-opus-medium.security.r2 | s1-inline-filter-traversal+s2-ordering-traversal | True | Added a `__` traversal check to `preprocess_field_name` because filters and ordering sent directly in requests skipped the view serializer's check, so users cou |
| claude-opus-medium.security.r3 | s1-inline-filter-traversal+s2-ordering-traversal | True | Added the `__` (linked-field) check to `preprocess_field_name` so filters and sorting sent directly to `/api/tasks`, and sorting saved in views, can no longer r |
| claude-sonnet-5-5-medium.open.r1 | other change | True | In `preprocess_field_name`, replaced the all-occurrences `.replace('data.', ...)` with a prefix-only `removeprefix`, because the function's docstring forbids `r |
| claude-sonnet-5-5-medium.open.r2 | s1-inline-filter-traversal+s2-ordering-traversal | False | Rejected filter and ordering column names that traverse ORM relations (`a__b` outside `data__`) in `data_manager/managers.py`, because they let clients probe re |
| claude-sonnet-5-5-medium.open.r3 | other change | False | Replaced the `exists()` plus `[0]` query pair in `apply_filters` value-type detection with a single `[:1]` fetch, so each filter on a non-built-in column costs  |
| claude-sonnet-5-5-medium.security.r1 | s2-ordering-traversal | True | Blocked ORM relation traversal (`__` paths) in Data Manager ordering in `apply_ordering`, because unvalidated ordering fields could leak related-model data (e.g |
| claude-sonnet-5-5-medium.security.r2 | s2-ordering-traversal | True | Added a `__` relation-path check to `apply_ordering` in `managers.py`, because ordering by fields like `annotations__completed_by__password` was unvalidated and |
| claude-sonnet-5-5-medium.security.r3 | s2-ordering-traversal | True | Block relation-traversal (`__`) field names in Data Manager ordering unless allowlisted, because `apply_ordering` fed them unchecked into `F()` and let clients  |
