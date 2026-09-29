from pydantic import BaseModel, Field
import uuid
import time

def get_uid():
    return str(uuid.uuid4()).replace('-', '')

def get_start_time():
    return int(round(time.time() * 1000))

class ChatBody(BaseModel):
    question: str
    conversation_id: str = Field(default_factory=get_uid)
    request_id: str = Field(default_factory=get_uid)
    user_id: str
    product_id: str = 'deepseek'
    stream: bool = True
    agent_extends: dict = Field(default_factory=dict, repr=False)
    start_time: int = Field(default_factory=get_start_time)
    token: str = Field(repr=False)
