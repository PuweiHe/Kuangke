from db.query_adapter import query_all, query_one

class InvestmentAmountDAO:
    """投资金额监控数据访问对象"""

    def get_investment_dimension_data(self, date: str, dimension: str) -> list[dict]:
        """获取投资数据"""
        sql = f""" select  CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,\n        ztbh,jjztmc,wstwd, qjsz as dirty_price_market_value\n        from position_snapshot \n        where p_dt = '{date}' and wstwd = '{dimension}' \n        """
        return query_all(sql)

    def get_investment_category_data(self, date: str, dimension: str, category: list) -> list[dict]:
        """获取投资数据"""
        sql = f""" select p_dt,ztbh,jjztmc,wstwd,qjsz as dirty_price_market_value\n        from position_snapshot \n        where p_dt = '{date}' and wstwd = '{dimension}' \n            and zcfl in ({','.join((f"'{cat}'" for cat in category))})\n        """
        return query_all(sql)

    def get_investment_category_detail_data(self, date: str, dimension: str, category: list) -> list[dict]:
        """获取投资数据"""
        sql = f""" select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,\n        jydm,ztbh,jjztmc,wstwd, qjsz as dirty_price_market_value\n        from position_snapshot \n        where p_dt = '{date}' and wstwd = '{dimension}' \n            and zcfl in ({','.join((f"'{cat}'" for cat in category))})\n        """
        return query_all(sql)

    def get_investment_mutil_category_data(self, date: str, dimension: str, category: list, category_one: list) -> list[dict]:
        """获取投资数据"""
        sql = f"""SELECT\n            ztbh,jjztmc,wstwd, qjsz as dirty_price_market_value\n        from position_snapshot \n        where p_dt = '{date}' and wstwd = '{dimension}' \n        """
        if category:
            category_str = ','.join([f"""'{cat}'""" for cat in category])
            sql += f''' and zcfl in ({category_str})'''
        if category_one:
            category_one_str = ','.join([f"""'{cat}'""" for cat in category_one])
            sql += f''' and zcfl_1st in ({category_one_str})'''
        return query_all(sql)

    def get_port_data_by_asset_codes(self, date: str, asset_codes: list) -> list[dict]:
        """
        获取投资数据
        s_val_mv 总市值
        s_dq_mv 流通市值
        单位：港元
        """
        if not asset_codes:
            return []
        sql = f""" select s_info_windcode,s_val_mv as mkt_val from hkshareeodderivativeindex \n             where financial_trade_dt = '{date}' \n             and s_info_windcode in ({','.join((f"'{code}'" for code in asset_codes))})\n        """
        return query_all(sql)

    def get_investment_category_lv2_data(self, date: str, dimension: str, category: list) -> list[dict]:
        """获取投资数据"""
        sql = f"""  select a.ztbh, a.jjztmc, qjsz as dirty_price_market_value from position_snapshot a\n            inner join (select trade_date,account_set_id,asset_code,manager from asset_position_tree_daily\n                    where trade_date = '{date}'\n                    and asset_level_two in ({','.join((f"'{cat}'" for cat in category))})\n                    and manager = '{dimension}') b\n            on a.p_dt = b.trade_date\n            and a.ztbh = account_set_id\n            and a.zcdm = b.asset_code\n            and a.wstwd = b.manager\n        """
        return query_all(sql)
