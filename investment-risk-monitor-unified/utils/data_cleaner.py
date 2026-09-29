"""
数据清洗模块

对原始查询数据进行清洗与标准化处理，
包括空值处理、类型转换、异常值过滤等。
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from utils.data_parser import DataParser


class DataCleaner:
    """数据清洗工具类"""

    # 金额字段列表（需要安全转换为 float）
    AMOUNT_FIELDS = ["holding_amount", "total_assets"]
    # 比例字段列表（0~1 之间的小数）
    RATIO_FIELDS = ["holding_ratio", "yield_rate"]

    @staticmethod
    def clean_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对行列表进行清洗：空值填充 + 类型转换

        Parameters
        ----------
        rows : list[dict]

        Returns
        -------
        list[dict]
            清洗后的行列表
        """
        defaults = {
            "holding_amount": 0.0,
            "holding_ratio": 0.0,
            "duration": 0.0,
            "yield_rate": 0.0,
            "rating": "",
            "is_blacklisted": 0,
            "is_whitelisted": 1,
            "province": "",
            "security_code": "",
            "security_name": "",
        }

        # 填充缺失值
        rows = DataParser.fill_missing_values(rows, defaults)

        # 类型转换
        for row in rows:
            for field in DataCleaner.AMOUNT_FIELDS:
                row[field] = DataParser.safe_float(row.get(field, 0))
            for field in DataCleaner.RATIO_FIELDS:
                row[field] = DataParser.safe_float(row.get(field, 0))

        return rows

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        对 DataFrame 进行清洗

        Parameters
        ----------
        df : pd.DataFrame

        Returns
        -------
        pd.DataFrame
        """
        # 列名标准化
        df = DataParser.normalize_column_names(df)

        # 金额字段：空值填充为 0
        for col in DataCleaner.AMOUNT_FIELDS:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(float)

        # 比例字段：空值填充为 0
        for col in DataCleaner.RATIO_FIELDS:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype(float)

        # 去除全空行
        df = df.dropna(how="all")

        return df

    @staticmethod
    def filter_outliers(
        rows: List[Dict[str, Any]],
        field: str,
        lower: Optional[float] = None,
        upper: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        过滤异常值

        Parameters
        ----------
        rows : list[dict]
        field : str
            过滤字段名
        lower : float, optional
            下界
        upper : float, optional
            上界

        Returns
        -------
        list[dict]
            过滤后的行列表
        """
        result = []
        for row in rows:
            value = DataParser.safe_float(row.get(field))
            if lower is not None and value < lower:
                continue
            if upper is not None and value > upper:
                continue
            result.append(row)
        return result
