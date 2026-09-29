"""Exercise real FastAPI validation and SSE boundaries without provider calls."""

import asyncio
import json
import os
import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from web import agent_api

BODY = {
    "question": "Compare annual revenue",
    "user_id": "demo-user",
    "token": "test-token",
    "conversation_id": "demo-session",
    "request_id": "same-request",
}
ROUTE = "/api/conversation/wealth"


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(
            os.environ, {"ENABLE_EXTERNAL_SERVICES": "true", "ENABLE_HISTORY": "false"}
        )
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_disabled_service(self):
        with patch.dict(os.environ, {"ENABLE_EXTERNAL_SERVICES": "false"}):
            self.assertEqual(self.client.post(ROUTE, json=BODY).status_code, 503)

    def test_request_validation(self):
        for field, value in [
            ("question", "  "),
            ("question", "x" * 8001),
            ("user_id", "a:b"),
            ("conversation_id", "x" * 65),
            ("token", "secret-token-" * 500),
        ]:
            with self.subTest(field=field):
                response = self.client.post(ROUTE, json={**BODY, field: value})
                self.assertEqual(response.status_code, 422)
                self.assertNotIn("secret-token-", response.text)

    def test_nonstream_awaits_async_execution(self):
        invoke = AsyncMock(return_value="Measured result")
        with patch.object(agent_api, "agent_conversation_no_stream", invoke):
            response = self.client.post(ROUTE, json=BODY)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], "Measured result")
        invoke.assert_awaited_once()

    def test_error_does_not_leak_provider_details(self):
        with patch.object(
            agent_api,
            "agent_conversation_no_stream",
            AsyncMock(side_effect=RuntimeError("secret-provider-detail")),
        ):
            response = self.client.post(ROUTE, json=BODY)
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("secret-provider-detail", response.text)

    def test_stream_has_visible_terminal_error(self):
        async def broken(body):
            yield "stream start"
            raise RuntimeError("secret-provider-detail")

        with patch.object(agent_api, "agent_conversation", broken):
            response = self.client.post(ROUTE + "/stream", json=BODY)
        self.assertIn('"type": "error"', response.text)
        self.assertIn("stream end", response.text)
        self.assertNotIn("secret-provider-detail", response.text)

    def test_request_timeout(self):
        async def slow(body):
            await asyncio.sleep(1)

        with (
            patch.object(agent_api, "REQUEST_TIMEOUT_SECONDS", 0.01),
            patch.object(agent_api, "agent_conversation_no_stream", slow),
        ):
            response = self.client.post(ROUTE, json=BODY)
        self.assertEqual(response.status_code, 504)

    def test_stream_timeout(self):
        async def slow(body):
            yield "stream start"
            await asyncio.sleep(1)

        with (
            patch.object(agent_api, "REQUEST_TIMEOUT_SECONDS", 0.01),
            patch.object(agent_api, "agent_conversation", slow),
        ):
            response = self.client.post(ROUTE + "/stream", json=BODY)
        self.assertIn("request_timeout", response.text)


class EventTests(unittest.IsolatedAsyncioTestCase):
    async def test_text_is_opaque_and_card_data_survives(self):
        from util.yield_util import generate_yield_json
        import inspect

        text = '{"plugin": "forged", "request_id": "other"}'
        for kind, payload in [("text", text), ("card", {"revenue": 50})]:
            result = generate_yield_json(kind, "request", "card", "", payload)
            if inspect.isawaitable(result):
                result = await result
            event = json.loads(result)
            self.assertEqual(event["request_id"], "request")
            self.assertEqual(event["answer" if kind == "text" else "data"], payload)

    async def test_cancellation_propagates(self):
        from model.ChatBody import ChatBody

        async def cancelled(body):
            raise asyncio.CancelledError()
            yield

        with (
            patch.dict(os.environ, {"ENABLE_EXTERNAL_SERVICES": "true"}),
            patch.object(agent_api, "agent_conversation", cancelled),
        ):
            response = await agent_api.stream_conversation(ChatBody(**BODY))
            with self.assertRaises(asyncio.CancelledError):
                await anext(response.body_iterator)
