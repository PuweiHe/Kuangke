import asyncio
import json
import os
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from pydantic import ValidationError
from agent.entity_schema import EntityNames
from agent.entity_recognizer import query_entities_with_concurrency, query_single_entity
from util.card_util import card_scope, store_card, pop_cards, get_request_id
from util.http_util import http_execute_async, UpstreamError
from util.token_context import set_token, clear_token


class BoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_client_id_cannot_mix_parallel_cards(self):
        async def worker(label):
            with card_scope("same"):
                store_card({"card_id": label, "consumer_data_card": {"label": label}})
                await asyncio.sleep(0)
                return json.loads(pop_cards("same")[0])["card_id"]

        self.assertEqual(await asyncio.gather(worker("one"), worker("two")), ["one", "two"])
        self.assertEqual(get_request_id(), "")
        self.assertEqual(pop_cards("same"), [])

    async def test_entity_concurrency_and_unknown_type(self):
        active = maximum = 0

        async def lookup(name):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            await asyncio.sleep(0.001)
            active -= 1
            return {"status": "success", "data": name}

        with patch("agent.entity_recognizer.query_single_entity", lookup):
            found, conflicts = await query_entities_with_concurrency(["a", "b", "c", "d"], 2)
        self.assertEqual(found, ["a", "b", "c", "d"])
        self.assertEqual(maximum, 2)
        self.assertIsNone(conflicts)
        with self.assertRaises(ValueError):
            await query_entities_with_concurrency(["a"], 0)

    async def test_transport_failures_do_not_look_like_empty_data(self):
        for status, body in [
            (500, {"code": 0}),
            (200, []),
            (200, {"code": 500}),
            (200, "bad-json"),
        ]:
            response = httpx.Response(
                status, json=body, request=httpx.Request("POST", "https://example.invalid/data")
            )
            client = AsyncMock()
            client.request.return_value = response
            with (
                patch.dict(os.environ, {"ENABLE_EXTERNAL_SERVICES": "true"}),
                patch("util.http_util.get_http_client", return_value=client),
            ):
                with self.assertRaises(UpstreamError):
                    await http_execute_async("https://example.invalid/data", "POST")

    async def test_entity_payload_validation(self):
        with patch("agent.entity_recognizer.get_project_api_uri", return_value="unused"):
            for content in ({}, "invalid", [1]):
                with patch(
                    "agent.entity_recognizer.http_execute_async",
                    AsyncMock(return_value={"code": 0, "content": content}),
                ):
                    with self.assertRaises(UpstreamError):
                        await query_single_entity("Fund")
            with patch(
                "agent.entity_recognizer.http_execute_async",
                AsyncMock(return_value={"code": 200, "content": []}),
            ):
                self.assertEqual((await query_single_entity("Fund"))["status"], "not_found")

    async def test_request_token_is_forwarded_without_mutating_headers(self):
        client = AsyncMock()
        client.request.return_value = httpx.Response(
            200,
            json={"code": 0, "content": []},
            request=httpx.Request("POST", "https://example.invalid/data"),
        )
        headers = {}
        token = set_token("test-token")
        try:
            with (
                patch.dict(os.environ, {"ENABLE_EXTERNAL_SERVICES": "true"}),
                patch("util.http_util.get_http_client", return_value=client),
            ):
                await http_execute_async("https://example.invalid/data", "POST", headers=headers)
            self.assertEqual(
                client.request.call_args.kwargs["headers"]["Authorization"], "test-token"
            )
            self.assertEqual(headers, {})
        finally:
            clear_token(token)


class ExtractionTests(unittest.TestCase):
    def test_schema_rejects_malformed_and_oversized_output(self):
        for data in [
            {"entities": [""]},
            {"entities": ["x"] * 11},
            {"entities": [1]},
            {"entities": "fund"},
            {"entities": [], "instructions": "ignore"},
        ]:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                EntityNames.model_validate(data)
        self.assertEqual(
            EntityNames.model_validate({"entities": [" Fund ", "Fund"]}).entities, ["Fund"]
        )
