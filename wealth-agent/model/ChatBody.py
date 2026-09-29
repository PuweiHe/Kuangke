"""Bound untrusted request fields before invoking models or data adapters."""

import time
import uuid
from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints

Identifier = Annotated[
    str, StringConstraints(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
]


class ChatBody(BaseModel):
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8000)
    ]
    conversation_id: Identifier = Field(default_factory=lambda: uuid.uuid4().hex)
    request_id: Identifier = Field(default_factory=lambda: uuid.uuid4().hex)
    user_id: Identifier
    product_id: Identifier = "deepseek"
    stream: bool = True
    agent_extends: dict = Field(default_factory=dict, repr=False)
    start_time: int = Field(default_factory=lambda: int(time.time() * 1000))
    token: str = Field(min_length=1, max_length=4096, repr=False)

    @property
    def session_key(self) -> str:
        return f"{self.product_id}:{self.user_id}:{self.conversation_id}"
