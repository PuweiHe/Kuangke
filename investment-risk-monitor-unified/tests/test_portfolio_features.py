"""Focused tests for date validation and the database lease protocol."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

date_spec = importlib.util.spec_from_file_location("date_utils_under_test", ROOT / "utils" / "date_utils.py")
date_module = importlib.util.module_from_spec(date_spec)
date_spec.loader.exec_module(date_module)
generate_date_range = date_module.generate_date_range
normalize_business_date = date_module.normalize_business_date


class FakeLockTable:
    def __init__(self):
        self.rows = {}

    def execute(self, sql, params):
        if sql.startswith("INSERT"):
            self.rows.setdefault(params[0], {"owner": None, "expiry": 0})
            return 1
        if "owner_token = NULL" in sql:
            task_name, token = params
            row = self.rows[task_name]
            if row["owner"] != token:
                return 0
            row.update(owner=None, expiry=0)
            return 1
        if "AND owner_token = %s AND expires_at_epoch > %s" in sql:
            expiry, task_name, token, now = params
            row = self.rows[task_name]
            if row["owner"] != token or row["expiry"] <= now:
                return 0
            row["expiry"] = expiry
            return 1
        token, instance, expiry, task_name, now = params
        row = self.rows[task_name]
        if row["owner"] is not None and row["expiry"] > now:
            return 0
        row.update(owner=token, expiry=expiry)
        return 1


def load_lock_module():
    logger = types.SimpleNamespace(**{name: lambda *a, **k: None for name in ("info", "debug", "warning", "error", "exception")})
    sys.modules["loguru"] = types.SimpleNamespace(logger=logger)
    sys.modules["db.query_adapter"] = types.SimpleNamespace(execute_update=lambda *a: None)
    spec = importlib.util.spec_from_file_location("lock_under_test", ROOT / "utils" / "distributed_lock.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DateTests(unittest.TestCase):
    def test_normalizes_and_validates_dates(self):
        self.assertEqual(normalize_business_date("2025-02-03"), "20250203")
        self.assertEqual(normalize_business_date("20250203"), "20250203")
        with self.assertRaises(ValueError):
            normalize_business_date("2025-02-30")

    def test_historical_range_is_inclusive(self):
        self.assertEqual(generate_date_range("20250228", "20250302"), ["20250228", "20250301", "20250302"])
        with self.assertRaises(ValueError):
            generate_date_range("20250302", "20250228")


class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.module = load_lock_module()
        self.table = FakeLockTable()
        self.module.execute_update = self.table.execute

    def test_only_one_owner_and_stale_release_cannot_unlock_successor(self):
        first = self.module.DistributedJobLock("daily", lease_seconds=9)
        second = self.module.DistributedJobLock("daily", lease_seconds=9)
        self.assertTrue(first.acquire())
        self.assertFalse(second.acquire())
        self.table.rows["daily"]["expiry"] = 0
        self.assertTrue(second.acquire())
        self.assertFalse(first.release())
        self.assertEqual(self.table.rows["daily"]["owner"], second.owner_token)
        self.assertTrue(second.renew())
        self.assertTrue(second.release())

    def test_exclusive_callback_is_skipped_when_owned(self):
        owner = self.module.DistributedJobLock("daily", lease_seconds=9)
        self.assertTrue(owner.acquire())
        calls = []
        executed, result = self.module.run_exclusive_job("daily", lambda: calls.append(1))
        self.assertFalse(executed)
        self.assertIsNone(result)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
