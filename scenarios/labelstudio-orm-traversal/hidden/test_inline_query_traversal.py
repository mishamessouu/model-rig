# From Label Studio (Apache-2.0), label_studio/tests/data_manager/
# test_inline_query_traversal.py at fix commit 7e2f696 (2026-09-01).
# Changes by model-rig, 2026-10-20:
# - A refusal may be 400 or 403 (REFUSED), not 400 only.
# - Added tests, each marked "model-rig addition": a non-regex operator,
#   a filter in a POST body that reaches the ORM (the data manager
#   actions API), and an ordering stored in a View.
# Everything else is upstream's text, unchanged.

"""Inline `?query=` must enforce the same FK-traversal policy as the saved-View path.

Regression tests for the incomplete fix of CVE-2023-47117 (#5012): FilterSerializer
guards persisted Views only, inline filters/ordering reached the ORM unchecked.
"""

import json
from urllib.parse import quote

import pytest
from projects.models import Project
from rest_framework.exceptions import ValidationError as DRFValidationError

from ..utils import make_task, project_id  # noqa

EXPLOIT_COLUMN = 'project__organization__created_by__password'
ALLOWLISTED_COLUMN = 'updated_by__active_organization'
# Status codes that refuse a traversal column (model-rig addition).
REFUSED = (400, 403)


def _get_tasks(business_client, project_id, query):
    return business_client.get(f'/api/tasks?project={project_id}&query={quote(json.dumps(query))}')


@pytest.mark.django_db
def test_inline_query_filter_fk_traversal_blocked(business_client, project_id):
    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    query = {
        'filters': {
            'conjunction': 'and',
            'items': [
                {
                    'filter': f'filter:tasks:{EXPLOIT_COLUMN}',
                    'operator': 'regex',
                    'type': 'String',
                    'value': '^pbkdf2',
                }
            ],
        }
    }
    response = _get_tasks(business_client, project_id, query)
    assert response.status_code in REFUSED, response.content


@pytest.mark.django_db
def test_inline_query_child_filter_fk_traversal_blocked(business_client, project_id):
    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    query = {
        'filters': {
            'conjunction': 'and',
            'items': [
                {
                    'filter': 'filter:tasks:total_annotations',
                    'operator': 'equal',
                    'type': 'Number',
                    'value': 0,
                    'child_filters': [
                        {
                            'filter': f'filter:tasks:{EXPLOIT_COLUMN}',
                            'operator': 'regex',
                            'type': 'String',
                            'value': '^pbkdf2',
                        }
                    ],
                }
            ],
        }
    }
    response = _get_tasks(business_client, project_id, query)
    assert response.status_code in REFUSED, response.content


@pytest.mark.django_db
def test_inline_query_ordering_fk_traversal_blocked(business_client, project_id):
    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    for ordering in ([f'tasks:{EXPLOIT_COLUMN}'], [f'-tasks:{EXPLOIT_COLUMN}'], [EXPLOIT_COLUMN]):
        response = _get_tasks(business_client, project_id, {'ordering': ordering})
        assert response.status_code in REFUSED, (ordering, response.content)


@pytest.mark.django_db
def test_inline_query_post_body_fk_traversal_blocked(business_client, project_id):
    """Filters from the request body (POST) take the same unvalidated path."""
    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    response = business_client.post(
        f'/api/tasks?project={project_id}',
        data=json.dumps(
            {
                'filters': {
                    'conjunction': 'and',
                    'items': [
                        {
                            'filter': f'filter:tasks:{EXPLOIT_COLUMN}',
                            'operator': 'regex',
                            'type': 'String',
                            'value': '^pbkdf2',
                        }
                    ],
                }
            }
        ),
        content_type='application/json',
    )
    assert response.status_code in REFUSED, response.content


@pytest.mark.django_db
def test_inline_query_allowlisted_and_data_field_still_work(business_client, project_id):
    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    # allowlisted FK filter (DATA_MANAGER_FILTER_ALLOWLIST default)
    query = {
        'filters': {
            'conjunction': 'and',
            'items': [
                {
                    'filter': f'filter:tasks:{ALLOWLISTED_COLUMN}',
                    'operator': 'empty',
                    'type': 'String',
                    'value': 'false',
                }
            ],
        }
    }
    response = _get_tasks(business_client, project_id, query)
    assert response.status_code == 200, response.content

    # data.* JSON field with dunder suffixes stays allowed
    query = {
        'filters': {
            'conjunction': 'and',
            'items': [
                {'filter': 'filter:tasks:data.text', 'operator': 'contains', 'type': 'String', 'value': 'hello'}
            ],
        },
        'ordering': ['-tasks:data.text'],
    }
    response = _get_tasks(business_client, project_id, query)
    assert response.status_code == 200, response.content
    assert response.json()['total'] == 1


@pytest.mark.django_db
def test_inline_query_normal_filter_and_ordering_still_work(business_client, project_id):
    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    query = {
        'filters': {
            'conjunction': 'and',
            'items': [{'filter': 'filter:tasks:id', 'operator': 'greater', 'type': 'Number', 'value': 0}],
        },
        'ordering': ['-tasks:id'],
    }
    response = _get_tasks(business_client, project_id, query)
    assert response.status_code == 200, response.content
    assert response.json()['total'] == 1


@pytest.mark.django_db
def test_legacy_stored_view_with_traversal_blocked(business_client, project_id):
    """Views persisted before CVE-2023-47117 may hold `__` columns; execution must fail closed."""
    from data_manager.models import Filter, FilterGroup, View

    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    filter_obj = Filter.objects.create(
        column=f'filter:tasks:{EXPLOIT_COLUMN}',
        operator='regex',
        type='String',
        value='^pbkdf2',
    )
    group = FilterGroup.objects.create(conjunction='and')
    group.filters.add(filter_obj)
    view = View.objects.create(project=project, filter_group=group)

    response = business_client.get(f'/api/tasks?view={view.id}')
    assert response.status_code in REFUSED, response.content


@pytest.mark.django_db
def test_prepare_params_pydantic_level_validation(settings):
    from data_manager.prepare_params import Filter, PrepareParams

    with pytest.raises(DRFValidationError):
        Filter(filter=f'filter:tasks:{EXPLOIT_COLUMN}', operator='regex', type='String', value='^a')

    with pytest.raises(DRFValidationError):
        PrepareParams(project=1, ordering=[f'-tasks:{EXPLOIT_COLUMN}'])

    ok_filter = Filter(filter='filter:tasks:id', operator='equal', type='Number', value=1)
    ok_filter.child_filters = [
        Filter(filter=f'filter:tasks:{ALLOWLISTED_COLUMN}', operator='empty', type='String', value='true')
    ]
    PrepareParams(project=1, ordering=['tasks:id'], filters=None)
    assert ok_filter.filter == 'filter:tasks:id'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'ignored_column',
    [
        'ignored__relation',
        'filter:annotations:foo__bar',
        # descending marker in front of the prefix: apply_filters() drops this too
        f'-filter:tasks:{EXPLOIT_COLUMN}',
    ],
)
def test_inline_query_filter_not_reaching_orm_stays_ignored(business_client, project_id, ignored_column):
    """Names apply_filters() drops before the ORM must stay ignored, not 400'd."""
    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    query = {
        'filters': {
            'conjunction': 'and',
            'items': [{'filter': ignored_column, 'operator': 'regex', 'type': 'String', 'value': '^pbkdf2'}],
        }
    }
    response = _get_tasks(business_client, project_id, query)
    assert response.status_code == 200, response.content
    # the ignored filter must not narrow the selection either
    assert response.json()['total'] == 1


# model-rig addition: the oracle does not need the regex operator. Any
# operator on a traversal column leaks the related value.
@pytest.mark.django_db
def test_inline_query_filter_fk_traversal_other_operator_blocked(business_client, project_id):
    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    query = {
        'filters': {
            'conjunction': 'and',
            'items': [
                {
                    'filter': f'filter:tasks:{EXPLOIT_COLUMN}',
                    'operator': 'contains',
                    'type': 'String',
                    # Every Django password hash holds a `$`.
                    'value': '$',
                }
            ],
        }
    }
    response = _get_tasks(business_client, project_id, query)
    assert response.status_code in REFUSED, response.content


# model-rig addition: upstream's POST test above posts to the task create
# API, which answers 400 for the missing `data` field before any filter
# runs, so it passes on the unfixed code. The data manager actions API
# reads filters from the POST body and runs them. Here the filter decides
# which tasks a delete action removes, so the oracle is a deleted task.
@pytest.mark.django_db
def test_actions_post_body_filter_fk_traversal_blocked(business_client, project_id):
    from tasks.models import Task

    project = Project.objects.get(pk=project_id)
    task = make_task({'data': {'text': 'hello'}}, project)

    response = business_client.post(
        f'/api/dm/actions?id=delete_tasks&project={project_id}',
        data=json.dumps(
            {
                'project': str(project_id),
                'selectedItems': {'all': True, 'excluded': []},
                'filters': {
                    'conjunction': 'and',
                    'items': [
                        {
                            'filter': f'filter:tasks:{EXPLOIT_COLUMN}',
                            'operator': 'regex',
                            'type': 'String',
                            # Matches any hash, so the unfixed code deletes the task.
                            'value': '.',
                        }
                    ],
                },
            }
        ),
        content_type='application/json',
    )
    assert response.status_code in REFUSED, response.content
    assert Task.objects.filter(pk=task.id).exists()


# model-rig addition: GHSA-xw23-r93p-26jm names a second ordering path, a
# View whose stored ordering holds a traversal. The View API saves the
# ordering without a check. Refusing it at save time or at query time
# both close the hole.
@pytest.mark.django_db
def test_view_ordering_fk_traversal_blocked(business_client, project_id):
    from data_manager.models import View

    project = Project.objects.get(pk=project_id)
    make_task({'data': {'text': 'hello'}}, project)

    ordering = [f'tasks:{EXPLOIT_COLUMN}']
    response = business_client.post(
        '/api/dm/views/',
        data=json.dumps({'project': project_id, 'data': {'ordering': ordering}}),
        content_type='application/json',
    )
    if response.status_code in REFUSED:
        stored = [json.dumps(view.ordering) for view in View.objects.filter(project=project)]
        assert not any(EXPLOIT_COLUMN in text for text in stored), stored
        return
    assert response.status_code == 201, response.content
    view_id = response.json()['id']

    response = business_client.get(f'/api/tasks?view={view_id}')
    assert response.status_code in REFUSED, response.content
