"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.rating_dao import RatingDAO
from config.settings import FORBIDDEN_PROVINCES
import re
import pandas as pd
DISABLED_ZONE = FORBIDDEN_PROVINCES
RATING_SCORE = {'AAA': 22, 'AA+': 21, 'AA': 20, 'AA-': 19, 'A+': 18, 'A': 17, 'A-': 16, 'BBB+': 15, 'BBB': 14, 'BBB-': 13, 'BB+': 12, 'BB': 11, 'BB-': 10, 'B+': 9, 'B': 8, 'B-': 7, 'CCC': 6, 'CC': 5, 'C': 4, 'D': 0}

def is_below_rating(rating: str, threshold: str) -> bool:
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
    if not rating:
        return False
    score = RATING_SCORE.get(rating)
    threshold_score = RATING_SCORE.get(threshold)
    if score is None or threshold_score is None:
        return False
    return score < threshold_score

class BondIssuerExternalRatingMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-RC-0001'
        self.monitor_title = '债券发行人外部评级'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['金融债', '企业债']
        pre_date = self.get_pre_date(biz_date)
        curr_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        pre_data = self.dao.get_investment_category_detail_data(pre_date, dimension, category)
        pre_zcdm_set = {bond['zcdm'] for bond in pre_data}
        new_bonds = [bond for bond in curr_data if bond['zcdm'] not in pre_zcdm_set]
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
        results = []
        below_rating = merged_pd[merged_pd['credit_rating'].apply(lambda r: is_below_rating(r, threshold) if pd.notna(r) and r else False)]
        unrated = merged_pd[merged_pd['credit_rating'].isna() | (merged_pd['credit_rating'] == '')]
        below_count = len(below_rating)
        unrated_count = len(unrated)
        is_alter = 0
        if below_count > 0:
            below_names = '、'.join(below_rating['issuer_name'].dropna().astype(str).tolist())
            alert_message = f'当期新增企业（公司）债券的发行人外部评级不在{threshold}级以上的数量有{below_count}个，分别是：{below_names}。'
            if unrated_count > 0:
                unrated_names = '、'.join(unrated['issuer_name'].dropna().astype(str).tolist())
                if unrated_names:
                    alert_message += f'未评级债券发行人包括：{unrated_names}。'
            is_alter = 1
        elif unrated_count > 0:
            unrated_names = '、'.join(unrated['issuer_name'].dropna().astype(str).tolist())
            if unrated_names:
                is_alter = 1
                alert_message = f'当期新增企业（公司）债券的发行人外部评级不在{threshold}级以上的数量为0个。未评级债券发行人包括：{unrated_names}。'
            else:
                alert_message = f'当期新增企业（公司）债券的发行人外部评级不在{threshold}级以上的数量为0个。'
        else:
            alert_message = f'当期新增企业（公司）债券的发行人外部评级不在{threshold}级以上的数量为0个。'
        results.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': below_count, 'alert_level': is_alter})
        return results

class EnterpriseBondRatingMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-RC-0002'
        self.monitor_title = '企业债券评级'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['企业债']
        pre_date = self.get_pre_date(biz_date)
        curr_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        pre_data = self.dao.get_investment_category_detail_data(pre_date, dimension, category)
        pre_zcdm_set = {bond['zcdm'] for bond in pre_data}
        new_bonds = [bond for bond in curr_data if bond['zcdm'] not in pre_zcdm_set]
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
        results = []
        below_rating = merged_pd[merged_pd['credit_rating'].apply(lambda r: is_below_rating(r, threshold) if pd.notna(r) and r else False)]
        unrated = merged_pd[merged_pd['credit_rating'].isna() | (merged_pd['credit_rating'] == '')]
        below_count = len(below_rating)
        unrated_count = len(unrated)
        is_alter = 0
        if below_count > 0:
            below_names = '、'.join(below_rating['issuer_name'].dropna().astype(str).tolist())
            alert_message = f'当期新增企业（公司）债券的发行人外部评级不在{threshold}级以上的数量有{below_count}个，分别是：{below_names}。'
            if unrated_count > 0:
                unrated_names = '、'.join(unrated['issuer_name'].dropna().astype(str).tolist())
                if unrated_names:
                    alert_message += f'未评级债券发行人包括：{unrated_names}。'
            is_alter = 1
        elif unrated_count > 0:
            unrated_names = '、'.join(unrated['issuer_name'].dropna().astype(str).tolist())
            if unrated_names:
                is_alter = 1
                alert_message = f'当期新增企业（公司）债券的发行人外部评级不在{threshold}级以上的数量为0个。未评级债券发行人包括：{unrated_names}。'
            else:
                alert_message = f'当期新增企业（公司）债券的发行人外部评级不在{threshold}级以上的数量为0个。'
        else:
            alert_message = f'当期新增企业（公司）债券的发行人外部评级不在{threshold}级以上的数量为0个。'
        results.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': below_count, 'alert_level': is_alter})
        return results

class InternalEnterpriseBondRatingMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-RC-0003'
        self.monitor_title = '示例机构企业债券评级'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['企业债']
        pre_date = self.get_pre_date(biz_date)
        curr_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        pre_data = self.dao.get_investment_category_detail_data(pre_date, dimension, category)
        pre_zcdm_set = {bond['zcdm'] for bond in pre_data}
        new_bonds = [bond for bond in curr_data if bond['zcdm'] not in pre_zcdm_set]
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
        threshold = self.threshold or 'BBB-'
        results = []
        below_rating = merged_pd[merged_pd['credit_rating'].apply(lambda r: is_below_rating(r, threshold) if pd.notna(r) and r else False)]
        unrated = merged_pd[merged_pd['credit_rating'].isna() | (merged_pd['credit_rating'] == '')]
        below_count = len(below_rating)
        unrated_count = len(unrated)
        is_alter = 0
        if below_count > 0:
            below_names = '、'.join(below_rating['issuer_name'].dropna().astype(str).tolist())
            alert_message = f'当期新增基础设施债权投资计划、不动产债权投资计划、集合资金信托计划等涉及信用评级的金融产品中，示例机构资管内部评级不在{threshold}级及以上的数量有{below_count}个，分别是：{below_names}。'
            if unrated_count > 0:
                unrated_names = '、'.join(unrated['issuer_name'].dropna().astype(str).tolist())
                if unrated_names:
                    alert_message += f'未评级产品包括：{unrated_names}。'
            is_alter = 1
        elif unrated_count > 0:
            unrated_names = '、'.join(unrated['issuer_name'].dropna().astype(str).tolist())
            if unrated_names:
                is_alter = 1
                alert_message = f'当期新增基础设施债权投资计划、不动产债权投资计划、集合资金信托计划等涉及信用评级的金融产品中，示例机构资管内部评级不在{threshold}级及以上的数量为0个。未评级产品包括：{unrated_names}。'
            else:
                alert_message = f'当期新增基础设施债权投资计划、不动产债权投资计划、集合资金信托计划等涉及信用评级的金融产品中，示例机构资管内部评级不在{threshold}级及以上的数量为0个。'
        else:
            alert_message = f'当期新增基础设施债权投资计划、不动产债权投资计划、集合资金信托计划等涉及信用评级的金融产品中，示例机构资管内部评级不在{threshold}级及以上的数量为0个。'
        results.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': below_count, 'alert_level': is_alter})
        return results

class UrbanInvestmentBondRegionMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-RC-0004'
        self.monitor_title = '城投债发行区域监控'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['企业债', '金融债']
        curr_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        new_bonds = [bond for bond in curr_data if bond['zcdm'] not in curr_data]
        asset_codes = list({bond['zcdm'] for bond in new_bonds})
        issuer_data = self.dao.get_bond_localgovt_dist_data(biz_date, asset_codes)
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
            merged_pd['province'] = None
        disabled_bonds = merged_pd[merged_pd['province'].isin(DISABLED_ZONE)]
        year = self.check_date[:4]
        is_alter = 0
        if len(disabled_bonds) > 0:
            province_counts = disabled_bonds.groupby('province').size()
            parts = [f'新增{prov}省份投资的债券{cnt}只' for prov, cnt in province_counts.items()]
            alert_message = f'{year}年至今，' + '，'.join(parts) + '。'
            is_alter = 1
        else:
            alert_message = f'{year}年至今，未新增禁投区域城投债。'
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': len(disabled_bonds), 'alert_level': is_alter}]
        return result

class DebtInvestmentPlanRatingMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-RC-0005'
        self.monitor_title = '债权投资计划、集合资金信托计划和资产证券化类产品外部债项评级'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['债权计划', '资产支持计划', '信托计划', '股权计划']
        pre_date = self.get_pre_date(biz_date)
        curr_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        pre_data = self.dao.get_investment_category_detail_data(pre_date, dimension, category)
        pre_zcdm_set = {bond['zcdm'] for bond in pre_data}
        new_bonds = [bond for bond in curr_data if bond['zcdm'] not in pre_zcdm_set]
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
        threshold = self.threshold or 'BBB-'
        year = self.check_date[:4]
        grouped_pd = merged_pd.groupby('ztbh')
        for ztbh, group in grouped_pd:
            portfolio_name = group['jjztmc'].iloc[0]
            below_rating = group[group['credit_rating'].apply(lambda r: is_below_rating(r, threshold) if pd.notna(r) and r else False)]
            is_alter = 0
            if len(below_rating) > 0:
                below_names = '、'.join(below_rating['zcmc'].dropna().astype(str).tolist())
                alert_message = f'{year}年至今，新增{below_names}，评级在{threshold}以下。'
                is_alter = 1
            else:
                alert_message = f'{year}年至今，未新增外部债项评级在{threshold}以下的债权投资计划、集合资金信托计划和资产证券化类产品、股权计划：非标类股权计划。'
            result = [{'portfolio_code': ztbh, 'portfolio_name': portfolio_name, 'alert_message': alert_message, 'indicator_value': len(below_rating), 'alert_level': is_alter}]
        return result

class InfrastructureRealEstateTrustRatingMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'RG-RC-0006'
        self.monitor_title = '基础设施、不动产、集合资金信托评级'
        self.dao = RatingDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['债权计划', '信托计划']
        pre_date = self.get_pre_date(biz_date)
        curr_data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        pre_data = self.dao.get_investment_category_detail_data(pre_date, dimension, category)
        pre_zcdm_set = {bond['zcdm'] for bond in pre_data}
        new_bonds = [bond for bond in curr_data if bond['zcdm'] not in pre_zcdm_set]
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
        threshold = self.threshold or 'BBB-'
        year = self.check_date[:4] if self.check_date else '2025'
        results = []
        below_rating = merged_pd[merged_pd['credit_rating'].apply(lambda r: is_below_rating(r, threshold) if pd.notna(r) and r else False)]
        is_alter = 0
        if len(below_rating) > 0:
            below_names = '、'.join(below_rating['zcmc'].dropna().astype(str).tolist())
            alert_message = f'{year}年至今，新增{below_names}'
            is_alter = 1
        else:
            alert_message = f'{year}年至今，未新增外部债项评级在{threshold}以下的基础设施、不动产、集合资金信托产品。'
        results.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': len(below_rating), 'alert_level': is_alter})
        return results
