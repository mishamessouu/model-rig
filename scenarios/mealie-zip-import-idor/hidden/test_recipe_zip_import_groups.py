# Hidden tests for the model-rig scenario mealie-zip-import-idor.
#
# Source: mealie (github.com/mealie-recipes/mealie), AGPL-3.0, file
# tests/integration_tests/user_recipe_tests/test_recipe_crud.py at the fix
# commit ab0c8d602fec77799a1abb713c107dc049fb0103 (GHSA-99wf-32rc-2767).
#
# What model-rig changed:
# - The fix added six tests to test_recipe_crud.py. They live here, in a
#   file of their own, so the agent's visible test_recipe_crud.py stays as
#   it is. Their bodies are byte-identical to upstream.
# - The imports, the module `tempdir` fixture, and `zip_recipe` are copied
#   from the same upstream file, because a fixture in a test module is not
#   shared with other modules. The imports for our own tests are added.
# - `zip_recipe_data` is a test helper the fix commit added. It is copied
#   here as it is upstream, so the tests do not depend on the agent's
#   copy of test_recipe_crud.py.
# - Tests marked "model-rig addition" below are ours. scenario.toml scores
#   them, not the upstream tests that check another group's rows; see the
#   comment above the additions.
#
# Changes on 2026-10-20, after the first batch:
# - The defect tests grade the security effect only, whatever the status
#   code. The upstream tests assert a 201 first, so a fix that closed the
#   tool hole but crashed on a foreign tool id scored as "fixed nothing".
# - The blank-slug tests send a real name. With a blank name, the unfixed
#   code fails on a category or tag and changes nothing, so a test that
#   accepts a refusal would pass on it.
# - The other group's row is read through a new session, not the
#   module-scoped one behind `g2_user.repos`, which can return a stale row.
# - A regression test copies an exported recipe from one group to another.
#   It is the functional half that the upstream tests mixed in.

import json
import os
import tempfile
from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from mealie.db.db_setup import SessionLocal
from mealie.repos.all_repositories import get_repositories
from mealie.schema.recipe.recipe import Recipe, RecipeCategory, RecipeSummary, RecipeTool
from mealie.schema.recipe.recipe_category import CategorySave, TagSave
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_tool import RecipeToolSave
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


@pytest.fixture(scope="module")
def tempdir() -> Generator[str]:
    with tempfile.TemporaryDirectory() as td:
        yield td


def zip_recipe(tempdir: str, recipe: RecipeSummary) -> dict:
    return zip_recipe_data(tempdir, json.loads(recipe.model_dump_json()))


def zip_recipe_data(tempdir: str, recipe_data: dict) -> dict:
    with tempfile.NamedTemporaryFile(mode="w+", dir=tempdir, suffix=".json", delete=False) as data_file:
        json.dump(recipe_data, data_file)
        data_file.flush()

        zip_file = os.path.join(tempdir, "zipfile.zip")
        with ZipFile(zip_file, "w") as zf:
            zf.write(data_file.name)

        return {"archive": Path(zip_file).read_bytes()}


# Upstream tests from the fix commit, unchanged.

def test_create_recipe_from_zip_tool_from_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str
):
    """A tool id from another group must not move or rename that group's tool."""
    other_name = random_string()
    other_tool = g2_user.repos.tools.create(RecipeToolSave(name=other_name, group_id=g2_user.group_id))

    recipe_name = random_string()
    recipe = RecipeSummary(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        tools=[RecipeTool(id=other_tool.id, name=random_string(), slug=other_tool.slug)],
    )
    r = api_client.post(api_routes.recipes_create_zip, files=zip_recipe(tempdir, recipe), headers=unique_user.token)
    assert r.status_code == 201

    untouched = g2_user.repos.tools.get_one(other_tool.id)
    assert untouched
    assert str(untouched.group_id) == str(g2_user.group_id)
    assert untouched.name == other_name

    imported = api_client.get(api_routes.recipes_slug(r.json()), headers=unique_user.token).json()
    assert len(imported["tools"]) == 1
    assert imported["tools"][0]["id"] != str(other_tool.id)
    assert imported["tools"][0]["groupId"] == str(unique_user.group_id)


def test_create_recipe_from_zip_camel_case_organizers_from_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str
):
    """camelCase input carries its own `groupId`, which must not link another group's organizers."""
    other_category = g2_user.repos.categories.create(CategorySave(name=random_string(), group_id=g2_user.group_id))
    other_tool = g2_user.repos.tools.create(RecipeToolSave(name=random_string(), group_id=g2_user.group_id))

    recipe_name = random_string()
    recipe = RecipeSummary(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        recipe_category=[
            RecipeCategory(
                id=other_category.id, group_id=g2_user.group_id, name=other_category.name, slug=other_category.slug
            )
        ],
        tools=[RecipeTool(id=other_tool.id, group_id=g2_user.group_id, name=other_tool.name, slug=other_tool.slug)],
    )
    recipe_data = json.loads(recipe.model_dump_json(by_alias=True))
    r = api_client.post(
        api_routes.recipes_create_zip, files=zip_recipe_data(tempdir, recipe_data), headers=unique_user.token
    )
    assert r.status_code == 201

    imported = api_client.get(api_routes.recipes_slug(r.json()), headers=unique_user.token).json()
    assert [c["groupId"] for c in imported["recipeCategory"]] == [str(unique_user.group_id)]
    assert [t["groupId"] for t in imported["tools"]] == [str(unique_user.group_id)]
    assert imported["recipeCategory"][0]["id"] != str(other_category.id)
    assert imported["tools"][0]["id"] != str(other_tool.id)


@pytest.mark.parametrize("organizer", ["recipe_category", "tags", "tools"])
def test_create_recipe_from_zip_blank_organizer_from_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str, organizer: str
):
    """An organizer with a blank name and slug cannot be resolved, so its foreign id must be dropped."""
    repo = {
        "recipe_category": g2_user.repos.categories,
        "tags": g2_user.repos.tags,
        "tools": g2_user.repos.tools,
    }[organizer]
    other_name = random_string()
    save_schema = RecipeToolSave if organizer == "tools" else CategorySave
    other = repo.create(save_schema(name=other_name, group_id=g2_user.group_id))

    recipe_name = random_string()
    recipe_data = json.loads(
        RecipeSummary(
            id=uuid4(),
            user_id=unique_user.user_id,
            group_id=unique_user.group_id,
            name=recipe_name,
            slug=recipe_name,
        ).model_dump_json()
    )
    recipe_data[organizer] = [{"id": str(other.id), "name": "", "slug": ""}]
    api_client.post(
        api_routes.recipes_create_zip, files=zip_recipe_data(tempdir, recipe_data), headers=unique_user.token
    )

    untouched = repo.get_one(other.id)
    assert untouched
    assert str(untouched.group_id) == str(g2_user.group_id)
    assert untouched.name == other_name


def test_create_recipe_from_zip_keeps_own_tool(api_client: TestClient, unique_user: TestUser, tempdir: str):
    own_tool = unique_user.repos.tools.create(RecipeToolSave(name=random_string(), group_id=unique_user.group_id))

    recipe_name = random_string()
    recipe = RecipeSummary(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        tools=[RecipeTool(id=own_tool.id, name=own_tool.name, slug=own_tool.slug)],
    )
    r = api_client.post(api_routes.recipes_create_zip, files=zip_recipe(tempdir, recipe), headers=unique_user.token)
    assert r.status_code == 201

    imported = api_client.get(api_routes.recipes_slug(r.json()), headers=unique_user.token).json()
    assert [t["id"] for t in imported["tools"]] == [str(own_tool.id)]


def test_create_recipe_from_zip_subrecipe_from_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str
):
    """A sub-recipe reference must not expose a recipe from another group."""
    other_slug = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=g2_user.token).json()
    other_recipe = api_client.get(api_routes.recipes_slug(other_slug), headers=g2_user.token).json()

    recipe_name = random_string()
    recipe = Recipe(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        recipe_ingredient=[
            RecipeIngredient(
                note="",
                referenced_recipe=Recipe(id=other_recipe["id"], name=other_recipe["name"], slug=other_recipe["slug"]),
            )
        ],
    )
    r = api_client.post(api_routes.recipes_create_zip, files=zip_recipe(tempdir, recipe), headers=unique_user.token)
    assert r.status_code == 201

    imported = api_client.get(api_routes.recipes_slug(r.json()), headers=unique_user.token).json()
    assert len(imported["recipeIngredient"]) == 1
    assert imported["recipeIngredient"][0]["referencedRecipe"] is None


def test_create_recipe_from_zip_keeps_own_subrecipe(api_client: TestClient, unique_user: TestUser, tempdir: str):
    own_slug = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=unique_user.token).json()
    own_recipe = api_client.get(api_routes.recipes_slug(own_slug), headers=unique_user.token).json()

    recipe_name = random_string()
    recipe = Recipe(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        recipe_ingredient=[
            RecipeIngredient(
                note="",
                referenced_recipe=Recipe(id=own_recipe["id"], name=own_recipe["name"], slug=own_recipe["slug"]),
            )
        ],
    )
    r = api_client.post(api_routes.recipes_create_zip, files=zip_recipe(tempdir, recipe), headers=unique_user.token)
    assert r.status_code == 201

    imported = api_client.get(api_routes.recipes_slug(r.json()), headers=unique_user.token).json()
    assert imported["recipeIngredient"][0]["referencedRecipe"]["id"] == own_recipe["id"]


# Model-rig additions from here on.
#
# The upstream tests above assert a 201 before they look at the other
# group's row, so they mix the security effect with the import still
# working. A fix that refuses or crashes on a foreign id closes the hole but
# fails them. The defect tests below send the same zips and grade the
# security effect only: the other group's row is untouched, and the recipe
# the import created, if any, holds no reference to it. A refusal (4xx or
# 5xx) passes. Whether a legitimate cross-group copy still imports is the
# regression test's question, at the end of this file.


def _import(api_client: TestClient, user: TestUser, files: dict):
    """Post the zip. Return the response, or None when the server raised.

    The test client raises a server error instead of returning a 500, so a
    crash on a foreign id lands here and counts as a refusal.
    """
    try:
        return api_client.post(api_routes.recipes_create_zip, files=files, headers=user.token)
    except Exception:
        return None


def _imported(api_client: TestClient, user: TestUser, r, recipe_slug: str) -> dict | None:
    """The recipe the import created, or None when it created none.

    After a refusal the recipe is looked up by the slug in the zip, so a
    recipe saved before the error is still checked.
    """
    slug = r.json() if r is not None and r.status_code < 400 else recipe_slug
    found = api_client.get(api_routes.recipes_slug(slug), headers=user.token)
    return found.json() if found.status_code == 200 else None


def _assert_not_linked(imported: dict | None, foreign_id) -> None:
    """The imported recipe, if any, holds no reference to the foreign row."""
    if imported is not None:
        assert str(foreign_id) not in json.dumps(imported)


def _assert_untouched(kind: str, row_id, group_id, name: str) -> None:
    """The other group's row is still in that group, under its own name.

    It reads through a new session. The module-scoped session behind
    `g2_user.repos` can return a stale row after a request changed it.
    """
    session = SessionLocal()
    try:
        untouched = getattr(get_repositories(session, group_id=group_id, household_id=None), kind).get_one(row_id)
        assert untouched
        assert str(untouched.group_id) == str(group_id)
        assert untouched.name == name
    finally:
        session.close()


# model-rig addition: test_create_recipe_from_zip_tool_from_another_group,
# graded on the security effect only.
def test_zip_import_keeps_tool_of_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str
):
    other_name = random_string()
    other_tool = g2_user.repos.tools.create(RecipeToolSave(name=other_name, group_id=g2_user.group_id))

    recipe_name = random_string()
    recipe = RecipeSummary(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        tools=[RecipeTool(id=other_tool.id, name=random_string(), slug=other_tool.slug)],
    )
    r = _import(api_client, unique_user, zip_recipe(tempdir, recipe))

    _assert_untouched("tools", other_tool.id, g2_user.group_id, other_name)
    _assert_not_linked(_imported(api_client, unique_user, r, recipe_name), other_tool.id)


# model-rig addition: test_create_recipe_from_zip_blank_organizer_from_another_group,
# which already skips the status code, plus the check on the imported recipe.
@pytest.mark.parametrize("organizer", ["recipe_category", "tags", "tools"])
def test_zip_import_keeps_blank_organizer_of_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str, organizer: str
):
    kind = {"recipe_category": "categories", "tags": "tags", "tools": "tools"}[organizer]
    other_name = random_string()
    save_schema = RecipeToolSave if organizer == "tools" else CategorySave
    other = getattr(g2_user.repos, kind).create(save_schema(name=other_name, group_id=g2_user.group_id))

    recipe_name = random_string()
    recipe_data = json.loads(
        RecipeSummary(
            id=uuid4(),
            user_id=unique_user.user_id,
            group_id=unique_user.group_id,
            name=recipe_name,
            slug=recipe_name,
        ).model_dump_json()
    )
    # Upstream sends a blank name too. The unfixed code then fails an
    # assert on the empty category or tag name and changes nothing, so a
    # test that accepts a refusal would pass on it. A real name is what
    # takes the row over.
    recipe_data[organizer] = [{"id": str(other.id), "name": random_string(), "slug": ""}]
    r = _import(api_client, unique_user, zip_recipe_data(tempdir, recipe_data))

    _assert_untouched(kind, other.id, g2_user.group_id, other_name)
    _assert_not_linked(_imported(api_client, unique_user, r, recipe_name), other.id)


# model-rig addition: the category half of
# test_create_recipe_from_zip_camel_case_organizers_from_another_group,
# graded on the security effect only. Split from the tool half, each hole
# is scored on its own.
def test_zip_import_keeps_camel_case_category_of_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str
):
    other_name = random_string()
    other_category = g2_user.repos.categories.create(CategorySave(name=other_name, group_id=g2_user.group_id))

    recipe_name = random_string()
    recipe = RecipeSummary(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        recipe_category=[
            RecipeCategory(
                id=other_category.id, group_id=g2_user.group_id, name=other_category.name, slug=other_category.slug
            )
        ],
    )
    recipe_data = json.loads(recipe.model_dump_json(by_alias=True))
    r = _import(api_client, unique_user, zip_recipe_data(tempdir, recipe_data))

    _assert_untouched("categories", other_category.id, g2_user.group_id, other_name)
    _assert_not_linked(_imported(api_client, unique_user, r, recipe_name), other_category.id)


# model-rig addition: the tool half of the same upstream camelCase test.
def test_zip_import_keeps_camel_case_tool_of_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str
):
    other_name = random_string()
    other_tool = g2_user.repos.tools.create(RecipeToolSave(name=other_name, group_id=g2_user.group_id))

    recipe_name = random_string()
    recipe = RecipeSummary(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        tools=[RecipeTool(id=other_tool.id, group_id=g2_user.group_id, name=other_tool.name, slug=other_tool.slug)],
    )
    recipe_data = json.loads(recipe.model_dump_json(by_alias=True))
    r = _import(api_client, unique_user, zip_recipe_data(tempdir, recipe_data))

    _assert_untouched("tools", other_tool.id, g2_user.group_id, other_name)
    _assert_not_linked(_imported(api_client, unique_user, r, recipe_name), other_tool.id)


def _subrecipe_zip(tempdir: str, unique_user: TestUser, recipe_name: str, other_recipe: dict, camel_case: bool) -> dict:
    recipe = Recipe(
        id=uuid4(),
        user_id=unique_user.user_id,
        group_id=unique_user.group_id,
        name=recipe_name,
        slug=recipe_name,
        recipe_ingredient=[
            RecipeIngredient(
                note="",
                referenced_recipe=Recipe(id=other_recipe["id"], name=other_recipe["name"], slug=other_recipe["slug"]),
            )
        ],
    )
    recipe_data = json.loads(recipe.model_dump_json(by_alias=camel_case))
    key = "referencedRecipe" if camel_case else "referenced_recipe"
    ingredients = recipe_data["recipeIngredient" if camel_case else "recipe_ingredient"]
    assert key in ingredients[0]
    return zip_recipe_data(tempdir, recipe_data)


# model-rig addition: test_create_recipe_from_zip_subrecipe_from_another_group,
# graded on the security effect only, in snake_case (as upstream) and in
# camelCase. A check on the `referenced_recipe` key alone misses
# `referencedRecipe`.
@pytest.mark.parametrize("camel_case", [False, True], ids=["snake_case", "camel_case"])
def test_zip_import_hides_subrecipe_of_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser, tempdir: str, camel_case: bool
):
    other_slug = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=g2_user.token).json()
    other_recipe = api_client.get(api_routes.recipes_slug(other_slug), headers=g2_user.token).json()

    recipe_name = random_string()
    r = _import(api_client, unique_user, _subrecipe_zip(tempdir, unique_user, recipe_name, other_recipe, camel_case))

    _assert_not_linked(_imported(api_client, unique_user, r, recipe_name), other_recipe["id"])
    still_there = api_client.get(api_routes.recipes_slug(other_slug), headers=g2_user.token)
    assert still_there.status_code == 200
    assert still_there.json()["id"] == other_recipe["id"]
    assert still_there.json()["name"] == other_recipe["name"]


def _organizer(row) -> dict:
    return {"id": str(row.id), "groupId": str(row.group_id), "name": row.name, "slug": row.slug}


# model-rig addition, a regression test: a legitimate copy of a recipe from
# one group to another on the same instance. The g2 group exports a recipe
# with its route, and a user of another group imports that zip. The zip
# names g2's category, tag, tool, and sub-recipe ids, as every such export
# does. The unfixed code and the upstream fix both import it with 201. A
# fix that refuses, or crashes on, every id from another group fails here.
def test_zip_import_copies_recipe_from_another_group(
    api_client: TestClient, unique_user: TestUser, g2_user: TestUser
):
    category = g2_user.repos.categories.create(CategorySave(name=random_string(), group_id=g2_user.group_id))
    tag = g2_user.repos.tags.create(TagSave(name=random_string(), group_id=g2_user.group_id))
    tool = g2_user.repos.tools.create(RecipeToolSave(name=random_string(), group_id=g2_user.group_id))
    sub_slug = api_client.post(api_routes.recipes, json={"name": random_string()}, headers=g2_user.token).json()
    sub_recipe = api_client.get(api_routes.recipes_slug(sub_slug), headers=g2_user.token).json()

    recipe_name = random_string()
    slug = api_client.post(api_routes.recipes, json={"name": recipe_name}, headers=g2_user.token).json()
    recipe = api_client.get(api_routes.recipes_slug(slug), headers=g2_user.token).json()
    recipe.update(
        {
            "recipeCategory": [_organizer(category)],
            "tags": [_organizer(tag)],
            "tools": [_organizer(tool)],
            "recipeIngredient": [
                {
                    "note": "the base",
                    "referencedRecipe": {"id": sub_recipe["id"], "name": sub_recipe["name"], "slug": sub_slug},
                }
            ],
        }
    )
    assert api_client.put(api_routes.recipes_slug(slug), json=recipe, headers=g2_user.token).status_code == 200

    export = api_client.get(
        api_routes.recipes_slug_exports(slug), params={"template_name": "zip"}, headers=g2_user.token
    )
    assert export.status_code == 200
    with ZipFile(BytesIO(export.content)) as zf:
        exported = "".join(zf.read(n).decode() for n in zf.namelist() if n.endswith(".json"))
    for row_id in (str(category.id), str(tag.id), str(tool.id), sub_recipe["id"]):
        assert row_id in exported

    r = api_client.post(api_routes.recipes_create_zip, files={"archive": export.content}, headers=unique_user.token)
    assert r.status_code == 201

    imported = api_client.get(api_routes.recipes_slug(r.json()), headers=unique_user.token).json()
    assert imported["name"] == recipe_name
    assert [c["name"] for c in imported["recipeCategory"]] == [category.name]
    assert [t["name"] for t in imported["tags"]] == [tag.name]
    assert [t["name"] for t in imported["tools"]] == [tool.name]
    assert [i["note"] for i in imported["recipeIngredient"]] == ["the base"]
