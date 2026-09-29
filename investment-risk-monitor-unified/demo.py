"""Offline synthetic demo of the same calculation used by the database monitor."""
import json
from core.position_limit import evaluate

if __name__ == "__main__":
    print(json.dumps(evaluate([{"ztbh":"P001","jjztmc":"Example Portfolio A","total_value":11}, {"ztbh":"P002","jjztmc":"Example Portfolio B","total_value":4}], 10), indent=2))
