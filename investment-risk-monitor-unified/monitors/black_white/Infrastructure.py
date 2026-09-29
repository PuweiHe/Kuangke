from core.asset_codes import whitelist_violations
"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.blac_white_dao import BlackWhiteDAO
from utils.date_utils import getYear
import pandas as pd

class REITSInvestmentScopeMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IF-0001'
        self.monitor_title = 'REITS投资范围监控'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_asset_data(biz_date, dimension, ['REITs'])
        year = getYear(biz_date)
        reits_fund_pool_whitelist = self.dao.get_reits_fund_pool_whitelist(year)
        return {'asset_datas': asset_datas, 'reits_fund_pool_whitelist': reits_fund_pool_whitelist}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas')
        reits_fund_pool_whitelist = data.get('reits_fund_pool_whitelist')
        if not asset_datas:
            return []
        valid_assets = [item for item in asset_datas if isinstance(item, dict)]
        if not valid_assets:
            return []
        whitelist_names = [item['bk_name'] for item in reits_fund_pool_whitelist if isinstance(item, dict) and 'bk_name' in item]
        asset_df = pd.DataFrame(valid_assets)
        if 'ztbh' not in asset_df.columns:
            return []
        asset_grouped = asset_df.groupby('ztbh')
        result = []
        for ztbh, group in asset_grouped:
            out_of_whitelist = []
            portfolio_name = group['jjztmc'].values[0] if 'jjztmc' in group.columns else str(ztbh)
            for _, row in group.iterrows():
                fund_name = row.get('zcmc', '')
                if fund_name and fund_name not in whitelist_names:
                    out_of_whitelist.append(row.get('zcmc', fund_name))
            if out_of_whitelist:
                funds_str = ','.join(out_of_whitelist)
                alert_message = f'''组合持仓的{funds_str}基础设施基金，在基础设施基金池白名单之外'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': portfolio_name, 'alert_message': alert_message, 'indicator_value': len(out_of_whitelist)})
        return result

class FVOCIFundPoolMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IF-0002'
        self.monitor_title = 'FVOCI的基金池监控'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        return {'asset_datas': [], 'reits_fund_whitelist': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas')
        reits_fund_whitelist = data.get('reits_fund_whitelist')
        if not asset_datas:
            return []
        whitelist_codes = set()
        if reits_fund_whitelist:
            whitelist_codes = {item.get('zcdm', '').split('.')[0] for item in reits_fund_whitelist if item.get('zcdm')}
        asset_df = pd.DataFrame(asset_datas)
        asset_grouped = asset_df.groupby('ztbh')
        result = []
        for ztbh, group in asset_grouped:
            out_of_whitelist = []
            for _, row in group.iterrows():
                fund_code = row.get('zcdm', '').split('.')[0]
                if fund_code and fund_code not in whitelist_codes:
                    out_of_whitelist.append(row.get('jjztmc', fund_code))
            if out_of_whitelist:
                funds_str = ','.join(out_of_whitelist)
                alert_message = f'''{funds_str}未在基础设施基金池范围内'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': group['jjztmc'].values[0], 'alert_message': alert_message, 'indicator_value': len(out_of_whitelist)})
        return result

class FVOCIStockPoolMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IF-0003'
        self.monitor_title = 'FVOCI的股票池监控'
        self.portfolio_code = '0'
        self.portfolio_name = ''
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_fvoci_asset_data(biz_date, dimension, ['股票'])
        fvoci_stock_pool_whitelist = self.dao.get_fvoci_stock_pool_whitelist(biz_date)
        return {'asset_datas': asset_datas, 'fvoci_stock_pool_whitelist': fvoci_stock_pool_whitelist}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = data.get('asset_datas')
        fvoci_stock_pool_whitelist = data.get('fvoci_stock_pool_whitelist')
        if not asset_datas:
            return []
        try:
            violations = whitelist_violations(asset_datas, fvoci_stock_pool_whitelist)
        except (ValueError, KeyError):
            return [{'portfolio_code': self.portfolio_code, 'portfolio_name': self.curr_dimension,
                     'indicator_value': None, 'alert_level': 2,
                     'alert_message': '[missing_data] Invalid asset code or unavailable whitelist'}]
        out_of_whitelist = {row.get('zcmc') or row['zcdm'] for row in violations}
        alert_level = 0
        if out_of_whitelist:
            alert_message = f'''{','.join(out_of_whitelist)}股票未在FVOCI会计分类股票池范围内'''
            alert_level = 1
        else:
            alert_message = '股票投资未超出FVOCI会计分类的股票池范围'
        result = [{'portfolio_code': self.portfolio_code, 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': '', 'alert_level': alert_level}]
        return result

class FVOCIFundInvestExitMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IF-0004'
        self.monitor_title = 'FVOCI的基金投资和退出'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        return {'pre_reits_asset_datas': [], 'reits_asset_datas': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        pre_reits_asset_datas = data.get('pre_reits_asset_datas')
        reits_asset_datas = data.get('reits_asset_datas')
        if not reits_asset_datas:
            return []
        pre_asset_keys = set()
        if pre_reits_asset_datas:
            pre_asset_keys = {(item.get('ztbh', ''), item.get('zcdm', '').split('.')[0]) for item in pre_reits_asset_datas if item.get('zcdm')}
        reits_df = pd.DataFrame(reits_asset_datas)
        reits_grouped = reits_df.groupby('ztbh')
        result = []
        for ztbh, group in reits_grouped:
            new_assets = []
            biz_date = group['p_dt'].values[0]
            for _, row in group.iterrows():
                asset_code = row.get('zcdm', '').split('.')[0]
                key = (ztbh, asset_code)
                if key not in pre_asset_keys:
                    new_assets.append(row.get('jjztmc', asset_code))
            if new_assets:
                assets_str = ','.join(new_assets)
                alert_message = f'''{biz_date}，新增了{assets_str}的投资，须关注是否有告知'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': group['jjztmc'].values[0], 'alert_message': alert_message, 'indicator_value': len(new_assets)})
        return result

class FVOCIFundBuySellMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-IF-0005'
        self.monitor_title = 'FVOCI的基金买入卖出'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        return {'pre_reits_asset_datas': [], 'reits_asset_datas': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        pre_reits_asset_datas = data.get('pre_reits_asset_datas')
        reits_asset_datas = data.get('reits_asset_datas')
        if not reits_asset_datas:
            return []
        pre_asset_keys = set()
        if pre_reits_asset_datas:
            pre_asset_keys = {(item.get('ztbh', ''), item.get('zcdm', '').split('.')[0]) for item in pre_reits_asset_datas if item.get('zcdm')}
        cur_asset_keys = set()
        cur_asset_map = {}
        if reits_asset_datas:
            for item in reits_asset_datas:
                code = item.get('zcdm', '').split('.')[0]
                ztbh = item.get('ztbh', '')
                key = (ztbh, code)
                cur_asset_keys.add(key)
                cur_asset_map[key] = item.get('jjztmc', code)
                cur_asset_map['biz_date', ztbh] = item.get('p_dt', '')
        pre_asset_map = {}
        if pre_reits_asset_datas:
            for item in pre_reits_asset_datas:
                code = item.get('zcdm', '').split('.')[0]
                ztbh = item.get('ztbh', '')
                pre_asset_map[ztbh, code] = item.get('jjztmc', code)
        from collections import defaultdict
        changes_by_portfolio = defaultdict(lambda: {'added': [], 'removed': [], 'biz_date': ''})
        for key in cur_asset_keys - pre_asset_keys:
            ztbh, _ = key
            changes_by_portfolio[ztbh]['added'].append(cur_asset_map.get(key, _))
            changes_by_portfolio[ztbh]['biz_date'] = cur_asset_map.get(('biz_date', ztbh), '')
        for key in pre_asset_keys - cur_asset_keys:
            ztbh, _ = key
            changes_by_portfolio[ztbh]['removed'].append(pre_asset_map.get(key, _))
            if not changes_by_portfolio[ztbh]['biz_date']:
                changes_by_portfolio[ztbh]['biz_date'] = cur_asset_map.get(('biz_date', ztbh), '')
        result = []
        name_map = {}
        if reits_asset_datas:
            for item in reits_asset_datas:
                name_map[item.get('ztbh', '')] = item.get('jjztmc', '')
        if pre_reits_asset_datas:
            for item in pre_reits_asset_datas:
                if item.get('ztbh', '') not in name_map:
                    name_map[item.get('ztbh', '')] = item.get('jjztmc', '')
        for ztbh, changes in changes_by_portfolio.items():
            parts = []
            if changes['added']:
                parts.append(f'''新增了{','.join(changes['added'])}''')
            if changes['removed']:
                parts.append(f'''减少了{','.join(changes['removed'])}''')
            if parts:
                change_str = ','.join(parts)
                alert_message = f'''{changes['biz_date']}，{change_str}的投资，须关注是否有告知'''
                result.append({'portfolio_code': ztbh, 'portfolio_name': name_map.get(ztbh, ztbh), 'alert_message': alert_message, 'indicator_value': len(changes['added']) + len(changes['removed'])})
        return result
