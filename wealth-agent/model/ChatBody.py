from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
import time

def get_uid():
    return str(uuid.uuid4()).replace('-', '')

def get_start_time():
    return int(round(time.time() * 1000))

class ChatBody(BaseModel):
    question: str
    conversation_id: str
    request_id: str = Field(default_factory=get_uid)
    user_id: str | None
    product_id: str = 'deepseek'
    stream: bool = True
    agent_extends: dict = Field(default_factory=dict, repr=False)
    start_time: int = Field(default_factory=get_start_time)
    token: str = Field(repr=False)

class TextPart(BaseModel):
    type: str = 'text'
    text: str

class FilePart(BaseModel):
    type: str = 'file'
    file: Dict[str, Any]

class DataPart(BaseModel):
    type: str = 'data'
    data: Dict[str, Any]

class AgentMessage(BaseModel):
    role: str
    parts: List[Dict[str, Any]]
    meta_data: Optional[Dict[str, Any]] = {}

class Configuration(BaseModel):
    deep_mode: Optional[bool] = False
    execution_mode: Optional[str] = 'normal'
    enable_agent_custom_message: Optional[bool] = True
    enable_message: Optional[bool] = True

class ChatRequest(BaseModel):
    context_id: str
    task_id: Optional[str] = None
    run_id: Optional[str] = None
    history: Optional[List[AgentMessage]] = None
    message: AgentMessage
    configuration: Optional[Configuration] = Configuration()
    meta_data: Optional[Dict[str, Any]] = None

class ForwardRequest(BaseModel):
    message: Dict[str, Any]
    stream: bool
    metadata: Dict[str, Any]
