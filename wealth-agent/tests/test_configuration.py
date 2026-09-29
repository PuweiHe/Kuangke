import os
import unittest
from unittest.mock import patch
from config import get_project_api_uri, get_project_client_config

class ConfigurationTests(unittest.TestCase):
    def test_external_calls_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):get_project_api_uri("demo", "query")
            with self.assertRaises(RuntimeError):get_project_client_config("demo", "model")
    def test_configured_relative_path(self):
        with patch.dict(os.environ, {"ENABLE_EXTERNAL_SERVICES":"true", "DATA_API_BASE_URL":"https://example.invalid", "DATA_API_PATHS_JSON":'{"query":"/query"}'}, clear=True):
            self.assertEqual(get_project_api_uri("demo","query"),"https://example.invalid/query")
    def test_reject_external_endpoint_override(self):
        with patch.dict(os.environ, {"ENABLE_EXTERNAL_SERVICES":"true", "DATA_API_BASE_URL":"https://example.invalid", "DATA_API_PATHS_JSON":'{"query":"//elsewhere.invalid"}'}, clear=True):
            with self.assertRaises(ValueError):get_project_api_uri("demo","query")
