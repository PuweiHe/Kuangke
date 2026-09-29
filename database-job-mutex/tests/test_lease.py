import sqlite3
import tempfile
import unittest
from pathlib import Path
from demo import Lease

class LeaseTests(unittest.TestCase):
    def test_exclusion_and_stale_release_across_connections(self):
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d)/"lease.db")
            a,b=sqlite3.connect(path),sqlite3.connect(path)
            try:
                now=[100]
                one=Lease(a,"job",lambda:now[0],seconds=10)
                two=Lease(b,"job",lambda:now[0],seconds=10)
                self.assertTrue(one.acquire())
                self.assertFalse(two.acquire())
                now[0]=111
                self.assertTrue(two.acquire())
                self.assertFalse(one.release())
                self.assertTrue(two.release())
                self.assertTrue(one.acquire())
            finally:
                a.close();b.close()
    def test_reject_invalid_lease(self):
        with sqlite3.connect(":memory:") as db:
            with self.assertRaises(ValueError):Lease(db,"job",lambda:100,seconds=0)
