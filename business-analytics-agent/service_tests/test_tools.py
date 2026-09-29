import os
import unittest
from unittest.mock import Mock, patch
from util.http_util import http_execute, UpstreamError
from agent.mutil_agent import extract_cards
from tools.sandbox_tool import sandbox_tool


class ToolTests(unittest.TestCase):
    def test_failed_business_code_is_not_empty_data(self):
        response = Mock(status_code=200)
        response.json.return_value = {"code": 500, "data": []}
        with (
            patch.dict(os.environ, {"ENABLE_EXTERNAL_SERVICES": "true"}),
            patch("util.http_util.requests.request", return_value=response) as request,
        ):
            with self.assertRaises(UpstreamError):
                http_execute("https://example.invalid/data", "POST", "test", {})
            self.assertEqual(request.call_args.kwargs["timeout"], (5, 20))
            self.assertFalse(request.call_args.kwargs["allow_redirects"])

    def test_card_parser_preserves_apostrophes(self):
        import json

        card = {"card_id": "branch", "consumer_data_card": {"name": "Branch's revenue"}}
        self.assertEqual(extract_cards(json.dumps([["summary"], card])), [card])
        self.assertEqual(extract_cards("ordinary text"), [])

    def test_model_cannot_enable_code_execution(self):
        with patch.dict(
            os.environ, {"ENABLE_EXTERNAL_SERVICES": "true", "ENABLE_CODE_EXECUTION": "false"}
        ):
            result = sandbox_tool.invoke({"code": "print(1)"})
        self.assertIn("disabled", result[0]["function_response"])
