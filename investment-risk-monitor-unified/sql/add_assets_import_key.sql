-- For existing installations: resolve duplicate keys before applying.
CREATE UNIQUE INDEX uk_assets_import ON risk_assets_list (category, category_2nd, asset_code, year);
