-- Minimal mapping contract used by the adapted ratio queries, both backends.
CREATE TABLE asset_position_tree_daily (
    trade_date BIGINT NOT NULL,
    account_set_id VARCHAR(100) NOT NULL,
    asset_code VARCHAR(100) NOT NULL,
    manager VARCHAR(100) NOT NULL,
    asset_level_one VARCHAR(100),
    asset_level_two VARCHAR(100)
);
CREATE INDEX idx_tree_position ON asset_position_tree_daily
    (trade_date, account_set_id, asset_code, manager);
