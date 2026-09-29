"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from poplib import LF
from monitors.monitor_base import MonitorBase
from dao.investment_ratio_dao import InvestmentRatioDAO
from utils.calc_utils import CalcUtils
import pandas as pd

class SingleIndustryConcentrationMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-IA-0001'
        self.monitor_title = '单一行业集中度'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_investment_dimension_data(biz_date, dimension)
        asset_codes = [item['zcdm'] for item in asset_datas if item is not None]
        asset_industry_data = self.dao.get_asset_industry_data(biz_date, asset_codes)
        return {'asset_datas': asset_datas, 'asset_industry_data': asset_industry_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas', [])
        asset_industry_data = data.get('asset_industry_data', {})
        if not asset_datas:
            return []
        df = pd.DataFrame(asset_datas)
        df['zchy'] = df['zcdm'].map(lambda code: asset_industry_data.get(code, '未知行业'))
        grouped = df.groupby('zchy').agg(industry_value=('dirty_price_market_value', 'sum')).reset_index()
        total_value = grouped['industry_value'].sum()
        if total_value == 0:
            return []
        grouped['concentration'] = grouped['industry_value'] / total_value
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.4
        threshold_str = f'''{threshold_float * 100:.2f}%''' if threshold_float is not None else self.threshold
        if threshold_float is not None:
            exceeded = grouped[grouped['concentration'] > threshold_float]
        else:
            exceeded = pd.DataFrame()
        result = []
        if not exceeded.empty:
            for _, row in exceeded.iterrows():
                conc_str = f'''{row['concentration'] * 100:.2f}%'''
                alert_message = f'''{row['zchy']}行业集中度为{conc_str}，超过{threshold_str}'''
                result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': conc_str, 'alert_level': 1})
        else:
            max_conc = grouped['concentration'].max()
            conc_str = f'''{max_conc * 100:.2f}%'''
            alert_message = f'''单一行业集中度{conc_str}，未超过{threshold_str}'''
            result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': float(max_conc), 'alert_level': 0})
        return result

class SingleBondHoldingRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-IA-0002'
        self.monitor_title = '单一债券持仓占比'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['政府债', '金融债', '企业债']
        data_numerator = self.dao.get_investment_category_data(biz_date, dimension, category)
        data_denominator = self.dao.get_investment_dimension_data(biz_date, dimension)
        return {'data_numerator': data_numerator, 'data_denominator': data_denominator}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data_numerator = data.get('data_numerator', [])
        data_denominator = data.get('data_denominator', [])
        if not data_numerator or not data_denominator:
            return []
        num_df = pd.DataFrame(data_numerator).groupby(['ztbh', 'zcdm']).agg(num_value=('dirty_price_market_value', 'sum'), jjztmc=('jjztmc', 'first')).reset_index()
        denom_df = pd.DataFrame(data_denominator).groupby('ztbh').agg(denom_value=('dirty_price_market_value', 'sum')).reset_index()
        merged = num_df.merge(denom_df, on='ztbh', how='inner')
        merged = merged[merged['denom_value'] != 0]
        merged['ratio'] = merged['num_value'] / merged['denom_value']
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
                alert_message = f'''{row['zcdm']}债券持仓占账户总额的比例为{ratio_str}，超过{threshold_str}'''
                result.append({'portfolio_code': row['ztbh'], 'portfolio_name': row['jjztmc'], 'alert_message': alert_message, 'indicator_value': ratio_str, 'alert_level': 1})
        else:
            for ztbh in merged['ztbh'].unique():
                portfolio_name = merged[merged['ztbh'] == ztbh]['jjztmc'].iloc[0]
                max_ratio = merged[merged['ztbh'] == ztbh]['ratio'].max()
                ratio_str = f'''{max_ratio * 100:.2f}%'''
                alert_message = f'''单一债券持仓占账户总额的比例均不超过{threshold_str}'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': portfolio_name, 'alert_message': alert_message, 'indicator_value': ratio_str, 'alert_level': 0})
        return result

class SingleBondIssueScaleRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-IA-0003'
        self.monitor_title = '单一债券持仓占发行规模占比'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['政府债', '金融债', '企业债']
        data_numerator = self.dao.get_investment_dimension_asset_data(biz_date, dimension, category)
        asset_codes = [item['zcdm'] for item in data_numerator if item['zcdm'] is not None]
        data_denominator = self.dao.get_investment_dw_asset_data(biz_date, asset_codes)
        return {'data_numerator': data_numerator, 'data_denominator': data_denominator}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data_numerator = data.get('data_numerator', [])
        data_denominator = data.get('data_denominator', [])
        if not data_numerator or not data_denominator:
            return []
        num_df = pd.DataFrame(data_numerator).groupby(['ztbh', 'zcdm']).agg(num_value=('dirty_price_market_value', 'sum'), jjztmc=('jjztmc', 'first')).reset_index()
        denom_df = pd.DataFrame(data_denominator).groupby('asset_code').agg(issue_scale=('issue_scale', 'sum')).reset_index()
        merged = num_df.merge(denom_df, left_on='zcdm', right_on='asset_code', how='inner')
        merged = merged[merged['issue_scale'] != 0]
        merged['ratio'] = merged['num_value'] / merged['issue_scale']
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
                alert_message = f'''{row['zcdm']}债券持仓占发行规模的比例为{ratio_str}，超过{threshold_str}'''
                result.append({'portfolio_code': row['ztbh'], 'portfolio_name': row['jjztmc'], 'alert_message': alert_message, 'indicator_value': ratio_str, 'alert_level': 1})
        else:
            for ztbh in merged['ztbh'].unique():
                portfolio_name = merged[merged['ztbh'] == ztbh]['jjztmc'].iloc[0]
                max_ratio = merged[merged['ztbh'] == ztbh]['ratio'].max()
                ratio_str = f'''{max_ratio * 100:.2f}%'''
                alert_message = f'''单一债券持仓占发行规模的比例均不超过{threshold_str}'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': portfolio_name, 'alert_message': alert_message, 'indicator_value': ratio_str, 'alert_level': 0})
        return result
