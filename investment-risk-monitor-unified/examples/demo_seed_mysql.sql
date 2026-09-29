-- Synthetic values only. Apply after sql/init.sql and sql/position_snapshot.sql.
INSERT INTO risk_rule_config
    (monitor_type, monitor_id, monitor_item, monitor_title, threshold, is_enabled)
VALUES
    ('example', 'DEMO-PL-0001', 'portfolio value', 'Example portfolio value limit', '10', 1);

INSERT INTO risk_dimension_config (monitor_id, dimension_code, trust_dimension)
VALUES ('DEMO-PL-0001', 'DEMO', 'DEMO');

INSERT INTO position_snapshot (p_dt, wstwd, ztbh, jjztmc, zcdm, zcmc, jjsz)
VALUES
    ('20250102', 'DEMO', 'P001', 'Example Portfolio A', 'A001', 'Example Asset A', 6.0),
    ('20250102', 'DEMO', 'P001', 'Example Portfolio A', 'A002', 'Example Asset B', 5.0),
    ('20250102', 'DEMO', 'P002', 'Example Portfolio B', 'B001', 'Example Asset C', 4.0);
