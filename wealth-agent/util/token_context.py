from contextvars import ContextVar
from typing import Optional
token_context: ContextVar[Optional[str]] = ContextVar('token_context', default=None)

def set_token(token: str):
    return token_context.set(token)

def get_token() -> Optional[str]:
    return token_context.get()

def clear_token(token_var):
    token_context.reset(token_var)
