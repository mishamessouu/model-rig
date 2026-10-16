from .domain import HOURLY_RATE


def invoice_total(booking, user):
    return booking.hours * HOURLY_RATE


def invoice_lines(booking, user):
    return [
        f"Invoice for booking {booking.id}",
        f"Customer: {user.name}",
        f"Room: {booking.room}, {booking.hours} h",
        f"Total: {invoice_total(booking, user)} SEK",
    ]
