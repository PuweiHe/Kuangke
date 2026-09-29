"""Deterministic branch metrics shared by the CLI and HTTP application."""

import math
import re
from typing import NotRequired, TypedDict


class Observation(TypedDict):
    branch_id: str
    year: int
    revenue_million: float


class BranchMetric(Observation):
    share: float | None
    growth: float | None


class Report(TypedDict):
    year: int
    total_revenue_million: float
    branches: list[BranchMetric]
    synthetic: bool
    selected_branch: NotRequired[BranchMetric | None]


def validate_records(records: list[Observation]) -> None:
    seen = set()
    for row in records:
        if not isinstance(row.get("branch_id"), str) or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,64}", row["branch_id"]
        ):
            raise ValueError("Invalid branch identifier")
        if type(row.get("year")) is not int or not 1900 <= row["year"] <= 9999:
            raise ValueError("Invalid reporting year")
        value = row.get("revenue_million")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError("Revenue must be finite and nonnegative")
        key = row["branch_id"], row["year"]
        if key in seen:
            raise ValueError("Duplicate branch-year observations")
        seen.add(key)


def summarize(records: list[Observation], year: int) -> Report:
    validate_records(records)
    current = [r for r in records if r["year"] == year]
    previous = {r["branch_id"]: r for r in records if r["year"] == year - 1}
    total = float(sum(r["revenue_million"] for r in current))
    if not math.isfinite(total):
        raise ValueError("Revenue total is not finite")
    output: list[BranchMetric] = []
    for row in sorted(current, key=lambda r: (-r["revenue_million"], r["branch_id"])):
        prior = previous.get(row["branch_id"])
        baseline = prior["revenue_million"] if prior else None
        growth = (row["revenue_million"] - baseline) / baseline if baseline else None
        if growth is not None and not math.isfinite(growth):
            raise ValueError("Growth is not finite")
        output.append(
            BranchMetric(
                **row, share=row["revenue_million"] / total if total else None, growth=growth
            )
        )
    return {"year": year, "total_revenue_million": total, "branches": output, "synthetic": True}
