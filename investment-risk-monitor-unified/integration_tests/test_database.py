"""Run explicitly against a fresh disposable MySQL/PostgreSQL database."""
import os
import sys
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ENABLED = os.getenv('RUN_DB_INTEGRATION') == '1'


@unittest.skipUnless(ENABLED, 'Set RUN_DB_INTEGRATION=1 for real database checks')
class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.getenv('DB_NAME', '').endswith('_test'):
            raise RuntimeError('Integration checks require a disposable database ending in _test')
        from config.settings import DB_TYPE
        from db.factory import get_pool
        from db.query_adapter import query_all, execute_update
        cls.dialect = DB_TYPE
        cls.pool = get_pool()
        cls.query = staticmethod(query_all)
        cls.update = staticmethod(execute_update)
        files = (['init.sql', 'position_snapshot.sql', 'mysql_job_lock.sql'] if DB_TYPE == 'mysql'
                 else ['postgres_init.sql', 'postgres_job_lock.sql'])
        files.append('asset_position_tree_mysql.sql' if DB_TYPE == 'mysql' else 'asset_position_tree.sql')
        # The suite deliberately requires a fresh DB rather than dropping tables.
        for filename in files:
            text = (ROOT / 'sql' / filename).read_text()
            text = '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('--'))
            for statement in text.split(';'):
                if statement.strip(): cls.update(statement)

    @classmethod
    def tearDownClass(cls):
        from db.factory import reset_pool
        reset_pool()

    def setUp(self):
        for table in ('risk_dimension_config', 'risk_rule_config', 'risk_assets_list', 'risk_monitor_result',
                      'risk_job_lock', 'asset_position_tree_daily', 'position_snapshot'):
            self.update('DELETE FROM ' + table)

    def test_config_upsert_and_unknown_dimension(self):
        from ingestion.config_import import prepare, apply_import, ImportValidationError
        for kind in ('rules', 'dimensions', 'assets'):
            rows = prepare(kind, ROOT / 'examples/config' / (kind + '.csv'))
            with self.pool.connection() as conn:
                apply_import(conn, self.dialect, kind, rows)
                apply_import(conn, self.dialect, kind, rows)
        self.assertEqual(self.query('SELECT COUNT(*) AS n FROM risk_assets_list')[0]['n'], 1)
        self.assertEqual(self.query('SELECT COUNT(*) AS n FROM risk_rule_config')[0]['n'], 1)
        bad = [dict(monitor_id='UNKNOWN', dimension_code='DEMO', trust_dimension='DEMO')]
        with self.assertRaises(ImportValidationError), self.pool.connection() as conn:
            apply_import(conn, self.dialect, 'dimensions', bad)
        self.assertEqual(self.query('SELECT COUNT(*) AS n FROM risk_dimension_config')[0]['n'], 1)

    def test_transaction_rollback_and_pool_reuse(self):
        with self.assertRaises(RuntimeError):
            with self.pool.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('INSERT INTO risk_job_lock (task_name, expires_at_epoch) VALUES (%s, %s)', ('rollback', 0))
                raise RuntimeError('synthetic failure')
        self.assertEqual(self.query('SELECT COUNT(*) AS n FROM risk_job_lock')[0]['n'], 0)
        self.assertEqual(self.query('SELECT 1 AS n')[0]['n'], 1)

    def test_concurrent_lease_renewal_expiry_and_stale_release(self):
        from utils.distributed_lock import DistributedJobLock
        locks = [DistributedJobLock('shared', 30) for _ in range(2)]
        barrier = threading.Barrier(2)
        def acquire(lock):
            barrier.wait(timeout=10)
            return lock.acquire()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(acquire, locks))
        self.assertEqual(sum(results), 1)
        owner, successor = (locks if results[0] else locks[::-1])
        self.assertTrue(owner.renew())
        self.update('UPDATE risk_job_lock SET expires_at_epoch = %s WHERE task_name = %s', (0, 'shared'))
        self.assertTrue(successor.acquire())
        self.assertFalse(owner.release())
        self.assertTrue(successor.release())

    def test_result_upsert(self):
        from dao.monitor_config_dao import MonitorConfigDAO
        from models.monitor_result import MonitorResult
        dao = MonitorConfigDAO()
        result = MonitorResult(monitor_id='DEMO', monitor_title='Example', check_date='20250102',
                               portfolio_code='P001', portfolio_name='Example', dimension_code='DEMO',
                               trust_dimension='DEMO', indicator_value='1', alert_level=0)
        dao.save_monitor_results([result])
        result.indicator_value, result.alert_level = None, 2
        result.alert_message = '[missing_data] Example unavailable denominator'
        dao.save_monitor_results([result])
        rows = self.query('SELECT indicator_value, alert_level FROM risk_monitor_result')
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['indicator_value'])
        self.assertEqual(rows[0]['alert_level'], 2)

    def test_ratio_query_mapping_fanout_and_monitor_execution(self):
        from ingestion.config_import import prepare, apply_import
        from dao.monitor_config_dao import MonitorConfigDAO
        from monitors.investment_ratio.investment_ratio_constraint import FinancialProductHoldingScaleRatioMonitor
        for kind in ('rules', 'dimensions'):
            with self.pool.connection() as conn:
                apply_import(conn, self.dialect, kind, prepare(kind, ROOT / 'examples/config' / (kind + '.csv')))
        for asset, category, amount in [('X', '非标类', 60), ('Y', '正回购', -40)]:
            self.update('INSERT INTO position_snapshot (p_dt,wstwd,ztbh,jjztmc,zcdm,zcfl,qjsz) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                        (20250102, 'DEMO', 'P001', 'Example', asset, category, amount))
        # Repeated mappings must not multiply the position amount.
        for _ in range(2):
            self.update('INSERT INTO asset_position_tree_daily (trade_date,account_set_id,asset_code,manager,asset_level_two) VALUES (%s,%s,%s,%s,%s)',
                        (20250102, 'P001', 'X', 'DEMO', '非标类'))
        config = MonitorConfigDAO().get_trust_dimension_config(monitor_id='IR-RC-0003')[0]
        result = FinancialProductHoldingScaleRatioMonitor().execute('20250102', config.monitor_id, 'DEMO', config)
        self.assertEqual(result['status'], 'success')
        rows = self.query('SELECT portfolio_code,indicator_value,alert_level FROM risk_monitor_result ORDER BY portfolio_code')
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(float(rows[0]['indicator_value']), .6)
        self.assertEqual(rows[0]['alert_level'], 0)
        self.assertIsNone(rows[1]['indicator_value'])
        self.assertEqual(rows[1]['alert_level'], 2)

    def test_import_rolls_back_after_partial_batch_failure(self):
        from ingestion.config_import import prepare, apply_import
        self.update("ALTER TABLE risk_rule_config ADD CONSTRAINT reject_example CHECK (monitor_item <> 'reject')")
        rows = prepare('rules', ROOT / 'examples/config/rules.csv')
        rows.append(dict(rows[0], monitor_id='DEMO-REJECT', monitor_item='reject'))
        try:
            with self.assertRaises(Exception), self.pool.connection() as conn:
                apply_import(conn, self.dialect, 'rules', rows)
            self.assertEqual(self.query('SELECT COUNT(*) AS n FROM risk_rule_config')[0]['n'], 0)
        finally:
            clause = 'DROP CHECK' if self.dialect == 'mysql' else 'DROP CONSTRAINT'
            self.update(f'ALTER TABLE risk_rule_config {clause} reject_example')

    def test_account_yield_aggregates_before_value_gate(self):
        from dao.financial_yield_dao import FinancialYieldDAO
        for amount, earnings in ((4, 1), (4, 2)):
            self.update('INSERT INTO position_snapshot (p_dt,wstwd,ztbh,jjztmc,qjsz,cwsy_bn,zhsy_bn,pjzjzy_bn) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                        (20250102, 'DEMO', 'P001', 'Example', amount, earnings, earnings * 2, 10))
        dao = FinancialYieldDAO()
        row = dao.get_account_yields('20250102', 'DEMO', ['P001'])[0]
        self.assertEqual(float(row['market_value']), 8)
        self.assertEqual(float(row['earnings']), 3)
        self.assertEqual(float(dao.get_account_yields('20250102', 'DEMO', ['P001'], True)[0]['earnings']), 6)
