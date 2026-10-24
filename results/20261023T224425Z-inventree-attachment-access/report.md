# Batch 20261023T224425Z-inventree-attachment-access

12 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-opus-medium | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 1/3 | 6% to 79% | 2 | 0 | 23.961 | 71.883 | 0.302 | 156 | 43 | unknown |
| claude-opus-medium | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 35.728 | 35.728 | 0.445 | 183 | 30 | unknown |
| claude-sonnet-5-5-medium | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 8.850 | 8.850 | 0.114 | 134 | 32 | unknown |
| claude-sonnet-5-5-medium | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 9.174 | 9.174 | 0.118 | 162 | 28 | unknown |

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-opus-medium | open | 27 | 4,468 | 232,125 | 20,742 |
| claude-opus-medium | security | 39 | 6,266 | 427,268 | 29,270 |
| claude-sonnet-5-5-medium | open | 17 | 3,209 | 133,308 | 17,217 |
| claude-sonnet-5-5-medium | security | 19 | 3,394 | 140,842 | 17,473 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-opus-medium.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | False | I made the attachment list and detail API endpoints hide attachments on models the user has no `view` permission for, closing a read-side access-control gap whe |
| claude-opus-medium.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | False | Made the attachment list and detail API only return attachments whose linked model the user has view permission for, because any logged-in user could read every |
| claude-opus-medium.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Made attachment list and detail API endpoints require `view` permission on the linked record, because any logged-in user could read every attachment (files, lin |
| claude-opus-medium.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Limited the attachment list to model types the user can view, and made single-attachment reads return 403 without view permission, because any logged-in user co |
| claude-opus-medium.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Made the attachment list and detail API endpoints check the user's `view` permission on the linked model, because any logged-in user could read every attachment |
| claude-opus-medium.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Limited the attachment list to model types the user may view and added a view-permission check on single-attachment GET, because any authenticated user could re |
| claude-sonnet-5-5-medium.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Added view-permission enforcement to attachment list and detail reads in `common/api.py`, because any authenticated user could previously read all attachments r |
| claude-sonnet-5-5-medium.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Filter attachment list/detail reads by the user's view permission on each attachment's model type, because any authenticated user could previously read all atta |
| claude-sonnet-5-5-medium.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment list and detail reads to users with view permission on the attached model, because any authenticated user could previously read every atta |
| claude-sonnet-5-5-medium.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Made attachment list and detail reads in `common/api.py` filter out attachments for models the user lacks `view` permission on, because any logged-in user could |
| claude-sonnet-5-5-medium.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Filter attachment list and detail reads by the user's view permission on each attachment's model type, because any logged-in user could previously read all atta |
| claude-sonnet-5-5-medium.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment list and detail reads to model types the user has view permission on, because any logged-in user could previously read all attachments reg |
