"""Synthetic branch metrics; this offline example does not invoke an LLM."""
import json
from pathlib import Path

def summarize(records, year):
    current = [r for r in records if r["year"] == year]
    keys = [(r["branch_id"], r["year"]) for r in records]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate branch-year observations")
    previous = {r["branch_id"]: r for r in records if r["year"] == year - 1}
    total = sum(r["revenue_million"] for r in current)
    output = []
    for r in sorted(current, key=lambda x: (-x["revenue_million"], x["branch_id"])):
        prior = previous.get(r["branch_id"], {}).get("revenue_million")
        output.append({**r, "share": r["revenue_million"] / total if total else None,
                       "growth": (r["revenue_million"] - prior) / prior if prior else None})
    return {"year": year, "total_revenue_million": total, "branches": output, "synthetic": True}

if __name__ == "__main__":
    records = json.loads((Path(__file__).parent / "examples/branches.json").read_text())
    print(json.dumps(summarize(records, 2025), indent=2))
