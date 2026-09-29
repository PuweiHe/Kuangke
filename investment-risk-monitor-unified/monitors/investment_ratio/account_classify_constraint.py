"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.investment_ratio_dao import InvestmentRatioDAO
import pandas as pd
from collections import defaultdict

class AmortizedCostBondMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-AC-0001'
        self.monitor_title = '到期类和摊余成本类债券'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['政府债', '金融债', '企业债']
        account_category = ['AC']
        data = self.dao.get_investment_account_data(biz_date, dimension, category, account_category)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        account_data = data.get('data', [])
        if not account_data:
            return []
        pd_data = pd.DataFrame(account_data)
        bond_names = pd_data['zcmc'].tolist()
        if not bond_names:
            return []
        bond_str = ', '.join(bond_names)
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': f'''{bond_str}债券需要确认是否可持有''', 'indicator_value': '', 'alert_level': 1}]
        return result

class FVOCIInfrastructureBuySellMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-AC-0002'
        self.monitor_title = 'FVOCI的基础设施基金买入卖出'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['公募REITS']
        account_category = ['FVOCI']
        pre_date = self.get_pre_date(biz_date)
        pre_account_data = self.dao.get_investment_account_data(pre_date, dimension, category, account_category)
        account_data = self.dao.get_investment_account_data(biz_date, dimension, category, account_category)
        return {'pre_data': pre_account_data, 'account_data': account_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        pre_data = data.get('pre_data', [])
        account_data = data.get('account_data', [])
        if not account_data:
            return []
        pre_asset_keys = set()
        pre_asset_map = {}
        if pre_data:
            for item in pre_data:
                code = item.get('zcdm', '').split('.')[0]
                pre_asset_keys.add(code)
                pre_asset_map[code] = item.get('jjztmc', code)
        cur_asset_keys = set()
        cur_asset_map = {}
        biz_date = ''
        if account_data:
            for item in account_data:
                code = item.get('zcdm', '').split('.')[0]
                cur_asset_keys.add(code)
                cur_asset_map[code] = item.get('jjztmc', code)
                if not biz_date:
                    biz_date = item.get('p_dt', '')
        added_assets = []
        removed_assets = []
        for code in cur_asset_keys - pre_asset_keys:
            added_assets.append(cur_asset_map.get(code, code))
        for code in pre_asset_keys - cur_asset_keys:
            removed_assets.append(pre_asset_map.get(code, code))
        result = []
        if added_assets or removed_assets:
            parts = []
            if added_assets:
                parts.append(f'''新增了{', '.join(added_assets)}''')
            if removed_assets:
                parts.append(f'''减少了{', '.join(removed_assets)}''')
            change_str = '、'.join(parts)
            alert_message = f'''{biz_date}，{change_str}的投资，须关注是否有告知'''
            result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': len(added_assets) + len(removed_assets), 'alert_level': 1})
        else:
            result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': f'''{biz_date},基础设施基金未发生买入/卖出''', 'indicator_value': 0, 'alert_level': 0})
        return result
