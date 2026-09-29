"""Replay synthetic extraction outputs through the live entity schema.

This measures contract behavior, not an LLM's extraction or routing accuracy.
"""

import json
from pathlib import Path
import sys
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.entity_schema import EntityNames


def evaluate(cases):
    results = []
    for case in cases:
        try:
            names = EntityNames.model_validate(case["output"]).entities
            passed = case["accepted"] and names == case["expected"]
        except ValidationError:
            passed = not case["accepted"]
        results.append({"id": case["id"], "passed": passed})
    return {
        "mode": "synthetic_output_contracts",
        "passed": sum(r["passed"] for r in results),
        "total": len(results),
        "results": results,
    }


if __name__ == "__main__":
    result = evaluate(json.loads(Path(__file__).with_name("extraction_contracts.json").read_text()))
    print(json.dumps(result, indent=2))
    raise SystemExit(result["passed"] != result["total"])
