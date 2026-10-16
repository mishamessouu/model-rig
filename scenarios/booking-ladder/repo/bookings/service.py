from .domain import HOURLY_RATE


class NotFound(Exception):
    pass


class BookingService:
    def __init__(self, repository, users):
        self.repository = repository
        self.users = users

    def book(self, user, room, title, hours):
        if user not in self.users:
            raise NotFound(user)
        if hours < 1 or hours > 8:
            raise ValueError("hours must be between 1 and 8")
        return self.repository.add(user, room, title, hours)

    def get(self, user, booking_id):
        booking = self.repository.get(booking_id)
        if booking is None or booking.owner != user:
            raise NotFound(booking_id)
        return booking

    def cancel(self, user, booking_id):
        booking = self.repository.get(booking_id)
        if booking is None:
            raise NotFound(booking_id)
        self.repository.set_status(booking_id, "cancelled")
        return self.repository.get(booking_id)

    def mine(self, user):
        return self.repository.for_owner(user)

    def search(self, user, term):
        return self.repository.search(user, term)

    def quote(self, user, hours):
        price = hours * HOURLY_RATE
        if self.users[user].member:
            price = price * 90 // 100
        return price
