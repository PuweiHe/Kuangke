import contextvars
import json
from typing import Any
_request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar('request_id', default='')
_card_registry: dict[str, list[str]] = {}

def set_request_id(request_id: str):
    _request_id_ctx.set(request_id)

def get_request_id() -> str:
    return _request_id_ctx.get()

def store_card(card: dict[str, Any]):
    rid = _request_id_ctx.get()
    if rid:
        _card_registry.setdefault(rid, []).append(json.dumps(card, ensure_ascii=False))

def pop_cards(request_id: str) -> list[str]:
    return _card_registry.pop(request_id, [])
