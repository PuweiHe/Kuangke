from db.query_adapter import query_all


class DurationDAO:
    """久期监控数据访问对象"""

    def get_fixed_income_duration_data(self, biz_date: str, monitor_id: str, dimension: str):
        sql = """
            select p_dt,zcdm,wstwd,ztbh,jjztmc,zcfl,qjsz,jq,mrrq
            from position_snapshot
            where p_dt = %s and wstwd = %s and zcfl = '固收' and jq != 0
        """
        params = [biz_date, dimension]
        return query_all(sql, params)

    def get_fixed_income_scale_duration_data(self, biz_date: str, monitor_id: str, dimension: str):
        sql = """
            select a.ztbh, a.jjztmc, qjsz, jq from position_snapshot a
            inner join (select trade_date,account_set_id,asset_code,asset_level_one from asset_position_tree_daily
            where trade_date = %s
            and asset_level_one = '固收类') b
            on a.p_dt = b.trade_date
            and a.ztbh = account_set_id
            and a.zcdm = b.asset_code

        where a.wstwd = %s and a.zcfl != '债券型基金' and a.jq != 0
        """
        params = [biz_date, dimension]
        return query_all(sql, params)

    def get_fixed_income_asset_scale_duration_data(
        self, biz_date: str, dimension: str, category: list
    ):
        if not category:
            return []
        sql = (
            """
           select hz.p_dt,hz.zcdm, hz.zcmc, hz.ztbh, hz.jjztmc, hz.qjsz, hz.jq from position_snapshot hz
            inner join
                (select account_set_code from fund_account_set where sub_account_dimension in ('传统','自有','资补债') and fund_account_status = 1) zf
                    on hz.ztbh = zf.account_set_code
            inner join
            (select account_set_id from asset_position_tree_daily
                where trade_date = %s and strategy_plate = '配置盘')  za
            on hz.ztbh = za.account_set_id
            where
                hz.p_dt = %s
                and hz.wstwd = %s
                and hz.zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
                and hz.jq >= 20
        """
        )
        params = [biz_date, biz_date, dimension, *category]
        return query_all(sql, params)

    def get_asset_duration_data(self, biz_date: str, dimension: str):
        sql = """
            select p_dt,zcdm,zcmc,ztbh,jjztmc,zcfl,qjsz,jq
            from position_snapshot
            where p_dt = %s and wstwd = %s and jq != 0
        """
        params = [biz_date, dimension]
        return query_all(sql, params)
