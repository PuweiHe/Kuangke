"""Pure portfolio limit calculation using explicit input data and threshold."""
import math

def evaluate(rows, limit):
    limit = float(limit)
    if not math.isfinite(limit) or limit < 0:
        raise ValueError("Limit must be finite and nonnegative")
    results = []
    for row in rows:
        raw = row["total_value"]
        if raw is None:
            raise ValueError("Market value is missing")
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError("Market value must be finite")
        breach = value > limit
        results.append({"portfolio_code": row["ztbh"], "portfolio_name": row["jjztmc"],
                        "indicator_value": value, "alert_level": 2 if breach else 0,
                        "alert_message": "Example limit exceeded" if breach else "Within example limit"})
    return results
