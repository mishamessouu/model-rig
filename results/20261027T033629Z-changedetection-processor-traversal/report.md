# Batch 20261027T033629Z-changedetection-processor-traversal

6 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-medium | open | 3 | s1-config-write-traversal+s2-unknown-processor-stored+s3-import-page-traversal x1, s1-config-write-traversal+s3-import-page-traversal x1, s2-unknown-processor-stored+s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 81.240 | 81.240 | 1.056 | 132 | 94 | unknown |
| claude-fable-5-1-medium | security | 3 | s1-config-write-traversal+s3-import-page-traversal x2, s2-unknown-processor-stored+s3-import-page-traversal x1 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 85.451 | 85.451 | 1.109 | 158 | 30 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-medium.open.r1 (example.com, raw.githubusercontent.com); claude-fable-5-1-medium.open.r2 (example.com, raw.githubusercontent.com); claude-fable-5-1-medium.open.r3 (example.com, raw.githubusercontent.com); claude-fable-5-1-medium.security.r1 (raw.githubusercontent.com); claude-fable-5-1-medium.security.r2 (raw.githubusercontent.com); claude-fable-5-1-medium.security.r3 (example.com, raw.githubusercontent.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-medium | open | 429 | 6,317 | 347,613 | 32,429 |
| claude-fable-5-1-medium | security | 557 | 6,284 | 445,288 | 33,873 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-medium.open.r1 | s1-config-write-traversal+s2-unknown-processor-stored+s3-import-page-traversal | True | I closed a path traversal where an unvalidated watch `processor` name became a filename inside the watch data directory, by validating processor names centrally |
| claude-fable-5-1-medium.open.r2 | s1-config-write-traversal+s3-import-page-traversal | True | Hardened the processor config file helpers in `processors/base.py` so a processor name can never read or write outside the watch's data directory, because it wa |
| claude-fable-5-1-medium.open.r3 | s2-unknown-processor-stored+s3-import-page-traversal | True | Validated the processor name in the datastore's add_watch against installed processors, because unvalidated names from shared-link imports and the UI import for |
| claude-fable-5-1-medium.security.r1 | s2-unknown-processor-stored+s3-import-page-traversal | True | Added processor-name validation to the store's add_watch so unvalidated callers (URL list importer, share-link metadata) can no longer store a path-traversal st |
| claude-fable-5-1-medium.security.r2 | s1-config-write-traversal+s3-import-page-traversal | True | Hardened the processor config file sink in `processors/base.py` to reject path traversal, because the user-controlled `processor` name was used unchecked as a f |
| claude-fable-5-1-medium.security.r3 | s1-config-write-traversal+s3-import-page-traversal | True | I confined processor config file reads and writes in `processors/base.py` to the watch's data directory, because an unvalidated `processor` value could traverse |
