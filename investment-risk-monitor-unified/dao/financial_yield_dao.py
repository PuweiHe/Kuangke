from db.query_adapter import query_all


class FinancialYieldDAO:
    """财务收益率数据访问对象"""

    def get_financial_return_dimension(self, date: str, dimension: str) -> list[dict]:
        """获取财务收益数据"""
        sql = """ select p_dt,ztbh,jjztmc,sum(cwsy_bn)/sum(pjzjzy_bn) as financial_yield_rate
        from position_snapshot
        where p_dt = %s
         and wstwd = %s
         and ztbh is not null
         group by ztbh,jjztmc,p_dt
         """
        params = [date, dimension]
        return query_all(sql, params)

    def get_financial_return_category(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按资产分类过滤）"""
        if not category:
            return []
        sql = (
            """ select p_dt,ztbh, jjztmc, cwsy_bn, pjzjzy_bn
        from position_snapshot
        where p_dt = %s
         and wstwd = %s
         and zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
         and ztbh is not null
         """
        )
        params = [date, dimension, *category]
        return query_all(sql, params)

    def get_financial_return_trust_strategy(
        self, date: str, dimension: str, category: list, trade_strategy: list
    ) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按分类与交易策略过滤）"""
        if not trade_strategy:
            return []
        if not category:
            return []
        sql = (
            """ select p_dt,ztbh,jjztmc,sum(cwsy_bn)/sum(pjzjzy_bn) as financial_yield_rate
            from position_snapshot
            where p_dt = %s
            and wstwd = %s
            and zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
            and jycl in ("""
            + ", ".join(["%s"] * len(trade_strategy))
            + """)
            and ztbh is not null
            group by ztbh,jjztmc,p_dt
         """
        )
        params = [date, dimension, *category, *trade_strategy]
        return query_all(sql, params)

    def get_financial_return_fixed(self, date: str, dimension: str, ztbh: list) -> list[dict]:
        """
        获取固定收益类专项委托户财务收益率
        表里面qjsz 存的数字是亿 把1000000 转换成亿为单位 1000000=1000000/100000000
        1000000/100000000=0.01
        """
        if not ztbh:
            return []
        sql = (
            """ select ztbh,jjztmc,sum(cwsy_bn)/sum(pjzjzy_bn) as financial_yield_rate
        from position_snapshot
        where p_dt = %s
         and wstwd = %s
         and ztbh in ("""
            + ", ".join(["%s"] * len(ztbh))
            + """)
         and qjsz > 0.01
         group by ztbh,jjztmc
         """
        )
        params = [date, dimension, *ztbh]
        return query_all(sql, params)

    def get_financial_return_ratio(
        self, date: str, dimension: str, category: str, trade_strategy: str
    ) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按分类与交易策略过滤）"""
        sql = """
        select a.ztbh, a.jjztmc, cwsy_bn, pjzjzy_bn from position_snapshot a
            inner join (select trade_date,account_set_id,asset_code from asset_position_tree_daily
                    where trade_date = %s
                    and strategy_plate = %s
                    and asset_level_two = %s) b
            on a.p_dt = b.trade_date
            and a.ztbh = account_set_id
            and a.zcdm = b.asset_code

            where a.wstwd = %s
         """
        params = [date, trade_strategy, category, dimension]
        return query_all(sql, params)

    def get_financial_return_ratio_liquidity(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按分类与交易策略过滤）"""
        if not category:
            return []
        sql = (
            """
        select a.ztbh, a.jjztmc, cwsy_bn, pjzjzy_bn from position_snapshot a
        inner join (select trade_date,account_set_id,asset_code from asset_position_tree_daily
        where trade_date = %s
          and asset_level_one in ("""
            + ", ".join(["%s"] * len(category))
            + """)) b
        on a.p_dt = b.trade_date
        and a.ztbh = account_set_id
        and a.zcdm = b.asset_code

        where a.wstwd = %s

         """
        )
        params = [date, *category, dimension]
        return query_all(sql, params)

    def get_investment_exclude_category_data(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按分类与交易策略过滤）"""
        if not category:
            return []
        sql = (
            """ select wstwd,sum(cwsy_bn) as financial_yield_x
        from position_snapshot
        where p_dt = %s
         and wstwd = %s
         and zcfl not in ("""
            + ", ".join(["%s"] * len(category))
            + """)
         group by wstwd
         """
        )
        params = [date, dimension, *category]
        return query_all(sql, params)

    def get_financial_return_dimension2(self, date: str, dimension: str) -> list[dict]:
        """获取财务收益数据"""
        sql = """ select wstwd,sum(cwsy_bn) as financial_yield_x,sum(pjzjzy_bn) as financial_yield_y
        from position_snapshot
        where p_dt = %s
         and wstwd = %s
         and ztbh is not null
         group by wstwd
         """
        params = [date, dimension]
        return query_all(sql, params)

    def get_account_yields(self, date, dimension, accounts, comprehensive=False):
        """Aggregate before any minimum-value gate; reject partial NULL inputs."""
        if not accounts:
            return []
        metric = "zhsy_bn" if comprehensive else "cwsy_bn"

        def complete_sum(column):
            return f"CASE WHEN COUNT({column}) = COUNT(*) THEN SUM({column}) ELSE NULL END"

        sql = (
            f"SELECT ztbh, MAX(jjztmc) AS jjztmc, {complete_sum('qjsz')} AS market_value, {complete_sum(metric)} AS earnings, {complete_sum('pjzjzy_bn')} AS capital FROM position_snapshot WHERE p_dt = %s AND wstwd = %s AND ztbh IN ("
            + ", ".join(["%s"] * len(accounts))
            + ") GROUP BY ztbh"
        )
        return query_all(sql, (date, dimension, *accounts))
