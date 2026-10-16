"""Behaviour every correct change keeps. Passes on the untouched fixture."""
import unittest

from bookings.api import handle
from bookings.invoice import invoice_lines, invoice_total
from bookings.service import NotFound

from .common import cli_output, make_service


class ServiceBehaviour(unittest.TestCase):
    def test_book_and_get_own(self):
        service = make_service()
        booking = service.book("alice", "Fjord", "Planning", 2)
        self.assertEqual(service.get("alice", booking.id).title, "Planning")

    def test_cannot_get_other_users_booking(self):
        service = make_service()
        booking = service.book("alice", "Fjord", "Planning", 2)
        with self.assertRaises(NotFound):
            service.get("bob", booking.id)

    def test_cancel_own(self):
        service = make_service()
        booking = service.book("alice", "Fjord", "Planning", 2)
        service.cancel("alice", booking.id)
        self.assertEqual(service.get("alice", booking.id).status, "cancelled")

    def test_hours_are_checked(self):
        with self.assertRaises(ValueError):
            make_service().book("alice", "Fjord", "Planning", 0)

    def test_search_own(self):
        service = make_service()
        planning = service.book("alice", "Fjord", "Planning", 1)
        service.book("alice", "Fjord", "Retro", 1)
        self.assertEqual([b.id for b in service.search("alice", "Plan")], [planning.id])
        self.assertEqual(len(service.search("alice", "")), 2)

    def test_quotes(self):
        service = make_service()
        self.assertEqual(service.quote("alice", 2), 360)
        self.assertEqual(service.quote("bob", 3), 600)

    def test_invoice_without_membership(self):
        service = make_service()
        booking = service.book("bob", "Glacier", "Interviews", 3)
        bob = service.users["bob"]
        self.assertEqual(invoice_total(booking, bob), 600)
        self.assertIn("600", "\n".join(invoice_lines(booking, bob)))


class ApiBehaviour(unittest.TestCase):
    def test_book_get_cancel(self):
        service = make_service()
        made = handle(service, {"user": "bob", "action": "book", "room": "Glacier",
                                "title": "Sync", "hours": "1"})
        self.assertEqual(made["status"], 201)
        got = handle(service, {"user": "bob", "action": "get", "id": made["id"]})
        self.assertEqual(got["title"], "Sync")
        gone = handle(service, {"user": "bob", "action": "cancel", "id": made["id"]})
        self.assertEqual((gone["status"], gone["state"]), (200, "cancelled"))

    def test_errors(self):
        service = make_service()
        self.assertEqual(handle(service, {"action": "get", "id": 1})["status"], 401)
        self.assertEqual(handle(service, {"user": "bob", "action": "get", "id": 99})["status"], 404)
        bad = {"user": "bob", "action": "book", "room": "G", "title": "T", "hours": "9"}
        self.assertEqual(handle(service, bad)["status"], 400)


class ReportBehaviour(unittest.TestCase):
    def test_report_lists_bookings_and_total(self):
        output = cli_output()
        for title in ("Planning", "Interviews", "Retro"):
            self.assertIn(title, output)
        self.assertIn("1140", output)
