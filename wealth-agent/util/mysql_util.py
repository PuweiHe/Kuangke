def update_agent(request_id: str, **kwargs):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def insert_agent_log_old(request_id: str, data: str):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

async def insert_agent_log(request_id: str, data: str):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def insert_agent_conversation_old(conversation_id, user_id, role, content, request_id='', extends=[], extends_id=''):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

async def insert_agent_conversation(conversation_id, user_id, role, content, request_id='', extends=[], extends_id=''):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def insert_agent_record_old(request_id, conversation_id, history_messages, agent, type, question, final_answer, start_time):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

async def insert_agent_record(request_id, conversation_id, history_messages, agent, question, final_answer, start_time):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

async def insert_agent_conversation_card(card_id, data_card, data_card_contain_id):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None
