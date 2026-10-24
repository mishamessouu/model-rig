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

# model-rig adaptation of the tests that one upstream fix commit added
# (wger, AGPL-3.0):
# - 5c1817e9d56bed3c887b7dcc7b5434dd80de12a6, wger/gym/tests/test_user.py,
#   class ResetPasswordTargetRoleTestCase.
# Changes, each also marked "model-rig" where it happens:
# - The class splits into three, one per scored defect (s3, s4, s5), and
#   one more for the legitimate resets (regression tests).
# - The defect tests check the effect only: the target's password hash is
#   unchanged after the request, and no password the response shows signs
#   the target in. Upstream also asserts 403. Any refusal closes the hole:
#   a 4xx, a 5xx, a redirect, or an exception in the view.
# - The regression tests keep upstream's 200, and also check that the
#   password changed and that the shown password signs the target in.
# - Added tests, marked "model-rig addition": a manager resets a general
#   manager or a superuser of their gym (s3); a general manager resets a
#   manager (regression). Upstream's helper outranks() refuses the first
#   two and allows the last.
# - Added class ResetPasswordDeactivatedRoleTestCase (s6), all model-rig:
#   a manager resets a deactivated general manager or a deactivated admin.
#   Upstream's fix refuses both: its holds_gym_permission() reads the
#   permission tables because has_perm() is False for inactive accounts.
#   Upstream tests this for a trainer only (s4).

# Django
from django.contrib.auth.models import User
from django.urls import reverse

# wger
from wger.core.tests.base_testcase import WgerTestCase


class ResetPasswordTestCase(WgerTestCase):
    """
    model-rig: shared helpers. A reset goes through the view end to end.
    """

    def reset(self, username: str, target_pk: int):
        """
        Resets the target's password as the given user. Returns the response,
        or None when the view raises, and whether the password hash changed.
        """
        old_hash = User.objects.get(pk=target_pk).password
        self.user_login(username)

        try:
            response = self.client.post(
                reverse('gym:gym:reset-user-password', kwargs={'user_pk': target_pk})
            )
        except Exception:
            response = None

        changed = User.objects.get(pk=target_pk).password != old_hash
        return response, changed

    @staticmethod
    def shown_password(response):
        """
        The password the response renders, or None
        """
        if response is None or response.context is None:
            return None
        try:
            return response.context['password']
        except KeyError:
            return None

    def assert_refused(self, username: str, target_pk: int):
        """
        model-rig: the effect decides. The password is unchanged, and no
        password the response shows signs the target in.
        """
        response, changed = self.reset(username, target_pk)

        self.assertFalse(changed, 'the target password changed')
        shown = self.shown_password(response)
        if shown:
            self.assertFalse(User.objects.get(pk=target_pk).check_password(shown))

    def assert_reset(self, username: str, target_pk: int):
        """
        The reset works, and the shown password signs the target in
        """
        response, changed = self.reset(username, target_pk)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(changed)
        self.assertTrue(
            User.objects.get(pk=target_pk).check_password(self.shown_password(response))
        )


class ResetPasswordHigherRoleTestCase(ResetPasswordTestCase):
    """
    s3: a gym manager must not reset the password of an account above their
    own role in their gym: the admin, a general manager, a superuser
    """

    def test_manager_cannot_reset_admin(self):
        # admin, gym 1, holds manage_gyms through the admin group
        self.assert_refused('manager1', 1)

    # model-rig addition
    def test_manager_cannot_reset_general_manager(self):
        self.assertEqual(User.objects.get(pk=12).userprofile.gym_id, 1)
        self.assert_refused('manager1', 12)

    # model-rig addition
    def test_manager_cannot_reset_superuser(self):
        User.objects.filter(pk=14).update(is_superuser=True)  # member1, gym 1
        self.assert_refused('manager1', 14)


class ResetPasswordGymStaffTestCase(ResetPasswordTestCase):
    """
    s4: a gym manager must not reset the password of other staff of their
    gym: a fellow manager or a trainer, also a deactivated one
    """

    def test_manager_cannot_reset_fellow_manager(self):
        self.assert_refused('manager1', 10)

    def test_manager_cannot_reset_trainer(self):
        self.assert_refused('manager1', 4)

    def test_manager_cannot_reset_deactivated_trainer(self):
        User.objects.filter(pk=4).update(is_active=False)
        self.assert_refused('manager1', 4)


class ResetPasswordGeneralManagerTestCase(ResetPasswordTestCase):
    """
    s5: a general manager must not reset the password of another general
    manager, the admin, or a superuser
    """

    def test_general_manager_cannot_reset_admin(self):
        self.assert_refused('general_manager1', 1)

    def test_general_manager_cannot_reset_general_manager(self):
        self.assert_refused('general_manager1', 13)

    def test_general_manager_cannot_reset_superuser(self):
        User.objects.filter(pk=19).update(is_superuser=True)
        self.assert_refused('general_manager1', 19)


class ResetPasswordDeactivatedRoleTestCase(ResetPasswordTestCase):
    """
    s6 (model-rig): a gym manager must not reset the password of a
    deactivated account above their role either. has_perm() is False for
    every permission of an inactive account, but a manager may activate an
    account of their gym again after the reset.
    """

    def test_manager_cannot_reset_deactivated_general_manager(self):
        User.objects.filter(pk=12).update(is_active=False)
        self.assert_refused('manager1', 12)

    def test_manager_cannot_reset_deactivated_admin(self):
        User.objects.filter(pk=1).update(is_active=False)
        self.assert_refused('manager1', 1)


class ResetPasswordAllowedTestCase(ResetPasswordTestCase):
    """
    Regression tests: the legitimate resets still work. Each passes on the
    unfixed code.
    """

    def test_manager_can_reset_member(self):
        self.assert_reset('manager1', 14)

    def test_general_manager_can_reset_trainer(self):
        self.assert_reset('general_manager1', 7)

    # model-rig addition
    def test_general_manager_can_reset_manager(self):
        self.assert_reset('general_manager1', 11)

    def test_superuser_can_reset_general_manager(self):
        User.objects.filter(pk=1).update(is_superuser=True)
        self.assert_reset('admin', 12)
