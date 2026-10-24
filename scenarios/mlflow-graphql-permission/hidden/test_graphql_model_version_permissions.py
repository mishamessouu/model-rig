# From MLflow (Apache-2.0), tests at fix commit 395db9d (2026-09-16):
# - test_graphql_nested_run_model_versions_filtered_by_model_permission and
#   test_graphql_search_model_versions_judges_prompts_by_prompt_grants from
#   tests/server/auth/test_auth.py;
# - test_nested_run_model_versions_use_requested_workspace_grants and the
#   helper _graphql_get_run_model_versions from
#   tests/server/auth/test_client_workspace.py.
# Changes by model-rig, 2026-10-20:
# - The tests live in one file. Fixtures and helpers come from the two
#   upstream modules by import, so this file holds only the new tests.
# - The prompt test is split in two: a registered-model grant must not reveal
#   a prompt version (the leak), and a prompt grant must reveal it.
# - Added tests, each marked "model-rig addition": permitted users and the
#   admin still see every nested version, through both GetRun and SearchRuns,
#   and the nested list follows a grant made after an earlier request.
# Everything else is upstream's text, unchanged.

import pytest
import requests

from mlflow.utils.workspace_utils import WORKSPACE_HEADER_NAME

from tests.helper_functions import random_str
from tests.server.auth.auth_test_utils import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    User,
    create_user,
    grant_role_permission,
)
from tests.server.auth.test_auth import _graphql_query, client  # noqa: F401
from tests.server.auth.test_client_workspace import (  # noqa: F401
    _create_experiment,
    _create_model_version,
    _create_registered_model,
    _create_run,
    _create_workspace,
    _graphql_search_model_versions,
    clear_credentials,
    workspace_client,
    workspace_setup,
)

NO_PERMISSION = [{"MLFLOW_AUTH_CONFIG_PATH": "fixtures/no_permission_auth.ini"}]

GET_RUN_QUERY = """
query($runId: String!) {
  mlflowGetRun(input: {runId: $runId}) {
    run { modelVersions { name version } }
  }
}
"""
SEARCH_RUNS_QUERY = """
query($experimentIds: [String]!) {
  mlflowSearchRuns(input: {experimentIds: $experimentIds}) {
    runs { modelVersions { name version } }
  }
}
"""


def _nested_names(tracking_uri, query, variables, auth):
    # model-rig: the upstream test's inner helper, shared by the added tests.
    response = _graphql_query(tracking_uri, query, variables=variables, auth=auth)
    response.raise_for_status()
    payload = response.json()
    assert payload.get("errors") in (None, [])
    if "mlflowGetRun" in payload["data"]:
        model_versions = payload["data"]["mlflowGetRun"]["run"]["modelVersions"]
    else:
        runs = payload["data"]["mlflowSearchRuns"]["runs"]
        assert len(runs) == 1, runs
        model_versions = runs[0]["modelVersions"]
    return sorted(mv["name"] for mv in model_versions)


def _graphql_get_run_model_versions(
    tracking_uri: str, workspace_name: str, auth: tuple[str, str], run_id: str
):
    query = """
    query GetRun($runId: String!){
      mlflowGetRun(input: {runId: $runId}){
        run { modelVersions { name version } }
      }
    }
    """
    resp = requests.post(
        f"{tracking_uri}/graphql",
        json={"query": query, "variables": {"runId": run_id}},
        auth=auth,
        headers={WORKSPACE_HEADER_NAME: workspace_name},
    )
    resp.raise_for_status()
    payload = resp.json()
    assert payload.get("errors") in (None, [])
    return payload["data"]["mlflowGetRun"]["run"]["modelVersions"]


def _run_with_five_models(client, monkeypatch, owner, prefix, grant_to=None, readable=()):
    # model-rig: the setup of the upstream nested test, shared by the added tests.
    username1, password1 = owner
    with User(username1, password1, monkeypatch):
        experiment_id = client.create_experiment(f"{prefix}_exp")
        run_id = client.create_run(experiment_id).info.run_id
        for i in range(5):
            rm = client.create_registered_model(f"{prefix}_model{i}")
            client.create_model_version(rm.name, f"runs:/{run_id}/model", run_id=run_id)
            if grant_to and i in readable:
                grant_role_permission(
                    client.tracking_uri, grant_to, "registered_model", rm.name, "READ"
                )
    return experiment_id, run_id


@pytest.mark.parametrize("client", NO_PERMISSION, indirect=True)
def test_graphql_search_model_versions_model_grant_does_not_reveal_prompt(client, monkeypatch):
    # Upstream's prompt test, the half that checks the leak.
    owner, owner_password = create_user(client.tracking_uri)
    model_reader, model_reader_password = create_user(client.tracking_uri)
    prompt_name = f"gql_prompt_{random_str()}"

    with User(owner, owner_password, monkeypatch):
        client.register_prompt(prompt_name, "Hello, {{name}}!")

    grant_role_permission(client.tracking_uri, model_reader, "registered_model", "*", "READ")

    query = """
    query SearchModelVersions($input: MlflowSearchModelVersionsInput){
      mlflowSearchModelVersions(input: $input){
        modelVersions { name version }
      }
    }
    """
    variables = {
        "input": {"filter": f"tags.`mlflow.prompt.is_prompt` = 'true' AND name = '{prompt_name}'"}
    }

    def visible_names(auth):
        response = _graphql_query(client.tracking_uri, query, variables=variables, auth=auth)
        response.raise_for_status()
        payload = response.json()
        assert payload.get("errors") in (None, [])
        return [mv["name"] for mv in payload["data"]["mlflowSearchModelVersions"]["modelVersions"]]

    # The admin sees it (model-rig addition: proves the query finds the prompt).
    assert visible_names((ADMIN_USERNAME, ADMIN_PASSWORD)) == [prompt_name]
    # A registered-model grant, even a wildcard, does not reach into the prompt namespace.
    assert visible_names((model_reader, model_reader_password)) == []


@pytest.mark.parametrize("client", NO_PERMISSION, indirect=True)
def test_graphql_search_model_versions_prompt_grant_reveals_prompt(client, monkeypatch):
    # Upstream's prompt test, the half that checks a prompt grant still works.
    owner, owner_password = create_user(client.tracking_uri)
    prompt_reader, prompt_reader_password = create_user(client.tracking_uri)
    prompt_name = f"gql_prompt_{random_str()}"

    with User(owner, owner_password, monkeypatch):
        client.register_prompt(prompt_name, "Hello, {{name}}!")

    grant_role_permission(client.tracking_uri, prompt_reader, "prompt", prompt_name, "READ")

    query = """
    query SearchModelVersions($input: MlflowSearchModelVersionsInput){
      mlflowSearchModelVersions(input: $input){
        modelVersions { name version }
      }
    }
    """
    variables = {
        "input": {"filter": f"tags.`mlflow.prompt.is_prompt` = 'true' AND name = '{prompt_name}'"}
    }
    response = _graphql_query(
        client.tracking_uri,
        query,
        variables=variables,
        auth=(prompt_reader, prompt_reader_password),
    )
    response.raise_for_status()
    payload = response.json()
    assert payload.get("errors") in (None, [])
    names = [mv["name"] for mv in payload["data"]["mlflowSearchModelVersions"]["modelVersions"]]
    # A prompt grant is what makes a prompt version readable, as on the REST search path.
    assert names == [prompt_name]


@pytest.mark.parametrize("client", NO_PERMISSION, indirect=True)
def test_graphql_nested_run_model_versions_filtered_by_model_permission(client, monkeypatch):
    """
    Regression test for GHSA-f253-vggg-rwh8: the nested run.modelVersions field must
    apply the same per-model READ filter as the top-level mlflowSearchModelVersions query.
    """
    username1, password1 = create_user(client.tracking_uri)
    username2, password2 = create_user(client.tracking_uri)

    readable = [0, 2, 4]

    with User(username1, password1, monkeypatch):
        experiment_id = client.create_experiment("gql_nested_mv_test_exp")
        run_id = client.create_run(experiment_id).info.run_id
        for i in range(5):
            rm = client.create_registered_model(f"gql_nested_mv_model{i}")
            client.create_model_version(rm.name, f"runs:/{run_id}/model", run_id=run_id)
            if i in readable:
                grant_role_permission(
                    client.tracking_uri, username2, "registered_model", rm.name, "READ"
                )

    # user2 can read the experiment (and thus the run) but only some of the models
    grant_role_permission(client.tracking_uri, username2, "experiment", experiment_id, "READ")

    get_run_query = """
    query($runId: String!) {
      mlflowGetRun(input: {runId: $runId}) {
        run { modelVersions { name version } }
      }
    }
    """
    search_runs_query = """
    query($experimentIds: [String]!) {
      mlflowSearchRuns(input: {experimentIds: $experimentIds}) {
        runs { modelVersions { name version } }
      }
    }
    """

    def nested_names(query, variables, auth):
        response = _graphql_query(client.tracking_uri, query, variables=variables, auth=auth)
        response.raise_for_status()
        payload = response.json()
        assert payload.get("errors") in (None, [])
        if "mlflowGetRun" in payload["data"]:
            model_versions = payload["data"]["mlflowGetRun"]["run"]["modelVersions"]
        else:
            runs = payload["data"]["mlflowSearchRuns"]["runs"]
            assert len(runs) == 1, runs
            model_versions = runs[0]["modelVersions"]
        return sorted(mv["name"] for mv in model_versions)

    get_run_vars = {"runId": run_id}
    search_runs_vars = {"experimentIds": [experiment_id]}

    # user1 (owner) sees every version through both nested paths
    assert nested_names(get_run_query, get_run_vars, (username1, password1)) == [
        f"gql_nested_mv_model{i}" for i in range(5)
    ]
    assert nested_names(search_runs_query, search_runs_vars, (username1, password1)) == [
        f"gql_nested_mv_model{i}" for i in range(5)
    ]

    # user2 only sees versions of models they can read, matching the top-level search
    assert nested_names(get_run_query, get_run_vars, (username2, password2)) == [
        f"gql_nested_mv_model{i}" for i in readable
    ]
    assert nested_names(search_runs_query, search_runs_vars, (username2, password2)) == [
        f"gql_nested_mv_model{i}" for i in readable
    ]


def test_nested_run_model_versions_use_requested_workspace_grants(workspace_setup):
    client, tracking_uri, workspace_a, username, password = workspace_setup
    workspace_b = f"team-{random_str()}"
    _create_workspace(tracking_uri, workspace_b)

    # In workspace A, a run has versions of two models; the same model name also exists
    # in workspace B so a grant there must not leak into A.
    shared_model = f"shared-{random_str()}"
    granted_model = f"granted-{random_str()}"
    exp_a = _create_experiment(tracking_uri, workspace_a)
    run_a = _create_run(tracking_uri, workspace_a, exp_a)
    for name in (shared_model, granted_model):
        _create_registered_model(tracking_uri, workspace_a, name)
        _create_model_version(tracking_uri, workspace_a, name, run_a)
    _create_registered_model(tracking_uri, workspace_b, shared_model)

    # Run access comes from the experiment grant alone; no workspace-wide grant, since
    # those fold into every resource type and would mask the per-model check.
    grant_role_permission(
        tracking_uri, username, "experiment", exp_a, "READ", workspace=workspace_a
    )
    grant_role_permission(
        tracking_uri, username, "registered_model", granted_model, "READ", workspace=workspace_a
    )
    grant_role_permission(
        tracking_uri, username, "registered_model", shared_model, "READ", workspace=workspace_b
    )

    nested = _graphql_get_run_model_versions(
        tracking_uri, workspace_a, auth=(username, password), run_id=run_a
    )
    assert {v["name"] for v in nested} == {granted_model}

    # The nested field agrees with the top-level search in the same workspace.
    top_level = _graphql_search_model_versions(
        tracking_uri, workspace_a, auth=(username, password), filter_string=f"run_id='{run_a}'"
    )
    assert {v["name"] for v in top_level} == {granted_model}


# model-rig addition: a user with READ on every model sees every nested version.
@pytest.mark.parametrize("client", NO_PERMISSION, indirect=True)
def test_nested_run_model_versions_permitted_reader_sees_all(client, monkeypatch):
    owner = create_user(client.tracking_uri)
    reader, reader_password = create_user(client.tracking_uri)
    experiment_id, run_id = _run_with_five_models(
        client, monkeypatch, owner, "gql_permitted", grant_to=reader, readable=range(5)
    )
    grant_role_permission(client.tracking_uri, reader, "experiment", experiment_id, "READ")
    every = [f"gql_permitted_model{i}" for i in range(5)]
    auth = (reader, reader_password)
    assert _nested_names(client.tracking_uri, GET_RUN_QUERY, {"runId": run_id}, auth) == every
    assert (
        _nested_names(
            client.tracking_uri, SEARCH_RUNS_QUERY, {"experimentIds": [experiment_id]}, auth
        )
        == every
    )


# model-rig addition: a wildcard model grant and the admin see every nested version.
@pytest.mark.parametrize("client", NO_PERMISSION, indirect=True)
def test_nested_run_model_versions_wildcard_reader_and_admin_see_all(client, monkeypatch):
    owner = create_user(client.tracking_uri)
    reader, reader_password = create_user(client.tracking_uri)
    experiment_id, run_id = _run_with_five_models(client, monkeypatch, owner, "gql_wildcard")
    grant_role_permission(client.tracking_uri, reader, "experiment", experiment_id, "READ")
    grant_role_permission(client.tracking_uri, reader, "registered_model", "*", "READ")
    every = [f"gql_wildcard_model{i}" for i in range(5)]
    for auth in ((reader, reader_password), (ADMIN_USERNAME, ADMIN_PASSWORD)):
        assert _nested_names(client.tracking_uri, GET_RUN_QUERY, {"runId": run_id}, auth) == every
        assert (
            _nested_names(
                client.tracking_uri, SEARCH_RUNS_QUERY, {"experimentIds": [experiment_id]}, auth
            )
            == every
        )


# model-rig addition: a grant made between two requests shows in the second,
# so a filter may not keep a user's grants beyond one request.
@pytest.mark.parametrize("client", NO_PERMISSION, indirect=True)
def test_nested_run_model_versions_follow_a_new_grant(client, monkeypatch):
    owner = create_user(client.tracking_uri)
    reader, reader_password = create_user(client.tracking_uri)
    experiment_id, run_id = _run_with_five_models(
        client, monkeypatch, owner, "gql_later", grant_to=reader, readable=[0]
    )
    grant_role_permission(client.tracking_uri, reader, "experiment", experiment_id, "READ")
    auth = (reader, reader_password)
    before = _nested_names(client.tracking_uri, GET_RUN_QUERY, {"runId": run_id}, auth)
    assert "gql_later_model0" in before
    grant_role_permission(
        client.tracking_uri, reader, "registered_model", "gql_later_model3", "READ"
    )
    after = _nested_names(client.tracking_uri, GET_RUN_QUERY, {"runId": run_id}, auth)
    assert {"gql_later_model0", "gql_later_model3"} <= set(after)
