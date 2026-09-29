"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
import pandas as pd
from monitors.monitor_base import MonitorBase
from dao.investment_amount_dao import InvestmentAmountDAO
from utils.calc_utils import CalcUtils

class BondInvestmentQuotaMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-IC-0001'
        self.monitor_title = '债券投资额度'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['公司债', '企业债', '政府债']
        data = self.dao.get_investment_category_data(biz_date, dimension, category)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = data.get('data', [])
        if not data:
            return []
        num_df = pd.DataFrame(data).groupby('ztbh').agg(total_value=('dirty_price_market_value', 'sum'), portfolio_name=('jjztmc', 'first'), dimension=('wstwd', 'first'))
        is_alter = 0

        def build_alert_message(row):
            if row['dimension'] == '委托示例机构己' and row['total_value'] > 25:
                is_alter = 1
                return f'''持仓总金额超过25亿，金额为{row['total_value']:.2f}亿'''
            elif row['dimension'] == '委托示例机构戊' and row['total_value'] > 15:
                is_alter = 1
                return f'''持仓总金额超过15亿，金额为{row['total_value']:.2f}亿'''
            else:
                return '持仓总金额未超过阈值'
        num_df['alert_message'] = num_df.apply(build_alert_message, axis=1)
        result = []
        for ztbh, row in num_df.iterrows():
            result.append({'portfolio_code': ztbh, 'portfolio_name': row['portfolio_name'], 'alert_message': row['alert_message'], 'indicator_value': row['total_value'], 'alert_level': is_alter})
        return result

class StockInvestmentQuotaMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-IC-0002'
        self.monitor_title = '股票投资额度'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = []
        category_one = ['股票', '长股投股票']
        data = self.dao.get_investment_mutil_category_data(biz_date, dimension, category, category_one)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = data.get('data', [])
        if not data:
            return []
        num_df = pd.DataFrame(data).groupby('ztbh').agg(total_value=('dirty_price_market_value', 'sum'), portfolio_name=('jjztmc', 'first'))
        is_alter = 0

        def build_alert_message(row):
            if row['total_value'] > 20:
                is_alter = 1
                return f'''持仓总金额超过20亿，金额为{row['total_value']:.2f}亿'''
            else:
                return '持仓总金额未超过阈值'
        num_df['alert_message'] = num_df.apply(build_alert_message, axis=1)
        result = []
        for ztbh, row in num_df.iterrows():
            result.append({'portfolio_code': ztbh, 'portfolio_name': row['portfolio_name'], 'alert_message': row['alert_message'], 'indicator_value': row['total_value'], 'alert_level': is_alter})
        return result
        pass

class MultiProductInfrastructureQuotaMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-IC-0003'
        self.monitor_title = '多种产品和基础设施投资额度'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['公募REITS']
        category_one = ['非标']
        data = self.dao.get_investment_mutil_category_data(biz_date, dimension, category, category_one)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = data.get('data', [])
        if not data:
            return []
        num_df = pd.DataFrame(data).groupby('ztbh').agg(total_value=('dirty_price_market_value', 'sum'), portfolio_name=('jjztmc', 'first'), dimension=('wstwd', 'first'))
        is_alter = 0

        def build_alert_message(row):
            if row['dimension'] == '委托示例机构己' and row['total_value'] > 18:
                is_alter = 1
                return f'''持仓总金额超过18亿，金额为{row['total_value']:.2f}亿'''
            elif row['dimension'] == '委托示例机构戊' and row['total_value'] > 12:
                is_alter = 1
                return f'''持仓总金额超过12亿，金额为{row['total_value']:.2f}亿'''
            else:
                return '持仓总金额未超过阈值'
        num_df['alert_message'] = num_df.apply(build_alert_message, axis=1)
        result = []
        for ztbh, row in num_df.iterrows():
            result.append({'portfolio_code': ztbh, 'portfolio_name': row['portfolio_name'], 'alert_message': row['alert_message'], 'indicator_value': row['total_value'], 'alert_level': is_alter})
        return result

class TotalInvestmentAmountMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-IC-0004'
        self.monitor_title = '投资总金额约束'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = self.dao.get_investment_dimension_data(biz_date, dimension)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = data.get('data', [])
        if not data:
            return []
        num_df = pd.DataFrame(data)
        total_value = num_df['dirty_price_market_value'].sum()
        threshold_float = CalcUtils.parse_threshold(self.threshold)
        amount_threshold = threshold_float if threshold_float is not None else 2
        if total_value > amount_threshold:
            alert_message = f'''持仓总金额超过{amount_threshold}亿美元，金额为{total_value:.2f}亿美元'''
            is_alter = 1
        else:
            alert_message = f'''持仓总金额未超过{amount_threshold}亿美元'''
            is_alter = 0
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': float(total_value), 'alert_level': is_alter}]
        return result

class SingleBondInvestmentAmountMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-IC-0005'
        self.monitor_title = '单只债券投资金额'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['公司债', '企业债', '政府债']
        data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = data.get('data', [])
        if not data:
            return []
        threshold = self.threshold if self.threshold else 8
        df = pd.DataFrame(data)
        exceeded_df = df[df['dirty_price_market_value'] > threshold]
        result = []
        if not exceeded_df.empty:
            bond_name_str = ', '.join(exceeded_df['bond_name'].dropna())
            total_amount = exceeded_df['dirty_price_market_value'].sum()
            alert_message = f'''{bond_name_str}债券投资金额超过（含）{threshold}亿元，总金额为{total_amount:.2f}亿'''
            alert_level = 1
            indicator_value = float(total_amount)
        else:
            alert_message = f'''单只债券投资金额均未超过阈值{threshold}亿元'''
            alert_level = 0
            indicator_value = 0
        result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': indicator_value, 'alert_level': alert_level})
        return result

class SingleStockInvestmentAmountMonitor(MonitorBase):
    """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""

    def __init__(self):
        super().__init__()
        self.monitor_id = 'IA-IC-0006'
        self.monitor_title = '单只股票投资金额'
        self.dao = InvestmentAmountDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        category = ['股票', '长股投股票']
        data = self.dao.get_investment_category_detail_data(biz_date, dimension, category)
        return {'data': data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        data = data.get('data', [])
        if not data:
            return []
        df = pd.DataFrame(data)
        threshold = self.threshold if self.threshold else 4
        exceeded_df = df[df['dirty_price_market_value'] > threshold]
        result = []
        if not exceeded_df.empty:
            stock_name_str = ', '.join(exceeded_df['jjztmc'].dropna())
            total_amount = exceeded_df['dirty_price_market_value'].sum()
            alert_message = f'''{stock_name_str}股票投资金额超过{threshold}亿元，总金额为{total_amount:.2f}亿'''
            alert_level = 1
            indicator_value = float(total_amount)
        else:
            alert_message = f'''单只股票投资金额均未超过阈值{threshold}亿元'''
            alert_level = 0
            indicator_value = 0
        result.append({'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': indicator_value, 'alert_level': alert_level})
        return result
