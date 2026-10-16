from .domain import price_for


def invoice_total(booking, user):
    return price_for(user, booking.hours)


def invoice_lines(booking, user):
    return [
        f"Invoice for booking {booking.id}",
        f"Customer: {user.name}",
        f"Room: {booking.room}, {booking.hours} h",
        f"Total: {invoice_total(booking, user)} SEK",
    ]
