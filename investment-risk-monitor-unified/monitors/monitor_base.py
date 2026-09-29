"""
监控基类

定义监控任务的基础接口与通用逻辑
供具体监控模块继承扩展
"""

from abc import ABC, abstractmethod
from core.asset_codes import normalize_asset_code
from typing import Any, Dict, List

from loguru import logger

from dao.risk_types_dao import RiskTypesDAO
from dao.monitor_config_dao import MonitorConfigDAO

from models.monitor_result import MonitorResult


class MonitorBase(ABC):
    """
    监控基类

    所有监控任务继承此基类，实现 execute 方法
    基类提供 DAO 访问、日期处理等通用能力
    """
    monitor_id: str = ""
    monitor_title: str = ""
    check_date: str = ""
    alert_level: int = 0
    threshold: str
    config: dict
    curr_dimension: str
    logger = logger

    def __init__(self):
        self.risk_types_dao = RiskTypesDAO()
        self.monitor_config_dao = MonitorConfigDAO()

    @abstractmethod
    def calculate(self, data: dict) -> List[Dict[str, Any]]:
        """计算监控指标并返回结果"""
        pass

    @abstractmethod
    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """
        获取指定日期的数据，由子类实现
        """
        pass

    def get_pre_date(self, biz_date: str) -> str:
        """获取前一天日期"""
        return self.risk_types_dao.get_pre_date(biz_date)

    def get_monitor_config(self, monitor_id: str) -> dict:
        """获取监控指标配置信息"""
        return self.monitor_config_dao.get_monitor_config_by_id(monitor_id)

    def execute(self, biz_date: str, monitor_id: str, dimension: str, config: dict) -> dict:
        """
        完整执行流程：取数 -> 计算 -> 保存 -> 返回保存状态

        Returns
        -------
        dict
            包含执行状态的字典
            - status: 'success' | 'error' | 'no_data'
            - saved_count: 保存的记录数（成功时）
            - error: 错误信息（失败时）
        """

        # 检查日期格式 都需要转成yyyyMMdd
        biz_date = biz_date.replace("-", "")
        self.check_date = biz_date

        #  设置监控指标ID，获取配置信息
        if not config:
            config = self.get_monitor_config(monitor_id)

        self.threshold = config.threshold
        self.config = config
        self.curr_dimension = dimension

        logger.info(f"开始执行监控指标: {config.monitor_title} ({self.monitor_id})")
        try:
            data = self.get_data(biz_date, monitor_id, dimension, scope=config.scope)
            if not data:
                logger.warning(f"监控指标执行警告: {self.monitor_title}, 无数据")
                return {"status": "no_data", "saved_count": 0}

            result = self.calculate(data)
            if not result:
                logger.info(f"监控指标执行警告: {self.monitor_title}, 无数据")
                return {"status": "no_data", "saved_count": 0}

            logger.info(f"监控指标执行结果: {self.monitor_title}, 数量: {len(result)}")

            # 构建 MonitorResult 对象列表
            monitor_results = [MonitorResult(
                monitor_category=getattr(config, "monitor_type", None),
                monitor_id=self.monitor_id,
                monitor_title=self.monitor_title,
                check_date=biz_date,
                portfolio_code=item.get("portfolio_code", ""),
                portfolio_name=item.get("portfolio_name", ""),
                dimension_code=getattr(config, 'dimension_code', '') or "",
                trust_dimension=getattr(config, 'trust_dimension', '') or dimension,
                monitor_item=getattr(config, 'monitor_item', ''),
                indicator_value=item.get("indicator_value"),
                alert_level=item.get("alert_level", 0),
                alert_message=item.get("alert_message"),
            ) for item in result]

            # 保存监控结果到数据库
            saved_count = 0
            if monitor_results:
                saved_count = self.monitor_config_dao.save_monitor_results(monitor_results)
                logger.info(f"监控结果已保存: {saved_count} 条记录")

            return {"status": "success", "saved_count": saved_count}
        except Exception as e:
            logger.error(f"监控指标执行异常: {self.monitor_title}, 错误: {e}")
            return {"status": "error", "error": str(e), "saved_count": 0}

    # 传入 265168.BOND.SH -> 265168
    def get_fmt_code(self, asset_code: str) -> str:
        return asset_code.split('.')[0]

    # 传入 265168.BOND.SH -> 265168.SH
    def get_fmt_suffix_code(self, asset_code: str) -> str:
        return normalize_asset_code(asset_code)
