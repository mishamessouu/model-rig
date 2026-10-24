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
# along with Workout Manager.  If not, see <http://www.gnu.org/licenses/>.

# model-rig adaptation of the tests that two upstream fix commits added
# (wger, AGPL-3.0):
# - dd28603abe5b5e3b33eb61e0f3baa94b36052e87, wger/gym/tests/test_config.py,
#   class EditGymConfigOwnershipTestCase.
# - d0ca31ca89be213a4c84b6793df2247fa85469b1, wger/gym/tests/test_admin_config.py,
#   class EditConfigPermissionTestCase.
# Both classes move into this one file. Changes, each also marked
# "model-rig" where it happens:
# - The defect tests check the effect only: the other gym's config, or the
#   admin config, is unchanged after the request. Upstream also asserts
#   403. Any refusal closes the hole: a 403, a 404, a redirect, a form
#   error, or an exception in the view.
# - Added test_config_of_other_gym_is_not_shown: a GET of another gym's
#   config edit form must not show that config's values. A fix that only
#   guards POST passes the upstream test but still shows the form.
# - Added test_config_of_other_gym_with_two_fields: the write test sends
#   the other field too, with a distinct value.
# - Added test_owner_without_permission_other_value: the unpermitted
#   owner posts the other value, so a fix that refuses one value only does
#   not pass.
# - test_config_of_own_gym (upstream) stays here but is not scored: it
#   edits config 3 of gym 2, and the unfixed view refuses that, so it
#   fails on the baseline. A regression test must pass on the baseline.

# Django
from django.contrib.auth.models import User
from django.urls import reverse

# wger
from wger.core.tests.base_testcase import WgerTestCase
from wger.gym.models import (
    GymAdminConfig,
    GymConfig,
)


def _request(client, method, url, data=None):
    """
    model-rig: send a request and return the response, or None when the view
    raises. A raised exception is a refusal too.
    """
    try:
        if method == 'get':
            return client.get(url)
        return client.post(url, data)
    except Exception:
        return None


class EditGymConfigOwnershipTestCase(WgerTestCase):
    """
    Managers can only edit the config of their own gym, also when the ids of the
    config and the gym differ (config 2 belongs to gym 3 in the fixtures)
    """

    data = {'weeks_inactive': 99, 'show_name': True}

    def edit(self, config_pk: int, data=None):
        self.user_login('manager3')  # gym 2
        return _request(
            self.client,
            'post',
            reverse('gym:config:edit', kwargs={'pk': config_pk}),
            data or self.data,
        )

    def test_config_of_other_gym(self):
        self.assertEqual(GymConfig.objects.get(pk=2).gym_id, 3)

        self.edit(2)
        # model-rig: upstream also asserts a 403 here. The effect decides.
        self.assertNotEqual(GymConfig.objects.get(pk=2).weeks_inactive, 99)

    # model-rig addition: the other field, with values that differ from the
    # fixture's, so neither field may change.
    def test_config_of_other_gym_with_two_fields(self):
        config = GymConfig.objects.get(pk=2)
        self.assertEqual(config.gym_id, 3)
        config.show_name = True
        config.save()

        self.edit(2, {'weeks_inactive': 31, 'show_name': ''})

        config = GymConfig.objects.get(pk=2)
        self.assertEqual(config.weeks_inactive, 4)
        self.assertTrue(config.show_name)

    # model-rig addition: the edit form of another gym's config must not show
    # its values. A refusal of any kind passes.
    def test_config_of_other_gym_is_not_shown(self):
        config = GymConfig.objects.get(pk=2)
        self.assertEqual(config.gym_id, 3)
        config.weeks_inactive = 4321
        config.save()

        self.user_login('manager3')  # gym 2
        response = _request(
            self.client, 'get', reverse('gym:config:edit', kwargs={'pk': 2})
        )
        if response is not None:
            self.assertNotIn(b'value="4321"', response.content)

    def test_config_of_own_gym(self):
        # model-rig: not scored, see the top of the file.
        self.assertEqual(GymConfig.objects.get(pk=3).gym_id, 2)

        response = self.edit(3)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GymConfig.objects.get(pk=3).weeks_inactive, 99)

    # model-rig addition: a regression test. A manager whose gym and config
    # share an id still edits it. It passes on the baseline.
    def test_config_of_own_gym_same_id(self):
        self.assertEqual(GymConfig.objects.get(pk=1).gym_id, 1)
        self.user_login('manager1')  # gym 1

        response = self.client.post(reverse('gym:config:edit', kwargs={'pk': 1}), self.data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(GymConfig.objects.get(pk=1).weeks_inactive, 99)


class EditConfigPermissionTestCase(WgerTestCase):
    """
    Editing the own admin config needs the change_gymadminconfig permission
    """

    def url(self):
        return reverse('gym:admin_config:edit', kwargs={'pk': 4})

    def strip(self):
        user = User.objects.get(username='trainer1')
        user.groups.clear()
        user.user_permissions.clear()

    def test_owner_with_permission(self):
        """
        A trainer can edit their own config
        """
        self.user_login('trainer1')
        response = self.client.post(self.url(), {'overview_inactive': ''})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(GymAdminConfig.objects.get(pk=4).overview_inactive)

    def test_owner_without_permission(self):
        """
        Owning the config is not enough without the permission
        """
        self.strip()

        self.user_login('trainer1')
        _request(self.client, 'post', self.url(), {'overview_inactive': ''})

        # model-rig: upstream also asserts a 403 here. The effect decides.
        self.assertTrue(GymAdminConfig.objects.get(pk=4).overview_inactive)

    # model-rig addition: the same, from the other value. A fix that refuses
    # one value only does not pass.
    def test_owner_without_permission_other_value(self):
        config = GymAdminConfig.objects.get(pk=4)
        config.overview_inactive = False
        config.save()
        self.strip()

        self.user_login('trainer1')
        _request(self.client, 'post', self.url(), {'overview_inactive': 'on'})

        self.assertFalse(GymAdminConfig.objects.get(pk=4).overview_inactive)

    # model-rig addition: a regression test. A gym manager, not only a
    # trainer, still edits their own admin config (manager1 owns config 9).
    def test_manager_owner_with_permission(self):
        self.assertEqual(GymAdminConfig.objects.get(pk=9).user.username, 'manager1')
        self.user_login('manager1')
        response = self.client.post(
            reverse('gym:admin_config:edit', kwargs={'pk': 9}), {'overview_inactive': ''}
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(GymAdminConfig.objects.get(pk=9).overview_inactive)
