"""Account-scoped holding rules and retained domain ratio monitors."""
from monitors.monitor_base import MonitorBase
from dao.investment_ratio_dao import InvestmentRatioDAO
from utils.calc_utils import CalcUtils
from core.holding_ratio import account_scope, evaluate_ratios
import pandas as pd


class HoldingScaleRatioMonitor(MonitorBase):
    """Share account completeness and threshold handling across four rules."""
    rule_id = ''
    title = ''
    categories = ()
    excluded_numerator = False
    absolute_denominator = False
    repo_gate = False
    tree_category = False
    default_threshold = 1.0

    def __init__(self):
        super().__init__()
        self.monitor_id = self.rule_id
        self.monitor_title = self.title
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date, monitor_id, dimension, **kwargs):
        expected = account_scope(kwargs.get('scope'))
        numerator = self.dao.get_ratio_positions(
            biz_date, dimension, self.categories, expected,
            exclude=self.excluded_numerator, tree_category=self.tree_category)
        denominator = self.dao.get_ratio_positions(
            biz_date, dimension, ['其他'], expected, exclude=True,
            absolute=self.absolute_denominator)
        # With no explicit scope, derive the universe from the entire snapshot.
        accounts = expected if expected is not None else self.dao.get_ratio_accounts(biz_date, dimension)
        repo = self.dao.get_repo_balances(biz_date, dimension, accounts) if self.repo_gate else None
        return dict(data_numerator=numerator, data_denominator=denominator,
                    expected=accounts, repo=repo)

    def calculate(self, data):
        raw = self.threshold
        threshold = self.default_threshold if raw is None or raw == '' else CalcUtils.parse_threshold(raw)
        if threshold is None:
            raise ValueError('Invalid ratio threshold')
        return evaluate_ratios(data.get('data_numerator', []), data.get('data_denominator', []),
                               threshold, data.get('expected'), data.get('repo'))


class BondHoldingScaleRatioMonitor(HoldingScaleRatioMonitor):
    rule_id, title = 'IR-RC-0001', 'Bond holding ratio'
    categories = ('正回购', '其他')
    excluded_numerator = True
    default_threshold = 1.5


class StockHoldingScaleRatioMonitor(HoldingScaleRatioMonitor):
    rule_id, title = 'IR-RC-0002', 'Stock holding ratio'
    categories = ('股票', '长股投股票')


class FinancialProductHoldingScaleRatioMonitor(HoldingScaleRatioMonitor):
    rule_id, title = 'IR-RC-0003', 'Financial product holding ratio'
    categories = ('非标类',)
    tree_category = True
    absolute_denominator = True
    repo_gate = True


class InfrastructureFundHoldingScaleRatioMonitor(HoldingScaleRatioMonitor):
    rule_id, title = 'IR-RC-0004', 'Infrastructure fund holding ratio'
    categories = ('公募REITS',)
    absolute_denominator = True
    repo_gate = True


class BondEntrustedInvestmentRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-RC-0005'
        self.monitor_title = '债券委托投资资金占比'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category_numerator = ['金融债', '企业债', '政府债']
        data_numerator = self.dao.get_investment_category_data(biz_date, dimension, category_numerator)
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
        num_df = pd.DataFrame(data_numerator)
        total_num_value = num_df['dirty_price_market_value'].sum()
        total_num_value = float(total_num_value)
        ratio = total_num_value / denom_value if denom_value != 0 else 0.0
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.08
        threshold_str = f'''{threshold_float * 100:.2f}%''' if threshold_float is not None else self.threshold
        is_alert = ratio > threshold_float
        if is_alert:
            alert_message = f'''债券委托投资资金占我司上季末总资产比例{ratio * 100:.2f}%，超过{threshold_str}'''
        else:
            alert_message = f'''债券委托投资资金占我司上季末总资产比例{ratio * 100:.2f}%，未超过{threshold_str}'''
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': float(ratio), 'alert_level': 1 if is_alert else 0}]
        return result

class StockEntrustedInvestmentRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-RC-0006'
        self.monitor_title = '股票委托投资资金占比'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category_numerator = ['股票', '长股投股票']
        data_numerator = self.dao.get_investment_category_data(biz_date, dimension, category_numerator)
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
        num_df = pd.DataFrame(data_numerator)
        total_num_value = num_df['dirty_price_market_value'].sum()
        total_num_value = float(total_num_value)
        ratio = total_num_value / denom_value if denom_value != 0 else 0.0
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.06
        threshold_str = f'''{threshold_float * 100:.2f}%''' if threshold_float is not None else self.threshold
        is_alert = ratio > threshold_float
        if is_alert:
            alert_message = f'''股票委托投资资金占我司上季末总资产比例{ratio * 100:.2f}%，超过{threshold_str}'''
        else:
            alert_message = f'''股票委托投资资金占我司上季末总资产比例{ratio * 100:.2f}%，未超过{threshold_str}'''
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': float(ratio), 'alert_level': 1 if is_alert else 0}]
        return result

class FinancialProductInvestmentRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-RC-0007'
        self.monitor_title = '金融产品投资资金占比'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category_numerator = ['非标类']
        data_numerator = self.dao.get_investment_category_data_new(biz_date, dimension, category_numerator)
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
        num_df = pd.DataFrame(data_numerator)
        total_num_value = num_df['dirty_price_market_value'].sum()
        total_num_value = float(total_num_value)
        ratio = total_num_value / denom_value if denom_value != 0 else 0.0
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.03
        threshold_str = f'''{threshold_float * 100:.2f}%''' if threshold_float is not None else self.threshold
        is_alert = ratio > threshold_float
        if is_alert:
            alert_message = f'''金融产品投资资金占我司上季末总资产比例{ratio * 100:.2f}%，超过{threshold_str}'''
        else:
            alert_message = f'''金融产品投资资金占我司上季末总资产比例{ratio * 100:.2f}%，未超过{threshold_str}'''
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': float(ratio), 'alert_level': 1 if is_alert else 0}]
        return result

class InfrastructureFundInvestmentRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-RC-0008'
        self.monitor_title = '基础设施投资基金占比'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category_numerator = ['公募REITS']
        data_numerator = self.dao.get_investment_category_data(biz_date, dimension, category_numerator)
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
        num_df = pd.DataFrame(data_numerator)
        total_num_value = num_df['dirty_price_market_value'].sum()
        total_num_value = float(total_num_value)
        ratio = total_num_value / denom_value if denom_value != 0 else 0.0
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.03
        threshold_str = f'''{threshold_float * 100:.2f}%''' if threshold_float is not None else self.threshold
        is_alert = ratio > threshold_float
        if is_alert:
            alert_message = f'''基础设施基金委托投资资金占我司上季末总资产比例{ratio * 100:.2f}%，超过{threshold_str}'''
        else:
            alert_message = f'''基础设施基金委托投资资金占我司上季末总资产比例{ratio * 100:.2f}%，未超过{threshold_str}'''
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': float(ratio), 'alert_level': 1 if is_alert else 0}]
        return result

class AccountLeverageRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-RC-0009'
        self.monitor_title = '账户杠杆率'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        investment_dimension_data = self.dao.get_investment_dimension_data(biz_date, dimension)
        asset_codes = [item['zcdm'] for item in investment_dimension_data if item is not None]
        valuation_data = self.dao.get_valuation_data(biz_date, asset_codes)
        return {'data': investment_dimension_data, 'valuation_data': valuation_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        valuation_data = data.get('valuation_data', [])
        if not valuation_data:
            return []
        total_asset = sum((v['asset'] for v in valuation_data))
        total_liability = sum((v['liability'] for v in valuation_data))
        if total_asset == 0:
            return []
        leverage_ratio = (total_asset - total_liability) / total_asset
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 1.5
        threshold_str = f'''{threshold_float * 100:.2f}%''' if threshold_float is not None and threshold_float > 1.5 else self.threshold
        is_alert = leverage_ratio > threshold_float
        leverage_pct = f'''{leverage_ratio * 100:.2f}%'''
        if is_alert:
            alert_msg = f'''账户杠杆率{leverage_pct}，超过{threshold_str}'''
        else:
            alert_msg = f'''账户杠杆率{leverage_pct}，未超过{threshold_str}'''
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_msg, 'indicator_value': float(leverage_ratio), 'alert_level': 1 if is_alert else 0}]
        return result

class AssetClassInvestmentRatioMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IR-RC-0010'
        self.monitor_title = '权益类、固收类、另类资产投资比例'
        self.dao = InvestmentRatioDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['正回购']
        data_numerator = self.dao.get_investment_category_data(biz_date, dimension, category)
        return {'data_numerator': data_numerator}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data_numerator = data.get('data_numerator', [])
        if not data_numerator:
            return []
        df = pd.DataFrame(data_numerator)
        result = []
        dirty_price_value = 0
        for _, row in df.iterrows():
            if row.get('dirty_price_market_value', 0) > 0:
                dirty_price_value += 1
        if dirty_price_value != 0:
            alert_msg = f'''委托账户内的权益类资产、固定收益类资产和另类投资资产投资比例合计超过资产净值的100%，为{dirty_price_value:.2f}%'''
        else:
            alert_msg = f'''委托账户内的权益类资产、固定收益类资产和另类投资资产投资比例合计不超过资产净值的100%'''
        result = [{'portfolio_code': row.get('ztbh', ''), 'portfolio_name': row.get('jjztmc', ''), 'alert_message': alert_msg, 'indicator_value': dirty_price_value, 'alert_level': 1 if dirty_price_value != 0 else 0}]
        return result
