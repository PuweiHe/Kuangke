"""
计算工具类
提供年化、百分比转换等通用计算静态方法，任何模块均可直接调用。
"""

from datetime import datetime
from typing import Optional, Union


class CalcUtils:
    """通用计算帮助类（纯静态方法，无需实例化）"""

    @staticmethod
    def annualize(value: float, ref_date: Optional[Union[str, datetime]] = None) -> float:
        """将累计值按本年已过天数年化。

        公式: annualized = value / 本年已过天数 * 365

        Args:
            value: 待年化的累计值（如本年累计收益率）
            ref_date: 参考日期，支持 YYYYMMDD 字符串或 datetime 对象；
                      为 None 时取当天

        Returns:
            float: 年化后的结果值
        """
        if ref_date is None:
            dt = datetime.now()
        elif isinstance(ref_date, str):
            dt = datetime.strptime(ref_date, "%Y%m%d")
        else:
            dt = ref_date

        year_start = datetime(dt.year, 1, 1)
        days_passed = (dt - year_start).days + 1  # 含当天

        if days_passed <= 0:
            return 0.0

        return value / days_passed * 365

    @staticmethod
    def parse_threshold(threshold_str: str) -> Optional[float]:
        """解析閘值字符串为小数。

        支持格式：'3%'、'3.00%'、'0.03'

        Args:
            threshold_str: 閘值字符串，如 '3%' 或 '0.03'

        Returns:
            float | None: 小数形式的閘值，解析失败时返回 None
        """
        if not threshold_str:
            return None
        s = threshold_str.strip()
        try:
            if s.endswith("%"):
                return float(s[:-1]) / 100
            return float(s)
        except ValueError:
            return None
