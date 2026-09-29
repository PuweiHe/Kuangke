"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
import re
import pandas as pd
from monitors.monitor_base import MonitorBase
from monitors.rating.risk_rating_constraint import is_below_rating
from utils.calc_utils import CalcUtils
from dao.rating_dao import RatingDAO
RATING_SCORE = {'AAA': 22, 'AA+': 21, 'AA': 20, 'AA-': 19, 'A+': 18, 'A': 17, 'A-': 16, 'BBB+': 15, 'BBB': 14, 'BBB-': 13, 'BB+': 12, 'BB': 11, 'BB-': 10, 'B+': 9, 'B': 8, 'B-': 7, 'CCC': 6, 'CC': 5, 'C': 4, 'D': 0}

class BondIssuerAndDebtCreditRatingMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-FI-0001'
        self.monitor_title = '债券发行人和债项信用评级'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['金融债', '企业债']
        current_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        asset_codes = [item['zcdm'] for item in current_data if item['zcdm'] is not None]
        issuer_data = self.dao.get_bond_issuer_dist_data(biz_date, asset_codes)
        return {'current_data': current_data, 'issuer_data': issuer_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        current_data = data.get('current_data', [])
        issuer_data = data.get('issuer_data', [])
        if not current_data or not issuer_data:
            return []
        curr_pd = pd.DataFrame(current_data)
        issuer_pd = pd.DataFrame(issuer_data)
        merged_pd = pd.merge(curr_pd, issuer_pd, left_on='zcdm', right_on='bond_code', how='left')
        results = []
        threshold = self.threshold or 'BBB'
        below_rating_bonds = merged_pd[merged_pd['credit_rating'].apply(lambda r: is_below_rating(r, threshold) if pd.notna(r) and r else False)]
        if len(below_rating_bonds) > 0:
            below_rating_bonds = below_rating_bonds.drop_duplicates(subset=['zcdm'])
        alert_message = ''
        alert_level = 0
        if len(below_rating_bonds) > 0:
            below_names = '、'.join(below_rating_bonds['zcmc'].dropna().astype(str).tolist())
            alert_message = f'{below_names}债券的发行人/债项信用评级不满足{threshold}级及以上。'
            alert_level = 1
        else:
            alert_message = f'持仓债券的发行人&债项信用评级满足{threshold}级及以上。'
        results = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': len(below_rating_bonds), 'alert_level': alert_level}]
        return results

class BBBRatedBondRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-FI-0002'
        self.monitor_title = 'BBB评级债券占比'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['金融债', '企业债']
        asset_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        asset_codes = [item['zcdm'] for item in asset_data if item['zcdm'] is not None]
        rating_data = self.dao.get_bond_rating_data(biz_date, asset_codes)
        bbb_rated_bonds = [bond for bond in rating_data if bond['credit_rating'] == 'BBB']
        bond_codes = list({bond['bond_code'] for bond in bbb_rated_bonds})
        data_numerator = self.dao.get_rated_bond_data(biz_date, dimension, bond_codes)
        data_denominator = self.dao.get_investment_dimension_data(biz_date, dimension)
        return {'data_numerator': data_numerator, 'data_denominator': data_denominator}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data_numerator = data.get('data_numerator', [])
        data_denominator = data.get('data_denominator', [])
        if not data_denominator:
            return []
        denominator_pd = pd.DataFrame(data_denominator)
        total_denominator = denominator_pd['dirty_price_market_value'].sum()
        if data_numerator:
            numerator_pd = pd.DataFrame(data_numerator)
            total_numerator = numerator_pd['dirty_price_market_value'].sum()
        else:
            total_numerator = 0
        ratio = total_numerator / total_denominator if total_denominator != 0 else 0.0
        ratio = float(ratio)
        threshold = CalcUtils.parse_threshold(self.threshold) if self.threshold else 0.12
        results = []
        is_alert = ratio > threshold
        if is_alert:
            alert_msg = f'BBB级或者相当于BBB级评级的债券账面余额超过该债券当期发行规模{threshold:.2%}，为{ratio:.2%}。'
        else:
            alert_msg = f'BBB级或者相当于BBB级评级的债券账面余额未超过该债券当期发行规模{threshold:.2%}。'
        results.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_msg, 'indicator_value': round(ratio, 4), 'alert_level': 1 if is_alert else 0})
        return results

class BBBRatedBondMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-FI-0003'
        self.monitor_title = 'BBB级债券'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['金融债', '企业债']
        asset_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        if not asset_data:
            return {'data_numerator': [], 'data_denominator': []}
        asset_codes = [item['zcdm'] for item in asset_data if item['zcdm'] is not None]
        if not asset_codes:
            return {'data_numerator': [], 'data_denominator': self.dao.get_investment_dimension_data(biz_date, dimension)}
        rating_data = self.dao.get_bond_rating_data(biz_date, asset_codes)
        if not rating_data:
            return {'data_numerator': [], 'data_denominator': self.dao.get_investment_dimension_data(biz_date, dimension)}
        a_minus_rated_bonds = [bond for bond in rating_data if RATING_SCORE.get(bond['credit_rating'], 0) >= RATING_SCORE.get('A-', 0)]
        if not a_minus_rated_bonds:
            return {'data_numerator': [], 'data_denominator': self.dao.get_investment_dimension_data(biz_date, dimension)}
        bond_codes = list({bond['bond_code'] for bond in a_minus_rated_bonds})
        bond_codes = [code.replace('.', '') for code in bond_codes]
        data_numerator = self.dao.get_rated_bond_data(biz_date, dimension, bond_codes)
        data_denominator = self.dao.get_investment_dimension_data(biz_date, dimension)
        return {'data_numerator': data_numerator, 'data_denominator': data_denominator}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data_numerator = data.get('data_numerator', [])
        data_denominator = data.get('data_denominator', [])
        if not data_numerator or not data_denominator:
            return []
        denominator_pd = pd.DataFrame(data_denominator)
        total_denominator = denominator_pd['dirty_price_market_value'].sum()
        if data_numerator:
            numerator_pd = pd.DataFrame(data_numerator)
            total_numerator = numerator_pd['dirty_price_market_value'].sum()
        else:
            total_numerator = 0
        ratio = total_numerator / total_denominator if total_denominator != 0 else 0.0
        ratio = float(ratio)
        threshold = CalcUtils.parse_threshold(self.threshold) if self.threshold else 0.15
        results = []
        is_alert = ratio < threshold
        if is_alert:
            alert_msg = f'投资组合中A-级（含）或者相当于A-级（含）以上占比低于{threshold:.2%}，占比为{ratio:.2%}。'
        else:
            alert_msg = f'投资组合中A-级（含）或者相当于A-级（含）以上占比不低于{threshold:.2%}。'
        results.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_msg, 'indicator_value': round(ratio, 4), 'alert_level': 1 if is_alert else 0})
        return results

class AMinusRatedBondRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-FI-0004'
        self.monitor_title = 'A-级债券占比'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['金融债', '企业债']
        asset_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        pre_date = self.get_pre_date(biz_date)
        pre_asset_data = self.dao.get_investment_category_detail_data(pre_date, dimension, category)
        pre_zcdm_set = {bond['zcdm'] for bond in pre_asset_data if bond.get('zcdm')}
        new_bonds = [bond for bond in asset_data if bond['zcdm'] not in pre_zcdm_set]
        asset_codes = list({bond['zcdm'] for bond in new_bonds})
        issuer_data = self.dao.get_bond_issuer_data(biz_date, asset_codes)
        return {'new_bonds': new_bonds, 'issuer_data': issuer_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        new_bonds = data.get('new_bonds', [])
        issuer_data = data.get('issuer_data', [])
        if not new_bonds:
            return []
        curr_pd = pd.DataFrame(new_bonds)
        if issuer_data:
            issuer_pd = pd.DataFrame(issuer_data)
            merged_pd = pd.merge(curr_pd, issuer_pd, left_on='zcdm', right_on='bond_code', how='left')
        else:
            merged_pd = curr_pd.copy()
            merged_pd['issuer_name'] = None
            merged_pd['credit_rating'] = None
        threshold = self.threshold or 'A-'
        below_rating_bonds = merged_pd[merged_pd['credit_rating'].apply(lambda r: is_below_rating(r, threshold) if pd.notna(r) and r else False)]
        results = []
        alert_msg = ''
        alert_level = 0
        if len(below_rating_bonds) > 0:
            below_rating_bonds = below_rating_bonds.drop_duplicates(subset=['zcdm'])
            pre_msg_str = ''
            for _, row in below_rating_bonds.iterrows():
                bond_name = row.get('zcmc', '')
                rating = row.get('credit_rating', '')
                pre_msg_str += f'{bond_name}债券的发行主体/担保主体评级为{rating}，'
            alert_level = 1
            alert_msg = pre_msg_str + alert_msg + '，在' + threshold + '以下。'
        else:
            alert_msg = f'新增企业债的发行主体/担保主体评级均在{threshold}以上。'
        results = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_msg, 'indicator_value': len(below_rating_bonds), 'alert_level': alert_level}]
        return results
