"""Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
from calendar import c
from monitors.monitor_base import MonitorBase
from dao.duration_dao import DurationDAO
from utils.date_utils import get_quarter_end, get_quarter_end_date
from config.settings import BASE_DATE
import pandas as pd
import json

class FixedIncomeScaleDurationMonitor(MonitorBase):

    def __init__(self):
        super().__init__()
        self.monitor_id = 'DR-EX-0001'
        self.monitor_title = '固收类资产规模久期目标监控'
        self.dao = DurationDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        month = int(biz_date.replace('-', '')[4:6])
        if month <= 3:
            return {'data': []}
        biz_date_formatted = biz_date.replace('-', '')
        last_quarter_end_date = get_quarter_end(biz_date_formatted)
        result = self.dao.get_fixed_income_scale_duration_data(last_quarter_end_date, monitor_id, dimension)
        return {'data': result}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        fixed_income_scale_duration = data.get('data', [])
        if not fixed_income_scale_duration:
            return []
        date = get_quarter_end_date(self.check_date)
        config = self.get_monitor_config(self.monitor_id)
        threshold = 1000
        if config.threshold:
            try:
                threshold_dict = json.loads(config.threshold)
                threshold = float(threshold_dict.get(date, 1000))
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                self.logger.warning(f'Failed to parse threshold JSON: {e}, using default value 1000')
                threshold = 1000
        fixed_income_scale_duration_df = pd.DataFrame(fixed_income_scale_duration)
        weighted_duration_sum = (fixed_income_scale_duration_df['jq'] * fixed_income_scale_duration_df['qjsz']).sum()
        if weighted_duration_sum > threshold:
            alert_message = f'加权久期总和为{weighted_duration_sum:.2f}亿，超过阈值{threshold}亿'
        else:
            alert_message = f'加权久期总和为{weighted_duration_sum:.2f}亿，未达到阈值{threshold}亿'
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': weighted_duration_sum, 'alert_level': 1 if weighted_duration_sum > threshold else 0}]
        return result

class FixedIncomeAssetBondDurationMonitor(MonitorBase):

    def __init__(self):
        super().__init__()
        self.monitor_id = 'DR-EX-0002'
        self.monitor_title = '固收类资产规模久期目标监控'
        self.dao = DurationDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        month = int(biz_date.replace('-', '')[4:6])
        if month <= 3:
            return {'data': []}
        biz_date_formatted = biz_date.replace('-', '')
        last_quarter_end_date = get_quarter_end(biz_date_formatted)
        category = ['政府债', '企业债', '金融债']
        curr_data = self.dao.get_fixed_income_asset_scale_duration_data(last_quarter_end_date, dimension, category)
        history_date = (kwargs.get('scope') or BASE_DATE).replace('-', '')
        prev_data = self.dao.get_fixed_income_asset_scale_duration_data(history_date, dimension, category)
        return {'cur_asset_data': curr_data, 'pre_asset_data': prev_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        pre_asset_data = data.get('pre_asset_data', [])
        cur_asset_data = data.get('cur_asset_data', [])
        if not pre_asset_data or not cur_asset_data:
            return []
        config = self.get_monitor_config(self.monitor_id)
        threshold = 25
        if config.threshold:
            try:
                threshold_dict = json.loads(config.threshold)
                biz_date_formatted = data.get('cur_asset_data', [{}])[0].get('p_dt', '').replace('-', '')
                threshold = float(threshold_dict.get(biz_date_formatted, 25))
            except (json.JSONDecodeError, ValueError, TypeError):
                try:
                    threshold = float(config.threshold)
                except (ValueError, TypeError):
                    threshold = 25
        pre_df = pd.DataFrame(pre_asset_data)
        cur_df = pd.DataFrame(cur_asset_data)
        pre_total_qjsz = pre_df['qjsz'].sum()
        cur_total_qjsz = cur_df['qjsz'].sum()
        change_value = cur_total_qjsz - pre_total_qjsz
        is_alert = 0
        if abs(change_value) > threshold:
            if change_value > 0:
                alert_message = f'增加金额为{change_value:.2f}亿元，超过阈值{threshold}亿元'
                is_alert = 1
            else:
                alert_message = f'减少金额为{abs(change_value):.2f}亿元，超过阈值{threshold}亿元'
                is_alert = 1
        else:
            alert_message = f'增减金额为{change_value:.2f}亿元，未达到阈值{threshold}亿元'
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': change_value, 'alert_level': is_alert}]
        return result

class FixedIncomeAssetDurationMonitor(MonitorBase):

    def __init__(self):
        super().__init__()
        self.monitor_id = 'DR-DEMO-0003'
        self.monitor_title = '固收类资产规模久期目标监控'
        self.dao = DurationDAO()

    def get_data(self, biz_date: str, monitor_id: str, dimension: str, **kwargs) -> dict:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_data = self.dao.get_asset_duration_data(biz_date, dimension)
        return {'asset_data': asset_data}

    def calculate(self, data: dict) -> list:
        """Generalized portfolio rule with synthetic defaults; configure limits for each use case."""
        asset_data = data.get('asset_data', [])
        if not asset_data:
            return []
        df_asset = pd.DataFrame(asset_data)
        weighted_duration = (df_asset['jq'] * df_asset['qjsz']).sum() / df_asset['qjsz'].sum()
        if weighted_duration > 5:
            alert_message = f'组合久期为{weighted_duration:.2f}年，超过阈值5年'
            is_alert = 1
        else:
            alert_message = f'组合久期为{weighted_duration:.2f}年，未达到阈值5年'
            is_alert = 0
        result = [{'portfolio_code': '0', 'portfolio_name': self.curr_dimension, 'alert_message': alert_message, 'indicator_value': weighted_duration, 'alert_level': is_alert}]
        return result
