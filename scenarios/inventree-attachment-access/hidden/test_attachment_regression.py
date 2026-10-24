"""Hidden regression tests for the model-rig scenario inventree-attachment-access.

model-rig's own tests, not upstream's. A user with view permission on the
linked model must still list and read its attachments. This is the allowed
half of upstream's test_attachment_read_permissions (fix commit
528bb085d7ccde10d76a8c78580d4659cabbe45c), split out so that a fix that
hides too much fails here, not in a defect test.

The module also imports upstream's visible attachment test classes, so one
test run (one test database, about 85 s of migrations) covers them all.
scenario.toml restores their files from the fixture before scoring.
"""

from django.urls import reverse

from common.test_api import AttachmentAPITests, AttachmentThumbnailAPITests
from common.test_attachment_access import AttachmentAccessBase
from common.tests import AttachmentTest
from part.test_api import AttachmentTest as PartAttachmentTest

__all__ = [
    'AttachmentAPITests',
    'AttachmentReadStillWorksTest',
    'AttachmentTest',
    'AttachmentThumbnailAPITests',
    'PartAttachmentTest',
]


class AttachmentReadStillWorksTest(AttachmentAccessBase):
    """Regression: view permission on the linked model still shows its attachments."""

    def assertListShows(self, attachment):
        """The plain list holds the attachment."""
        response = self.get(reverse('api-attachment-list'), expected_code=200)
        self.assertIn(attachment.pk, self.result_ids(response))

    def assertDetailShows(self, attachment):
        """The detail endpoint returns the attachment with its comment."""
        response = self.get(
            reverse('api-attachment-detail', kwargs={'pk': attachment.pk}),
            expected_code=200,
        )
        self.assertEqual(response.data['pk'], attachment.pk)
        self.assertEqual(response.data['comment'], attachment.comment)

    def test_part_role_shows_part_attachment(self):
        """Part view permission lists and reads a part's attachment."""
        self.assignRole('part.view')

        self.assertListShows(self.part_attachment)
        self.assertDetailShows(self.part_attachment)

        response = self.get(
            reverse('api-attachment-list'),
            {'model_type': 'part', 'model_id': self.part.pk},
            expected_code=200,
        )
        self.assertEqual(self.result_ids(response), {self.part_attachment.pk})

    def test_both_roles_show_both_attachments(self):
        """Part and stock view permission list and read both attachments."""
        self.assignRole('part.view')
        self.assignRole('stock.view')

        for attachment in (self.part_attachment, self.stock_attachment):
            self.assertListShows(attachment)
            self.assertDetailShows(attachment)

    def test_superuser_shows_both_attachments(self):
        """A superuser lists and reads every attachment."""
        self.user.is_superuser = True
        self.user.save()

        for attachment in (self.part_attachment, self.stock_attachment):
            self.assertListShows(attachment)
            self.assertDetailShows(attachment)
