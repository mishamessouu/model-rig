"""Hidden tests for the model-rig scenario inventree-attachment-access.

Source: InvenTree (github.com/inventree/InvenTree), MIT. The upstream test
is test_attachment_read_permissions in
src/backend/InvenTree/common/test_api.py at the fix commit
528bb085d7ccde10d76a8c78580d4659cabbe45c ("User permissions check for
Attachment API", #12689).

What model-rig changed:
- The upstream test is copied below, in a class of its own, with its body
  unchanged. scenario.toml does not score it. It asserts 403 on a denied
  detail read, so a correct fix that answers 404, or that hides the row
  from the queryset, would fail it. It also mixes the denied reads with
  the allowed ones.
- The defect tests are ours. They send the same requests as upstream, plus
  filtered and paginated list requests, and grade the effect only: the
  response must not hold the attachment's row or its comment or link. Any
  refusal passes: a 4xx or 5xx status, or an exception in the view.
- The regression tests are in test_attachment_regression.py.
"""

import uuid

from django.urls import reverse

from common.models import Attachment
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from stock.models import StockItem


class AttachmentAccessBase(InvenTreeAPITestCase):
    """A part and a stock item, each with one link attachment.

    The test user is staff (the InvenTreeAPITestCase default) and starts
    with no roles, as in the upstream test.
    """

    def setUp(self):
        """Create the linked models and their attachments."""
        super().setUp()

        tag = uuid.uuid4().hex

        self.part = Part.objects.create(name='Attachable Part', description='A part')
        self.item = StockItem.objects.create(part=self.part, quantity=10)

        self.secrets = {}

        self.part_attachment = self.make_attachment('part', self.part.pk, tag)
        self.stock_attachment = self.make_attachment('stockitem', self.item.pk, tag)

    def make_attachment(self, model_type, model_id, tag):
        """Create one attachment whose comment and link are unique markers."""
        comment = f'rig-{model_type}-comment-{tag}'
        link = f'https://example.com/rig-{model_type}-link-{tag}'

        attachment = Attachment.objects.create(
            model_type=model_type, model_id=model_id, comment=comment, link=link
        )

        self.secrets[attachment.pk] = (comment, link)

        return attachment

    def fetch(self, url, data=None):
        """GET a URL. Return the response, or None if the view raised."""
        try:
            return self.client.get(url, data=data)
        except Exception:
            return None

    def result_ids(self, response):
        """The attachment ids in a successful list response."""
        if response is None or response.status_code >= 400:
            return set()

        data = response.data

        if isinstance(data, dict):
            data = data.get('results', [])

        return {row.get('pk') for row in data if isinstance(row, dict)}

    def assertNoLeak(self, response, attachment, what):
        """The response holds neither the attachment's row nor its data."""
        if response is None:
            return

        body = response.content.decode(errors='replace')

        for secret in self.secrets[attachment.pk]:
            self.assertNotIn(secret, body, f'{what}: {secret} leaked')

        if response.status_code < 400 and isinstance(response.data, dict):
            self.assertNotEqual(
                response.data.get('pk'), attachment.pk, f'{what}: row leaked'
            )

    def assertListHides(self, attachment, data=None):
        """A list request with these query parameters hides the attachment."""
        response = self.fetch(reverse('api-attachment-list'), data)
        what = f'list {data or {}}'

        self.assertNoLeak(response, attachment, what)
        self.assertNotIn(attachment.pk, self.result_ids(response), f'{what}: row leaked')

    def assertDetailHides(self, attachment):
        """A detail request for the attachment shows none of it."""
        url = reverse('api-attachment-detail', kwargs={'pk': attachment.pk})

        self.assertNoLeak(self.fetch(url), attachment, f'detail {attachment.pk}')


class AttachmentListAccessTest(AttachmentAccessBase):
    """Defect s1: the list endpoint shows attachments of models the user cannot view."""

    def list_queries(self, attachment):
        """The ways to ask the list endpoint for one attachment."""
        return [
            None,
            {'limit': 50},
            {'model_type': attachment.model_type},
            {'model_type': attachment.model_type, 'model_id': attachment.model_id},
            {'search': attachment.comment},
        ]

    def test_no_role_lists_no_attachment(self):
        """A user with no roles lists no attachment at all."""
        for attachment in (self.part_attachment, self.stock_attachment):
            for data in self.list_queries(attachment):
                self.assertListHides(attachment, data)

    def test_part_role_lists_no_stock_attachment(self):
        """Part view permission does not show a stock item's attachment."""
        self.assignRole('part.view')

        for data in self.list_queries(self.stock_attachment):
            self.assertListHides(self.stock_attachment, data)


class AttachmentDetailAccessTest(AttachmentAccessBase):
    """Defect s2: the detail endpoint returns attachments of models the user cannot view."""

    def test_no_role_reads_no_attachment(self):
        """A user with no roles reads no attachment."""
        self.assertDetailHides(self.part_attachment)
        self.assertDetailHides(self.stock_attachment)

    def test_part_role_reads_no_stock_attachment(self):
        """Part view permission does not show a stock item's attachment."""
        self.assignRole('part.view')

        self.assertDetailHides(self.stock_attachment)


class UpstreamAttachmentReadPermissionsTest(InvenTreeAPITestCase):
    """Upstream's test from the fix commit, body unchanged. Not scored."""

    def test_attachment_read_permissions(self):
        """Test that reading attachments is gated on the linked model's own view permission.

        A user should not be able to list or retrieve attachments linked to a model
        type they have no view permission for, even though attachments themselves
        have no RuleSet of their own (see users.ruleset.get_ruleset_ignore).
        """
        from common.models import Attachment
        from part.models import Part
        from stock.models import StockItem

        part = Part.objects.create(name='Attachable Part', description='A part')
        item = StockItem.objects.create(part=part, quantity=10)

        part_attachment = Attachment.objects.create(
            model_type='part',
            model_id=part.pk,
            comment='part attachment',
            link='https://example.com/part',
        )
        stock_attachment = Attachment.objects.create(
            model_type='stockitem',
            model_id=item.pk,
            comment='stock attachment',
            link='https://example.com/stock',
        )

        # User has no roles at all - should see nothing, and be denied on direct retrieve
        list_url = reverse('api-attachment-list')
        response = self.get(list_url, expected_code=200)
        result_ids = {result['pk'] for result in response.data}
        self.assertNotIn(part_attachment.pk, result_ids)
        self.assertNotIn(stock_attachment.pk, result_ids)

        self.get(
            reverse('api-attachment-detail', kwargs={'pk': part_attachment.pk}),
            expected_code=403,
        )
        self.get(
            reverse('api-attachment-detail', kwargs={'pk': stock_attachment.pk}),
            expected_code=403,
        )

        # Grant 'view' permission on 'part' only
        self.assignRole('part.view')

        response = self.get(list_url, expected_code=200)
        result_ids = {result['pk'] for result in response.data}
        self.assertIn(part_attachment.pk, result_ids)
        self.assertNotIn(stock_attachment.pk, result_ids)

        self.get(
            reverse('api-attachment-detail', kwargs={'pk': part_attachment.pk}),
            expected_code=200,
        )
        self.get(
            reverse('api-attachment-detail', kwargs={'pk': stock_attachment.pk}),
            expected_code=403,
        )

        # Granting 'stock' view permission too now exposes both
        self.assignRole('stock.view')

        response = self.get(list_url, expected_code=200)
        result_ids = {result['pk'] for result in response.data}
        self.assertIn(part_attachment.pk, result_ids)
        self.assertIn(stock_attachment.pk, result_ids)

        self.get(
            reverse('api-attachment-detail', kwargs={'pk': stock_attachment.pk}),
            expected_code=200,
        )
