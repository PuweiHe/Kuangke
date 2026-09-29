from db.query_adapter import query_all, query_one

class RatingDAO:

    def get_investment_dimension_data(self, biz_date: str, dimension: str):
        sql = f""" select p_dt, CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm\n        ,jydm,ztbh,jjztmc, qjsz as dirty_price_market_value\n        from position_snapshot \n        where p_dt = '{biz_date}' and wstwd = '{dimension}' \n        """
        return query_all(sql)

    def get_investment_category_detail_data(self, date: str, dimension: str, category: list) -> list[dict]:
        """获取投资数据"""
        sql = f""" select p_dt, CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm, \n            jydm, zcmc ,ztbh, jjztmc, qjsz as dirty_price_market_value\n        from position_snapshot \n        where p_dt = '{date}' and wstwd = '{dimension}' \n            and zcfl in ({','.join((f"'{cat}'" for cat in category))})\n        """
        return query_all(sql)

    def get_bond_issuer_data(self, date: str, bond_code: list) -> list[dict]:
        """获取债券发行人数据"""
        if not bond_code:
            return []
        sql = f""" \n            WITH RankedRatings AS (\n                SELECT\n                    i.s_info_windcode      AS bond_code,\n                    i.s_info_compname      AS issuer_name,\n                    r.b_info_creditrating  AS credit_rating,\n                    r.b_rate_style         AS rating_type,\n                    r.ann_dt               AS announcement_date,\n                    ROW_NUMBER() OVER (PARTITION BY i.s_info_windcode ORDER BY r.ann_dt DESC) AS rn\n                FROM reference_data.cbondissuer i\n                JOIN reference_data.cbondissuerrating r\n                    ON i.s_info_compcode = r.s_info_compcode\n                WHERE i.s_info_windcode IN ({','.join((f"'{code}'" for code in bond_code))})\n                AND r.ann_dt <= '{date}'\n            )\n            SELECT\n                bond_code,\n                issuer_name,\n                credit_rating,\n                rating_type,\n                announcement_date\n            FROM RankedRatings\n            WHERE rn = 1\n\n        """
        return query_all(sql)

    def get_bond_issuer_dist_data(self, date: str, bond_code: list) -> list[dict]:
        """获取债券发行人数据"""
        if not bond_code:
            return []
        sql = f""" \n            SELECT\n                a.s_info_windcode      AS bond_code,\n                a.s_info_compname      AS issuer_name,\n                b.b_info_creditrating  AS credit_rating,\n                b.b_rate_style         AS rating_type,\n                b.ann_dt               AS announcement_date      \n            FROM reference_data.cbondissuer a\n            JOIN reference_data.cbondissuerrating b\n                ON a.s_info_compcode = b.s_info_compcode\n            WHERE s_info_windcode IN ({','.join((f"'{code}'" for code in bond_code))})\n            AND ann_dt <= '{date}'\n        """
        return query_all(sql)

    def get_bond_rating_data(self, date: str, bond_code: list) -> list[dict]:
        """获取债券评级数据"""
        if not bond_code:
            return []
        sql = f""" \n            SELECT\n                s_info_windcode      AS bond_code,\n                b_info_creditrating  AS credit_rating,\n                ann_dt               AS announcement_date\n            FROM reference_data.cbondrating \n            WHERE s_info_windcode IN ({','.join((f"'{code}'" for code in bond_code))})\n            AND ann_dt <= '{date}'\n        """
        return query_all(sql)

    def get_rated_bond_data(self, date: str, dimension: str, bond_code: list) -> list[dict]:
        """获取 BBB 等级的债券数据"""
        if not bond_code:
            return []
        sql = f""" \n            select p_dt,zcdm,jydm,ztbh,jjztmc, qjsz as dirty_price_market_value\n        from position_snapshot \n        where p_dt = '{date}' and wstwd = '{dimension}' \n            and jydm in ({','.join((f"'{code}'" for code in bond_code))})\n        """
        return query_all(sql)

    def get_bond_localgovt_dist_data(self, date: str, bond_code: list) -> list[dict]:
        """获取债券发行人数据"""
        if not bond_code:
            return []
        sql = f''' \n            SELECT \n                a.s_info_windcode as bond_code,    -- 债券代码\n                a.s_info_name as bond_short_name,        -- 债券简称\n                a.b_info_issuer as issuer_name,      -- 发行人名称\n                c.province,           -- 发行人所在省份 (发行区域)\n                c.city,               -- 发行人所在城市\n                c.district            -- 发行人所在区县\n            FROM reference_data.cbonddescription a\n            -- 关联债券发行人表，通过债券代码匹配\n            LEFT JOIN reference_data.cbondissuer b \n                ON a.s_info_windcode = b.s_info_windcode\n            -- 关联公司基本资料表，通过发行人公司代码匹配\n            LEFT JOIN reference_data.compintroduction c \n                ON b.s_info_compcode = c.comp_id\n            WHERE c.province IS NOT NULL\n            AND a.s_info_windcode IN ({','.join((f"'{code}'" for code in bond_code))})\n        '''
        return query_all(sql)
