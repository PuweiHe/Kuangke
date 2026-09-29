"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.investment_ra_mo_dao import InvestmentRAmountDAO
from utils.calc_utils import CalcUtils
import pandas as pd

class SingleAssetCumulativeInvestmentAmountMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IRA-SC-0001'
        self.monitor_title = '单一标的资产累计投资金额监控'
        self.dao = InvestmentRAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data_numerator = self.dao.get_investment_dimension_data(biz_date, dimension)
        asset_codes = [item['zcdm'] for item in data_numerator if item['zcdm'] is not None]
        asset_data = self.dao.get_dw_investment_data(asset_codes)
        filter_asset_codes = [item['asset_code'] for item in asset_data if item['asset_code'] is not None]
        data_numerator = [item for item in data_numerator if item['zcdm'] not in filter_asset_codes]
        if not data_numerator:
            return {'data_numerator': [], 'data_denominator': []}
        data_denominator = self.dao.get_investment_data_lake(biz_date)
        return {'data_numerator': data_numerator, 'data_denominator': data_denominator}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data_numerator = data.get('data_numerator', [])
        data_denominator = data.get('data_denominator', [])
        if not data_numerator or not data_denominator:
            return []
        denom_value = float(data_denominator[0].get('dirty_price_market_value', 0) or 0)
        if denom_value == 0:
            return []
        AMOUNT_THRESHOLD = 10
        num_df = pd.DataFrame(data_numerator).groupby('zcdm').agg(num_value=('dirty_price_market_value', 'sum'), asset_name=('jjztmc', 'first'))
        num_df['num_value'] = num_df['num_value'].astype(float).fillna(0)
        num_df['ratio'] = num_df['num_value'] / (denom_value / 100000000) * 100
        threshold_float = CalcUtils.parse_threshold(self.threshold)
        ratio_threshold = threshold_float if threshold_float is not None else 0.05
        threshold_str = f'''{ratio_threshold * 100:.2f}%''' if threshold_float is not None else self.threshold

        def build_alert_message(row):
            ratio_pct = f'''{row['ratio']:.2f}%'''
            amount_yi_str = f'''{row['num_value']:.2f}'''
            ratio_exceeded = row['ratio'] > ratio_threshold
            amount_exceeded = row['num_value'] > AMOUNT_THRESHOLD
            if ratio_exceeded and amount_exceeded:
                return f'''{row['asset_name']}资产的累计投资金额为{amount_yi_str}亿元，高于{AMOUNT_THRESHOLD}亿元；{row['asset_name']}资产的投资金额占示例机构资管上季末总资产的{ratio_pct}，超过上限比例{threshold_str}'''
            elif amount_exceeded:
                return f'''{row['asset_name']}资产的累计投资金额为{amount_yi_str}亿元，高于{AMOUNT_THRESHOLD}亿元'''
            elif ratio_exceeded:
                return f'''{row['asset_name']}资产的投资金额占示例机构资管上季末总资产的{ratio_pct}，超过上限比例{threshold_str}'''
            else:
                return f'''单一标的资产累计投资金额不高于示例机构保险上一季度末总资产{denom_value / 100000000:.2f}亿元或{AMOUNT_THRESHOLD}亿元的投资'''
        num_df['alert_message'] = num_df.apply(build_alert_message, axis=1)
        result = []
        if not num_df.empty:
            for zcdm, row in num_df.iterrows():
                result.append({'portfolio_code': zcdm, 'portfolio_name': row['asset_name'], 'alert_message': row['alert_message'], 'indicator_value': row['ratio'], 'alert_level': 1 if row['ratio'] <= ratio_threshold else 0})
        else:
            result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': '单一标的资产累计投资金额不高于示例机构保险上一季度末总资产或10亿元的投资', 'indicator_value': 0, 'alert_level': 0})
        return result
