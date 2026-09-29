"""Failures remain visible across a batch and across a rule's dimensions."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


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


def runner():
    logger = types.SimpleNamespace(
        **{
            name: lambda *a, **k: None
            for name in ("info", "debug", "warning", "error", "exception")
        }
    )
    mocks = {
        "loguru": types.SimpleNamespace(logger=logger),
        "dao.risk_types_dao": types.SimpleNamespace(RiskTypesDAO=lambda: object()),
        "dao.monitor_config_dao": types.SimpleNamespace(MonitorConfigDAO=FakeConfigDAO),
        "models.monitor_rule_config": types.SimpleNamespace(MonitorRuleConfig=FakeConfig),
    }
    with patch.dict(sys.modules, mocks):
        spec = importlib.util.spec_from_file_location(
            "runner_under_test", Path(__file__).resolve().parents[1] / "monitors/monitor_runner.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.MonitorRunner()


class RunnerContractTests(unittest.TestCase):
    def test_failed_monitor_is_counted_as_failure(self):
        subject = runner()
        subject._load_monitor_class = lambda *_: types.SimpleNamespace(
            execute=lambda **_: {"status": "error", "saved_count": 0}
        )
        result = subject.run("2025-01-02")
        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["fail_count"], 1)
        self.assertEqual(result["results"][0]["status"], "error")

    def test_earlier_dimension_failure_is_not_hidden_by_last_success(self):
        subject = runner()
        subject.monitor_config_dao.get_trust_dimension_config = lambda **_: [
            FakeConfig(),
            FakeConfig(),
        ]
        results = iter([{"status": "error"}, {"status": "success"}])
        subject._execute_single_monitor = lambda **_: next(results)
        result = subject.run_by_monitor_id("DEMO-FAIL-0001", "20250102")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["fail_count"], 1)
        self.assertEqual(len(result["results"]), 2)

    def test_single_dimension_contract_is_preserved(self):
        subject = runner()
        subject._execute_single_monitor = lambda **_: {"status": "success", "saved_count": 2}
        self.assertEqual(
            subject.run_by_monitor_id("DEMO-FAIL-0001", "20250102"),
            {"status": "success", "saved_count": 2},
        )
