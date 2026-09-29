"""Run the actual supervisor and async specialist with a scripted chat model."""

import os
import unittest
from unittest.mock import patch, AsyncMock
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from fastapi.testclient import TestClient
from main import app
from agent import mutil_agent as orchestration


class ScriptedModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


class GraphTests(unittest.TestCase):
    def test_supervisor_awaits_specialist_and_data_tool(self):
        calls = []

        @tool("query_fund_info_tool")
        async def data_tool(query: str) -> str:
            """Return synthetic evidence for a research request."""
            calls.append(query)
            return "Synthetic revenue is 50"

        model = ScriptedModel(
            messages=iter(
                [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {"name": "fund_event", "args": {"request": "lookup"}, "id": "route"}
                        ],
                    ),
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "query_fund_info_tool",
                                "args": {"query": "lookup"},
                                "id": "data",
                            }
                        ],
                    ),
                    AIMessage(content="Synthetic revenue is 50"),
                    AIMessage(content="The synthetic value is 50"),
                ]
            )
        )
        with (
            patch.dict(os.environ, {"ENABLE_EXTERNAL_SERVICES": "true", "ENABLE_HISTORY": "false"}),
            patch.object(orchestration, "query_fund_info_tool", data_tool),
            patch.object(orchestration, "_get_cached_model", return_value=model),
            patch.object(orchestration, "recognize_and_query_entities", AsyncMock(return_value=[])),
        ):
            with TestClient(app) as client:
                response = client.post(
                    "/api/conversation/wealth",
                    json={"question": "lookup", "user_id": "demo", "token": "test-token"},
                )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["data"], "The synthetic value is 50")
        self.assertEqual(calls, ["lookup"])
