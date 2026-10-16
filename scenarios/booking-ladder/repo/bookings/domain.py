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
