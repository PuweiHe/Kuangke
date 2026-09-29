"""
监控工具模块

提供监控相关的辅助函数，包括日期范围生成
结果格式化、监控摘要统计等
"""

from typing import Any, Dict, List

from utils.date_utils import get_today, format_date

from config.settings import MONITOR_START_DATE


class MonitorUtils:
    """监控辅助工具类"""

    @staticmethod
    def get_monitor_date_range(start_date: str = MONITOR_START_DATE, end_date: str = None) -> List[str]:
        """
        生成监控日期范围

        Parameters
        ----------
        start_date : str
            起始日期
        end_date : str, optional
            结束日期，默认为今天

        Returns
        -------
        list[str]
            日期列表
        """
        if end_date is None:
            end_date = get_today()
        return [start_date, end_date]

    @staticmethod
    def format_violation_summary(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        格式化违规结果摘要

        Parameters
        ----------
        violations : list[dict]

        Returns
        -------
        dict
            包含 total / by_risk_type / by_severity 等统计
        """
        total = len(violations)
        by_risk_type = {}
        by_severity = {"高": 0, "中": 0, "低": 0}

        for v in violations:
            rt = v.get("risk_type", "未知")
            by_risk_type[rt] = by_risk_type.get(rt, 0) + 1

            sev = v.get("severity", "中")
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total": total,
            "by_risk_type": by_risk_type,
            "by_severity": by_severity,
        }

    @staticmethod
    def build_violation_record(
        risk_type: str,
        security_code: str,
        security_name: str,
        violation_detail: str,
        raw_data: Dict[str, Any] = None,
        severity: str = "中",
    ) -> Dict[str, Any]:
        """
        构建标准格式的违规记录

        Parameters
        ----------
        risk_type : str
        security_code : str
        security_name : str
        violation_detail : str
        raw_data : dict, optional
        severity : str

        Returns
        -------
        dict
        """
        record = {
            "risk_type": risk_type,
            "security_code": security_code,
            "security_name": security_name,
            "violation_detail": violation_detail,
            "severity": severity,
        }
        if raw_data:
            record["raw_data"] = raw_data
        return record
