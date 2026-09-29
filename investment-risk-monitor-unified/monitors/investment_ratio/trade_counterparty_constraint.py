"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.investment_ratio_dao import InvestmentRatioDAO
from utils.calc_utils import CalcUtils
import pandas as pd
import re

class SingleBondBalanceRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-TC-0001'
        self.monitor_title = '单一债券余额占比'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['政府债', '企业债', '金融债']
        data_numerator = self.dao.get_investment_dimension_asset_data(biz_date, dimension, category)
        asset_codes = [item['zcdm'] for item in data_numerator if item['zcdm'] is not None]
        data_denominator = self.dao.get_investment_dw_issuer_data(biz_date, asset_codes)
        return {'data_numerator': data_numerator, 'data_denominator': data_denominator}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data_numerator = data.get('data_numerator', [])
        data_denominator = data.get('data_denominator', [])
        if not data_numerator or not data_denominator:
            return []
        num_df = pd.DataFrame(data_numerator)
        denom_df = pd.DataFrame(data_denominator)
        merged = num_df.merge(denom_df, left_on='zcdm', right_on='asset_code', how='left')
        merged = merged[merged['issue_scale'] != 0]
        merged['ratio'] = merged['dirty_price_market_value'] / merged['issue_scale']
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.15
        threshold_str = f'''{threshold_float * 100:.2f}%''' if threshold_float is not None else self.threshold
        if threshold_float is not None:
            exceeded = merged[merged['ratio'] > threshold_float]
        else:
            exceeded = pd.DataFrame()
        result = []
        if not exceeded.empty:
            for _, row in exceeded.iterrows():
                ratio_str = f'''{row['ratio'] * 100:.2f}%'''
                alert_message = f'''{row['zcmc']}债券持仓占发行规模的比例为{ratio_str}，超过{threshold_str}'''
                result.append({'portfolio_code': row['ztbh'], 'portfolio_name': row['jjztmc'], 'alert_message': alert_message, 'indicator_value': ratio_str, 'alert_level': 1})
        else:
            for ztbh in merged['ztbh'].unique():
                portfolio_name = merged[merged['ztbh'] == ztbh]['jjztmc'].iloc[0]
                max_ratio = merged[merged['ztbh'] == ztbh]['ratio'].max()
                ratio_str = f'''{max_ratio * 100:.2f}%'''
                alert_message = f'''单一债券持仓占发行规模的比例均不超过{threshold_str}'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': portfolio_name, 'alert_message': alert_message, 'indicator_value': ratio_str, 'alert_level': 0})
        return result
