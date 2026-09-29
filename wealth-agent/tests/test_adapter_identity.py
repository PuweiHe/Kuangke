"""External adapter calls must not silently use a shared user identity."""

import os
import unittest
from unittest.mock import patch

from util.adapter_identity import get_data_api_user_id


class AdapterIdentityTests(unittest.TestCase):
    def test_missing_identity_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'DATA_API_USER_ID'):
                get_data_api_user_id()

    def test_explicit_identity_is_used(self):
        with patch.dict(os.environ, {'DATA_API_USER_ID': 'SYNTHETIC_USER'}):
            self.assertEqual(get_data_api_user_id(), 'SYNTHETIC_USER')
