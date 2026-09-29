"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.investment_amount_dao import InvestmentAmountDAO
from utils.calc_utils import CalcUtils
import pandas as pd

class EquityStockMarketValueMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-AC-0001'
        self.monitor_title = '权益类股票市值'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['股票']
        asset_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        if not asset_data:
            return {'asset_data': [], 'port_data': []}
        asset_codes = [item['zcdm'] for item in asset_data if item['zcdm'] is not None]
        port_data = self.dao.get_port_data_by_asset_codes(biz_date, asset_codes)
        return {'asset_data': asset_data, 'port_data': port_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_data = data.get('asset_data', [])
        port_data = data.get('port_data', [])
        if not asset_data or not port_data:
            return []
        df = pd.DataFrame(asset_data)
        port_df = pd.DataFrame(port_data)
        df = pd.merge(df, port_df, left_on='zcdm', right_on='s_info_windcode', how='left')
        if 'mkt_val' in df.columns:
            df['mkt_val'] = df['mkt_val'].fillna(0)
        else:
            df['mkt_val'] = 0
        self.logger.info('Asset data merge completed: %s rows', len(df))
        total_value = df['mkt_val'].sum()
        total_value = float(total_value)
        threshold = CalcUtils.parse_threshold(self.threshold) if self.threshold else 10
        if total_value < threshold:
            alert_msg = f'权益类资产中股票市值或预计市值低于{threshold:.0f}亿港元，为{total_value:.2f}亿港元'
            alert_level = 1
        else:
            alert_msg = f'权益类股票市值或预计市值不低于{threshold:.0f}亿港元'
            alert_level = 0
        results = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_msg, 'indicator_value': total_value, 'alert_level': alert_level}]
        return results
