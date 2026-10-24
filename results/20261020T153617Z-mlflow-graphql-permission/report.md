# Batch 20261020T153617Z-mlflow-graphql-permission

12 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-opus-medium | open | 3 | s1-nested-run-model-versions x3 | 3/3 | 44% to 100% | 0 | 0 | 44.971 | 44.971 | 0.557 | 353 | 53 | unknown |
| claude-opus-medium | security | 3 | s1-nested-run-model-versions x3 | 3/3 | 44% to 100% | 0 | 0 | 32.118 | 32.118 | 0.409 | 274 | 5 | unknown |
| claude-sonnet-5-5-medium | open | 3 | other change x2, s1-nested-run-model-versions x1 | 1/3 | 6% to 79% | 0 | 0 | 11.293 | 33.880 | 0.149 | 208 | 9 | unknown |
| claude-sonnet-5-5-medium | security | 3 | s1-nested-run-model-versions x3 | 3/3 | 44% to 100% | 0 | 0 | 17.350 | 17.350 | 0.221 | 288 | 7 | unknown |

The network proxy refused a host in these runs: claude-opus-medium.open.r1 (github.com, releases.astral.sh); claude-opus-medium.open.r2 (github.com, releases.astral.sh); claude-opus-medium.open.r3 (github.com, releases.astral.sh); claude-opus-medium.security.r1 (github.com, releases.astral.sh); claude-opus-medium.security.r2 (github.com, releases.astral.sh); claude-opus-medium.security.r3 (github.com, releases.astral.sh); claude-sonnet-5-5-medium.open.r1 (github.com, releases.astral.sh); claude-sonnet-5-5-medium.open.r2 (github.com, releases.astral.sh); claude-sonnet-5-5-medium.open.r3 (files.pythonhosted.org, github.com, pypi.org, releases.astral.sh); claude-sonnet-5-5-medium.security.r1 (github.com, releases.astral.sh); claude-sonnet-5-5-medium.security.r2 (github.com, releases.astral.sh); claude-sonnet-5-5-medium.security.r3 (github.com, releases.astral.sh). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-opus-medium | open | 41 | 7,609 | 594,252 | 35,704 |
| claude-opus-medium | security | 31 | 4,976 | 373,168 | 29,379 |
| claude-sonnet-5-5-medium | open | 20 | 3,351 | 199,401 | 23,779 |
| claude-sonnet-5-5-medium | security | 30 | 5,460 | 400,545 | 31,514 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-opus-medium.open.r1 | s1-nested-run-model-versions | True | Filtered the run's nested GraphQL `modelVersions` field by registered-model read permission, because it let any user who could read a run see model versions the |
| claude-opus-medium.open.r2 | s1-nested-run-model-versions | True | I made the GraphQL auth middleware filter the nested `run.modelVersions` field by registered-model read permission, because it showed users model versions of re |
| claude-opus-medium.open.r3 | s1-nested-run-model-versions | True | Fixed GraphQL auth so a run's nested `modelVersions` field hides registered models the user can't read, because it was leaking models that the REST API and `mlf |
| claude-opus-medium.security.r1 | s1-nested-run-model-versions | True | Added the nested run `modelVersions` GraphQL field to the auth middleware's checked fields and filtered its results by registered-model read permission, because |
| claude-opus-medium.security.r2 | s1-nested-run-model-versions | True | Made the GraphQL auth middleware filter the nested `Run.modelVersions` field by registered-model read permission, because it let any user who could read a run s |
| claude-opus-medium.security.r3 | s1-nested-run-model-versions | True | Added the nested `modelVersions` GraphQL field to the authorization middleware's protected fields and filtered its results by registered-model read permission,  |
| claude-sonnet-5-5-medium.open.r1 | other change | True | Made GraphQL `mlflowSearchRuns`/`mlflowSearchDatasets` deny non-admin requests with empty `experiment_ids`, because the old code skipped the permission check an |
| claude-sonnet-5-5-medium.open.r2 | s1-nested-run-model-versions | True | Filtered the nested `MlflowRun.modelVersions` GraphQL field by registered-model read permission, because it leaked model versions to users who couldn't read tho |
| claude-sonnet-5-5-medium.open.r3 | other change | True | Filtered the nested run `modelVersions` GraphQL field by registered-model read permission in the auth middleware, because it let users read model versions of mo |
| claude-sonnet-5-5-medium.security.r1 | s1-nested-run-model-versions | True | Filtered the nested `modelVersions` field in the GraphQL authorization middleware by registered-model read permission, because run queries returned model versio |
| claude-sonnet-5-5-medium.security.r2 | s1-nested-run-model-versions | True | Added a read-permission check and filter for the nested run `modelVersions` GraphQL field, because it let users read model versions of registered models they ha |
| claude-sonnet-5-5-medium.security.r3 | s1-nested-run-model-versions | True | Added the nested GraphQL `modelVersions` field to the auth middleware's protected fields and filtered it by registered-model read permission, because a user who |
