from dataclasses import dataclass

# Price per started hour, in whole kronor.
HOURLY_RATE = 200


@dataclass
class User:
    name: str
    member: bool = False


@dataclass
class Booking:
    id: int
    owner: str
    room: str
    title: str
    hours: int
    status: str = "active"


def price_for(user, hours):
    """The one pricing rule: members pay 90 percent."""
    price = hours * HOURLY_RATE
    if user.member:
        price = price * 90 // 100
    return price
