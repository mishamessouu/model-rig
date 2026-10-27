# Batch 20261027T113800Z-inventree-attachment-access

6 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-medium | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 2/3 | 21% to 94% | 1 | 0 | 0 | 0 | 87.209 | 130.813 | 1.109 | 267 | 100 | unknown |
| claude-fable-5-1-medium | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 117.212 | 117.212 | 1.453 | 310 | 45 | unknown |

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-medium | open | 461 | 7,563 | 377,098 | 31,606 |
| claude-fable-5-1-medium | security | 610 | 10,923 | 604,912 | 37,490 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-medium.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | False | I added view-permission filtering to the attachment list and detail API, because reads were the only attachment operation with no authorization check against th |
| claude-fable-5-1-medium.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | I made attachment list and detail GET endpoints enforce the view permission of the linked model, because the API already guarded edit and delete but let any log |
| claude-fable-5-1-medium.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | I made attachment list and detail reads enforce the linked model's view permission, because unauthenticated-by-role users could previously read every attachment |
| claude-fable-5-1-medium.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Filtered attachment list and detail reads by the user's view permission on the target model type, because every write path already enforced model-based permissi |
| claude-fable-5-1-medium.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Added view-permission enforcement to the attachment list and detail read endpoints in common/api.py, because any authenticated user could previously enumerate a |
| claude-fable-5-1-medium.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Added view-permission filtering to the attachment list and detail API so authenticated users can no longer read attachments for models they lack a view role on, |
