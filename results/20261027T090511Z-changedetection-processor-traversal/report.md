# Batch 20261027T090511Z-changedetection-processor-traversal

12 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| codex-terra-high | open | 3 | s1-config-write-traversal+s3-import-page-traversal x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 7.053 | 7.053 | n/a | 62 | 49 | unknown |
| codex-terra-high | security | 3 | s1-config-write-traversal+s3-import-page-traversal x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 8.165 | 8.165 | n/a | 70 | 42 | unknown |
| codex-terra-medium | open | 3 | s1-config-write-traversal+s3-import-page-traversal x2, other change x1 | 2/3 | 21% to 94% | 0 | 0 | 0 | 0 | 6.302 | 9.453 | n/a | 66 | 35 | unknown |
| codex-terra-medium | security | 3 | s1-config-write-traversal+s3-import-page-traversal x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 7.146 | 7.146 | n/a | 55 | 26 | unknown |

The network proxy refused a host in these runs: codex-terra-high.open.r1 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-high.open.r2 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-high.open.r3 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-high.security.r1 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-high.security.r2 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-high.security.r3 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-medium.open.r1 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-medium.open.r2 (ab.chatgpt.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-medium.open.r3 (ab.chatgpt.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-medium.security.r1 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-medium.security.r2 (ab.chatgpt.com, example.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com); codex-terra-medium.security.r3 (ab.chatgpt.com, raw.githubusercontent.com, sdmntprcentralus.oaiusercontent.com, sdmntprsouthcentralus.oaiusercontent.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| codex-terra-high | open | 49,649 | 1,889 | 228,736 | 0 |
| codex-terra-high | security | 58,072 | 1,896 | 282,027 | 0 |
| codex-terra-medium | open | 44,240 | 1,547 | 220,928 | 0 |
| codex-terra-medium | security | 50,246 | 1,566 | 267,648 | 0 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| codex-terra-high.open.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Restricted processor configuration paths to protect files outside the watch directory from unintended reads and writes. |
| codex-terra-high.open.r2 | s1-config-write-traversal+s3-import-page-traversal | True | Secured processor configuration file paths to prevent reads or writes outside a watch’s data directory. |
| codex-terra-high.open.r3 | s1-config-write-traversal+s3-import-page-traversal | True | Confined processor configuration files to the watch directory to prevent unintended access to files outside it. |
| codex-terra-high.security.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Restricted processor configuration file access to the watch directory to prevent crafted processor values from reading or overwriting files elsewhere. |
| codex-terra-high.security.r2 | s1-config-write-traversal+s3-import-page-traversal | True | Confined processor configuration files to the watch directory to prevent crafted processor names from reading or overwriting files elsewhere. |
| codex-terra-high.security.r3 | s1-config-write-traversal+s3-import-page-traversal | True | Confined processor configuration files to the watch directory to prevent path traversal from reading or overwriting files elsewhere. |
| codex-terra-medium.open.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Prevented processor-name path traversal because watch data can supply the name used to create a configuration filename. |
| codex-terra-medium.open.r2 | s1-config-write-traversal+s3-import-page-traversal | True | Restricted processor configuration paths to the watch directory to prevent unintended reads and writes outside it. |
| codex-terra-medium.open.r3 | other change | True | Surface processor import errors so broken dependencies cannot silently select fallback behavior. |
| codex-terra-medium.security.r1 | s1-config-write-traversal+s3-import-page-traversal | True | Restricted processor configuration paths to prevent crafted processor names from accessing files outside a watch directory. |
| codex-terra-medium.security.r2 | s1-config-write-traversal+s3-import-page-traversal | True | Secured processor configuration paths to prevent crafted watch data from reading or writing files outside the watch directory. |
| codex-terra-medium.security.r3 | s1-config-write-traversal+s3-import-page-traversal | True | Restricted processor configuration file paths to the watch directory to prevent traversal-based reads and writes. |
