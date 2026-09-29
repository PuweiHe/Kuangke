"""Each request owns its cards, even when clients reuse a request ID."""

from contextlib import contextmanager
from contextvars import ContextVar
import json

_cards: ContextVar[list | None] = ContextVar("cards", default=None)
_request_id: ContextVar[str] = ContextVar("request_id", default="")


@contextmanager
def card_scope(request_id):
    cards_token = _cards.set([])
    id_token = _request_id.set(request_id)
    try:
        yield
    finally:
        _cards.reset(cards_token)
        _request_id.reset(id_token)


def get_request_id():
    return _request_id.get()


def store_card(card):
    cards = _cards.get()
    if cards is not None:
        encoded = json.dumps(card, ensure_ascii=False, allow_nan=False)
        if encoded not in cards:
            cards.append(encoded)


def pop_cards(request_id):
    cards = _cards.get()
    if cards is None or request_id != _request_id.get():
        return []
    result = cards[:]
    cards.clear()
    return result
