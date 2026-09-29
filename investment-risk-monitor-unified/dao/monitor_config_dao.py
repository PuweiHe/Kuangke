"""
规则数据访问对象

封装监控规则的数据库查询与持久化操作，
包括规则配置查询、规则版本管理、规则结果存储等。
"""
from typing import Any, Dict, List, Optional
from models.monitor_rule_config import MonitorRuleConfig
import pandas as pd
from db.query_adapter import query_all, query_one
from loguru import logger

class MonitorConfigDAO:
    """规则数据访问对象"""

    def get_snapshot_count(self, biz_date: str) -> int:
        """Return the number of source positions available for one date."""
        row = query_one('SELECT COUNT(*) AS row_count FROM position_snapshot WHERE p_dt = %s', (biz_date,))
        return int(row['row_count']) if row else 0

    def get_monitor_config_by(self, monitor_id: str, dimension: str) -> list:
        """
        根据监控ID和维度查询监控配置

        Returns
        -------
        list[MonitorRuleConfig]
            监控配置列表（MonitorRuleConfig对象格式）
        """
        sql = '\n            SELECT *\n            FROM risk_rule_config \n            WHERE is_enabled = 1\n              AND monitor_id = %s\n              AND dimension_code = %s\n        '
        results = query_all(sql, (monitor_id, dimension))
        return [MonitorRuleConfig.from_dict(r) for r in results]

    def get_monitor_config_by_id(self, monitor_id: str):
        """
        根据监控ID查询监控配置

        Returns
        -------
        dict or None
            监控配置（字典格式），如果不存在则返回 None
        """
        sql = '\n            SELECT *\n            FROM risk_rule_config \n            WHERE is_enabled = 1\n              AND monitor_id = %s\n        '
        result = query_one(sql, (monitor_id,))
        if result:
            return MonitorRuleConfig.from_dict(result)
        return None

    def get_monitor_configs(self) -> list:
        """
        获取所有监控配置

        Returns
        -------
        list[MonitorRuleConfig]
            监控配置列表（MonitorRuleConfig对象）
        """
        sql = '\n            SELECT *\n            FROM risk_rule_config \n            WHERE is_enabled = 1\n        '
        results = query_all(sql)
        return [MonitorRuleConfig.from_dict(r) for r in results]

    def get_trust_dimension_by_monitor_id(self, monitor_id: str) -> list:
        """
        根据监控ID查询受托维度
        Returns
        -------
        list[dict]
            受托维度列表（字典格式）
        """
        sql = '\n            SELECT dimension_code, trust_dimension\n            FROM risk_dimension_config\n            WHERE monitor_id = %s\n        '
        return query_all(sql, (monitor_id,))

    def get_trust_dimension_config(self, monitor_id: str=None, dimension: str=None) -> list:
        """
        根据监控ID查询受托维度
        Returns
        -------
        list[MonitorRuleConfig]
            受托维度列表（MonitorRuleConfig对象格式）
        """
        sql = '\n            select a.monitor_id,a.dimension_code,a.trust_dimension,b.monitor_type,b.monitor_type_2nd,b.monitor_type_3rd,\n            b.monitor_item,b.monitor_title,b.alert_level,b.requirements,b.filter_logic,b.indicator,b.operator,\n            b.threshold,b.alert_content,b.normal_content,b.scope,b.default_value,b.max_value,b.is_enabled\n            from risk_dimension_config a\n            left join risk_rule_config b on a.monitor_id = b.monitor_id\n            where \n              b.is_enabled = 1\n        '
        params = []
        if monitor_id:
            sql += ' and a.monitor_id = %s'
            params.append(monitor_id)
        if dimension:
            sql += ' and a.dimension_code = %s'
            params.append(dimension)
        results = query_all(sql, tuple(params))
        return [MonitorRuleConfig.from_dict(r) for r in results]

    def save_monitor_results(self, results: list) -> int:
        """Persist results with an upsert supported by the selected database."""
        if not results:
            return 0
        from config.settings import DB_TYPE
        from db.factory import get_pool
        columns = 'portfolio_code, portfolio_name, monitor_id, monitor_name, monitor_category, dimension_code, trust_dimension, monitor_item, check_date, indicator_value, alert_level, alert_message'
        values_sql = '(' + ', '.join(['%s'] * 12) + ')'
        update_columns = ('portfolio_name', 'monitor_name', 'monitor_category', 'dimension_code', 'monitor_item', 'indicator_value', 'alert_level', 'alert_message')
        if DB_TYPE == 'mysql':
            updates = ', '.join((f'{name} = VALUES({name})' for name in update_columns))
            upsert = f'ON DUPLICATE KEY UPDATE {updates}'
        else:
            updates = ', '.join((f'{name} = EXCLUDED.{name}' for name in update_columns))
            upsert = f'ON CONFLICT (monitor_id, check_date, portfolio_code, trust_dimension) DO UPDATE SET {updates}'
        sql = f'INSERT INTO risk_monitor_result ({columns}) VALUES {values_sql} {upsert}'
        values = [(result.portfolio_code, result.portfolio_name, result.monitor_id, result.monitor_title, result.monitor_category, result.dimension_code, result.trust_dimension, result.monitor_item, result.check_date, str(result.indicator_value) if result.indicator_value is not None else None, result.alert_level, result.alert_message) for result in results]
        with get_pool().connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(sql, values)
            conn.commit()
        logger.info(f'Saved {len(values)} monitoring results')
        return len(values)
