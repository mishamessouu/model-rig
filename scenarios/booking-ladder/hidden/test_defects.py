"""One test class per planted defect. Each fails on the untouched fixture."""
import unittest

from bookings.invoice import invoice_lines, invoice_total

from .common import cli_output, make_service


class DoubleTotal(unittest.TestCase):
    def test_report_total_printed_once(self):
        lines = [line for line in cli_output().splitlines() if "1140" in line]
        self.assertEqual(len(lines), 1)


class InvoiceDiscount(unittest.TestCase):
    def test_member_invoice_matches_quote(self):
        service = make_service()
        booking = service.book("alice", "Fjord", "Planning", 2)
        alice = service.users["alice"]
        self.assertEqual(invoice_total(booking, alice), service.quote("alice", 2))
        self.assertIn("360", "\n".join(invoice_lines(booking, alice)))


class SqlInjection(unittest.TestCase):
    def test_search_does_not_show_other_owners(self):
        service = make_service()
        service.book("alice", "Fjord", "Planning", 1)
        secret = service.book("bob", "Glacier", "Secret merger", 1)
        found = service.search("alice", "%' OR owner LIKE '%")
        self.assertNotIn(secret.id, [booking.id for booking in found])

    def test_search_title_with_apostrophe(self):
        service = make_service()
        booking = service.book("alice", "Fjord", "O'Brien review", 1)
        found = service.search("alice", "O'Brien")
        self.assertEqual([item.id for item in found], [booking.id])


class CancelOwnership(unittest.TestCase):
    def test_other_user_cannot_cancel(self):
        service = make_service()
        booking = service.book("alice", "Fjord", "Planning", 1)
        with self.assertRaises(Exception):
            service.cancel("bob", booking.id)
        self.assertEqual(service.get("alice", booking.id).status, "active")
