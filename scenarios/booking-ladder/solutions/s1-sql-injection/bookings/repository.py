import sqlite3

from .domain import Booking

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY,
    owner TEXT NOT NULL,
    room TEXT NOT NULL,
    title TEXT NOT NULL,
    hours INTEGER NOT NULL,
    status TEXT NOT NULL
)
"""

COLUMNS = "id, owner, room, title, hours, status"


class BookingRepository:
    def __init__(self, path=":memory:"):
        self.db = sqlite3.connect(path)
        self.db.execute(SCHEMA)

    def add(self, owner, room, title, hours):
        cursor = self.db.execute(
            "INSERT INTO bookings (owner, room, title, hours, status) "
            "VALUES (?, ?, ?, ?, 'active')",
            (owner, room, title, hours),
        )
        self.db.commit()
        return self.get(cursor.lastrowid)

    def get(self, booking_id):
        row = self.db.execute(
            f"SELECT {COLUMNS} FROM bookings WHERE id = ?", (booking_id,)
        ).fetchone()
        return Booking(*row) if row else None

    def set_status(self, booking_id, status):
        self.db.execute(
            "UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id)
        )
        self.db.commit()

    def for_owner(self, owner):
        rows = self.db.execute(
            f"SELECT {COLUMNS} FROM bookings WHERE owner = ? ORDER BY id",
            (owner,),
        ).fetchall()
        return [Booking(*row) for row in rows]

    def search(self, owner, term):
        rows = self.db.execute(
            f"SELECT {COLUMNS} FROM bookings "
            "WHERE owner = ? AND title LIKE ? ORDER BY id",
            (owner, f"%{term}%"),
        ).fetchall()
        return [Booking(*row) for row in rows]

    def all_active(self):
        rows = self.db.execute(
            f"SELECT {COLUMNS} FROM bookings WHERE status = 'active' ORDER BY id"
        ).fetchall()
        return [Booking(*row) for row in rows]
