from db.query_adapter import query_all


class RatingDAO:
    def get_investment_dimension_data(self, biz_date: str, dimension: str):
        sql = """ select p_dt, CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm
        ,jydm,ztbh,jjztmc, qjsz as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
        """
        params = [biz_date, dimension]
        return query_all(sql, params)

    def get_investment_category_detail_data(
        self, date: str, dimension: str, category: list
    ) -> list[dict]:
        """获取投资数据"""
        if not category:
            return []
        sql = (
            """ select p_dt, CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm,
            jydm, zcmc ,ztbh, jjztmc, qjsz as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
            and zcfl in ("""
            + ", ".join(["%s"] * len(category))
            + """)
        """
        )
        params = [date, dimension, *category]
        return query_all(sql, params)

    def get_bond_issuer_data(self, date: str, bond_code: list) -> list[dict]:
        """获取债券发行人数据"""
        if not bond_code:
            return []
        sql = (
            """
            WITH RankedRatings AS (
                SELECT
                    i.s_info_windcode      AS bond_code,
                    i.s_info_compname      AS issuer_name,
                    r.b_info_creditrating  AS credit_rating,
                    r.b_rate_style         AS rating_type,
                    r.ann_dt               AS announcement_date,
                    ROW_NUMBER() OVER (PARTITION BY i.s_info_windcode ORDER BY r.ann_dt DESC) AS rn
                FROM reference_data.cbondissuer i
                JOIN reference_data.cbondissuerrating r
                    ON i.s_info_compcode = r.s_info_compcode
                WHERE i.s_info_windcode IN ("""
            + ", ".join(["%s"] * len(bond_code))
            + """)
                AND r.ann_dt <= %s
            )
            SELECT
                bond_code,
                issuer_name,
                credit_rating,
                rating_type,
                announcement_date
            FROM RankedRatings
            WHERE rn = 1

        """
        )
        params = [*bond_code, date]
        return query_all(sql, params)

    def get_bond_issuer_dist_data(self, date: str, bond_code: list) -> list[dict]:
        """获取债券发行人数据"""
        if not bond_code:
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
            + ", ".join(["%s"] * len(bond_code))
            + """)
            AND ann_dt <= %s
        """
        )
        params = [*bond_code, date]
        return query_all(sql, params)

    def get_bond_rating_data(self, date: str, bond_code: list) -> list[dict]:
        """获取债券评级数据"""
        if not bond_code:
            return []
        sql = (
            """
            SELECT
                s_info_windcode      AS bond_code,
                b_info_creditrating  AS credit_rating,
                ann_dt               AS announcement_date
            FROM reference_data.cbondrating
            WHERE s_info_windcode IN ("""
            + ", ".join(["%s"] * len(bond_code))
            + """)
            AND ann_dt <= %s
        """
        )
        params = [*bond_code, date]
        return query_all(sql, params)

    def get_rated_bond_data(self, date: str, dimension: str, bond_code: list) -> list[dict]:
        """获取 BBB 等级的债券数据"""
        if not bond_code:
            return []
        sql = (
            """
            select p_dt,zcdm,jydm,ztbh,jjztmc, qjsz as dirty_price_market_value
        from position_snapshot
        where p_dt = %s and wstwd = %s
            and jydm in ("""
            + ", ".join(["%s"] * len(bond_code))
            + """)
        """
        )
        params = [date, dimension, *bond_code]
        return query_all(sql, params)

    def get_bond_localgovt_dist_data(self, date: str, bond_code: list) -> list[dict]:
        """获取债券发行人数据"""
        if not bond_code:
            return []
        sql = (
            """
            SELECT
                a.s_info_windcode as bond_code,    -- 债券代码
                a.s_info_name as bond_short_name,        -- 债券简称
                a.b_info_issuer as issuer_name,      -- 发行人名称
                c.province,           -- 发行人所在省份 (发行区域)
                c.city,               -- 发行人所在城市
                c.district            -- 发行人所在区县
            FROM reference_data.cbonddescription a
            -- 关联债券发行人表，通过债券代码匹配
            LEFT JOIN reference_data.cbondissuer b
                ON a.s_info_windcode = b.s_info_windcode
            -- 关联公司基本资料表，通过发行人公司代码匹配
            LEFT JOIN reference_data.compintroduction c
                ON b.s_info_compcode = c.comp_id
            WHERE c.province IS NOT NULL
            AND a.s_info_windcode IN ("""
            + ", ".join(["%s"] * len(bond_code))
            + """)
        """
        )
        params = [*bond_code]
        return query_all(sql, params)
