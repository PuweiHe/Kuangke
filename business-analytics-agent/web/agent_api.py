"""Conversation boundaries: validation, time budget, event errors and cleanup."""

import asyncio
from contextlib import contextmanager
import logging
from fastapi import APIRouter, HTTPException
from sse_starlette import EventSourceResponse
from config import external_services_enabled
from model.ChatBody import ChatBody
from agent.mutil_agent import agent_conversation, agent_conversation_no_stream
from util.yield_util import generate_yield_json

logger = logging.getLogger(__name__)
agent_router = APIRouter(prefix="/api/conversation")
REQUEST_TIMEOUT_SECONDS = 45


@contextmanager
def request_scope(body):
    body.agent_extends = {"token": body.token}
    yield


def require_enabled():
    if not external_services_enabled():
        raise HTTPException(
            503,
            detail={
                "code": "services_disabled",
                "message": "External services are disabled; run the synthetic demo.",
            },
        )


def failure(exc):
    if isinstance(exc, TimeoutError):
        return 504, "request_timeout", "The request exceeded its time budget"
    return 502, "upstream_failure", "The model or data service could not complete the request"


@agent_router.post("/portfolio/stream")
async def stream_conversation(body: ChatBody):
    require_enabled()

    async def events():
        try:
            with request_scope(body):
                async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
                    async for event in agent_conversation(body):
                        yield event
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _, code, message = failure(exc)
            logger.warning(
                "conversation_failed request_id=%s error_type=%s",
                body.request_id,
                type(exc).__name__,
            )
            yield generate_yield_json(
                "error", body.request_id, "", "", {"code": code, "message": message}
            )
            yield "stream end"

    return EventSourceResponse(events(), send_timeout=15)


@agent_router.post("/portfolio")
async def conversation(body: ChatBody):
    require_enabled()
    body.stream = False
    try:
        with request_scope(body):
            async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
                answer = await agent_conversation_no_stream(body)
            return {"code": 200, "msg": "success", "data": answer, "request_id": body.request_id}
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        status, code, message = failure(exc)
        logger.warning(
            "conversation_failed request_id=%s error_type=%s", body.request_id, type(exc).__name__
        )
        raise HTTPException(
            status, detail={"code": code, "message": message, "request_id": body.request_id}
        ) from exc
