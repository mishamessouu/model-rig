# Batch 20261027T040408Z-labelstudio-orm-traversal

6 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-medium | open | 3 | other change x2, s1-inline-filter-traversal x1 | 1/3 | 6% to 79% | 0 | 2 | 2 | 0 | n/a | n/a | 1.124 | 166 | 78 | unknown |
| claude-fable-5-1-medium | security | 3 | s1-inline-filter-traversal x2, other change x1 | 2/3 | 21% to 94% | 0 | 1 | 1 | 0 | n/a | n/a | 1.165 | 205 | 55 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-medium.open.r1 (pypi.org); claude-fable-5-1-medium.open.r2 (pypi.org); claude-fable-5-1-medium.security.r1 (pypi.org); claude-fable-5-1-medium.security.r2 (pypi.org); claude-fable-5-1-medium.security.r3 (pypi.org). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-medium | open | 473 | 6,380 | 434,841 | 35,125 |
| claude-fable-5-1-medium | security | 515 | 7,397 | 465,575 | 33,858 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-medium.open.r1 | other change | True |  |
| claude-fable-5-1-medium.open.r2 | s1-inline-filter-traversal | True | I enforced the foreign-key traversal allowlist inside `apply_filters` via a shared validator, because filters sent inline through the `query` parameter bypassed |
| claude-fable-5-1-medium.open.r3 | other change | True |  |
| claude-fable-5-1-medium.security.r1 | s1-inline-filter-traversal | True | Added a foreign-key traversal check inside `apply_filters` in `data_manager/managers.py`, because ad hoc `query` filters bypassed the serializer-only check and  |
| claude-fable-5-1-medium.security.r2 | s1-inline-filter-traversal | True | Added a foreign-key traversal check inside `apply_filters` in `data_manager/managers.py` so ad-hoc `query` filters are held to the same `__` allowlist rule as s |
| claude-fable-5-1-medium.security.r3 | other change | True |  |
