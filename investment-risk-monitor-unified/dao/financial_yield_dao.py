from db.query_adapter import query_all, query_one

class FinancialYieldDAO:
    """财务收益率数据访问对象"""

    def get_financial_return_dimension(self, date: str, dimension: str) -> list[dict]:
        """获取财务收益数据"""
        sql = f""" select p_dt,ztbh,jjztmc,sum(cwsy_bn)/sum(pjzjzy_bn) as financial_yield_rate \n        from position_snapshot \n        where p_dt = '{date}' \n         and wstwd = '{dimension}'\n         and ztbh is not null \n         group by ztbh,jjztmc,p_dt\n         """
        return query_all(sql)

    def get_financial_return_category(self, date: str, dimension: str, category: list) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按资产分类过滤）"""
        sql = f""" select p_dt,ztbh, jjztmc, cwsy_bn, pjzjzy_bn\n        from position_snapshot \n        where p_dt = '{date}' \n         and wstwd = '{dimension}' \n         and zcfl in ({','.join((f"'{cat}'" for cat in category))}) \n         and ztbh is not null\n         """
        return query_all(sql)

    def get_financial_return_trust_strategy(self, date: str, dimension: str, category: list, trade_strategy: list) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按分类与交易策略过滤）"""
        sql = f""" select p_dt,ztbh,jjztmc,sum(cwsy_bn)/sum(pjzjzy_bn) as financial_yield_rate \n            from position_snapshot \n            where p_dt = '{date}' \n            and wstwd = '{dimension}'\n            and zcfl in ({','.join((f"'{cat}'" for cat in category))}) \n            and jycl in ({','.join((f"'{trade}'" for trade in trade_strategy))})\n            and ztbh is not null\n            group by ztbh,jjztmc,p_dt\n         """
        return query_all(sql)

    def get_financial_return_fixed(self, date: str, dimension: str, ztbh: list) -> list[dict]:
        """
            获取固定收益类专项委托户财务收益率
            表里面qjsz 存的数字是亿 把1000000 转换成亿为单位 1000000=1000000/100000000
            1000000/100000000=0.01
        """
        sql = f""" select ztbh,jjztmc,sum(cwsy_bn)/sum(pjzjzy_bn) as financial_yield_rate \n        from position_snapshot \n        where p_dt = '{date}' \n         and wstwd = '{dimension}' \n         and ztbh in ({','.join((f"'{ztbh}'" for ztbh in ztbh))}) \n         and qjsz > 0.01\n         group by ztbh,jjztmc\n         """
        return query_all(sql)

    def get_financial_return_ratio(self, date: str, dimension: str, category: str, trade_strategy: str) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按分类与交易策略过滤）"""
        sql = f""" \n        select a.ztbh, a.jjztmc, cwsy_bn, pjzjzy_bn from position_snapshot a\n            inner join (select trade_date,account_set_id,asset_code from asset_position_tree_daily\n                    where trade_date = '{date}'\n                    and strategy_plate = '{trade_strategy}'\n                    and asset_level_two = '{category}') b\n            on a.p_dt = b.trade_date\n            and a.ztbh = account_set_id\n            and a.zcdm = b.asset_code\n\n            where a.wstwd = '{dimension}'\n         """
        return query_all(sql)

    def get_financial_return_ratio_liquidity(self, date: str, dimension: str, category: list) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按分类与交易策略过滤）"""
        category_str = ','.join([f"""'{c}'""" for c in category])
        sql = f""" \n        select a.ztbh, a.jjztmc, cwsy_bn, pjzjzy_bn from position_snapshot a\n        inner join (select trade_date,account_set_id,asset_code from asset_position_tree_daily\n        where trade_date = '{date}'\n          and asset_level_one in ({category_str})) b\n        on a.p_dt = b.trade_date\n        and a.ztbh = account_set_id\n        and a.zcdm = b.asset_code\n\n        where a.wstwd = '{dimension}'\n        \n         """
        return query_all(sql)

    def get_investment_exclude_category_data(self, date: str, dimension: str, category: list) -> list[dict]:
        """获取财务收益数据（分子为 cwsy_bn 财务收益，按分类与交易策略过滤）"""
        sql = f""" select wstwd,sum(cwsy_bn) as financial_yield_x\n        from position_snapshot \n        where p_dt = '{date}' \n         and wstwd = '{dimension}' \n         and zcfl not in ({','.join((f"'{cat}'" for cat in category))})\n         group by wstwd\n         """
        return query_all(sql)

    def get_financial_return_dimension2(self, date: str, dimension: str) -> list[dict]:
        """获取财务收益数据"""
        sql = f""" select wstwd,sum(cwsy_bn) as financial_yield_x,sum(pjzjzy_bn) as financial_yield_y\n        from position_snapshot \n        where p_dt = '{date}' \n         and wstwd = '{dimension}'\n         and ztbh is not null \n         group by wstwd\n         """
        return query_all(sql)

    def get_account_yields(self, date, dimension, accounts, comprehensive=False):
        """Aggregate before any minimum-value gate; reject partial NULL inputs."""
        if not accounts:
            return []
        metric = 'zhsy_bn' if comprehensive else 'cwsy_bn'
        def complete_sum(column):
            return f'CASE WHEN COUNT({column}) = COUNT(*) THEN SUM({column}) ELSE NULL END'
        sql = (f"SELECT ztbh, MAX(jjztmc) AS jjztmc, {complete_sum('qjsz')} AS market_value, "
               f"{complete_sum(metric)} AS earnings, {complete_sum('pjzjzy_bn')} AS capital "
               "FROM position_snapshot WHERE p_dt = %s AND wstwd = %s AND ztbh IN (" +
               ', '.join(['%s'] * len(accounts)) + ') GROUP BY ztbh')
        return query_all(sql, (date, dimension, *accounts))
