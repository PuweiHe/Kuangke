"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from math import log
from monitors.monitor_base import MonitorBase
from dao.financial_yield_dao import FinancialYieldDAO
from utils.calc_utils import CalcUtils
import pandas as pd

class FixedIncomeYieldMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-RO-0001'
        self.monitor_title = '固收类财务收益率监控'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category_lv2 = '债券类'
        trade_strategy = '交易盘'
        data = self.dao.get_financial_return_ratio(biz_date, dimension, category_lv2, trade_strategy)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        if not fetch_data:
            return []
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.02
        result = []
        fin_df = pd.DataFrame(fetch_data)
        has_raw_data = 'cwsy_bn' in fin_df.columns and 'pjzjzy_bn' in fin_df.columns
        if has_raw_data:
            total_cwsy = fin_df['cwsy_bn'].sum()
            total_pjzjzy = fin_df['pjzjzy_bn'].sum()
            if total_pjzjzy != 0:
                raw_yield = total_cwsy / total_pjzjzy
            else:
                raw_yield = 0.0
        else:
            raw_yield = 0.0
        try:
            raw_yield = float(raw_yield)
        except (TypeError, ValueError):
            raw_yield = 0.0
        annualized = CalcUtils.annualize(raw_yield, self.check_date)
        annualized_str = f'{annualized * 100:.2f}%'
        threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
        is_below_threshold = threshold_float is not None and annualized < threshold_float
        if is_below_threshold:
            alert_message = f'固收类交易盘今年以来财务收益率为{annualized_str}，未达收益目标{threshold_str}'
        else:
            alert_message = f'固收类交易盘今年以来财务收益率为{annualized_str}，达到收益目标{threshold_str}'
        result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': annualized, 'alert_level': 1 if is_below_threshold else 0})
        return result

class FixedIncomeNonStdLiquidityYieldMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-RO-0002'
        self.monitor_title = '固收类、非标类、流动性及其他财务收益率监控'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category_lv1 = ['固收类', '流动性及其他类']
        data = self.dao.get_financial_return_ratio_liquidity(biz_date, dimension, category_lv1)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        if not fetch_data:
            return []
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.03
        result = []
        fin_df = pd.DataFrame(fetch_data)
        has_raw_data = 'cwsy_bn' in fin_df.columns and 'pjzjzy_bn' in fin_df.columns
        if has_raw_data:
            total_cwsy = fin_df['cwsy_bn'].sum()
            total_pjzjzy = fin_df['pjzjzy_bn'].sum()
            if total_pjzjzy != 0:
                raw_yield = total_cwsy / total_pjzjzy
            else:
                raw_yield = 0.0
        else:
            raw_yield = 0.0
        try:
            raw_yield = float(raw_yield)
        except (TypeError, ValueError):
            raw_yield = 0.0
        annualized = CalcUtils.annualize(raw_yield, self.check_date)
        annualized_str = f'{annualized * 100:.2f}%'
        threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
        is_below_threshold = threshold_float is not None and annualized < threshold_float
        if is_below_threshold:
            alert_message = f'固收类资产、非标类资产、流动性及其他合计收益目标：合计的新准则财务收益率为{annualized_str}，未达目标{threshold_str}'
        else:
            alert_message = f'固收类资产、非标类资产、流动性及其他合计收益目标：合计的新准则财务收益率为{annualized_str}，达到目标{threshold_str}'
        result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': annualized, 'alert_level': 1 if is_below_threshold else 0})
        return result

class StockYieldMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-RO-0003'
        self.monitor_title = '股票类财务收益率监控'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['股票']
        data = self.dao.get_financial_return_category(biz_date, dimension, category)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data', [])
        if not fetch_data:
            return []
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.06
        result = []
        fin_df = pd.DataFrame(fetch_data)
        has_raw_data = 'cwsy_bn' in fin_df.columns and 'pjzjzy_bn' in fin_df.columns
        if has_raw_data:
            total_cwsy = fin_df['cwsy_bn'].sum()
            total_pjzjzy = fin_df['pjzjzy_bn'].sum()
            if total_pjzjzy != 0:
                raw_yield = total_cwsy / total_pjzjzy
            else:
                raw_yield = 0.0
        else:
            raw_yield = 0.0
        try:
            raw_yield = float(raw_yield)
        except (TypeError, ValueError):
            raw_yield = 0.0
        annualized = CalcUtils.annualize(raw_yield, self.check_date)
        annualized_str = f'{annualized * 100:.2f}%'
        threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
        is_below_threshold = threshold_float is not None and annualized < threshold_float
        if is_below_threshold:
            alert_message = f'股票类资产今年以来财务收益率为{annualized_str}，未达收益目标{threshold_str}'
        else:
            alert_message = f'股票类资产今年以来财务收益率为{annualized_str}，达到收益目标{threshold_str}'
        result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': annualized, 'alert_level': 1 if is_below_threshold else 0})
        return result

class FinancialYieldMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'FY-RO-0004'
        self.monitor_title = '财务收益率监控'
        self.dao = FinancialYieldDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category_numerator = ['正回购', '其他']
        data_numerator = self.dao.get_investment_exclude_category_data(biz_date, dimension, category_numerator)
        data_denominator = self.dao.get_financial_return_dimension2(biz_date, dimension)
        return {'data_numerator': data_numerator, 'data_denominator': data_denominator}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fetch_data = data.get('data_numerator', [])
        fetch_data_denominator = data.get('data_denominator', [])
        if not fetch_data or not fetch_data_denominator:
            return []
        df_numerator = pd.DataFrame(fetch_data)
        df_denominator = pd.DataFrame(fetch_data_denominator)
        yield_ratio_x = df_numerator['financial_yield_x'].sum()
        yield_ratio_y = df_denominator['financial_yield_y'].sum()
        yield_ratio = 0
        if yield_ratio_y != 0:
            yield_ratio = yield_ratio_x / yield_ratio_y
        threshold_float = CalcUtils.parse_threshold(self.threshold) or 0.04
        result = []
        annualized = CalcUtils.annualize(yield_ratio, self.check_date)
        annualized_str = f'{annualized * 100:.2f}%'
        threshold_str = f'{threshold_float * 100:.2f}%' if threshold_float is not None else self.threshold
        is_below_threshold = threshold_float is not None and annualized < threshold_float
        if is_below_threshold:
            alert_message = f'股票类资产今年以来财务收益率为{annualized_str}，未达收益目栙{threshold_str}'
        else:
            alert_message = f'股票类资产今年以来财务收益率为{annualized_str}，达到收益目栙{threshold_str}'
        result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': annualized, 'alert_level': is_below_threshold and 1 or 0})
        return result
