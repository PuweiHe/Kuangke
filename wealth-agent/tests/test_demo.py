import json
from pathlib import Path
import unittest
from demo import execute

class ToolTests(unittest.TestCase):
    def test_synthetic_cases(self):
        cases = json.loads((Path(__file__).resolve().parents[1] / "evals/synthetic_cases.json").read_text())
        for case in cases:
            with self.subTest(case=case["id"]):
                result = execute(case["request"])
                self.assertEqual(result["status"], case["expected_status"])
                self.assertEqual([r["id"] for r in result["data"]], case["expected_ids"])
    def test_missing_history_is_not_zero(self):
        self.assertIsNone(execute({"action": "compare", "ids": ["FUND004"]})["data"][0]["return_1y"])
    def test_invalid_request(self):
        for req in [{"action":"resolve","query":""},{"action":"screen","limit":0},{"action":"compare","ids":[]}]:
            with self.assertRaises(ValueError): execute(req)
