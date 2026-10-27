# Batch 20261025T231744Z-changedetection-processor-traversal

18 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-high | open | 3 | s1-config-write-traversal+s3-import-page-traversal x2, s1-config-write-traversal+s2-unknown-processor-stored+s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 133.676 | 133.676 | 1.675 | 247 | 149 | unknown |
| claude-fable-5-1-high | security | 3 | s1-config-write-traversal+s3-import-page-traversal x2, s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 117.705 | 117.705 | 1.512 | 195 | 88 | unknown |
| claude-opus-high | open | 3 | s3-import-page-traversal x2, s1-config-write-traversal+s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 33.561 | 33.561 | 0.430 | 228 | 42 | unknown |
| claude-opus-high | security | 3 | s3-import-page-traversal x2, s2-unknown-processor-stored+s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 30.321 | 30.321 | 0.392 | 90 | 14 | unknown |
| claude-sonnet-5-5-high | open | 3 | s2-unknown-processor-stored+s3-import-page-traversal x2, s1-config-write-traversal+s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 17.742 | 17.742 | 0.233 | 68 | 44 | unknown |
| claude-sonnet-5-5-high | security | 3 | s3-import-page-traversal x3 | 3/3 | 44% to 100% | 0 | 0 | 19.975 | 19.975 | 0.259 | 79 | 9 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-high.open.r1 (example.com, raw.githubusercontent.com); claude-fable-5-1-high.open.r2 (example.com, raw.githubusercontent.com); claude-fable-5-1-high.open.r3 (changedetection.io, example.com, raw.githubusercontent.com); claude-fable-5-1-high.security.r1 (example.com, raw.githubusercontent.com); claude-fable-5-1-high.security.r2 (changedetection.io, raw.githubusercontent.com); claude-fable-5-1-high.security.r3 (raw.githubusercontent.com); claude-opus-high.open.r1 (browser-chrome, example.com, raw.githubusercontent.com, somesite-abc.com, unraid.net, www.cooeeelnews.com, www.coolnews.com, www.test.com); claude-opus-high.open.r2 (example.com, raw.githubusercontent.com); claude-opus-high.open.r3 (browser-chrome, example.com, raw.githubusercontent.com, somesite-abc.com, unraid.net, www.cooeeelnews.com, www.coolnews.com, www.test.com); claude-opus-high.security.r1 (example.com, raw.githubusercontent.com); claude-opus-high.security.r2 (example.com, raw.githubusercontent.com); claude-opus-high.security.r3 (example.com, raw.githubusercontent.com); claude-sonnet-5-5-high.open.r1 (raw.githubusercontent.com); claude-sonnet-5-5-high.open.r2 (example.com, raw.githubusercontent.com); claude-sonnet-5-5-high.open.r3 (raw.githubusercontent.com); claude-sonnet-5-5-high.security.r1 (example.com, raw.githubusercontent.com); claude-sonnet-5-5-high.security.r2 (example.com, raw.githubusercontent.com); claude-sonnet-5-5-high.security.r3 (example.com, raw.githubusercontent.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-high | open | 589 | 12,211 | 624,229 | 45,142 |
| claude-fable-5-1-high | security | 503 | 9,524 | 552,471 | 44,617 |
| claude-opus-high | open | 32 | 5,204 | 369,365 | 31,505 |
| claude-opus-high | security | 31 | 4,296 | 347,831 | 29,518 |
| claude-sonnet-5-5-high | open | 28 | 4,814 | 371,652 | 36,825 |
| claude-sonnet-5-5-high | security | 35 | 5,416 | 475,186 | 39,201 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-high.open.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Hardened the processor config file helpers in `processors/base.py` to refuse any filename that escapes the watch's data directory, because the unvalidated `proc |
| claude-fable-5-1-high.open.r2 | s1-config-write-traversal+s2-unknown-processor-stored+s3-import-page-traversal | True | I closed a path traversal where an untrusted watch `processor` name (via backup restore or share-link import) was embedded unchecked into on-disk file names, by |
| claude-fable-5-1-high.open.r3 | s1-config-write-traversal+s3-import-page-traversal | True | Added a path-safety guard to the processor config file helpers in `processors/base.py` so a processor name can never read or write outside the watch's data dire |
| claude-fable-5-1-high.security.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Hardened the processor extra-config file read/write in `processors/base.py` so the filename derived from a watch's `processor` value can never escape the watch' |
| claude-fable-5-1-high.security.r2 | s3-import-page-traversal | True | Added processor allowlist validation to the UI import endpoint in `changedetectionio/blueprint/imports/__init__.py`, because it was the only entry point that le |
| claude-fable-5-1-high.security.r3 | s1-config-write-traversal+s3-import-page-traversal | True | I hardened `get_extra_watch_config` and `update_extra_watch_config` in `processors/base.py` to refuse filenames that escape the watch's data directory, because  |
| claude-opus-high.open.r1 | s3-import-page-traversal | True | The `/import` URL-list endpoint now rejects unknown `processor` values, because the processor name is later used as a filename for the processor config JSON, wh |
| claude-opus-high.open.r2 | s1-config-write-traversal+s3-import-page-traversal | True | I made the processor-config file helpers in `processors/base.py` accept only plain filenames, because a watch's `processor` value (which a restored backup can s |
| claude-opus-high.open.r3 | s3-import-page-traversal | True | I made the UI `/import` route accept only known processor names, because it was the one entry point that stored an unchecked `processor` value that later become |
| claude-opus-high.security.r1 | s3-import-page-traversal | True | I added a check in the `/import` route that the `processor` value is a known processor, because the raw value was later used as a filename and allowed path trav |
| claude-opus-high.security.r2 | s3-import-page-traversal | True | Made the web `/import` route check the `processor` value against the available processors, because unchecked values were stored on watches and later used to bui |
| claude-opus-high.security.r3 | s2-unknown-processor-stored+s3-import-page-traversal | True | Added a check in `add_watch` that drops any `processor` that isn't a registered processor, because the value goes into on-disk filenames and could otherwise be  |
| claude-sonnet-5-5-high.open.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Stopped the watch's processor name from being used as a path outside the watch data directory when reading or writing its config JSON, because the URL-list impo |
| claude-sonnet-5-5-high.open.r2 | s2-unknown-processor-stored+s3-import-page-traversal | True | Validate the `processor` name in `add_watch` against installed processors, because the Add Watch form, URL importer and share links passed it unchecked into fil |
| claude-sonnet-5-5-high.open.r3 | s2-unknown-processor-stored+s3-import-page-traversal | True | Made `add_watch` reject unregistered processor names, because the bulk import form and share-link JSON could otherwise put an arbitrary string into watch file p |
| claude-sonnet-5-5-high.security.r1 | s3-import-page-traversal | True | Validated the `processor` value on the UI URL-list import endpoint against the known processors, because it was unchecked and flowed into file paths (`{processo |
| claude-sonnet-5-5-high.security.r2 | s3-import-page-traversal | True | Added a processor allow-list check to the UI `/import` endpoint, because its unvalidated `processor` value is used in file names (`history-<name>.txt`, `<name>. |
| claude-sonnet-5-5-high.security.r3 | s3-import-page-traversal | True | Validate the `processor` value on the URL import form against the available processors, because it was stored unchecked and later used to build a `<processor>.j |
