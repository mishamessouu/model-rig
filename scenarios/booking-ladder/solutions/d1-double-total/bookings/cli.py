from .domain import User
from .repository import BookingRepository
from .service import BookingService


def demo_service():
    users = {"alice": User("alice", member=True), "bob": User("bob")}
    service = BookingService(BookingRepository(), users)
    service.book("alice", "Fjord", "Planning", 2)
    service.book("bob", "Glacier", "Interviews", 3)
    service.book("alice", "Fjord", "Retro", 1)
    return service


def report_total(service):
    return sum(
        service.quote(booking.owner, booking.hours)
        for booking in service.repository.all_active()
    )


def print_report(service):
    for booking in service.repository.all_active():
        price = service.quote(booking.owner, booking.hours)
        print(f"{booking.id:>3}  {booking.room:<8} {booking.title:<12} {price:>5} SEK")
    print(f"Total: {report_total(service)} SEK")


def main():
    service = demo_service()
    print("Active bookings")
    print_report(service)


if __name__ == "__main__":
    main()
