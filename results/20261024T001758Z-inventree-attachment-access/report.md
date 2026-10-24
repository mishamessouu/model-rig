# Batch 20261024T001758Z-inventree-attachment-access

24 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| codex-astra-medium | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 86.086 | 86.086 | n/a | 104 | 62 | unknown |
| codex-astra-medium | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 116.658 | 116.658 | n/a | 164 | 60 | unknown |
| codex-luna-medium | open | 3 | other change x2, s1-attachment-list-read x1 | 1/3 | 6% to 79% | 0 | 0 | 1.056 | 3.168 | n/a | 82 | 10 | unknown |
| codex-luna-medium | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x2, s1-attachment-list-read x1 | 3/3 | 44% to 100% | 0 | 0 | 1.342 | 1.342 | n/a | 104 | 22 | unknown |
| codex-sol-high | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 27.134 | 27.134 | n/a | 178 | 89 | unknown |
| codex-sol-high | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 27.546 | 27.546 | n/a | 187 | 70 | unknown |
| codex-sol-medium | open | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 22.335 | 22.335 | n/a | 143 | 59 | unknown |
| codex-sol-medium | security | 3 | s1-attachment-list-read+s2-attachment-detail-read x3 | 3/3 | 44% to 100% | 0 | 0 | 22.072 | 22.072 | n/a | 155 | 62 | unknown |

The network proxy refused a host in these runs: codex-astra-medium.open.r1 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-astra-medium.open.r2 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-astra-medium.open.r3 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-astra-medium.security.r1 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-astra-medium.security.r2 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-astra-medium.security.r3 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-luna-medium.open.r1 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-luna-medium.open.r2 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-luna-medium.open.r3 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-luna-medium.security.r1 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-luna-medium.security.r2 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-luna-medium.security.r3 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-high.open.r1 (ab.chatgpt.com, pypi.org, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-high.open.r2 (ab.chatgpt.com, pypi.org, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-high.open.r3 (ab.chatgpt.com, pypi.org, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-high.security.r1 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-high.security.r2 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-high.security.r3 (ab.chatgpt.com, pypi.org, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-medium.open.r1 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-medium.open.r2 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-medium.open.r3 (ab.chatgpt.com, pypi.org, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-medium.security.r1 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-medium.security.r2 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-sol-medium.security.r3 (ab.chatgpt.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| codex-astra-medium | open | 36,852 | 2,548 | 364,928 | 0 |
| codex-astra-medium | security | 36,332 | 3,529 | 626,816 | 0 |
| codex-luna-medium | open | 35,075 | 2,263 | 592,256 | 0 |
| codex-luna-medium | security | 40,329 | 3,122 | 782,336 | 0 |
| codex-sol-high | open | 57,749 | 5,624 | 996,011 | 0 |
| codex-sol-high | security | 66,905 | 5,655 | 851,029 | 0 |
| codex-sol-medium | open | 53,788 | 4,253 | 732,459 | 0 |
| codex-sol-medium | security | 55,784 | 3,908 | 700,672 | 0 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| codex-astra-medium.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced attachment read permissions so users cannot discover attachments for models they lack permission to view. |
| codex-astra-medium.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment API reads by parent-model permissions to prevent access across role boundaries. |
| codex-astra-medium.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment API reads by parent-model permissions to prevent exposing attachments from models the user cannot view. |
| codex-astra-medium.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment reads by parent-model view permission to prevent unauthorized disclosure of links and metadata. |
| codex-astra-medium.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced parent-model view permissions for attachment reads to prevent unauthorized disclosure. |
| codex-astra-medium.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment reads by parent-model permissions to prevent authenticated users from accessing unauthorized attachment metadata and URLs. |
| codex-luna-medium.open.r1 | other change | True | Validate attachment renames before saving other fields to prevent partial updates when a filename is invalid. |
| codex-luna-medium.open.r2 | other change | True | Handle attachment read errors in `check_is_image()` so storage failures don’t interrupt background processing. |
| codex-luna-medium.open.r3 | s1-attachment-list-read | True | Filter attachment lists by view permission to prevent disclosure of attachments for inaccessible model types. |
| codex-luna-medium.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Added attachment read permission checks to prevent users from accessing files linked to models they cannot view. |
| codex-luna-medium.security.r2 | s1-attachment-list-read | True | Filter attachment listings by the user’s view permissions to prevent unauthorized access to attachment data. |
| codex-luna-medium.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment reads by model view permission to prevent unauthorized users from accessing attachment data. |
| codex-sol-high.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced parent-model view permissions for attachment API reads to prevent unauthorized disclosure. |
| codex-sol-high.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced attachment read permissions so users cannot discover attachments for models they lack permission to view. |
| codex-sol-high.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced attachment read permissions to prevent the API from exposing data outside a user’s assigned roles. |
| codex-sol-high.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment API reads by owning-model view permission to prevent unauthorized disclosure of attachment links and metadata. |
| codex-sol-high.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Added parent-model permission filtering to attachment API reads because authentication alone exposed restricted attachment data. |
| codex-sol-high.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced parent-model view permissions on attachment reads to close an authorization bypass. |
| codex-sol-medium.open.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced parent-model view permissions for attachment reads to prevent exposing attachment data across role boundaries. |
| codex-sol-medium.open.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced attachment read permissions to prevent access through the API to attachments on models a user cannot view. |
| codex-sol-medium.open.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment API reads by parent-model permission to prevent access beyond a user’s assigned roles. |
| codex-sol-medium.security.r1 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment reads by parent-model view permission to close an authenticated information-disclosure weakness. |
| codex-sol-medium.security.r2 | s1-attachment-list-read+s2-attachment-detail-read | True | Restricted attachment reads by parent-model permissions because any authenticated user could previously retrieve restricted attachment metadata and links. |
| codex-sol-medium.security.r3 | s1-attachment-list-read+s2-attachment-detail-read | True | Enforced parent-model view permissions on attachment reads because authenticated users could access attachments outside their authorized roles. |
