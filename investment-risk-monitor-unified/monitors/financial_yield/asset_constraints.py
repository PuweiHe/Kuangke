"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from loguru import logger
from monitors.monitor_base import MonitorBase
from dao.financial_yield_dao import FinancialYieldDAO
from utils.calc_utils import CalcUtils

class EquityComprehensiveYieldMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
    WARNING_THRESHOLD = -0.15
    STOP_LOSS_THRESHOLD = -0.25

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-AC-0001'
        self.monitor_title = '权益类资产综合收益率监控'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['股票', '股票型基金', '股票型保险资管产品', '混合型保险资管产品', '混合型基金', '长股投股票', '未上市企业股权', '股权基金']
        return {'data': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        if not fetch_data:
            return []
        warn_str = f'{self.WARNING_THRESHOLD * 100:.2f}%'
        stop_str = f'{self.STOP_LOSS_THRESHOLD * 100:.2f}%'
        result = []
        for item in fetch_data:
            yield_rate = item.get('financial_yield_rate', 0)
            yield_str = f'{yield_rate * 100:.2f}%'
            if yield_rate < self.STOP_LOSS_THRESHOLD:
                alert_message = f'止损：权益类资产综合收益率{yield_str}，已达止损线{stop_str}'
            elif yield_rate < self.WARNING_THRESHOLD:
                alert_message = f'预警：权益类资产综合收益率{yield_str}，已达预警线{warn_str}'
            else:
                alert_message = f'正常：权益类资产综合收益率{yield_str}，已达正常线0.00%'
            portfolio_code = item.get('ztbh', '')
            portfolio_name = item.get('jjztmc', '')
            result.append({'portfolio_code': portfolio_code, 'portfolio_name': portfolio_name, 'alert_message': alert_message, 'indicator_value': yield_rate})
        return result

class FixedIncomeComprehensiveYieldMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-AC-0002'
        self.monitor_title = '固收综合收益率监控'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['股票', '股票型基金', '股票型保险资管产品', '混合型保险资管产品', '混合型基金', '长股投股票']
        return {'data': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        if not fetch_data:
            return []
        threshold_float = CalcUtils.parse_threshold(self.threshold) if self.threshold else 0.02
        result = []
        for item in fetch_data:
            yield_rate = item.get('financial_yield_rate', 0)
            annualized = CalcUtils.annualize(yield_rate)
            annualized_str = f'{annualized * 100:.2f}%'
            threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
            if annualized < threshold_float:
                alert_message = f'预警：固收类专项委托户年化综合收益率{annualized_str}，未达目标{threshold_str}%'
            else:
                alert_message = f'正常：固收类专项委托户年化综合收益率{annualized_str}，达到目标{threshold_str}%'
            result.append({'portfolio_code': item.get('ztbh', ''), 'portfolio_name': item.get('jjztmc', ''), 'alert_message': alert_message, 'indicator_value': annualized})
        return result
