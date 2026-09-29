import json
import uuid
from util.mysql_util import insert_agent_conversation_card

def get_uid():
    return str(uuid.uuid4()).replace('-', '')
res_tool = {'customer_info_tool': '查询客户基本信息', 'customer_hold_info_tool': '查询客户持仓信息', 'customer_opened_business_info_tool': '查询指定客户的已开通业务信息', 'customer_available_business_info_tool': '查询指定客户的可开通业务信息', 'customer_participated_business_info_tool': '查询指定客户的已参与业务信息', 'web_search_tool': '正在联网搜索', 'filter_customer_info_tool': '筛选客户基本信息数据', 'filter_revenue_generation_info_tool': '筛选客户创收数据', 'filter_property_info_tool': '筛选客户资产数据', 'asset_information_tool': '查询客户资产信息', 'revenue_generating_information_tool': '查询客户创收信息', 'transaction_volume_information_tool': '查询客户交易量信息', 'filter_indicator_tool': '正在筛选用户指标数据', 'get_labels_tool': '正在查询标签数据', 'branch_company_info_tool': '查询机构基本信息', 'business_management_tool': '筛选机构经营指标数据', 'performance_report_tool': '正在生成业绩报告', 'sandbox_tool': '正在计算并绘图'}

def generate_yield_json(type, request_id, name, status, data):
    global result
    if type == 'text':
        if 'plugin' in data and 'request_id' in data:
            result = json.loads(data)
        else:
            result = {'type': type, 'request_id': request_id, 'answer': data}
    elif type == 'plugin':
        result = {'type': type, 'request_id': request_id, 'plugin': {'request_id': request_id, 'pluginName': name, 'status': status, 'describe': data}}
    else:
        data_id = get_uid()
        result = {'type': type, 'request_id': request_id, 'card_id': name, 'data': {}, 'data_id': data_id}
        result_data = {'type': type, 'request_id': request_id, 'card_id': name, 'data': data}
        pass
    return json.dumps(result, ensure_ascii=False)
