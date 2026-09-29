"""Exercise the synthetic browser demo over HTTP and its SQLite boundary."""

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from portfolio_demo.server import MetricsRepository, make_handler


RECORDS = json.loads((Path(__file__).resolve().parents[1] / 'examples/branches.json').read_text())


class PortfolioDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repository = MetricsRepository(RECORDS)
        try:
            cls.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(cls.repository))
        except PermissionError:
            cls.repository.close()
            raise unittest.SkipTest('Loopback sockets are unavailable in this sandbox')
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.repository.close()

    def request(self, path):
        try:
            with urlopen(self.base + path, timeout=2) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_branch_selection_and_missing_baseline(self):
        status, report = self.request('/api/metrics?year=2025&branch_id=BRANCH003')
        self.assertEqual(status, 200)
        self.assertEqual(report['total_revenue_million'], 100)
        self.assertEqual(report['selected_branch']['share'], 0.2)
        self.assertIsNone(report['selected_branch']['growth'])
        self.assertEqual(report['branches'][0]['growth'], 0.25)
        self.assertTrue(report['synthetic'])

    def test_available_years_and_static_ui(self):
        self.assertEqual(self.request('/api/years'), (200, {'years': [2025, 2024], 'synthetic': True}))
        with urlopen(self.base + '/', timeout=2) as response:
            self.assertIn(b'Branch performance', response.read())
            self.assertEqual(response.headers['Content-Type'], 'text/html; charset=utf-8')

    def test_bad_query_and_unknown_branch(self):
        for path, expected in [
            ('/api/metrics', 400),
            ('/api/metrics?year=2025&year=2024', 400),
            ('/api/metrics?year=2025&branch_id=%27%20OR%201%3D1', 404),
            ('/api/metrics?year=2026', 404),
            ('/api/metrics?year=2025&debug=1', 400),
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], expected)


class RepositoryTests(unittest.TestCase):
    def test_duplicate_observation_rejected_by_database(self):
        with self.assertRaises(ValueError):
            MetricsRepository(RECORDS + [RECORDS[-1]])

    def test_parameterized_branch_lookup(self):
        repository = MetricsRepository(RECORDS)
        try:
            with self.assertRaises(LookupError):
                repository.report(2025, "' OR 1=1")
            self.assertIsNone(repository.report(2025, 'BRANCH003')['selected_branch']['growth'])
        finally:
            repository.close()


if __name__ == '__main__':
    unittest.main()
