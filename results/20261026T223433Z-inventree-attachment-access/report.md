# Batch 20261026T223433Z-inventree-attachment-access

18 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-high | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 2/3 | 21% to 94% | 1 | 0 | 0 | 0 | 127.678 | 191.517 | 1.586 | 320 | 93 | unknown |
| claude-fable-5-1-high | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x2, s1-attachment-list-read x1 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 182.720 | 182.720 | 2.240 | 326 | 48 | unknown |
| claude-opus-high | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 1/3 | 6% to 79% | 2 | 0 | 0 | 0 | 33.003 | 99.008 | 0.411 | 195 | 60 | unknown |
| claude-opus-high | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 52.380 | 52.380 | 0.645 | 301 | 26 | unknown |
| claude-sonnet-5-5-high | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 18.902 | 18.902 | 0.236 | 194 | 68 | unknown |
| claude-sonnet-5-5-high | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 13.947 | 13.947 | 0.177 | 160 | 38 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-high.open.r3 (pypi.org); claude-fable-5-1-high.security.r2 (raw.githubusercontent.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-high | open | 621 | 12,156 | 592,374 | 41,173 |
| claude-fable-5-1-high | security | 663 | 18,098 | 910,298 | 55,048 |
| claude-opus-high | open | 34 | 6,194 | 358,339 | 26,868 |
| claude-opus-high | security | 49 | 9,479 | 659,736 | 40,414 |
| claude-sonnet-5-5-high | open | 35 | 6,865 | 417,440 | 31,422 |
| claude-sonnet-5-5-high | security | 27 | 5,001 | 265,308 | 25,151 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-high.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | I made the attachment list and detail endpoints filter by view permission on the linked model, because the write side already enforced target-model permissions  |
| claude-fable-5-1-high.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | False | I made attachment list and detail API responses respect the 'view' permission of the attached model, because write operations were already permission-checked wh |
| claude-fable-5-1-high.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | I made the attachment list and detail endpoints filter by the user's view permission on the target model, because any logged-in user could previously read every |
| claude-fable-5-1-high.security.r1 | s1-attachment-list-read | True | Added view-permission filtering to the attachment list API endpoint in `common/api.py`, because it previously returned every attachment to any authenticated use |
| claude-fable-5-1-high.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Added view-permission filtering to the attachment list and detail endpoints, because any authenticated user could previously enumerate and download attachments  |
| claude-fable-5-1-high.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced view permission on attachment reads (list filtering plus a 403 on detail GET) in common/api.py, because the API let any authenticated user read every a |
| claude-opus-high.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | False | Made the attachment list and detail API only return attachments on models the user can view, because any logged-in user could read attachments on records they h |
| claude-opus-high.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | I made the attachment list and detail API endpoints only return attachments on record types the user can view, because the write paths already enforced permissi |
| claude-opus-high.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | False | The attachment list and detail endpoints now only return attachments for models the user has `view` permission on, so users can no longer read attachments (e.g. |
| claude-opus-high.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Made the attachment list and detail endpoints check `view` permission on the attached object's type, because any logged-in user could list and download attachme |
| claude-opus-high.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | I restricted read access to attachments in `common/api.py` to the model types the user can view, because any authenticated user could read every attachment's fi |
| claude-opus-high.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Limited attachment list/detail reads in `common/api.py` to model types the user can view, because any logged-in user could list and download attachments on reco |
| claude-sonnet-5-5-high.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Filter attachment list/detail reads by the user's view permission on the target model, because any authenticated user could previously read every attachment, in |
| claude-sonnet-5-5-high.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment list/detail reads to users with view permission on the attached model's type, because any authenticated user could previously read all att |
| claude-sonnet-5-5-high.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Filter attachment list/detail reads by per-model `view` permission, because any logged-in user could previously read attachments for models they had no access t |
| claude-sonnet-5-5-high.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Added a per-model `view` permission filter to the attachment API's list and detail reads in `common/api.py`, because any authenticated user could previously rea |
| claude-sonnet-5-5-high.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment list/detail reads to users with view permission on the parent model type, because any authenticated user could previously read all attachm |
| claude-sonnet-5-5-high.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment list and detail reads to models the user has view permission on, because any authenticated user could previously read all attachments rega |
