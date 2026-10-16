import io
from contextlib import redirect_stdout

from bookings.domain import User
from bookings.repository import BookingRepository
from bookings.service import BookingService


def make_service():
    users = {"alice": User("alice", member=True), "bob": User("bob")}
    return BookingService(BookingRepository(), users)


def cli_output():
    from bookings import cli

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        cli.main()
    return buffer.getvalue()
