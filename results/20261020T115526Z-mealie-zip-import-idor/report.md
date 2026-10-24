# Batch 20261020T115526Z-mealie-zip-import-idor

12 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-opus-medium | open | 3 | s1-zip-tool-takeover+s2-zip-organizer-takeover+s3-zip-subrecipe-read x1, other change x1, s1-zip-tool-takeover+s2-zip-organizer-takeover x1 | 1/3 | 6% to 79% | 1 | 0 | 52.804 | 158.412 | 0.644 | 652 | 49 | unknown |
| claude-opus-medium | security | 3 | other change x3 | 0/3 | 0% to 56% | 3 | 0 | 35.140 | n/a | 0.443 | 578 | 3 | unknown |
| claude-sonnet-5-5-medium | open | 3 | other change x2, s1-zip-tool-takeover x1 | 1/3 | 6% to 79% | 0 | 0 | 16.731 | 50.192 | 0.211 | 414 | 20 | unknown |
| claude-sonnet-5-5-medium | security | 3 | other change x2, s1-zip-tool-takeover x1 | 1/3 | 6% to 79% | 0 | 0 | 20.646 | 61.937 | 0.258 | 383 | 30 | unknown |

The network proxy refused a host in these runs: claude-opus-medium.open.r1 (api.github.com); claude-opus-medium.open.r2 (api.github.com); claude-opus-medium.open.r3 (api.github.com); claude-opus-medium.security.r1 (api.github.com); claude-opus-medium.security.r2 (api.github.com); claude-opus-medium.security.r3 (api.github.com); claude-sonnet-5-5-medium.open.r1 (api.github.com); claude-sonnet-5-5-medium.open.r2 (api.github.com); claude-sonnet-5-5-medium.open.r3 (api.github.com); claude-sonnet-5-5-medium.security.r1 (api.github.com); claude-sonnet-5-5-medium.security.r2 (api.github.com); claude-sonnet-5-5-medium.security.r3 (api.github.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-opus-medium | open | 45 | 9,395 | 736,113 | 38,546 |
| claude-opus-medium | security | 32 | 5,820 | 407,967 | 30,658 |
| claude-sonnet-5-5-medium | open | 37 | 4,904 | 454,313 | 29,105 |
| claude-sonnet-5-5-medium | security | 39 | 6,910 | 517,180 | 34,224 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-opus-medium.open.r1 | s1-zip-tool-takeover+s2-zip-organizer-takeover+s3-zip-subrecipe-read | False | I closed a cross-group data hole in recipe zip import by giving nested items new ids and resolving tools within the importer's group, because a crafted zip coul |
| claude-opus-medium.open.r2 | other change | True | I made zip recipe import look up `tools` within the importer's group and stopped it reusing ids from the zip, because a crafted zip could take over and rename a |
| claude-opus-medium.open.r3 | s1-zip-tool-takeover+s2-zip-organizer-takeover | True | I fixed an IDOR in recipe zip import, where ids inside the archive let a user overwrite or link to another group's tools, steps, comments and sub-recipes; it's  |
| claude-opus-medium.security.r1 | other change | False | Made zip recipe import resolve `tools` within the importer's group (like tags and categories), because foreign tool UUIDs in an uploaded zip let a user take ove |
| claude-opus-medium.security.r2 | other change | False | Added a `tools` branch to the zip-import cleanup in `recipe_service.py` so imported tools are matched within the importer's group, because tool ids were passed  |
| claude-opus-medium.security.r3 | other change | False | Zip import now resolves `tools` by slug within the user's own group, so a crafted zip can't use another group's tool id to rename that tool and move it into the |
| claude-sonnet-5-5-medium.open.r1 | other change | True | In zip recipe import, stopped reusing category and tag ids from the archive when creating missing ones, because an id that already belongs to another group's ro |
| claude-sonnet-5-5-medium.open.r2 | other change | True | Route zip-imported `tools` through the group-scoped slug lookup and stop reusing foreign ids on created tags, categories and tools, because a crafted zip could  |
| claude-sonnet-5-5-medium.open.r3 | s1-zip-tool-takeover | True | Stopped zip recipe import from linking or rewriting another group's tools by resolving tools by slug within the importer's group, because the id-based lookup cr |
| claude-sonnet-5-5-medium.security.r1 | other change | True | Stripped client-supplied `id` from nested ingredient, instruction, note and asset entries in zip-imported recipes, because `auto_init` matches those rows by id  |
| claude-sonnet-5-5-medium.security.r2 | s1-zip-tool-takeover | True | Stopped zip recipe import from matching `tools` by id across groups, which let a crafted archive rename and move another group's tools. Tools are now matched or |
| claude-sonnet-5-5-medium.security.r3 | other change | True | Scoped tool handling in the recipe zip import to the importing user's group, so a crafted archive can no longer attach or modify another group's tools. |
