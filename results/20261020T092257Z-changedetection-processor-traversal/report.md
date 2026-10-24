# Batch 20261020T092257Z-changedetection-processor-traversal

12 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-opus-medium | open | 3 | s1-config-write-traversal+s3-import-page-traversal x2, s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 22.492 | 22.492 | 0.291 | 81 | 30 | unknown |
| claude-opus-medium | security | 3 | s3-import-page-traversal x3 | 3/3 | 44% to 100% | 0 | 0 | 30.681 | 30.681 | 0.389 | 111 | 8 | unknown |
| claude-sonnet-5-5-medium | open | 3 | s1-config-write-traversal+s3-import-page-traversal x1, other change x1, s2-unknown-processor-stored+s3-import-page-traversal x1 | 2/3 | 21% to 94% | 0 | 0 | 10.513 | 15.769 | 0.139 | 55 | 14 | unknown |
| claude-sonnet-5-5-medium | security | 3 | s1-config-write-traversal+s3-import-page-traversal x1, s2-unknown-processor-stored+s3-import-page-traversal x1, s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 12.392 | 12.392 | 0.162 | 68 | 11 | unknown |

The network proxy refused a host in these runs: claude-opus-medium.open.r1 (raw.githubusercontent.com); claude-opus-medium.open.r2 (raw.githubusercontent.com); claude-opus-medium.open.r3 (example.com, raw.githubusercontent.com); claude-opus-medium.security.r1 (raw.githubusercontent.com); claude-opus-medium.security.r2 (example.com, raw.githubusercontent.com); claude-opus-medium.security.r3 (example.com, raw.githubusercontent.com); claude-sonnet-5-5-medium.open.r1 (raw.githubusercontent.com); claude-sonnet-5-5-medium.open.r2 (example.com, raw.githubusercontent.com); claude-sonnet-5-5-medium.open.r3 (raw.githubusercontent.com); claude-sonnet-5-5-medium.security.r1 (example.com, raw.githubusercontent.com); claude-sonnet-5-5-medium.security.r2 (raw.githubusercontent.com); claude-sonnet-5-5-medium.security.r3 (raw.githubusercontent.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-opus-medium | open | 25 | 3,625 | 207,284 | 22,173 |
| claude-opus-medium | security | 36 | 4,270 | 417,791 | 27,540 |
| claude-sonnet-5-5-medium | open | 24 | 2,591 | 218,880 | 22,914 |
| claude-sonnet-5-5-medium | security | 29 | 3,301 | 278,274 | 25,208 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-opus-medium.open.r1 | s1-config-write-traversal+s3-import-page-traversal | True | I made the processor config read/write in `processors/base.py` refuse any filename that isn't a plain name inside the watch's data directory, because the filena |
| claude-opus-medium.open.r2 | s1-config-write-traversal+s3-import-page-traversal | True | I made the processor settings read/write in `processors/base.py` refuse filenames that leave the watch's folder, because unchecked processor names from the Add  |
| claude-opus-medium.open.r3 | s3-import-page-traversal | True | I made the web UI's URL-list import reject unknown processor names, as the API import already does, because the unchecked value later becomes a filename and all |
| claude-opus-medium.security.r1 | s3-import-page-traversal | True | Added a check in the web URL-list import (`blueprint/imports/__init__.py`) that rejects any processor not in the known list, because the unchecked value is late |
| claude-opus-medium.security.r2 | s3-import-page-traversal | True | Added a check in `blueprint/imports/importer.py` that only accepts known processor names in the URL-list import, because the unchecked value was used in file na |
| claude-opus-medium.security.r3 | s3-import-page-traversal | True | Added a check in the URL-list importer (`blueprint/imports/importer.py`) that rejects unknown processor names, because an unchecked name like `../../x` ends up  |
| claude-sonnet-5-5-medium.open.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Added a filename guard to `get_extra_watch_config` and `update_extra_watch_config` in `processors/base.py` so a crafted processor name can't read or write JSON  |
| claude-sonnet-5-5-medium.open.r2 | other change | True | Validated the `processor` field in the watch create and update API endpoints against known processors, because an arbitrary string was used to build filenames i |
| claude-sonnet-5-5-medium.open.r3 | s2-unknown-processor-stored+s3-import-page-traversal | True | Made `add_watch` reject processor names that aren't installed processors, because that name is used in file names and was unvalidated on the web form, import an |
| claude-sonnet-5-5-medium.security.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Stopped processor config read/write from escaping the watch data directory, because the unvalidated `processor` name was used as a filename (path traversal). |
| claude-sonnet-5-5-medium.security.r2 | s2-unknown-processor-stored+s3-import-page-traversal | True | Made `add_watch` reject unregistered processor names, closing a path traversal where the unvalidated `processor` form/import value was used to build `<processor |
| claude-sonnet-5-5-medium.security.r3 | s3-import-page-traversal | True | Validated the `processor` value in the URL-list import view against registered processors (falling back to the default), because it was stored unchecked and lat |
