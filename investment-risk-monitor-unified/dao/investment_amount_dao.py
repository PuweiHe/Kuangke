from db.query_adapter import query_all


class InvestmentAmountDAO:
    """投资金额监控数据访问对象"""

    def get_investment_dimension_data(self, date: str, dimension: str) -> list[dict]:
        """获取投资数据"""
        sql = """ select  CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
        ztbh,jjztmc,wstwd, qjsz as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
        """
        params = [date, dimension]
        return query_all(sql, params)

    def get_investment_category_data(self, date: str, dimension: str, category: list) -> list[dict]:
        """获取投资数据"""
        if not category:
            return []
        sql = (
            """ select p_dt,ztbh,jjztmc,wstwd,qjsz as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
            and zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
        """
        )
        params = [date, dimension, *category]
        return query_all(sql, params)

    def get_investment_category_detail_data(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取投资数据"""
        if not category:
            return []
        sql = (
            """ select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
        jydm,ztbh,jjztmc,wstwd, qjsz as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
            and zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
        """
        )
        params = [date, dimension, *category]
        return query_all(sql, params)

    def get_investment_mutil_category_data(
        self, date: str, dimension: str, category: list, category_one: list
    ) -> list[dict]:
        """获取投资数据"""
        sql = """SELECT
            ztbh,jjztmc,wstwd, qjsz as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
        """
        params = [date, dimension]
        if category:
            sql += " and zcfl in (" + ", ".join(["%s"] * len(category)) + ")"
            params.extend([*category])
        if category_one:
            sql += " and zcfl_1st in (" + ", ".join(["%s"] * len(category_one)) + ")"
            params.extend([*category_one])
        return query_all(sql, params)

    def get_port_data_by_asset_codes(self, date: str, asset_codes: list) -> list[dict]:
        """
        获取投资数据
        s_val_mv 总市值
        s_dq_mv 流通市值
        单位：港元
        """
        if not asset_codes:
            return []
        sql = (
            """ select s_info_windcode,s_val_mv as mkt_val from hkshareeodderivativeindex
             where financial_trade_dt = %s
             and s_info_windcode in ("""
            + ", ".join(["%s"] * len(asset_codes))
            + """)
        """
        )
        params = [date, *asset_codes]
        return query_all(sql, params)

    def get_investment_category_lv2_data(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取投资数据"""
        if not category:
            return []
        sql = (
            """  select a.ztbh, a.jjztmc, qjsz as dirty_price_market_value from position_snapshot a
            inner join (select trade_date,account_set_id,asset_code,manager from asset_position_tree_daily
                    where trade_date = %s
                    and asset_level_two in ("""
            + ", ".join(["%s"] * len(category))
            + """)
                    and manager = %s) b
            on a.p_dt = b.trade_date
            and a.ztbh = account_set_id
            and a.zcdm = b.asset_code
            and a.wstwd = b.manager
        """
        )
        params = [date, *category, dimension]
        return query_all(sql, params)
