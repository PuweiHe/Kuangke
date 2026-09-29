"""Offline deterministic data-tool demonstration; no language model is invoked."""
import json
from pathlib import Path

DATA = Path(__file__).parent / "examples" / "funds.json"

def execute(request, records=None):
    records = json.loads(DATA.read_text()) if records is None else records
    action = request.get("action")
    if action == "resolve":
        query = request.get("query", "").strip().casefold()
        if not query:
            raise ValueError("query must not be empty")
        matches = [r for r in records if query == r["id"].casefold() or query in r["name"].casefold()]
        return {"status": "not_found" if not matches else "resolved" if len(matches) == 1 else "ambiguous", "data": matches}
    if action == "screen":
        limit = request.get("limit", 10)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        matches = [r for r in records if request.get("category", r["category"]) == r["category"] and r["assets_million"] >= request.get("min_assets_million", 0)]
        matches.sort(key=lambda r: (r["return_1y"] is None, -(r["return_1y"] or 0), r["id"]))
        return {"status": "ok", "data": matches[:limit], "total": len(matches)}
    if action == "compare":
        ids = request.get("ids", [])
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids):
            raise ValueError("ids must be a nonempty list of strings")
        lookup = {r["id"]: r for r in records}
        missing = [i for i in ids if i not in lookup]
        return {"status": "partial" if missing else "ok", "data": [lookup[i] for i in dict.fromkeys(ids) if i in lookup], "missing": missing}
    return {"status": "unsupported", "data": [], "reason": "No tool supports this action; returns are never guaranteed."}

if __name__ == "__main__":
    print(json.dumps(execute({"action": "screen", "category": "equity", "limit": 3}), indent=2))
