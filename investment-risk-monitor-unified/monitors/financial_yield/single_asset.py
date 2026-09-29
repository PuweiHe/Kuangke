"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.financial_yield_dao import FinancialYieldDAO

class SingleAssetMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
    'Generalized portfolio rule with synthetic defaults; configure limits for each use case.'
    WARNING_THRESHOLD = -0.15
    STOP_LOSS_THRESHOLD = -0.25

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-SA-0001'
        self.monitor_title = '单一资产监控'
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
        results = []
        warn_str = f'{self.WARNING_THRESHOLD * 100:.2f}%'
        stop_str = f'{self.STOP_LOSS_THRESHOLD * 100:.2f}%'
        for item in fetch_data:
            yield_rate = item.get('financial_yield_rate', 0)
            yield_str = f'{yield_rate * 100:.2f}%'
            if yield_rate <= self.STOP_LOSS_THRESHOLD:
                alert_message = f'止损：单一权益类资产综合收益率{yield_str}，已达止损线{stop_str}'
            elif yield_rate <= self.WARNING_THRESHOLD:
                alert_message = f'预警：单一权益类资产综合收益率{yield_str}，已达预警线{warn_str}'
            else:
                alert_message = f'正常：单一权益类资产综合收益率为{yield_str}'
            results.append({'portfolio_code': item.get('ztbh', ''), 'portfolio_name': item.get('jjztmc', ''), 'alert_message': alert_message, 'indicator_value': yield_rate, 'alert_level': 1 if yield_rate <= self.WARNING_THRESHOLD else 0})
        return results
