from db.query_adapter import query_all, query_one

class InvestmentRAmountDAO:
    """投资金额/比例数据访问对象"""

    def get_investment_dimension_data(self, date: str, dimension: str) -> list[dict]:
        """获取投资数据"""
        sql = f""" select CONCAT(SUBSTRING_INDEX(zcdm, '.', 1),'.',SUBSTRING_INDEX(zcdm, '.', -1)) as zcdm, \n        ztbh, jjztmc, zcfl, qjsz as dirty_price_market_value\n        from position_snapshot \n        where p_dt = {date} and wstwd = '{dimension}' \n        """
        return query_all(sql)

    def get_investment_data_lake(self, date: str) -> list[dict]:
        """
        获取投资数据
        """
        date_int = int(date.replace('-', ''))
        sql = f''' select bbzd_date as p_dt, num_value as dirty_price_market_value\n        from reference_report \n        where bbzd_date = {date_int} and value_type = 1\n        '''
        return query_all(sql)

    def get_dw_investment_data(self, asset_codes: list) -> list[dict]:
        """获取投资数据"""
        if not asset_codes:
            return []
        sql = f""" \n            select asset_code, asset_name from (\n                SELECT\n                    s_info_windcode AS asset_code,\n                    b_info_fullname AS asset_name,\n                    CASE\n                        WHEN b_info_issuer LIKE '%财政部%' THEN '中央政府债券'\n                        WHEN b_info_issuer LIKE '%省人民政府%'\n                            OR b_info_issuer LIKE '%市人民政府%'\n                            OR b_info_issuer LIKE '%自治区人民政府%'\n                            OR b_info_issuer LIKE '%直辖市人民政府%' THEN '省级政府债券'\n                        WHEN b_info_issuer IN ('国家开发银行', '中国农业发展银行', '中国进出口银行')\n                        OR b_info_issuertype IN ('政策性银行','中国人民银行','国有商业银行','股份制商业银行','证券公司','其他金融机构') THEN '政策性金融债'\n                        WHEN b_info_issuer LIKE '%城市建设投资%'\n                            OR b_info_issuer LIKE '%城投%'\n                            OR b_info_issuer LIKE '%交通投资%'\n                            OR b_info_issuer LIKE '%国有资产投资%' THEN '准政府债券'\n                        ELSE '其他债券'\n                    END AS bond_type\n                FROM cbonddescription) as cspt\n            where bond_type in ('投资境内中央政府债券','省级政府债券','准政府债券','政策性金融债','银行存款','现金')\n            and asset_code in ({','.join((f"'{code}'" for code in asset_codes))})\n        """
        return query_all(sql)
