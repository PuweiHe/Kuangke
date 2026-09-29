"""Input validation and transaction rollback without external database services."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ingestion.config_import import ImportValidationError, SCHEMAS, apply_import, prepare, validate
ROOT = Path(__file__).resolve().parents[1]


class ImportTests(unittest.TestCase):
    def test_examples_and_percentage_conversion(self):
        for kind in SCHEMAS:
            rows = prepare(kind, ROOT / 'examples/config' / (kind + '.csv'))
            self.assertEqual(len(rows), 1)
        self.assertEqual(prepare('rules', ROOT / 'examples/config/rules.csv')[0]['threshold'], '0.75')
        self.assertEqual(prepare('assets', ROOT / 'examples/config/assets.csv')[0]['asset_code'], '00001.HK')

    def test_duplicate_keys_and_bad_threshold_report_row(self):
        rows = prepare('rules', ROOT / 'examples/config/rules.csv')
        with self.assertRaises(ImportValidationError) as ctx:
            validate('rules', SCHEMAS['rules'][2], [(2, rows[0]), (3, rows[0])])
        self.assertIn('Row 3', str(ctx.exception))
        for bad in ('NaN', '-1', '=1+1', '#REF!', 'abc'):
            with self.assertRaises(ImportValidationError):
                validate('rules', SCHEMAS['rules'][2], [(2, dict(rows[0], threshold=bad))])

    def test_numeric_identifier_is_rejected(self):
        rows = prepare('assets', ROOT / 'examples/config/assets.csv')
        with self.assertRaises(ImportValidationError):
            validate('assets', SCHEMAS['assets'][2], [(2, dict(rows[0], asset_code=1))])

    def test_column_errors_and_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'bad.csv'
            for content in ('', 'monitor_id,monitor_id\nA,A\n', 'monitor_id\nA,B\n'):
                p.write_text(content)
                with self.assertRaises(ImportValidationError): prepare('rules', p)

    def test_write_failure_rolls_back_without_commit(self):
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.executemany.side_effect = RuntimeError('synthetic failure')
        rows = prepare('rules', ROOT / 'examples/config/rules.csv')
        with self.assertRaises(RuntimeError): apply_import(connection, 'mysql', 'rules', rows)
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()

    def test_dimension_requires_existing_rule(self):
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchone.return_value = None
        with self.assertRaises(ImportValidationError):
            apply_import(connection, 'pg', 'dimensions', prepare('dimensions', ROOT / 'examples/config/dimensions.csv'))
        connection.rollback.assert_called_once()
