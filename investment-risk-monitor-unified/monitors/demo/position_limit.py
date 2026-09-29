from core.position_limit import evaluate
"""Synthetic example: monitor portfolio market value against a configured limit."""

from db.query_adapter import query_all
from monitors.monitor_base import MonitorBase


class PositionLimitMonitor(MonitorBase):
    def __init__(self):
        super().__init__()
        self.monitor_id = "DEMO-PL-0001"
        self.monitor_title = "Example portfolio value limit"

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        rows = query_all(
            "SELECT ztbh, jjztmc, SUM(jjsz) AS total_value "
            "FROM position_snapshot WHERE p_dt = %s AND wstwd = %s "
            "GROUP BY ztbh, jjztmc",
            (biz_date, dimension),
        )
        return {"rows": rows}

    def calculate(self, data: dict) -> list:
        return evaluate(data["rows"], self.threshold)
