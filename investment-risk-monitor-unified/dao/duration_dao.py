from db.query_adapter import query_all, query_one

class DurationDAO:
    """久期监控数据访问对象"""

    def get_fixed_income_duration_data(self, biz_date: str, monitor_id: str, dimension: str):
        sql = f"\n            select p_dt,zcdm,wstwd,ztbh,jjztmc,zcfl,qjsz,jq,mrrq\n            from position_snapshot\n            where p_dt = '{biz_date}' and wstwd = '{dimension}' and zcfl = '固收' and jq != 0\n        "
        return query_all(sql)

    def get_fixed_income_scale_duration_data(self, biz_date: str, monitor_id: str, dimension: str):
        sql = f"\n            select a.ztbh, a.jjztmc, qjsz, jq from position_snapshot a\n            inner join (select trade_date,account_set_id,asset_code,asset_level_one from asset_position_tree_daily\n            where trade_date = '{biz_date}'\n            and asset_level_one = '固收类') b\n            on a.p_dt = b.trade_date\n            and a.ztbh = account_set_id\n            and a.zcdm = b.asset_code\n\n        where a.wstwd = '{dimension}' and a.zcfl != '债券型基金' and a.jq != 0\n        "
        return query_all(sql)

    def get_fixed_income_asset_scale_duration_data(self, biz_date: str, dimension: str, category: list):
        category_str = ','.join([f"'{c}'" for c in category])
        sql = f"\n           select hz.p_dt,hz.zcdm, hz.zcmc, hz.ztbh, hz.jjztmc, hz.qjsz, hz.jq from position_snapshot hz\n            inner join\n                (select account_set_code from fund_account_set where sub_account_dimension in ('传统','自有','资补债') and fund_account_status = 1) zf\n                    on hz.ztbh = zf.account_set_code\n            inner join\n            (select account_set_id from asset_position_tree_daily \n                where trade_date = '{biz_date}' and strategy_plate = '配置盘')  za\n            on hz.ztbh = za.account_set_id\n            where\n                hz.p_dt = '{biz_date}'\n                and hz.wstwd = '{dimension}'\n                and hz.zcfl in ({category_str})\n                and hz.jq >= 20\n        "
        return query_all(sql)

    def get_asset_duration_data(self, biz_date: str, dimension: str):
        sql = f"\n            select p_dt,zcdm,zcmc,ztbh,jjztmc,zcfl,qjsz,jq\n            from position_snapshot\n            where p_dt = '{biz_date}' and wstwd = '{dimension}' and jq != 0\n        "
        return query_all(sql)
