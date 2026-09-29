"""Verify monitor failures remain failures at the runner boundary."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class FakeConfig:
    monitor_id = "DEMO-FAIL-0001"
    monitor_title = "Failure example"
    monitor_type = "example"
    monitor_item = "example"
    trust_dimension = "DEMO"
    dimension_code = "DEMO"


class FakeConfigDAO:
    def get_snapshot_count(self, biz_date):
        return 1

    def get_trust_dimension_config(self, **kwargs):
        return [FakeConfig()]


class FakeMonitor:
    def execute(self, **kwargs):
        return {"status": "error", "error": "synthetic failure", "saved_count": 0}


class RunnerContractTests(unittest.TestCase):
    def test_failed_monitor_is_counted_as_failure(self):
        logger = types.SimpleNamespace(**{name: lambda *a, **k: None for name in ("info", "debug", "warning", "error", "exception")})
        sys.modules["loguru"] = types.SimpleNamespace(logger=logger)
        sys.modules["dao.risk_types_dao"] = types.SimpleNamespace(RiskTypesDAO=lambda: object())
        sys.modules["dao.monitor_config_dao"] = types.SimpleNamespace(MonitorConfigDAO=FakeConfigDAO)
        sys.modules["models.monitor_rule_config"] = types.SimpleNamespace(MonitorRuleConfig=FakeConfig)
        spec = importlib.util.spec_from_file_location("runner_under_test", ROOT / "monitors" / "monitor_runner.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        runner = module.MonitorRunner()
        runner._load_monitor_class = lambda *_: FakeMonitor()
        result = runner.run("2025-01-02")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["fail_count"], 1)
        self.assertEqual(result["results"][0]["status"], "error")


if __name__ == "__main__":
    unittest.main()
