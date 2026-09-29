import unittest
from core.position_limit import evaluate

class PositionLimitTests(unittest.TestCase):
    def test_threshold_boundary(self):
        rows=[{"ztbh":"P001","jjztmc":"Example A","total_value":10},{"ztbh":"P002","jjztmc":"Example B","total_value":11}]
        self.assertEqual([r["alert_level"] for r in evaluate(rows,10)],[0,2])
    def test_missing_and_nonfinite_are_not_safe_positions(self):
        for value in [None,float("nan"),float("inf")]:
            with self.assertRaises(ValueError):evaluate([{"ztbh":"P001","jjztmc":"Example A","total_value":value}],10)
