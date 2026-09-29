def execute_insert_sql(sql_command, **kwargs):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def execute_select_sql(sql_command, **kwargs):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def execute_update_sql(sql_command, **kwargs):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def update_agent(request_id: str, **kwargs):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def insert_agent_log(request_id: str, data: str):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def insert_agent_conversation(conversation_id, user_id, role, content, request_id='', extends=[], extends_id=''):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def insert_agent_record(request_id, conversation_id, history_messages, agent, type, question, final_answer, start_time):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None

def insert_agent_conversation_card(card_id, data_card, data_card_contain_id):
    """No-op audit adapter: request content is not persisted in this portfolio."""
    return None
