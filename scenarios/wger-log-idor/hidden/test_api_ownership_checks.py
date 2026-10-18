# This file is part of wger Workout Manager.
#
# wger Workout Manager is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# wger Workout Manager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License

# Standard Library
import json

# Django
from django.urls import reverse

# Third Party
from rest_framework import status

# wger
from wger.core.tests.base_testcase import WgerTestCase
from wger.manager.models import (
    Day,
    Slot,
    SlotEntry,
    WorkoutLog,
    WorkoutSession,
)


# Status codes that refuse a foreign reference (model-rig, 2026-10-17).
REFUSED = (
    status.HTTP_400_BAD_REQUEST,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_404_NOT_FOUND,
)


def _copy(obj, **changes):
    """Save a copy of a fixture object with some fields changed (model-rig)."""
    obj.pk = None
    obj.id = None
    obj._state.adding = True
    for name, value in changes.items():
        setattr(obj, name, value)
    obj.save()
    return obj


def _own_day_and_slot_entry_for_test_user():
    """
    model-rig addition: user 'test' (pk=2, not staff) owns routine pk=3 but
    no day or slot entry in the fixtures, so copy admin's under routine 3.
    The staff user alone cannot show that a fix still lets owners in.
    """
    day = _copy(Day.objects.get(pk=1), routine_id=3)
    slot = _copy(Slot.objects.get(pk=1), day=day)
    entry = _copy(SlotEntry.objects.get(pk=1), slot=slot)
    return day, entry

class WorkoutLogSlotEntryOwnershipTestCase(WgerTestCase):
    """
    Make sure the API rejects cross-user references on the ``slot_entry``
    foreign key when creating or updating a WorkoutLog.

    Slot entry pk=1 belongs to routine pk=1 (user 'admin', pk=1).
    Routine pk=2 belongs to user 'test' (pk=2).
    """

    def test_create_with_foreign_slot_entry_is_forbidden(self):
        """
        POST /api/v2/workoutlog/ from user 'test' must not be able to attach
        a log to admin's slot_entry, even if the request's ``routine`` is
        owned by user 'test'.
        """
        self.user_login('test')

        victim_slot_entry = SlotEntry.objects.get(pk=1)
        self.assertEqual(victim_slot_entry.slot.day.routine.user_id, 1)

        response = self.client.post(
            reverse('workoutlog-list'),
            data={
                'routine': 2,
                'slot_entry': victim_slot_entry.pk,
                'exercise': 1,
                'repetitions': 999,
                'repetitions_unit': 1,
                'weight': 999,
                'weight_unit': 1,
                'date': '2024-01-01',
                'iteration': 1,
            },
        )

        # model-rig change from upstream: upstream asserts 403. A refusal
        # with 400 or 404 is as secure; the record check below decides.
        self.assertIn(response.status_code, REFUSED)
        self.assertFalse(
            WorkoutLog.objects.filter(slot_entry=victim_slot_entry, weight=999).exists()
        )

    def test_create_with_own_slot_entry_is_allowed(self):
        """
        Ensure the new ownership check does not break the legitimate case.
        """
        self.user_login()

        own_slot_entry = SlotEntry.objects.get(pk=1)
        self.assertEqual(own_slot_entry.slot.day.routine.user_id, 1)

        response = self.client.post(
            reverse('workoutlog-list'),
            data={
                'routine': 1,
                'slot_entry': own_slot_entry.pk,
                'exercise': 1,
                'repetitions': 5,
                'repetitions_unit': 1,
                'weight': 50,
                'weight_unit': 1,
                'date': '2024-01-01',
                'iteration': 1,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_own_slot_entry_as_regular_user_is_allowed(self):
        """
        model-rig addition: the owner check must not lock out an owner who
        is not staff.
        """
        self.user_login('test')
        _, own_slot_entry = _own_day_and_slot_entry_for_test_user()

        response = self.client.post(
            reverse('workoutlog-list'),
            data={
                'routine': 3,
                'slot_entry': own_slot_entry.pk,
                'exercise': 1,
                'repetitions': 5,
                'repetitions_unit': 1,
                'weight': 50,
                'weight_unit': 1,
                'date': '2024-01-01',
                'iteration': 1,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_with_foreign_slot_entry_is_forbidden(self):
        """
        model-rig addition: an update must not attach a log to admin's
        slot entry either, so a check in create() alone does not count.
        """
        self.user_login('test')

        created = self.client.post(
            reverse('workoutlog-list'),
            data={
                'routine': 3,
                'exercise': 1,
                'repetitions': 5,
                'repetitions_unit': 1,
                'weight': 50,
                'weight_unit': 1,
                'date': '2024-01-01',
                'iteration': 1,
            },
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        log_id = created.json()['id']

        response = self.client.patch(
            reverse('workoutlog-detail', kwargs={'pk': log_id}),
            data=json.dumps({'slot_entry': 1}),
            content_type='application/json',
        )

        self.assertIn(response.status_code, REFUSED)
        self.assertNotEqual(WorkoutLog.objects.get(pk=log_id).slot_entry_id, 1)


class WorkoutLogNextLogOwnershipTestCase(WgerTestCase):
    """
    Make sure the API rejects cross-user references on the ``next_log``
    foreign key. Without the ownership check the model save() silently
    nulls the field, but the API should respond with 403 for consistency
    with the other foreign keys on this resource.

    WorkoutLog pk=1 belongs to user 'admin' (pk=1).
    Routine pk=3 belongs to user 'test' (pk=2).
    """

    def test_create_with_foreign_next_log_is_forbidden(self):
        self.user_login('test')

        victim_log = WorkoutLog.objects.get(pk=1)
        self.assertEqual(victim_log.user_id, 1)

        response = self.client.post(
            reverse('workoutlog-list'),
            data={
                'routine': 3,
                'next_log': victim_log.pk,
                'exercise': 1,
                'repetitions': 5,
                'repetitions_unit': 1,
                'weight': 50,
                'weight_unit': 1,
                'date': '2024-01-01',
                'iteration': 1,
            },
        )

        # model-rig change from upstream: upstream asserts 403. A refusal
        # with 400 or 404 is as secure; the record check below decides.
        self.assertIn(response.status_code, REFUSED)
        # model-rig addition: upstream checks only the status code here.
        self.assertFalse(
            WorkoutLog.objects.filter(next_log=victim_log, repetitions=5, weight=50).exists()
        )

    def test_create_with_own_next_log_is_allowed(self):
        """
        model-rig addition: the legitimate case still works, so a fix that
        refuses every next_log scores as a regression.
        """
        self.user_login()

        own_log = WorkoutLog.objects.get(pk=1)
        self.assertEqual(own_log.user_id, 1)

        response = self.client.post(
            reverse('workoutlog-list'),
            data={
                'routine': 1,
                'next_log': own_log.pk,
                'exercise': 1,
                'repetitions': 6,
                'repetitions_unit': 1,
                'weight': 51,
                'weight_unit': 1,
                'date': '2024-01-01',
                'iteration': 1,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            WorkoutLog.objects.filter(next_log=own_log, repetitions=6, weight=51).exists()
        )


class WorkoutSessionDayOwnershipTestCase(WgerTestCase):
    """
    Make sure the API rejects cross-user references on the ``day``
    foreign key when creating a WorkoutSession.

    Day pk=1 belongs to routine pk=1 (user 'admin', pk=1).
    Routine pk=3 belongs to user 'test' (pk=2).
    """

    def test_create_with_foreign_day_is_forbidden(self):
        self.user_login('test')

        victim_day = Day.objects.get(pk=1)
        self.assertEqual(victim_day.routine.user_id, 1)

        response = self.client.post(
            reverse('workoutsession-list'),
            data={
                'routine': 3,
                'day': victim_day.pk,
                'date': '2024-02-01',
                'notes': '',
                'impression': '2',
            },
        )

        # model-rig change from upstream: upstream asserts 403. A refusal
        # with 400 or 404 is as secure; the record check below decides.
        self.assertIn(response.status_code, REFUSED)
        self.assertFalse(WorkoutSession.objects.filter(day=victim_day, routine_id=3).exists())

    def test_create_with_own_day_is_allowed(self):
        """
        Smoke test: the legitimate case (own routine + own day) still works.
        Day pk=1 belongs to user 'admin'.
        """
        self.user_login()

        own_day = Day.objects.get(pk=1)
        self.assertEqual(own_day.routine.user_id, 1)

        response = self.client.post(
            reverse('workoutsession-list'),
            data={
                'routine': 1,
                'day': own_day.pk,
                'date': '2024-02-15',
                'notes': '',
                'impression': '2',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_own_day_as_regular_user_is_allowed(self):
        """
        model-rig addition: the owner check must not lock out an owner who
        is not staff.
        """
        self.user_login('test')
        own_day, _ = _own_day_and_slot_entry_for_test_user()

        response = self.client.post(
            reverse('workoutsession-list'),
            data={
                'routine': 3,
                'day': own_day.pk,
                'date': '2024-02-15',
                'notes': '',
                'impression': '2',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_with_foreign_day_is_forbidden(self):
        """
        model-rig addition: an update must not attach a session to admin's
        day either, so a check in create() alone does not count.

        WorkoutSession pk=5 belongs to user 'test', routine pk=3.
        """
        self.user_login('test')

        own_session = WorkoutSession.objects.get(pk=5)
        self.assertEqual(own_session.user_id, 2)

        response = self.client.patch(
            reverse('workoutsession-detail', kwargs={'pk': own_session.pk}),
            data=json.dumps({'day': 1}),
            content_type='application/json',
        )

        self.assertIn(response.status_code, REFUSED)
        self.assertNotEqual(WorkoutSession.objects.get(pk=5).day_id, 1)
