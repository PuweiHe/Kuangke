from db.query_adapter import query_all


class BlackWhiteDAO:
    def get_asset_dimension_date(self, biz_date: str, dimension: str):
        """
        获取资产维度日期
        """
        sql = """select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
            p_dt, zcmc, jydm, wstwd, ztbh, jjztmc, zcfl from position_snapshot
        where p_dt = %s and wstwd = %s"""
        return query_all(sql, (biz_date, dimension))

    def get_asset_data(self, biz_date: str, dimension: str, categorys: list):
        """
        获取股票资产数据
        """
        if not categorys:
            return []
        placeholders = ",".join(["%s"] * len(categorys))
        sql = f"""select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,\n            p_dt, zcmc, wstwd, ztbh, jjztmc, zcfl from position_snapshot\n        where p_dt = %s and wstwd = %s and zcfl in ({placeholders})"""
        params = [biz_date, dimension] + categorys
        return query_all(sql, params)

    def get_ban_soya_data(self):
        """
        获取豆粕资产列表
        """
        sql = "select fund_code from bsc_basics where fund_name like '%豆粕%'"
        return query_all(sql)

    def get_invest_soya_list(self, biz_date: str, asset_codes: list):
        """
        获取投资豆粕资产列表
        """
        if not asset_codes:
            return []
        year = int(biz_date[:4])
        sql = (
            """select asset_code from risk_assets_list
                where category_2nd = 'SOYA' and asset_code in ("""
            + ", ".join(["%s"] * len(asset_codes))
            + ") and year = %s"
        )
        params = [*asset_codes, year]
        return query_all(sql, params)

    def get_asset_by_investment_style(self):
        """
        获取投资豆粕(基金)资产数据
        """
        sql = """ select main_code from reference_data.bsc_basics
                where invest_style in ('豆粕期货型','黄金现货合约','原油主题基金','有色金属期货型','能源化工期货型', '白银期货型')
                and invest_type in ('商品型', 'QDII','另类投资型') """
        return query_all(sql)

    def get_trade_counterparty_data(self, biz_date: str, dimension: str):
        """
        获取交易对手数据，包含公司债和企业债
        """
        sql = """select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
            p_dt, zcmc, wstwd, ztbh, jjztmc, zcfl from position_snapshot
        where p_dt = %s and wstwd = %s and zcfl in ('公司债','企业债')"""
        return query_all(sql, (biz_date, dimension))

    def get_trade_counterparty_guarantor_data(self, biz_date: str, asset_codes: list):
        """
        TODO: 需确认
        获取交易对手担保主体数据
        """
        if not asset_codes:
            return []
        placeholders = ",".join(["%s"] * len(asset_codes))
        sql = f"""select p_dt, zcdm, wstwd, ztbh, jjztmc, zcfl from position_snapshot\n        where p_dt = %s and zcdm in ({placeholders})"""
        params = [biz_date] + asset_codes
        return query_all(sql, params)

    def get_guarantor_data(self, biz_date: str, asset_codes: list):
        """
        获取担保主体数据
        """
        if not asset_codes:
            return []
        sql = (
            """
            SELECT
                a.s_info_windcode      AS bond_code,
                a.s_info_compname      AS issuer_name,
                b.b_info_creditrating  AS credit_rating,
                b.b_rate_style         AS rating_type,
                b.ann_dt               AS announcement_date
            FROM reference_data.cbondissuer a
            JOIN reference_data.cbondissuerrating b
                ON a.s_info_compcode = b.s_info_compcode
            WHERE s_info_windcode IN ("""
            + ", ".join(["%s"] * len(asset_codes))
            + """)
            AND ann_dt <= %s
        """
        )
        params = [*asset_codes, biz_date]
        return query_all(sql, params)

    def get_stock_asset_data(self, biz_date: str, dimension: str):
        """
        获取股票资产数据
        """
        sql = """select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
            p_dt, jydm, wstwd, ztbh, jjztmc, zcfl from position_snapshot
        where p_dt = %s and wstwd = %s and zcfl = '股票'"""
        return query_all(sql, (biz_date, dimension))

    def get_stock_pool_whitelist(self, biz_date: str, asset_codes: list):
        """
        备注：当前已废弃
        获取股票池白名单
        """
        if not asset_codes:
            return []
        placeholders = ",".join(["%s"] * len(asset_codes))
        sql = f"""select p_dt, zcdm, wstwd, ztbh, jjztmc, zcfl from position_snapshot\n        where p_dt = %s and zcdm in ({placeholders})"""
        params = [biz_date] + asset_codes
        return query_all(sql, params)

    def get_reits_fund_pool_whitelist(self, year: int):
        """
        获取REITS基金池白名单
        """
        sql = """select asset_code as bk_name from risk_assets_list
                where category_2nd = 'REITs' and year = %s"""
        return query_all(sql, (year,))

    def get_subordinated_bond_blacklist(self):
        """
        获取次级债、资本补充债黑名单
        (资本补充债 归属到了次级债下面 所以直接 b_info_subordinateornot = '1')
        """
        sql = """ SELECT s_info_windcode,b_info_issuer
                    FROM reference_data.cbonddescription WHERE b_info_subordinateornot = '1'
                    AND b_info_issuer = '示例保险机构' """
        return query_all(sql)

    def get_reits_fund_whitelist(self, biz_date: str, asset_codes: list):
        """
        TODO: 需确认
        获取REITS基金白名单
        """
        if not asset_codes:
            return []
        placeholders = ",".join(["%s"] * len(asset_codes))
        sql = f"""select \n            CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,\n            p_dt, wstwd, ztbh, jjztmc, zcfl from position_snapshot\n        where p_dt = %s and zcdm in ({placeholders})"""
        params = [biz_date] + asset_codes
        return query_all(sql, params)

    def get_target_whitelist(self, biz_date: str, asset_codes: list):
        """
        TODO: 需确认
        获取目标白名单
        """
        if not asset_codes:
            return []
        placeholders = ",".join(["%s"] * len(asset_codes))
        sql = f"""select p_dt, zcdm, wstwd, ztbh, jjztmc, zcfl from position_snapshot\n        where p_dt = %s and zcdm in ({placeholders})"""
        params = [biz_date] + asset_codes
        return query_all(sql, params)

    def get_whitelist_investment_scope(self, biz_date: str, asset_codes: list):
        """
        TODO: 需确认
        获取白名单投资范围
        """
        if not asset_codes:
            return []
        placeholders = ",".join(["%s"] * len(asset_codes))
        sql = f"""select p_dt, zcdm, wstwd, ztbh, jjztmc, zcfl from position_snapshot\n        where p_dt = %s and zcdm in ({placeholders})"""
        params = [biz_date] + asset_codes
        return query_all(sql, params)

    def get_real_estate_industry_ban(self, biz_date: str, asset_codes: list):
        """
        获取房地产行业禁投名单
        """
        if not asset_codes:
            return []
        sql = (
            """
            with stk_ind as (
                select a.const_code as main_code from reference_data.const_stk_ind_sw a,
                        (select const_code,max(ann_date) max_date from reference_data.const_stk_ind_sw
                                                                where const_code in ("""
            + ", ".join(["%s"] * len(asset_codes))
            + """) and ann_date <= %s
                                                                group by const_code ) b
                where a.const_code = b.const_code and a.ann_date = b.max_date
                        and a.ind_name = '房地产'
                ),
            fund_ind as (
                select a.main_code from reference_data.annip_stk_ind_alloc_all a,
                                    (select main_code,max(end_date) max_date from reference_data.annip_stk_ind_alloc_all
                                                                where main_code in ("""
            + ", ".join(["%s"] * len(asset_codes))
            + """) and end_date <= %s
                                                                group by main_code ) b
                where a.main_code = b.main_code and a.end_date = b.max_date
                        and a.industry_name = '房地产'

                )
            select * from stk_ind
            union all
            select * from fund_ind
        """
        )
        params = [*asset_codes, biz_date, *asset_codes, biz_date]
        return query_all(sql, params)

    def get_fvoci_asset_data(self, biz_date, dimension, asset_codes):
        """Keep raw codes for shared normalization; bind all filter values."""
        if not asset_codes:
            return []
        sql = (
            "SELECT zcdm, p_dt, zcmc, jydm, wstwd, ztbh, jjztmc, zcfl FROM position_snapshot WHERE p_dt = %s AND wstwd = %s AND zcfl IN ("
            + ",".join(["%s"] * len(asset_codes))
            + ") AND kjfl = %s"
        )
        return query_all(sql, (biz_date, dimension, *asset_codes, "FVOCI"))

    def get_fvoci_stock_pool_whitelist(self, biz_date: str):
        """
        获取FVOCI股票池白名单
        """
        sql = """
            with hs300 as (
                select s_con_windcode from reference_data.aindexhs300weight where trade_dt = %s
            ),
            csi500 as (
                select s_con_windcode from reference_data.aindexcsi500weight where trade_dt = %s
            )
            select s_info_windcode as asset_code from reference_data.hksharedescription
            union all
            select s_con_windcode from hs300
            union all
            select s_con_windcode from csi500

        """
        params = [biz_date, biz_date]
        return query_all(sql, params)

    def get_public_reits_asset_data(
        self, biz_date: str, dimension: str, asset_category: str, account_category: str = None
    ):
        """
        获取REITS资产数据
        """
        if not asset_category:
            return []
        sql = """select
            CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
            p_dt, wstwd, ztbh, jjztmc, ccsl from position_snapshot
        where p_dt = %s and wstwd = %s and zcfl = %s"""
        if account_category:
            sql += " and kjfl = %s"
            return query_all(sql, (biz_date, dimension, asset_category, account_category))
        return query_all(sql, (biz_date, dimension, asset_category))

    def get_trade_counterparty_blacklist(self, year: int):
        """
        获取交易对手黑名单
        """
        sql = """select asset_code as bk_name from risk_assets_list
                where category_2nd = 'COUNTERPARTY' and year = %s"""
        return query_all(sql, (year,))
