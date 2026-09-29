import os
import redis
import json
from config.config import config
from langchain_core.messages import HumanMessage, AIMessage
redis_pool = redis.ConnectionPool(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'], password=config['redis']['password'], max_connections=config['redis']['max_connections'])

def get_redis_client():
    return redis.Redis(connection_pool=redis_pool)
SESSION_QUEUE_MAX_LEN = 5

def add_message_to_redis(session_id: str, human_message: str, ai_response: str):
    if os.getenv('ENABLE_HISTORY', 'false').lower() != 'true':
        return None
    r = get_redis_client()
    key = f'mge_conversation:{session_id}'
    message = json.dumps({'human': human_message, 'ai': ai_response}, ensure_ascii=False)
    r.rpush(key, message)
    r.ltrim(key, -SESSION_QUEUE_MAX_LEN, -1)
    r.expire(key, 3600)

def get_history_messages(session_id: str):
    if os.getenv('ENABLE_HISTORY', 'false').lower() != 'true':
        return []
    r = get_redis_client()
    key = f'mge_conversation:{session_id}'
    messages = r.lrange(key, 0, -1)
    history_message = []
    for msg in messages:
        if msg and 'human' in json.loads(msg.decode('utf-8')):
            history_message.append(HumanMessage(content=str(json.loads(msg.decode('utf-8')).get('human'))))
        if msg and 'ai' in json.loads(msg.decode('utf-8')):
            history_message.append(AIMessage(content=str(json.loads(msg.decode('utf-8')).get('ai'))))
    return history_message
