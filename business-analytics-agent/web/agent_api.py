import asyncio
from fastapi import APIRouter
from agent.mutil_agent import agent_conversation, agent_conversation_no_stream
from sse_starlette import EventSourceResponse
from config.logger import logger as log
from model.ChatBody import ChatBody
from util.mysql_util import insert_agent_log
agent_router = APIRouter(prefix='/api/conversation')

@agent_router.post('/portfolio/stream')
async def chat(chat_body: ChatBody):
    log.info('Application event')
    if chat_body.token:
        chat_body.agent_extends['token'] = chat_body.token
    pass
    return EventSourceResponse(agent_conversation(chat_body), media_type='text/event-stream')

@agent_router.post('/portfolio')
async def chat(chat_body: ChatBody):
    log.info('Application event')
    if chat_body.token:
        chat_body.agent_extends['token'] = chat_body.token
    chat_body.stream = False
    pass
    res = await asyncio.to_thread(agent_conversation_no_stream, chat_body)
    return {'code': 200, 'msg': '操作成功', 'data': res}
