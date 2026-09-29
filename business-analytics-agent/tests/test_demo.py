import unittest
from demo import summarize

class MetricTests(unittest.TestCase):
    def test_share_growth_and_missing_baseline(self):
        result = summarize([{"branch_id":"A","year":2024,"revenue_million":40},{"branch_id":"A","year":2025,"revenue_million":50},{"branch_id":"B","year":2025,"revenue_million":50}],2025)
        self.assertEqual(result["total_revenue_million"],100)
        self.assertEqual(result["branches"][0]["growth"],0.25)
        self.assertIsNone(result["branches"][1]["growth"])
        self.assertEqual(sum(r["share"] for r in result["branches"]),1)
    def test_zero_total(self):
        self.assertIsNone(summarize([{"branch_id":"A","year":2025,"revenue_million":0}],2025)["branches"][0]["share"])
    def test_duplicate_observation(self):
        row={"branch_id":"A","year":2025,"revenue_million":1}
        with self.assertRaises(ValueError): summarize([row,row],2025)
    def test_empty_year(self):
        self.assertEqual(summarize([],2025)["branches"],[])
