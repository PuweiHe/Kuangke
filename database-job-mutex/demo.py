"""SQLite demonstration of owner-checked leases; MySQL integration is separate."""
import sqlite3
import uuid

class Lease:
    def __init__(self, connection, name, clock, seconds=30):
        if seconds <= 0:
            raise ValueError("Lease duration must be positive")
        self.db, self.name, self.clock, self.seconds = connection, name, clock, seconds
        self.token = uuid.uuid4().hex
        self.db.execute("CREATE TABLE IF NOT EXISTS locks (name TEXT PRIMARY KEY, owner TEXT, expires REAL NOT NULL)")
        self.db.execute("INSERT OR IGNORE INTO locks VALUES (?, NULL, 0)", (name,))
        self.db.commit()
    def acquire(self):
        now = self.clock()
        with self.db:
            return self.db.execute("UPDATE locks SET owner=?, expires=? WHERE name=? AND (owner IS NULL OR expires<=?)",(self.token, now+self.seconds, self.name, now)).rowcount == 1
    def release(self):
        with self.db:
            return self.db.execute("UPDATE locks SET owner=NULL, expires=0 WHERE name=? AND owner=?", (self.name,self.token)).rowcount == 1

if __name__ == "__main__":
    with sqlite3.connect(":memory:") as db:
        first, second = Lease(db,"demo",lambda:100), Lease(db,"demo",lambda:100)
        print({"first_acquired":first.acquire(), "second_acquired":second.acquire()})
