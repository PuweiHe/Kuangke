from core.holding_ratio import account_scope
"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from monitors.monitor_base import MonitorBase
from dao.financial_yield_dao import FinancialYieldDAO
from utils.calc_utils import CalcUtils

class AccountYieldMonitor(MonitorBase):
    """Configured accounts with aggregate-value eligibility and explicit missing data."""
    rule_id = ''
    title = ''
    comprehensive = False

    def __init__(self):
        super().__init__()
        self.monitor_id, self.monitor_title = self.rule_id, self.title
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date, monitor_id, dimension, **kwargs):
        accounts = account_scope(kwargs.get('scope'))
        if not accounts:
            raise ValueError('An explicit JSON account scope is required')
        return {'data': self.dao.get_account_yields(biz_date, dimension, accounts, self.comprehensive),
                'accounts': accounts}

    def calculate(self, data):
        from core.account_yield import evaluate_account_yields
        target = CalcUtils.parse_threshold(self.threshold)
        if target is None:
            raise ValueError('An explicit yield target is required')
        minimum = getattr(self.config, 'default_value', None)
        minimum = 0 if minimum is None or minimum == '' else float(minimum)
        return evaluate_account_yields(data['data'], data['accounts'], target, minimum, self.check_date)


class FixedIncomeSpecialAccountYieldMonitor(AccountYieldMonitor):
    rule_id, title = 'FY-IO-0001', 'Fixed income account financial yield'


class EquitySpecialAccountYieldMonitor(AccountYieldMonitor):
    rule_id, title = 'FY-IO-0002', 'Equity account comprehensive yield'
    comprehensive = True


class TrustPlanYieldTargetMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-IO-0003'
        self.monitor_title = '集合资金信托计划财务收益率目标'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['信托计划']
        return {'data': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        if not fetch_data:
            return []
        threshold_float = CalcUtils.parse_threshold(self.threshold)
        result = []
        for item in fetch_data:
            raw_yield = item.get('financial_yield_rate') or 0
            try:
                raw_yield = float(raw_yield)
            except (TypeError, ValueError):
                raw_yield = 0.0
            annualized = CalcUtils.annualize(raw_yield, self.check_date)
            annualized_str = f'{annualized * 100:.2f}%'
            threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
            is_below_threshold = threshold_float is not None and annualized < threshold_float
            if is_below_threshold:
                alert_message = f'集合资金信托计划年化财务收益率{annualized_str}，未达目标{threshold_str}'
            else:
                alert_message = f'集合资金信托计划年化财务收益率{annualized_str}，达到目标{threshold_str}'
            result.append({'portfolio_code': item['ztbh'], 'portfolio_name': item['jjztmc'], 'alert_message': alert_message, 'indicator_value': annualized, 'alert_level': is_below_threshold and 1 or 0})
        return result

class ABSYieldTargetMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-IO-0004'
        self.monitor_title = '资产证券化产品财务收益率目标'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['资产支持证券', '资产支持计划']
        return {'data': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        if not fetch_data:
            return []
        threshold_float = CalcUtils.parse_threshold(self.threshold)
        result = []
        for item in fetch_data:
            raw_yield = item.get('financial_yield_rate') or 0
            try:
                raw_yield = float(raw_yield)
            except (TypeError, ValueError):
                raw_yield = 0.0
            annualized = CalcUtils.annualize(raw_yield)
            annualized_str = f'{annualized * 100:.2f}%'
            threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
            if threshold_float is not None and annualized < threshold_float:
                alert_message = f'资产证券化产品年化财务收益率{annualized_str}，未达目标{threshold_str}'
            else:
                alert_message = f'资产证券化产品年化财务收益率{annualized_str}，达到目标{threshold_str}'
            result.append({'portfolio_code': item['ztbh'], 'portfolio_name': item['jjztmc'], 'alert_message': alert_message, 'indicator_value': annualized})
        return result

class WealthProductAnnualYieldTargetMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-IO-0005'
        self.monitor_title = '理财产品年化财务收益率目标'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        return {'data': []}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        if not fetch_data:
            return []
        threshold_float = CalcUtils.parse_threshold(self.threshold)
        result = []
        for item in fetch_data:
            raw_yield = item.get('financial_yield_rate') or 0
            try:
                raw_yield = float(raw_yield)
            except (TypeError, ValueError):
                raw_yield = 0.0
            annualized = CalcUtils.annualize(raw_yield)
            annualized_str = f'{annualized * 100:.2f}%'
            threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
            if threshold_float is not None and annualized < threshold_float:
                alert_message = f'理财产品年化财务收益率{annualized_str}，未达目标{threshold_str}'
            else:
                alert_message = f'理财产品年化财务收益率{annualized_str}，达到目标{threshold_str}'
            result.append({'portfolio_code': item['ztbh'], 'portfolio_name': item['jjztmc'], 'alert_message': alert_message, 'indicator_value': annualized})
        return result

class InfrastructureFundYieldTargetMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-IO-0006'
        self.monitor_title = '基础设施基金专项委托户财务收益率目标'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        _default_ztbh = account_scope(kwargs.get('scope'))
        if not _default_ztbh:
            raise ValueError('An explicit JSON account scope is required')
        financial_return_infra_data = self.dao.get_financial_return_fixed(biz_date, dimension, _default_ztbh)
        return {'data': financial_return_infra_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        threshold_float = CalcUtils.parse_threshold(self.threshold)
        result = []
        for item in fetch_data:
            raw_yield = item.get('financial_yield_rate') or 0
            try:
                raw_yield = float(raw_yield)
            except (TypeError, ValueError):
                raw_yield = 0.0
            annualized = CalcUtils.annualize(raw_yield, self.check_date)
            annualized_str = f'{annualized * 100:.2f}%'
            threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
            is_below_threshold = threshold_float is not None and annualized < threshold_float
            if is_below_threshold:
                alert_message = f'基础设施基金专项委托户年化财务收益率{annualized_str}，未达目标{threshold_str}'
            else:
                alert_message = f'基础设施基金专项委托户年化财务收益率{annualized_str}，达到目标{threshold_str}'
            result.append({'portfolio_code': item['ztbh'], 'portfolio_name': item['jjztmc'], 'alert_message': alert_message, 'indicator_value': annualized, 'alert_level': is_below_threshold and 1 or 0})
        return result

class DebtPlanYieldTargetMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-IO-0007'
        self.monitor_title = '债权计划财务收益率目标'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        _default_ztbh = account_scope(kwargs.get('scope'))
        if not _default_ztbh:
            raise ValueError('An explicit JSON account scope is required')
        financial_return_debt_data = self.dao.get_financial_return_fixed(biz_date, dimension, _default_ztbh)
        return {'data': financial_return_debt_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        threshold_float = CalcUtils.parse_threshold(self.threshold)
        result = []
        for item in fetch_data:
            raw_yield = item.get('financial_yield_rate') or 0
            try:
                raw_yield = float(raw_yield)
            except (TypeError, ValueError):
                raw_yield = 0.0
            annualized = CalcUtils.annualize(raw_yield, self.check_date)
            annualized_str = f'{annualized * 100:.2f}%'
            threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
            is_below_threshold = threshold_float is not None and annualized < threshold_float
            if is_below_threshold:
                alert_message = f'债权计划年化财务收益率{annualized_str}，未达目标{threshold_str}'
            else:
                alert_message = f'债权计划年化财务收益率{annualized_str}，达到目标{threshold_str}'
            result.append({'portfolio_code': item['ztbh'], 'portfolio_name': item['jjztmc'], 'alert_message': alert_message, 'indicator_value': annualized, 'alert_level': is_below_threshold and 1 or 0})
        return result
