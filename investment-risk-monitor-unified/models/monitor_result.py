"""
监控结果与告警记录数据模型
使用 dataclass 定义核心数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional



@dataclass
class MonitorResult:
    """
    单条监控结果

    Attributes:
        id: 数据库自增主键（可选）
        portfolio_code: 监控组合CODE
        portfolio_name: 监控组合名称
        monitor_id: 监控指标唯一标识
        monitor_title: 监控指标名称
        dimension_code: 委托维度ID
        trust_dimension: 委托维度
        monitor_item: 监控事项
        check_date: 检查日期（YYYY-MM-DD）
        indicator_value: 指标当前值
        alert_level: 告警级别（0/1/2 表示正常/黄色/红色）
        alert_message: 告警描述信息
        created_at: 记录创建时间
    """
    monitor_id: str
    monitor_title: str
    check_date: str
    portfolio_code: str
    portfolio_name: str
    dimension_code: str
    trust_dimension: str
    monitor_category: Optional[str] = None
    monitor_item: Optional[str] = None
    indicator_value: Optional[str] = None
    alert_level: str = "0"
    alert_message: Optional[str] = None
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
