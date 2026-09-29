"""Use a real SQLite transaction to check the DB-API adapter's batch contract."""

import importlib.util
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys
import types
import unittest
from unittest.mock import patch


class QueryAdapterTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        self.addCleanup(self.db.close)
        outer = self

        class Cursor:
            def __enter__(self):
                self.cursor = outer.db.cursor()
                return self

            def __exit__(self, *args):
                self.cursor.close()

            def execute(self, sql, params=None):
                self.cursor.execute(sql.replace("%s", "?"), params or ())

            def executemany(self, sql, values):
                self.cursor.executemany(sql.replace("%s", "?"), values)

            def __getattr__(self, name):
                return getattr(self.cursor, name)

        @contextmanager
        def connection():
            with self.db:
                yield types.SimpleNamespace(cursor=Cursor)

        pool = types.SimpleNamespace(connection=connection)
        with patch.dict(sys.modules, {"db.factory": types.SimpleNamespace(get_pool=lambda: pool)}):
            spec = importlib.util.spec_from_file_location(
                "adapter_under_test", Path(__file__).resolve().parents[1] / "db/query_adapter.py"
            )
            self.adapter = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.adapter)

    def test_batch_preserves_column_order(self):
        self.assertEqual(
            self.adapter.insert_many(
                "sample", [{"id": 1, "value": "first"}, {"value": "second", "id": 2}]
            ),
            2,
        )
        self.assertEqual(
            self.adapter.query_one("SELECT * FROM sample WHERE id = %s", (2,)),
            {"id": 2, "value": "second"},
        )

    def test_failed_batch_rolls_back_every_row(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.adapter.insert_many(
                "sample", [{"id": 1, "value": "first"}, {"id": 1, "value": "duplicate"}]
            )
        self.assertEqual(self.adapter.query_all("SELECT * FROM sample"), [])

    def test_rejects_bad_identifiers_and_mismatched_columns(self):
        for table, rows in [
            ("sample; DROP TABLE sample", [{"id": 1}]),
            ("sample", [{"id": 1}, {"value": "different"}]),
        ]:
            with self.assertRaises(ValueError):
                self.adapter.insert_many(table, rows)
