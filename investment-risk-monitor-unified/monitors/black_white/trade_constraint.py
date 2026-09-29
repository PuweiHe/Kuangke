"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from re import L
from monitors.monitor_base import MonitorBase
from dao.blac_white_dao import BlackWhiteDAO
from utils.date_utils import getYear
import pandas as pd

class TradeCounterpartyConstraint(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'BW-TC-0001'
        self.monitor_title = '交易对手/担保主体约束监控'
        self.dao = BlackWhiteDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_datas = self.dao.get_trade_counterparty_data(biz_date, dimension)
        asset_codes = [item['zcdm'] for item in asset_datas if item is not None]
        asset_codes = list(set(asset_codes))
        year = getYear(biz_date)
        blacklist = self.dao.get_trade_counterparty_blacklist(year)
        bond_guarangor = self.dao.get_guarantor_data(biz_date, asset_codes)
        return {'asset_datas': asset_datas, 'counterparty': blacklist, 'guarantor': bond_guarangor}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        mnt_result = {'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': '', 'indicator_value': '', 'alert_level': 0}
        asset_datas = data.get('asset_datas')
        guarantor = data.get('guarantor')
        if not guarantor or not asset_datas:
            mnt_result['alert_message'] = '无数据'
            return [mnt_result]
        asset_df = pd.DataFrame(asset_datas)
        guarantor_df = pd.DataFrame(guarantor)
        merged_df = pd.merge(asset_df, guarantor_df, left_on='zcdm', right_on='bond_code', how='left')
        blacklist = data.get('counterparty')
        white_name_list = [item['bk_name'] for item in blacklist if item is not None]
        if len(white_name_list) > 0:
            merged_df = merged_df[merged_df['issuer_name'].isin(white_name_list) == False]
        if not merged_df.empty:
            msg = ''
            for _, row in merged_df.iterrows():
                msg += f'''{row['zcmc']}的交易对手为{row['issuer_name']}、'''
            mnt_result['alert_message'] = f'''{msg}，未在交易对手白名单内'''
        else:
            mnt_result['alert_message'] = '所有持仓债券的交易对手均在白名单内'
        return [mnt_result]
