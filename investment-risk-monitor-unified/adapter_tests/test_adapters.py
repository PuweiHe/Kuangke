"""Production modules with mocked IO; requires application dependencies."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dao.investment_ratio_dao import InvestmentRatioDAO
from monitors.investment_ratio.investment_ratio_constraint import FinancialProductHoldingScaleRatioMonitor
from monitors.black_white.Infrastructure import FVOCIStockPoolMonitor
from ingestion.config_import import prepare, ImportValidationError


class AdapterTests(unittest.TestCase):
    def test_bound_values_and_exists_avoid_mapping_fanout(self):
        with patch('dao.investment_ratio_dao.query_all', return_value=[]) as query:
            InvestmentRatioDAO().get_ratio_positions('20250102', "demo' OR 1=1", ['example'], ['P001'], tree_category=True)
            sql, params = query.call_args.args
            self.assertIn('EXISTS', sql)
            self.assertNotIn("demo' OR 1=1", sql)
            self.assertEqual(params, ('20250102', "demo' OR 1=1", 'example', 'P001'))

    def test_absolute_denominator_and_caller_contract(self):
        with patch('dao.investment_ratio_dao.query_all', return_value=[]) as query:
            InvestmentRatioDAO().get_ratio_positions('20250102', 'DEMO', ['other'], absolute=True, exclude=True)
            self.assertIn('ABS(a.qjsz) AS dirty_price_market_value', query.call_args.args[0])
        monitor = FinancialProductHoldingScaleRatioMonitor()
        monitor.threshold = '0'
        with patch.object(monitor.dao, 'get_ratio_positions', return_value=[]) as positions, patch.object(monitor.dao, 'get_repo_balances', return_value=[]):
            data = monitor.get_data('20250102', monitor.monitor_id, 'DEMO', scope='["P001"]')
            self.assertEqual(positions.call_args.kwargs['absolute'], True)
            self.assertEqual(monitor.calculate(data)[0]['evaluation_status'], 'missing_data')

    def test_whitelist_monitor_uses_codes_not_dictionaries(self):
        monitor = FVOCIStockPoolMonitor()
        monitor.curr_dimension = 'DEMO'
        result = monitor.calculate({'asset_datas': [{'zcdm': '00001.STK.SHSC'}],
                                    'fvoci_stock_pool_whitelist': [{'asset_code': '00001.HK'}]})
        self.assertEqual(result[0]['alert_level'], 0)
        result = monitor.calculate({'asset_datas': [{'zcdm': '00001.HK'}], 'fvoci_stock_pool_whitelist': []})
        self.assertEqual(result[0]['alert_level'], 2)

    def test_xlsx_reading_and_formula_rejection(self):
        # Temporary test fixtures only; no original workbook is read or copied.
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'example.xlsx'
            book = Workbook()
            book.active.append(['category', 'category_2nd', 'asset_code', 'year', 'is_valid'])
            book.active.append(['allow', 'equity', '00001.HK', 2025, 1])
            book.save(path)
            self.assertEqual(prepare('assets', path)[0]['asset_code'], '00001.HK')
            book.active['C2'] = '=1+1'
            book.save(path)
            with self.assertRaises(ImportValidationError): prepare('assets', path)

    def test_special_account_scope_has_no_customer_defaults(self):
        from monitors.financial_yield.investment_objective import FixedIncomeSpecialAccountYieldMonitor
        monitor = FixedIncomeSpecialAccountYieldMonitor()
        with self.assertRaises(ValueError): monitor.get_data('20250102', monitor.monitor_id, 'DEMO')
        with patch.object(monitor.dao, 'get_account_yields', return_value=[]) as query:
            monitor.get_data('20250102', monitor.monitor_id, 'DEMO', scope='["P001"]')
            self.assertEqual(query.call_args.args[2], ['P001'])
