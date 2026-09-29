"""Regression cases for incomplete accounts, applicability and code matching."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.holding_ratio import account_scope, evaluate_ratios
from core.asset_codes import normalize_asset_code, whitelist_violations


def row(code, value):
    return {'ztbh': code, 'jjztmc': 'Example ' + code, 'dirty_price_market_value': value}


class RatioTests(unittest.TestCase):
    def test_threshold_equality_and_zero_are_valid(self):
        self.assertEqual(evaluate_ratios([row('A', 5)], [row('A', 10)], .5)[0]['evaluation_status'], 'ok')
        self.assertEqual(evaluate_ratios([row('A', 1)], [row('A', 10)], 0)[0]['evaluation_status'], 'breach')

    def test_missing_accounts_survive_join(self):
        result = evaluate_ratios([row('A', 1)], [row('B', 10)], .5, ['A', 'B', 'C'])
        self.assertEqual([r['portfolio_code'] for r in result], ['A', 'B', 'C'])
        self.assertTrue(all(r['alert_level'] == 2 and r['indicator_value'] is None for r in result))

    def test_zero_negative_and_nonfinite_are_not_safe(self):
        for value in (0, -1, None, float('nan'), float('inf')):
            with self.subTest(value=value):
                self.assertEqual(evaluate_ratios([row('A', 1)], [row('A', value)], 1)[0]['alert_level'], 2)

    def test_repo_missing_differs_from_known_zero(self):
        for repo, expected in (([], 'missing_data'), ([row('A', 0)], 'not_applicable'), ([row('A', -1)], 'breach')):
            result = evaluate_ratios([row('A', 2)], [row('A', 1)], 1, ['A'], repo)
            self.assertEqual(result[0]['evaluation_status'], expected)

    def test_aggregation_and_scope(self):
        result = evaluate_ratios([row('A', 2), row('A', 3), row('B', 9)], [row('A', 10)], .4, ['A'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['indicator_value'], .5)
        for bad in ('A', '[]', '["A","A"]', '[1]'):
            with self.assertRaises(ValueError): account_scope(bad)

    def test_bad_threshold_and_missing_identifier(self):
        for bad in (-1, float('inf'), float('nan')):
            with self.assertRaises(ValueError): evaluate_ratios([], [], bad)
        with self.assertRaises(ValueError): evaluate_ratios([{'dirty_price_market_value': 1}], [], 1)


class AssetCodeTests(unittest.TestCase):
    def test_suffix_and_leading_zero_normalization(self):
        self.assertEqual(normalize_asset_code('00001.STK.SHSC'), '00001.HK')
        self.assertEqual(normalize_asset_code('00002.STK.SZSC'), '00002.HK')
        self.assertEqual(normalize_asset_code('123.BOND.YHJ'), '123.IB')
        self.assertEqual(normalize_asset_code('123.BOND.SH'), '123.SH')

    def test_dictionary_whitelist_matches_and_unknown_reference_fails(self):
        positions = [{'zcdm': '00001.STK.SHSC'}, {'zcdm': '00002.HK'}]
        self.assertEqual(whitelist_violations(positions, [{'asset_code': '00001.HK'}]), positions[1:])
        with self.assertRaises(ValueError): whitelist_violations(positions, [])
        with self.assertRaises(ValueError): normalize_asset_code('.')


class AccountYieldTests(unittest.TestCase):
    def test_yield_scope_missing_zero_capital_and_minimum(self):
        from core.account_yield import evaluate_account_yields
        rows = [dict(ztbh='A', market_value=10, earnings=1, capital=100),
                dict(ztbh='B', market_value=10, earnings=0, capital=0),
                dict(ztbh='C', market_value=1, earnings=0, capital=1)]
        result = evaluate_account_yields(rows, ['A', 'B', 'C', 'D'], .01, 5, '20251231')
        self.assertEqual([r['evaluation_status'] for r in result], ['ok', 'invalid_data', 'not_applicable', 'missing_data'])
        self.assertAlmostEqual(result[0]['indicator_value'], .01)

    def test_missing_yield_is_not_zero_and_duplicate_rejected(self):
        from core.account_yield import evaluate_account_yields
        row = dict(ztbh='A', market_value=10, earnings=None, capital=100)
        self.assertEqual(evaluate_account_yields([row], ['A'], 0, 0, '20251231')[0]['alert_level'], 2)
        with self.assertRaises(ValueError): evaluate_account_yields([row, row], ['A'], 0, 0, '20251231')
