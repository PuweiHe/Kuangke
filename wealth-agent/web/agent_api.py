from fastapi import APIRouter
from agent.mutil_agent import agent_conversation, agent_conversation_no_stream
from sse_starlette import EventSourceResponse
from config.logger import logger as log
from model.ChatBody import ChatBody
from model.exceptions import TokenInvalidError
from util.mysql_util import insert_agent_log
from util.token_context import set_token, clear_token
from util.yield_util import generate_yield_json
agent_router = APIRouter(prefix='/api/conversation')

@agent_router.post('/wealth/stream')
async def chat(chat_body: ChatBody):
    log.info('Application event')
    pass

    async def generate_with_token():
        token_var = set_token(chat_body.token)
        try:
            async for chunk in agent_conversation(chat_body):
                yield chunk
        except TokenInvalidError as e:
            log.error('Application event')
            error_msg = f'{{"code": "10000013", "msg": "{str(e)}"}}'
            yield (await generate_yield_json('text', chat_body.request_id, '', '', error_msg))
        finally:
            clear_token(token_var)
    return EventSourceResponse(generate_with_token(), media_type='text/event-stream')

@agent_router.post('/wealth')
async def chat(chat_body: ChatBody):
    log.info('Application event')
    pass
    token_var = set_token(chat_body.token)
    try:
        res = await agent_conversation_no_stream(chat_body)
        return {'code': 200, 'msg': '操作成功', 'data': res}
    except TokenInvalidError as e:
        log.error('Application event')
        return {'code': 10000013, 'msg': str(e), 'data': None}
    finally:
        clear_token(token_var)
