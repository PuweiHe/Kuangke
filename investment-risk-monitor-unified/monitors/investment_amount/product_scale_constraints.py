import json
"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.investment_amount_dao import InvestmentAmountDAO
from utils.calc_utils import CalcUtils
import pandas as pd

class FixedIncomeScaleMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-PS-0001'
        self.monitor_title = '固收类规模监控'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['政府债', '金融债', '企业债', '资产支持计划', '资产支持证券', '持有型不动产ABS', '债券型基金', '固收类保险资管产品', '货币类产品']
        data = self.dao.get_investment_category_data(biz_date, dimension, category)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = data.get('data', [])
        if not data:
            return []
        df = pd.DataFrame(data)
        total_value = df['dirty_price_market_value'].sum()
        YEAR_THRESHOLD = 60
        YEAR_END_THRESHOLD = 50
        is_year_end = self.check_date.replace('-', '').endswith('1231')
        year = self.check_date[:4]
        is_alter = 0
        if is_year_end:
            year_in_exceeded = total_value > YEAR_THRESHOLD
            year_end_exceeded = total_value > YEAR_END_THRESHOLD
            year_in_msg = f'为{total_value:.2f}亿元，高于{YEAR_THRESHOLD}亿元' if year_in_exceeded else f'{total_value:.2f}亿元，未高于{YEAR_THRESHOLD}亿元'
            year_end_msg = f'为{total_value:.2f}亿元，高于{YEAR_END_THRESHOLD}亿元' if year_end_exceeded else f'{total_value:.2f}亿元，未高于{YEAR_END_THRESHOLD}亿元'
            alert_message = f'固收类基金及产品（不含资本占用1%的货币市场型基金及产品）在{year}年内余额{year_in_msg}；{year}年末余额{year_end_msg}'
            is_alter = year_in_exceeded or year_end_exceeded
        else:
            year_in_exceeded = total_value > YEAR_THRESHOLD
            year_in_msg = f'为{total_value:.2f}亿元，高于{YEAR_THRESHOLD}亿元' if year_in_exceeded else f'{total_value:.2f}亿元，未高于{YEAR_THRESHOLD}亿元'
            alert_message = f'固收类基金及产品（不含资本占用1%的货币市场型基金及产品）在{year}年内余额{year_in_msg}'
            is_alter = year_in_exceeded
        result = [{'portfolio_code': '', 'portfolio_name': '固收类基金及产品', 'alert_message': alert_message, 'indicator_value': total_value, 'alert_level': is_alter}]
        return result

class StockScaleMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-PS-0002'
        self.monitor_title = '股票类资产规模监控'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['股票类']
        data = self.dao.get_investment_category_lv2_data(biz_date, dimension, category)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = data.get('data', [])
        if not data:
            return []
        df = pd.DataFrame(data)
        total_value = df['dirty_price_market_value'].sum()
        threshold_conf = getattr(self.config, 'threshold', '{}') or '{}'
        threshold = json.loads(threshold_conf)
        YEAR_THRESHOLD = threshold.get('thisyear', 100)
        quarter_thresholds = {1: threshold.get('Q1', 80), 2: threshold.get('Q2', 80), 3: threshold.get('Q3', 80), 4: threshold.get('Q4', 80)}
        year = self.check_date[:4]
        month = int(self.check_date.replace('-', '')[4:6])
        current_quarter = (month - 1) // 3 + 1
        quarter_names = {1: '第一季度', 2: '第二季度', 3: '第三季度', 4: '第四季度'}
        is_alter = 0
        alert_parts = []
        year_exceeded = total_value > YEAR_THRESHOLD
        year_msg = f'为{total_value:.2f}亿元，高于{YEAR_THRESHOLD}亿元' if year_exceeded else f'为{total_value:.2f}亿元，未高于{YEAR_THRESHOLD}亿元'
        alert_parts.append(f'股票类资产规模在{year}年内余额{year_msg}')
        if year_exceeded:
            is_alter = 1
        for q in range(1, current_quarter + 1):
            quarter_name = quarter_names[q]
            quarter_threshold = quarter_thresholds[q]
            quarter_exceeded = total_value > quarter_threshold
            quarter_msg = f'为{total_value:.2f}亿元，高于{quarter_threshold}亿元' if quarter_exceeded else f'为{total_value:.2f}亿元，未高于{quarter_threshold}亿元'
            alert_parts.append(f'股票类资产规模在{year}年{quarter_name}内余额{quarter_msg}')
            if quarter_exceeded:
                is_alter = 1
        alert_message = '；'.join(alert_parts) + '。'
        result = [{'portfolio_code': '', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': total_value, 'alert_level': is_alter}]
        return result
