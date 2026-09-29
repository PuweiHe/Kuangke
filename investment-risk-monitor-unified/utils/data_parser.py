"""
数据解析模块

将原始查询结果解析为标准化的数据结构，
支持类型转换、缺失值填充、列名标准化等。
"""

from typing import Any, Dict, List, Optional

import pandas as pd


class DataParser:
    """数据解析工具类"""

    @staticmethod
    def parse_rows_to_dict(rows: List[Dict[str, Any]], key_column: str = "security_code") -> Dict[str, Dict[str, Any]]:
        """
        将行列表转换为以 key_column 为键的字典映射

        Parameters
        ----------
        rows : list[dict]
            查询结果行
        key_column : str
            用作字典键的列名，默认 security_code

        Returns
        -------
        dict
            key_column_value -> row_dict
        """
        result = {}
        for row in rows:
            key = row.get(key_column, "")
            if key:
                result[key] = row
        return result

    @staticmethod
    def safe_float(value: Any, default: float = 0.0) -> float:
        """
        安全地将值转换为浮点数

        Parameters
        ----------
        value : Any
            原始值
        default : float
            转换失败时的默认值

        Returns
        -------
        float
        """
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_int(value: Any, default: int = 0) -> int:
        """
        安全地将值转换为整数

        Parameters
        ----------
        value : Any
            原始值
        default : int
            转换失败时的默认值

        Returns
        -------
        int
        """
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """
        将 DataFrame 列名标准化为小写+下划线格式

        Parameters
        ----------
        df : pd.DataFrame

        Returns
        -------
        pd.DataFrame
        """
        df.columns = [
            col.strip().lower().replace(" ", "_").replace("-", "_")
            for col in df.columns
        ]
        return df

    @staticmethod
    def fill_missing_values(rows: List[Dict[str, Any]], defaults: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        为缺失字段填充默认值

        Parameters
        ----------
        rows : list[dict]
        defaults : dict
            列名 -> 默认值

        Returns
        -------
        list[dict]
        """
        for row in rows:
            for col, default_val in defaults.items():
                if col not in row or row[col] is None:
                    row[col] = default_val
        return rows
