from db.query_adapter import query_all


class InvestmentRatioDAO:
    """投资比例数据访问对象"""

    def get_investment_dimension_data(self, date: str, dimension: str) -> list[dict]:
        """获取投资数据"""
        sql = """ select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
            ztbh,jjztmc, qjsz as dirty_price_market_value
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
            """ select ztbh,zcdm,jjztmc, qjsz as dirty_price_market_value, nhzhsyl_by
        from position_snapshot
        where p_dt = %s and wstwd = %s
            and zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
        """
        )
        params = [date, dimension, *category]
        return query_all(sql, params)

    def get_investment_exclude_category_data(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取投资数据"""
        if not category:
            return []
        sql = (
            """ select ztbh,sum(qjsz) as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
            and zcfl not in ("""
            + ", ".join(["%s"] * len(category))
            + """)
            group by ztbh
        """
        )
        params = [date, dimension, *category]
        return query_all(sql, params)

    def get_investment_data_lake(self, date: str) -> list[dict]:
        """
        获取投资数据
        """
        sql = """ select bbzd_date as p_dt, num_value as dirty_price_market_value
        from reference_report
        where bbzd_date = %s and value_type = 1
        """
        params = [date]
        return query_all(sql, params)

    def get_valuation_data(self, date: str, asset_codes: list) -> list[dict]:
        """获取估值数据"""
        if not asset_codes:
            return []
        sql = (
            """
            select vp.valuation_product_id, asset, (asset - debit) as liability, net_asset from valuation_product_summary vp
            inner join (select valuation_product_id, max(parse_date) max_date
                from valuation_orig_position where parse_date <= %s
                    and stock_code in ("""
            + ", ".join(["%s"] * len(asset_codes))
            + """)  group by valuation_product_id) ap
            on vp.valuation_product_id = ap.valuation_product_id and vp.parse_date = ap.max_date

        """
        )
        params = [date, *asset_codes]
        return query_all(sql, params)

    def get_investment_account_data(
        self, date: str, dimension: str, category: list, account_category: list
    ) -> list[dict]:
        """获取投资数据"""
        if not account_category:
            return []
        if not category:
            return []
        sql = (
            """ select p_dt,zcdm,zcmc,ztbh,jjztmc,zcdm,kjfl
        from position_snapshot
        where p_dt = %s and wstwd = %s
            and zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
            and kjfl in ("""
            + ", ".join(["%s"] * len(account_category))
            + """)
        """
        )
        params = [date, dimension, *category, *account_category]
        return query_all(sql, params)

    def get_investment_dimension_asset_data(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取投资数据"""
        if not category:
            return []
        sql = (
            """ select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
        zcmc,jydm,ztbh,jjztmc,kjfl,qjsz as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
            and zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
        """
        )
        params = [date, dimension, *category]
        return query_all(sql, params)

    def get_investment_dw_asset_data(self, date: str, asset_codes: list) -> list[dict]:
        """
        获取投资数据
        """
        if not asset_codes:
            return []
        sql = (
            """
        select s_info_windcode as asset_code, b_issue_amountact as issue_scale from cbonddescription
        where s_info_windcode in ("""
            + ", ".join(["%s"] * len(asset_codes))
            + """)
        """
        )
        params = [*asset_codes]
        return query_all(sql, params)

    def get_investment_dw_issuer_data(self, date: str, asset_codes: list) -> list[dict]:
        """获取投资数据"""
        if not asset_codes:
            return []
        sql = (
            """
        select s_info_windcode as asset_code, b_issue_amountact as issue_scale from cbonddescription
        where s_info_windcode in ("""
            + ", ".join(["%s"] * len(asset_codes))
            + """)
        """
        )
        params = [*asset_codes]
        return query_all(sql, params)

    def get_asset_industry_data(self, date: str, asset_codes: list) -> dict:
        """
        获取资产行业数据
        Returns
        -------
        dict
            资产代码到行业名称的映射字典，例如：{'SH600000': '银行', 'SZ000001': '房地产'}
        """
        if not asset_codes:
            return []
        if not asset_codes:
            return {}
        sql = (
            """
            select a.const_code as asset_code, a.ind_name as industry_name
            from const_stk_ind_sw a
            inner join (
                select const_code, max(ann_date) as max_date
                from const_stk_ind_sw
                where const_code in ("""
            + ", ".join(["%s"] * len(asset_codes))
            + """)
                    and ann_date <= %s
                group by const_code
            ) b on a.const_code = b.const_code and a.ann_date = b.max_date
        """
        )
        params = [*asset_codes, date]
        result = query_all(sql, params)
        return {item["asset_code"]: item["industry_name"] for item in result}

    def get_investment_category_data_new(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取投资数据"""
        if not category:
            return []
        sql = (
            """
            select a.ztbh, a.jjztmc, sum(qjsz) as dirty_price_market_value from position_snapshot a
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
            group by a.ztbh, a.jjztmc
        """
        )
        params = [date, *category, dimension]
        return query_all(sql, params)

    def get_ratio_accounts(self, date, dimension):
        rows = query_all(
            "SELECT DISTINCT ztbh FROM position_snapshot WHERE p_dt = %s AND wstwd = %s AND ztbh IS NOT NULL",
            (date, dimension),
        )
        return [str(row["ztbh"]) for row in rows]

    def get_ratio_positions(
        self,
        date,
        dimension,
        categories,
        accounts=None,
        exclude=False,
        absolute=False,
        tree_category=False,
    ):
        """Bound values and use EXISTS to avoid duplicate mapping fan-out."""
        if not categories or accounts == []:
            return []
        placeholders = ", ".join(["%s"] * len(categories))
        params = [date, dimension]
        amount = "ABS(a.qjsz)" if absolute else "a.qjsz"
        sql = f"SELECT a.ztbh, a.jjztmc, {amount} AS dirty_price_market_value FROM position_snapshot a WHERE a.p_dt = %s AND a.wstwd = %s"
        if tree_category:
            sql += f" AND EXISTS (SELECT 1 FROM asset_position_tree_daily b WHERE b.trade_date = a.p_dt AND b.account_set_id = a.ztbh AND b.asset_code = a.zcdm AND b.manager = a.wstwd AND b.asset_level_two IN ({placeholders}))"
        else:
            sql += f" AND a.zcfl {'NOT IN' if exclude else 'IN'} ({placeholders})"
        params.extend(categories)
        if accounts is not None:
            sql += " AND a.ztbh IN (" + ", ".join(["%s"] * len(accounts)) + ")"
            params.extend(accounts)
        return query_all(sql, tuple(params))

    def get_repo_balances(self, date, dimension, accounts):
        """Return known zero only for accounts with a source snapshot."""
        if not accounts:
            return []
        sql = (
            "SELECT ztbh, MAX(jjztmc) AS jjztmc, CASE WHEN SUM(CASE WHEN zcfl = %s AND qjsz IS NULL THEN 1 ELSE 0 END) > 0 THEN NULL ELSE SUM(CASE WHEN zcfl = %s THEN qjsz ELSE 0 END) END AS dirty_price_market_value FROM position_snapshot WHERE p_dt = %s AND wstwd = %s AND ztbh IN ("
            + ", ".join(["%s"] * len(accounts))
            + ") GROUP BY ztbh"
        )
        return query_all(sql, ("正回购", "正回购", date, dimension, *accounts))
