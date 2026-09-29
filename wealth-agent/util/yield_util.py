import json
import uuid
from util.mysql_util import insert_agent_conversation_card

def get_uid():
    return str(uuid.uuid4()).replace('-', '')
res_tool = {'query_fund_info_tool': '获取基金相关信息', 'query_customer_info_tool': '获取客户相关信息', 'query_manager_info_tool': '获取基金经理相关信息', 'query_company_info_tool': '获取基金公司相关信息', 'compare_funds_tool': '正在进行基金比较', 'choose_fund_tool': '筛选符合条件的基金', 'choose_customer_tool': '筛选符合条件的客户', 'choose_manager_tool': '筛选符合条件的基金经理', 'choose_company_tool': '筛选符合条件的基金公司'}

async def generate_yield_json(type, request_id, name, status, data):
    if type == 'text':
        if 'plugin' in data and 'request_id' in data:
            result = json.loads(data)
        else:
            result = {'type': type, 'request_id': request_id, 'answer': data}
        return json.dumps(result, ensure_ascii=False)
    elif type == 'plugin':
        result = {'type': type, 'request_id': request_id, 'plugin': {'request_id': request_id, 'pluginName': name, 'status': status, 'describe': name}}
        return json.dumps(result, ensure_ascii=False)
    elif type == 'thinking':
        safe_data = data.replace('\\', '\\\\').replace('"', '\\"')
        result = {'type': type, 'request_id': request_id, 'thinking': {'request_id': request_id, 'content': safe_data}}
        return json.dumps(result, ensure_ascii=False)
    else:
        data_id = get_uid()
        result = {'type': type, 'request_id': request_id, 'card_id': name, 'data': {}, 'data_id': data_id}
        result_data = {'type': type, 'request_id': request_id, 'card_id': name, 'data': data, 'data_id': data_id}
        pass
        return json.dumps(result, ensure_ascii=False)
