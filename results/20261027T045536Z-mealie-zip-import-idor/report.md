# Batch 20261027T045536Z-mealie-zip-import-idor

6 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-medium | open | 3 | s1-zip-tool-takeover x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 136.949 | 136.949 | 1.718 | 631 | 69 | unknown |
| claude-fable-5-1-medium | security | 3 | s1-zip-tool-takeover x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 147.681 | 147.681 | 1.843 | 563 | 72 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-medium.open.r1 (api.github.com); claude-fable-5-1-medium.open.r2 (api.github.com); claude-fable-5-1-medium.open.r3 (api.github.com); claude-fable-5-1-medium.security.r1 (api.github.com); claude-fable-5-1-medium.security.r2 (api.github.com); claude-fable-5-1-medium.security.r3 (api.github.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-medium | open | 781 | 11,093 | 906,469 | 46,433 |
| claude-fable-5-1-medium | security | 803 | 12,182 | 994,516 | 48,885 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-medium.open.r1 | s1-zip-tool-takeover | True | Made recipe zip import resolve tools by slug within the importer's own group instead of trusting the exported tool id, because the previous behavior let any use |
| claude-fable-5-1-medium.open.r2 | s1-zip-tool-takeover | True | Scoped `tools` in the recipe zip import to the importer's group, because it was the one relationship the import left unscoped, letting a crafted zip link a reci |
| claude-fable-5-1-medium.open.r3 | s1-zip-tool-takeover | True | I closed a cross-tenant write in the recipe zip import where an imported tool, tag, or category carrying another group's id would rename and re-home that group' |
| claude-fable-5-1-medium.security.r1 | s1-zip-tool-takeover | True | Added group-scoped slug resolution for tools in the recipe zip import, because an imported tool id was looked up globally, letting a user in one group attach an |
| claude-fable-5-1-medium.security.r2 | s1-zip-tool-takeover | True | Made the recipe zip import resolve tools through the group-scoped repository, drop imported comments, and strip untrusted nested ids, because the unscoped ORM l |
| claude-fable-5-1-medium.security.r3 | s1-zip-tool-takeover | True | Made zip recipe import resolve `tools` only within the caller's group, because the unscoped ORM lookup let any user attach to and overwrite another group's tool |
