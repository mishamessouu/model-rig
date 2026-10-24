# Licence notice: mealie files

The files below come from mealie, a self-hosted recipe manager:
https://github.com/mealie-recipes/mealie.

mealie is licensed under the GNU Affero General Public License, version 3
(GitHub reports the SPDX id `AGPL-3.0` for its `LICENSE`, and its
`pyproject.toml` says `AGPL-3.0-only`). The files below keep that licence.
The Apache-2.0 licence of the rest of this repository does not apply to
them.

Full licence text: https://github.com/mealie-recipes/mealie/blob/mealie-next/LICENSE

## Files and their upstream source

| File in this repository | Upstream path | Upstream commit |
|---|---|---|
| `hidden/test_recipe_zip_import_groups.py` | `tests/integration_tests/user_recipe_tests/test_recipe_crud.py` (part) | `ab0c8d602fec77799a1abb713c107dc049fb0103` |
| `solutions/s1-zip-tool-takeover/mealie/services/recipe/recipe_service.py` | `mealie/services/recipe/recipe_service.py` | `ab0c8d602fec77799a1abb713c107dc049fb0103` |

The solution file is byte-identical to upstream at the fix commit. Its git
blob id, `ae34df0f739972bf5a70da9733eb98381d3cac2c`, matches the GitHub
contents API on 2026-10-20.

## Commits

- Fix commit: `ab0c8d602fec77799a1abb713c107dc049fb0103` (2026-10-05),
  "Merge commit from fork". Advisory GHSA-99wf-32rc-2767 (CWE-639),
  "Recipe zip import lets a user take over another group's tools and read
  another group's recipes".
- Fixture commit: `46497a95ef183ba011e2e4d950ee0ce618acb124`, the parent
  of the fix commit. `model-rig prepare mealie-zip-import-idor` fetches it
  from upstream. It is not stored in this repository.

`scenario.toml` in this folder is part of model-rig and is Apache-2.0.

Changes from upstream in `hidden/test_recipe_zip_import_groups.py`:

- The six tests the fix added to `test_recipe_crud.py` are moved to a file
  of their own. Their bodies are unchanged.
- The imports, the `tempdir` fixture, and `zip_recipe` come from the same
  upstream file. `zip_recipe_data` is the helper the fix commit added, as
  it is upstream. Unused imports are left out, and the imports our own
  tests need are added.
- Added tests, marked "model-rig addition". Changed on 2026-10-20:
  - Defect tests that send the same zips as the upstream tests but check
    the security effect only, whatever the status code: the other group's
    tool, category, tag, or recipe is untouched, and the imported recipe,
    if any, holds no reference to it. They cover the plain tool case, the
    blank slug case (with a real name, not a blank one), the category half
    and the tool half of the upstream camelCase test, and the sub-recipe
    case in snake_case and camelCase.
  - A regression test: a recipe exported by one group, with a category,
    tag, tool, and sub-recipe, still imports into another group.

`wrong/*.patch` are known wrong fixes that `rig check` must not score as
a success. Their context lines come from
`mealie/services/recipe/recipe_service.py` at the fixture commit, under
AGPL-3.0; the added lines are model-rig's. `wrong/refuse-foreign-zip.patch`
was added on 2026-10-20.
