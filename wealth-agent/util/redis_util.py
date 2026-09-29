import os
import redis.asyncio as redis
import json
import asyncio
from config.config import config
from config.logger import logger as log
_redis_client = None
_lock = asyncio.Lock()
SESSION_QUEUE_MAX_LEN = 3

async def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    async with _lock:
        if _redis_client is not None:
            return _redis_client
        try:
            redis_pool = redis.ConnectionPool(host=config['redis']['host'], port=config['redis']['port'], password=config['redis']['password'], db=config['redis']['db'], max_connections=config['redis'].get('max_connections', 20), socket_timeout=5, socket_connect_timeout=3, retry_on_timeout=True, health_check_interval=30)
            _redis_client = redis.Redis(connection_pool=redis_pool)
            await _redis_client.ping()
            log.info('Application event')
        except Exception as e:
            log.error('Application event')
            raise
    return _redis_client

async def add_message_to_redis(session_id: str, human_message: str, ai_response: str):
    if os.getenv('ENABLE_HISTORY', 'false').lower() != 'true':
        return None
    try:
        r = await _get_redis_client()
        key = f'''etf_conversation:{session_id}'''
        message = json.dumps({'human': human_message, 'ai': ai_response}, ensure_ascii=False)
        await r.rpush(key, message)
        await r.ltrim(key, -SESSION_QUEUE_MAX_LEN, -1)
        await r.expire(key, 3600)
    except Exception as e:
        log.error('Application event')

async def get_history_messages(session_id: str, max_messages: int=None) -> str:
    if os.getenv('ENABLE_HISTORY', 'false').lower() != 'true':
        return ''
    try:
        r = await _get_redis_client()
        key = f'''etf_conversation:{session_id}'''
        limit = max_messages if max_messages is not None else SESSION_QUEUE_MAX_LEN
        messages = await r.lrange(key, -limit, -1)
        history_parts = []
        for msg in messages:
            data = json.loads(msg.decode('utf-8'))
            history_parts.append(f'''human: {data.get('human', '')}\nassistant: {data.get('ai', '')}''')
        return '\n'.join(history_parts)
    except Exception as e:
        log.error('Application event')
        return ''
