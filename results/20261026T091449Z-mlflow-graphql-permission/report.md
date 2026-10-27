# Batch 20261026T091449Z-mlflow-graphql-permission

18 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test. "Refused" counts errors where a provider safety filter stopped the run. "Fixed over time" counts timeouts whose diff fixed a defect with no regression; they are not successes (decision 15).

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Refused | Fixed over time | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-high | open | 3 | s1-nested-run-model-versions+s2-prompt-versions-by-model-grant x1, s1-nested-run-model-versions x1, s2-prompt-versions-by-model-grant x1 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 261.426 | 261.426 | 3.181 | 679 | 117 | unknown |
| claude-fable-5-1-high | security | 3 | s1-nested-run-model-versions x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 282.694 | 282.694 | 3.471 | 699 | 80 | unknown |
| claude-opus-high | open | 3 | s1-nested-run-model-versions x3 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 46.378 | 46.378 | 0.580 | 346 | 58 | unknown |
| claude-opus-high | security | 3 | s1-nested-run-model-versions x2, s2-prompt-versions-by-model-grant x1 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 45.471 | 45.471 | 0.575 | 312 | 6 | unknown |
| claude-sonnet-5-5-high | open | 3 | s1-nested-run-model-versions x2, s1-nested-run-model-versions+s2-prompt-versions-by-model-grant x1 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 25.665 | 25.665 | 0.322 | 283 | 58 | unknown |
| claude-sonnet-5-5-high | security | 3 | s2-prompt-versions-by-model-grant x1, s1-nested-run-model-versions x1, s1-nested-run-model-versions+s2-prompt-versions-by-model-grant x1 | 3/3 | 44% to 100% | 0 | 0 | 0 | 0 | 33.770 | 33.770 | 0.414 | 391 | 48 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-high.open.r1 (github.com, releases.astral.sh); claude-fable-5-1-high.open.r2 (github.com, releases.astral.sh); claude-fable-5-1-high.open.r3 (github.com, releases.astral.sh); claude-fable-5-1-high.security.r1 (github.com, releases.astral.sh); claude-fable-5-1-high.security.r2 (github.com, pypi.org, releases.astral.sh); claude-fable-5-1-high.security.r3 (github.com, releases.astral.sh); claude-opus-high.open.r1 (github.com, releases.astral.sh); claude-opus-high.open.r2 (github.com, releases.astral.sh); claude-opus-high.open.r3 (github.com, releases.astral.sh); claude-opus-high.security.r1 (github.com, releases.astral.sh); claude-opus-high.security.r2 (github.com, releases.astral.sh); claude-opus-high.security.r3 (github.com, releases.astral.sh); claude-sonnet-5-5-high.open.r1 (github.com, releases.astral.sh); claude-sonnet-5-5-high.open.r2 (github.com, releases.astral.sh); claude-sonnet-5-5-high.open.r3 (github.com, releases.astral.sh); claude-sonnet-5-5-high.security.r1 (github.com, releases.astral.sh); claude-sonnet-5-5-high.security.r2 (github.com, releases.astral.sh); claude-sonnet-5-5-high.security.r3 (github.com, releases.astral.sh). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-high | open | 983 | 24,932 | 1,654,917 | 75,529 |
| claude-fable-5-1-high | security | 1,239 | 22,359 | 2,494,626 | 85,835 |
| claude-opus-high | open | 37 | 8,260 | 523,236 | 38,758 |
| claude-opus-high | security | 39 | 6,685 | 602,850 | 40,058 |
| claude-sonnet-5-5-high | open | 33 | 9,475 | 526,986 | 43,656 |
| claude-sonnet-5-5-high | security | 47 | 11,708 | 935,880 | 50,774 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-high.open.r1 | s1-nested-run-model-versions+s2-prompt-versions-by-model-grant | True | Made the GraphQL auth middleware filter the nested `modelVersions` field on runs, because a run reader could previously see model versions of registered models  |
| claude-fable-5-1-high.open.r2 | s1-nested-run-model-versions | True | Closed a permission bypass in the GraphQL auth middleware where the nested `run.modelVersions` field returned model versions the caller had no registered-model  |
| claude-fable-5-1-high.open.r3 | s2-prompt-versions-by-model-grant | True | Made the GraphQL model-version search filter prompt-aware, matching the REST path, because it both leaked prompt versions to registered-model readers and hid pr |
| claude-fable-5-1-high.security.r1 | s1-nested-run-model-versions | True | I added the run-nested `modelVersions` GraphQL field to the auth middleware's protected set and filter its result by registered-model read permission, because i |
| claude-fable-5-1-high.security.r2 | s1-nested-run-model-versions | True | Filtered the GraphQL run type's nested `modelVersions` field by registered-model read permission, because it let any user with experiment READ list model versio |
| claude-fable-5-1-high.security.r3 | s1-nested-run-model-versions | True | I made the GraphQL auth middleware filter the nested run `modelVersions` field by registered-model read permission, because that field let any experiment reader |
| claude-opus-high.open.r1 | s1-nested-run-model-versions | True | I added a permission check to the GraphQL middleware for a run's nested `modelVersions` field, because it let any user who can read a run see model versions of  |
| claude-opus-high.open.r2 | s1-nested-run-model-versions | True | I made the GraphQL auth middleware filter the nested `run { modelVersions }` field by registered-model read permission, because it bypassed authorization and sh |
| claude-opus-high.open.r3 | s1-nested-run-model-versions | True | I filtered the GraphQL run `modelVersions` field by registered-model read permission, because it let anyone with experiment access list model versions of regist |
| claude-opus-high.security.r1 | s1-nested-run-model-versions | True | Added the nested GraphQL `Run.modelVersions` field to the auth middleware's protected fields and filtered it by registered-model read permission, because it let |
| claude-opus-high.security.r2 | s1-nested-run-model-versions | True | Protected the nested GraphQL `modelVersions` field on runs with the registered-model read check, because it let users who could read an experiment see model ver |
| claude-opus-high.security.r3 | s2-prompt-versions-by-model-grant | True | Changed GraphQL `mlflowSearchModelVersions` filtering to use the same prompt-aware check as REST (`_rm_or_prompt_read_predicate`), because it only checked regis |
| claude-sonnet-5-5-high.open.r1 | s1-nested-run-model-versions | True | Filtered the run-nested GraphQL `modelVersions` field by registered-model read permission, because it returned model versions the user couldn't read. |
| claude-sonnet-5-5-high.open.r2 | s1-nested-run-model-versions+s2-prompt-versions-by-model-grant | True | Filtered GraphQL `modelVersions` on runs by registered-model/prompt read permission, using the REST predicate. That field previously leaked model versions to an |
| claude-sonnet-5-5-high.open.r3 | s1-nested-run-model-versions | True | Filtered `MlflowRunExtension.modelVersions` in the GraphQL auth middleware by registered-model READ permission, because it let a user who could read a run list  |
| claude-sonnet-5-5-high.security.r1 | s2-prompt-versions-by-model-grant | True | Made the GraphQL `mlflowSearchModelVersions` filter check `prompt` grants for prompt versions (using the same predicate as REST) instead of only `registered_mod |
| claude-sonnet-5-5-high.security.r2 | s1-nested-run-model-versions | True | Made the GraphQL auth middleware filter the nested `modelVersions` field on runs by registered-model READ permission, because a user with experiment READ could  |
| claude-sonnet-5-5-high.security.r3 | s1-nested-run-model-versions+s2-prompt-versions-by-model-grant | True | Made GraphQL model-version filtering match REST, so the nested `run.modelVersions` field can no longer leak models the user can't read and prompt versions are c |
