# Batch 20261026T033428Z-mealie-zip-import-idor

18 runs. Success means at least one planted defect fixed, no regression, and no agent error or timeout. Cost prices the stored tokens with today's `copilot` price sheet, in credits; a cell with an unpriced run shows n/a. The interval is a 95% Wilson interval for the success rate. With three runs it is wide, so rank two cells only with a test on the runs, such as Fisher's exact test.

| Cell | Prompt | n | Picks | Success | 95% interval | Regressions | Errors | Mean credits | credits per success | Mean reported USD | Mean s | Mean lines changed | Fix after cutoff |
|---|---|---:|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| claude-fable-5-1-high | open | 3 | s1-zip-tool-takeover x2, s1-zip-tool-takeover+s2-zip-organizer-takeover x1 | 2/3 | 21% to 94% | 0 | 1 | n/a | n/a | 1.763 | 992 | 85 | unknown |
| claude-fable-5-1-high | security | 3 | other change x1, s1-zip-tool-takeover x1, s1-zip-tool-takeover+s2-zip-organizer-takeover x1 | 2/3 | 21% to 94% | 0 | 1 | n/a | n/a | 3.286 | 1,432 | 71 | unknown |
| claude-opus-high | open | 3 | other change x2, s1-zip-tool-takeover x1 | 1/3 | 6% to 79% | 0 | 0 | 60.706 | 182.118 | 0.741 | 473 | 61 | unknown |
| claude-opus-high | security | 3 | other change x2, s1-zip-tool-takeover x1 | 1/3 | 6% to 79% | 0 | 0 | 41.760 | 125.280 | 0.521 | 500 | 11 | unknown |
| claude-sonnet-5-5-high | open | 3 | s1-zip-tool-takeover x3 | 3/3 | 44% to 100% | 0 | 0 | 26.353 | 26.353 | 0.329 | 411 | 73 | unknown |
| claude-sonnet-5-5-high | security | 3 | s1-zip-tool-takeover x3 | 3/3 | 44% to 100% | 0 | 0 | 25.766 | 25.766 | 0.320 | 412 | 56 | unknown |

The network proxy refused a host in these runs: claude-fable-5-1-high.open.r1 (api.github.com); claude-fable-5-1-high.open.r2 (api.github.com); claude-fable-5-1-high.open.r3 (api.github.com); claude-fable-5-1-high.security.r1 (api.github.com); claude-fable-5-1-high.security.r2 (api.github.com); claude-fable-5-1-high.security.r3 (api.github.com); claude-opus-high.open.r1 (api.github.com); claude-opus-high.open.r2 (api.github.com); claude-opus-high.open.r3 (api.github.com); claude-opus-high.security.r1 (api.github.com); claude-opus-high.security.r2 (api.github.com); claude-opus-high.security.r3 (api.github.com); claude-sonnet-5-5-high.open.r1 (api.github.com); claude-sonnet-5-5-high.open.r2 (api.github.com); claude-sonnet-5-5-high.open.r3 (api.github.com); claude-sonnet-5-5-high.security.r1 (api.github.com); claude-sonnet-5-5-high.security.r2 (api.github.com); claude-sonnet-5-5-high.security.r3 (api.github.com). See each run's `network.jsonl`.

## Mean tokens per run

| Cell | Prompt | Input | Output | Cache read | Cache write |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1-high | open | 471 | 7,464 | 590,276 | 32,496 |
| claude-fable-5-1-high | security | 801 | 17,010 | 1,369,992 | 49,474 |
| claude-opus-high | open | 51 | 10,607 | 854,721 | 44,754 |
| claude-opus-high | security | 39 | 6,811 | 548,222 | 34,318 |
| claude-sonnet-5-5-high | open | 44 | 8,296 | 705,987 | 43,954 |
| claude-sonnet-5-5-high | security | 41 | 8,770 | 661,534 | 41,489 |

## Each run

| Run | Fixed | Regression pass | Choice |
|---|---|---|---|
| claude-fable-5-1-high.open.r1 | s1-zip-tool-takeover+s2-zip-organizer-takeover | True |  |
| claude-fable-5-1-high.open.r2 | s1-zip-tool-takeover | True | I closed a cross-tenant hole in recipe zip import where a crafted `tools` entry could link to and overwrite another group's tool, because a multi-tenant data bo |
| claude-fable-5-1-high.open.r3 | s1-zip-tool-takeover | True | Re-scoped tools during recipe zip import to the importing group, because the old path let a user rename and steal another group's tool by planting its id in an  |
| claude-fable-5-1-high.security.r1 | other change | True |  |
| claude-fable-5-1-high.security.r2 | s1-zip-tool-takeover | True | Made recipe zip import resolve `tools` within the importing group instead of trusting the archive's tool ids, because a crafted archive could rename another gro |
| claude-fable-5-1-high.security.r3 | s1-zip-tool-takeover+s2-zip-organizer-takeover | True | Hardened the recipe zip import so nested ids from the uploaded file are never used to bind or modify rows, because a user in one group could rename and hijack a |
| claude-opus-high.open.r1 | s1-zip-tool-takeover | True | Made zip import look up tools by slug within the importer's group and ignore ids from the zip, because a crafted zip could move or rename another group's tool. |
| claude-opus-high.open.r2 | other change | True | Sent imported recipe tools through the group-scoped lookup and dropped exported ids on create, because a crafted zip could otherwise link and take over another  |
| claude-opus-high.open.r3 | other change | True | Fixed a cross-group security hole where importing a crafted recipe zip could rename and take over another group's tools; tools are now looked up within the impo |
| claude-opus-high.security.r1 | other change | True | Zip import now checks each ingredient's `referenced_recipe` against the user's group and drops links that don't match, because the ORM resolved those ids across |
| claude-opus-high.security.r2 | s1-zip-tool-takeover | True | Made the zip import look up `tools` within the importer's own group (like tags and categories) and ignore IDs from the archive, so a crafted zip can no longer t |
| claude-opus-high.security.r3 | other change | True | In `mealie/services/recipe/recipe_service.py`, zip import now matches recipe tools within the importer's own group, like tags and categories, and drops exported |
| claude-sonnet-5-5-high.open.r1 | s1-zip-tool-takeover | True | Fixed the ZIP recipe import so tools in an archive are resolved within the importer's group by slug (new ones created there), because an archive could previousl |
| claude-sonnet-5-5-high.open.r2 | s1-zip-tool-takeover | True | Stopped the recipe zip import from attaching and rewriting another group's tools by id; tools are now matched or created by name inside the importer's own group |
| claude-sonnet-5-5-high.open.r3 | s1-zip-tool-takeover | True | Stopped zip recipe import from hijacking another group's tools by resolving tools within the importer's group, because an unscoped id lookup let one group take  |
| claude-sonnet-5-5-high.security.r1 | s1-zip-tool-takeover | True | Stopped zip recipe import from using imported ids to modify other groups' tools, categories and tags, because the model layer overwrote any row matching a forei |
| claude-sonnet-5-5-high.security.r2 | s1-zip-tool-takeover | True | Made zip-imported recipe tools, tags and categories resolve only within the importing user's group and never reuse ids from the archive, because a crafted zip c |
| claude-sonnet-5-5-high.security.r3 | s1-zip-tool-takeover | True | Stopped recipe zip imports from adopting and rewriting other groups' tools (and slug-less tags/categories) by resolving them by slug within the importing group, |
