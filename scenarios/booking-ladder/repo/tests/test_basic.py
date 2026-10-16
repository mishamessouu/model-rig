import unittest

from bookings.api import handle
from bookings.domain import User
from bookings.repository import BookingRepository
from bookings.service import BookingService


def make_service():
    users = {"alice": User("alice", member=True), "bob": User("bob")}
    return BookingService(BookingRepository(), users)


class BasicTest(unittest.TestCase):
    def test_book_and_get(self):
        service = make_service()
        booking = service.book("alice", "Fjord", "Planning", 2)
        self.assertEqual(service.get("alice", booking.id).title, "Planning")

    def test_quote_without_membership(self):
        self.assertEqual(make_service().quote("bob", 3), 600)

    def test_api_books(self):
        response = handle(
            make_service(),
            {"user": "bob", "action": "book", "room": "Glacier",
             "title": "Sync", "hours": "1"},
        )
        self.assertEqual(response["status"], 201)


if __name__ == "__main__":
    unittest.main()
