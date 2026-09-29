"""
监控规则配置数据模型

对应数据库表 risk_rule_config，使用 dataclass 定义。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MonitorRuleConfig:
    """
    监控规则配置

    对应表 risk_rule_config，定义每条监控规则的完整信息，
    包括监控类型、筛选逻辑、阈值、告警内容等。

    Attributes
    ----------
    id : int | None
        唯一标识（数据库自增主键）
    monitor_type : str
        对应 risk_types 中的枚举值（如 black_white）
    monitor_id : str
        监控ID，如 BW-RB-0001
    monitor_item : str
        监控事项（如"标的投资范围约束"）
    monitor_title : str
        监控标题（如"禁投标的监控"）
    dimension_code : str | None
        维度代码
    trust_dimension : str | None
        维度（如"资产分类"、"交易对手"）
    filter_logic : str | None
        筛选逻辑（用于策略判断）
    indicator : str | None
        需要监控的指标（如"交易对手"）
    operator : str | None
        运算符（如 not in, >, <, = 等）
    threshold : str | None
        阈值（如白名单、数值、列表等）
    alert_content : str | None
        触发预警时的内容
    normal_content : str | None
        正常状态下的提示内容
    scope : str | None
        范围（如"单只资产"、"组合级别"）
    default_value : str | None
        默认值
    limit : str | None
        最大值限制（如"<=0"、">=100"）
    is_enabled : int
        是否启用（0: 禁用, 1: 启用）
    created_at : datetime
        创建时间
    updated_at : datetime
        更新时间
    """

    monitor_type: str
    monitor_id: str
    monitor_item: str
    monitor_title: str
    dimension_code: Optional[str] = None
    trust_dimension: Optional[str] = None
    alert_level: Optional[str] = None
    filter_logic: Optional[str] = None
    indicator: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[str] = None
    alert_content: Optional[str] = None
    normal_content: Optional[str] = None
    scope: Optional[str] = None
    default_value: Optional[str] = None
    limit: Optional[str] = None
    is_enabled: int = 1
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_active(self) -> bool:
        """规则是否处于启用状态"""
        return self.is_enabled == 1

    def to_dict(self) -> dict:
        """转换为字典（便于序列化与数据库写入）"""
        return {
            "id": self.id,
            "monitor_type": self.monitor_type,
            "monitor_id": self.monitor_id,
            "monitor_item": self.monitor_item,
            "monitor_title": self.monitor_title,
            "dimension_code": self.dimension_code,
            "trust_dimension": self.trust_dimension,
            "filter_logic": self.filter_logic,
            "indicator": self.indicator,
            "operator": self.operator,
            "threshold": self.threshold,
            "alert_content": self.alert_content,
            "normal_content": self.normal_content,
            "scope": self.scope,
            "default_value": self.default_value,
            "limit": self.limit,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MonitorRuleConfig":
        """从字典构造实例（便于从数据库查询结果映射）"""
        return cls(
            id=data.get("id"),
            monitor_type=data.get("monitor_type", ""),
            monitor_id=data.get("monitor_id", ""),
            monitor_item=data.get("monitor_item", ""),
            monitor_title=data.get("monitor_title", ""),
            dimension_code=data.get("dimension_code"),
            trust_dimension=data.get("trust_dimension"),
            filter_logic=data.get("filter_logic"),
            indicator=data.get("indicator"),
            operator=data.get("operator"),
            threshold=data.get("threshold"),
            alert_content=data.get("alert_content"),
            normal_content=data.get("normal_content"),
            scope=data.get("scope"),
            default_value=data.get("default_value"),
            limit=data.get("limit"),
            is_enabled=data.get("is_enabled", 1),
            created_at=data.get("created_at", datetime.now()),
            updated_at=data.get("updated_at", datetime.now()),
        )
