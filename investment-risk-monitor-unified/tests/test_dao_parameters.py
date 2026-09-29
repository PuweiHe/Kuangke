"""Exercise DAO filter boundaries without a database or private reference data."""

import importlib.util
import inspect
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class ParameterTests(unittest.TestCase):
    def test_filter_values_never_become_sql(self):
        attack = "quoted' OR 'x'='x"
        dao_dir = Path(__file__).resolve().parents[1] / "dao"
        modules = [
            "blac_white",
            "duration",
            "financial_yield",
            "investment_amount",
            "investment_ra_mo",
            "investment_ratio",
            "rating",
        ]
        calls = []
        adapter = types.ModuleType("db.query_adapter")

        def query(sql, params=None):
            calls.append((sql, params or ()))
            self.assertNotIn(attack, sql)
            self.assertEqual(sql.count("%s"), len(params or ()), sql)
            return []

        adapter.query_all = query
        adapter.query_one = query
        with patch.dict(sys.modules, {"db.query_adapter": adapter}):
            for name in modules:
                spec = importlib.util.spec_from_file_location(name, dao_dir / f"{name}_dao.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                cls = next(c for _, c in inspect.getmembers(module, inspect.isclass))
                instance = cls()
                for method_name, method in inspect.getmembers(instance, inspect.ismethod):
                    if not method_name.startswith("get_"):
                        continue
                    kwargs = {}
                    for key, parameter in inspect.signature(method).parameters.items():
                        if parameter.default is not inspect.Parameter.empty:
                            continue
                        if key in {"date", "biz_date"}:
                            kwargs[key] = "20250102"
                        elif key == "year":
                            kwargs[key] = 2025
                        elif parameter.annotation is list or key in {"categories", "accounts"}:
                            kwargs[key] = [attack, "ordinary"]
                        else:
                            kwargs[key] = attack
                    with self.subTest(dao=name, method=method_name):
                        method(**kwargs)
        self.assertGreater(len(calls), 50)

    def test_empty_category_filter_returns_no_rows(self):
        adapter = types.ModuleType("db.query_adapter")
        adapter.query_all = lambda *_: self.fail("Empty IN filters must not execute")
        adapter.query_one = adapter.query_all
        with patch.dict(sys.modules, {"db.query_adapter": adapter}):
            path = Path(__file__).resolve().parents[1] / "dao/investment_ratio_dao.py"
            spec = importlib.util.spec_from_file_location("empty_ratio", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(
                module.InvestmentRatioDAO().get_investment_category_data("20250102", "DEMO", []), []
            )
