"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from re import L
from monitors.monitor_base import MonitorBase
from dao.blac_white_dao import BlackWhiteDAO
from utils.date_utils import getYear
import pandas as pd

class BanSoyaMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IC-0001'
        self.monitor_title = '禁投标的监控（豆粕）'
        self.dao = BlackWhiteDAO()
        self.portfolio_code = '0'
        self.portfolio_name = '委托资管'

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_asset_dimension_date(biz_date, dimension)
        if not asset_datas:
            return {'asset_datas': [], 'black_list': [], 'fund_black_list': []}
        self.logger.debug('Loaded %s asset records', len(asset_datas))
        asset_codes = [row.get('zcdm') for row in asset_datas if row.get('zcdm') is not None]
        asset_codes = list(set(asset_codes))
        year = getYear(biz_date)
        result = self.dao.get_invest_soya_list(year, asset_codes)
        fund_asset_datas = self.dao.get_asset_by_investment_style()
        return {'asset_datas': asset_datas, 'black_list': result, 'fund_black_list': fund_asset_datas}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas')
        black_list = data.get('black_list')
        fund_black_list = data.get('fund_black_list')
        if not asset_datas:
            return []
        asset_df = pd.DataFrame(asset_datas)
        if 'zcdm' not in asset_df.columns or 'ztbh' not in asset_df.columns:
            return []
        asset_df = asset_df[~asset_df['zcdm'].isin(fund_black_list)]
        asset_df = asset_df[~asset_df['zcdm'].isin(black_list)]
        zcmc_list = asset_df['zcmc'].unique()
        result = []
        alert_message = ''
        alert_level = 0
        if len(zcmc_list) > 0:
            alert_message = f'''持仓禁投标的产品：{','.join(zcmc_list)}，不在投资范围之内，请关注'''
            alert_level = 1
        else:
            alert_message = '持仓资产，均在投资范围之内'
        result.append({'portfolio_code': self.portfolio_code, 'portfolio_name': self.portfolio_name, 'alert_message': alert_message, 'indicator_value': '', 'alert_level': alert_level})
        return result

class StockInvestmentScopeMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IC-0002'
        self.monitor_title = '股票投资范围'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        return {'asset_dates': [], 'stock_pool_whitelist': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_dates = data.get('asset_dates')
        stock_pool_whitelist = data.get('stock_pool_whitelist')
        if not asset_dates:
            return []
        valid_assets = [item for item in asset_dates if isinstance(item, dict)]
        if not valid_assets:
            return []
        result = []
        return result

class SubordinatedBondWhitelistMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IC-0003'
        self.monitor_title = '次级债、资本补充债白名单'
        self.portfolio_code = '0'
        self.portfolio_name = '委托资管'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_asset_dimension_date(biz_date, dimension)
        result = self.dao.get_subordinated_bond_blacklist()
        return {'asset_datas': asset_datas, 'subordinated_bond_blacklist': result}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas')
        subordinated_bond_whitelist = data.get('subordinated_bond_blacklist')
        if not asset_datas:
            return []
        asset_df = pd.DataFrame(asset_datas)
        result = []
        blacklist = [item['s_info_windcode'] for item in subordinated_bond_whitelist]
        in_blacklist = set()
        for _, row in asset_df.iterrows():
            bond_code = row.get('zcdm')
            if bond_code in blacklist:
                in_blacklist.add(row.get('zcmc', bond_code))
        alert_level = 0
        if in_blacklist:
            bonds_str = ','.join(in_blacklist)
            alert_message = f'''组合持仓的{bonds_str}次级债、资本补充债，不在投资范围内。'''
            alert_level = 1
        else:
            alert_message = '组合持仓的次级债、资本补充债，均在投资范围内。'
        result.append({'portfolio_code': self.portfolio_code, 'portfolio_name': self.portfolio_name, 'alert_message': alert_message, 'indicator_value': 0, 'alert_level': alert_level})
        return result

class RealEstateIndustryBanMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IC-0004'
        self.monitor_title = '禁投房地产行业'
        self.portfolio_code = '0'
        self.portfolio_name = ''
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_asset_dimension_date(biz_date, dimension)
        if not asset_datas:
            return {'asset_datas': [], 'real_estate_industry_ban': []}
        asset_codes = [item['zcdm'] for item in asset_datas if item.get('zcdm') is not None]
        result = self.dao.get_real_estate_industry_ban(biz_date, asset_codes)
        return {'asset_datas': asset_datas, 'real_estate_industry_ban': result}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas')
        real_estate_industry_ban = data.get('real_estate_industry_ban')
        if not asset_datas:
            return []
        banned_codes = [item.get('main_code', '') for item in real_estate_industry_ban if item.get('main_code')]
        asset_df = pd.DataFrame(asset_datas)
        if 'zcdm' not in asset_df.columns or 'ztbh' not in asset_df.columns:
            return []
        real_estate_holdings = set()
        for _, row in asset_df.iterrows():
            asset_code = row.get('zcdm', '')
            if asset_code in banned_codes:
                real_estate_holdings.add(row.get('zcmc', asset_code))
        alert_level = 0
        if real_estate_holdings:
            alert_message = f'''持仓行业中有房地产行业（{','.join(real_estate_holdings)}）'''
            alert_level = 1
        else:
            alert_message = '无房地产行业持仓'
        result = [{'portfolio_code': self.portfolio_code, 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': len(real_estate_holdings), 'alert_level': alert_level}]
        return result

class TargetWhitelistMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IC-0005'
        self.monitor_title = '标的白名单'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_asset_dimension_date(biz_date, dimension)
        if not asset_datas:
            return {'asset_datas': [], 'target_whitelist': []}
        valid_assets = [item for item in asset_datas if isinstance(item, dict)]
        if not valid_assets:
            return {'asset_datas': [], 'target_whitelist': []}
        asset_codes = [item['zcdm'].split('.')[0] for item in valid_assets if item.get('zcdm') and isinstance(item.get('zcdm'), str)]
        result = self.dao.get_target_whitelist(biz_date, asset_codes)
        return {'asset_datas': [], 'target_whitelist': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas')
        target_whitelist = data.get('target_whitelist')
        if not asset_datas or not target_whitelist:
            return []
        whitelist_codes = set()
        if target_whitelist:
            whitelist_codes = {item.get('zcdm', '').split('.')[0] for item in target_whitelist if item.get('zcdm') and isinstance(item.get('zcdm'), str)}
        valid_assets = [item for item in asset_datas if isinstance(item, dict)]
        if not valid_assets:
            return []
        asset_df = pd.DataFrame(valid_assets)
        if 'zcdm' not in asset_df.columns or 'ztbh' not in asset_df.columns:
            return []
        asset_grouped = asset_df.groupby('ztbh')
        result = []
        for ztbh, group in asset_grouped:
            out_of_whitelist = []
            for _, row in group.iterrows():
                asset_code = row.get('zcdm', '')
                if isinstance(asset_code, str) and '.' in asset_code:
                    asset_code = asset_code.split('.')[0]
                    if asset_code and asset_code not in whitelist_codes:
                        out_of_whitelist.append(row.get('jjztmc', asset_code))
            if out_of_whitelist:
                targets_str = ','.join(out_of_whitelist)
                alert_message = f'''组合持仓的{targets_str}标的，在白名单之外'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': group['jjztmc'].values[0] if 'jjztmc' in group.columns else str(ztbh), 'alert_message': alert_message, 'indicator_value': len(out_of_whitelist)})
        return result

class WhitelistInvestmentScopeMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IC-0006'
        self.monitor_title = '白名单投资范围'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_asset_dimension_date(biz_date, dimension)
        if not asset_datas:
            return {'asset_datas': [], 'whitelist_investment_scope': []}
        valid_assets = [item for item in asset_datas if isinstance(item, dict)]
        if not valid_assets:
            return {'asset_datas': [], 'whitelist_investment_scope': []}
        asset_codes = [item['zcdm'].split('.')[0] for item in valid_assets if item.get('zcdm') and isinstance(item.get('zcdm'), str)]
        result = self.dao.get_whitelist_investment_scope(biz_date, asset_codes)
        return {'asset_datas': [], 'whitelist_investment_scope': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas')
        whitelist_investment_scope = data.get('whitelist_investment_scope')
        if not asset_datas or not whitelist_investment_scope:
            return []
        whitelist_codes = set()
        if whitelist_investment_scope:
            whitelist_codes = {item.get('zcdm', '').split('.')[0] for item in whitelist_investment_scope if item.get('zcdm') and isinstance(item.get('zcdm'), str)}
        valid_assets = [item for item in asset_datas if isinstance(item, dict)]
        if not valid_assets:
            return []
        asset_df = pd.DataFrame(valid_assets)
        if 'zcdm' not in asset_df.columns or 'ztbh' not in asset_df.columns:
            return []
        asset_grouped = asset_df.groupby('ztbh')
        result = []
        for ztbh, group in asset_grouped:
            out_of_whitelist = []
            for _, row in group.iterrows():
                asset_code = row.get('zcdm', '')
                if isinstance(asset_code, str) and '.' in asset_code:
                    asset_code = asset_code.split('.')[0]
                    if asset_code and asset_code not in whitelist_codes:
                        out_of_whitelist.append(row.get('jjztmc', asset_code))
            if out_of_whitelist:
                scope_str = ','.join(out_of_whitelist)
                alert_message = f'''组合投资范围，在白名单之外（{scope_str}）'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': group['jjztmc'].values[0] if 'jjztmc' in group.columns else str(ztbh), 'alert_message': alert_message, 'indicator_value': len(out_of_whitelist)})
        return result
