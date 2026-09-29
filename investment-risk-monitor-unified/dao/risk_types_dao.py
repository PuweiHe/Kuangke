"""
风险类型数据访问对象

提供通用的日期查询和数据访问功能
"""

from db.query_adapter import query_one


class RiskTypesDAO:
    """
    风险类型数据访问对象

    提供通用的日期查询和数据访问功能
    """

    def get_pre_date(self, biz_date: str) -> str:
        """
        查询指定日期的前一天日期

        Parameters
        ----------
        biz_date : str
            业务日期，格式: YYYY-MM-DD

        Returns
        -------
        str
            前一天的日期，格式: YYYY-MM-DD
        """
        sql = """
            SELECT MAX(p_dt) AS pre_date
            FROM position_snapshot
            WHERE p_dt < %s
        """
        result = query_one(sql, (biz_date,))
        return result["pre_date"] if result else None
