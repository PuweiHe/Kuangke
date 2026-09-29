from util.http_util import UpstreamError
from typing import Any, List, Dict
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到基金公司筛选结果'

@tool('choose_company_tool', args_schema={'type': 'object', 'properties': {'mngScale': {'type': 'string', 'description': '管理规模(元), 规则举例：等于5万时填 50000~50000 ，大于5万时填 50000~ ，小于5万时填 ~50000 ， 大于5万且小于8万时填 50000~80000'}, 'mngAvgYear': {'type': 'string', 'description': '经理平均任职年限，规则举例：等于5年时填 5~5 ，大于5年时填 5~ ，小于5年时填 ~5 ， 大于5年且小于8年时填 5~8'}, 'mngNum': {'type': 'string', 'description': '基金经理数量，规则举例：等于5时填 5~5 ，大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'fdNum': {'type': 'string', 'description': '基金数量，规则举例：等于5时填 5~5 ，大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'pageNum': {'type': 'number', 'default': 1, 'description': '页码，默认为1'}, 'pageSize': {'type': 'number', 'default': 10, 'description': '每页数量，默认为10'}, 'orderBy': {'type': 'string', 'description': '排序字段, 必须为已有筛选指标'}, 'isasc': {'type': 'boolean', 'description': '排序方式，True-升序 False-降序', 'enum': [True, False]}}, 'required': ['pageNum', 'pageSize']})
async def choose_company_tool(**kwargs):
    """Choose company tool. Use validated tool arguments and return adapter results."""
    arguments = kwargs
    choose_result, card = await get_choose_company(arguments)
    if choose_result and card:
        store_card(card)
        return [[choose_result], None]
    elif isinstance(choose_result, str) and card is None:
        return [[choose_result], None]
    else:
        return [[_ERROR_MESSAGE], None]

async def get_choose_company(arguments: dict) -> Any:
    """Get choose company. Use validated tool arguments and return adapter results."""
    try:
        payload = {}
        param_mapping = {'mngScale': arguments.get('mngScale'), 'mngAvgYear': arguments.get('mngAvgYear'), 'mngNum': arguments.get('mngNum'), 'fdNum': arguments.get('fdNum'), 'pageNum': arguments.get('pageNum', 1), 'pageSize': arguments.get('pageSize', 10), 'orderBy': arguments.get('orderBy', 'mngScale'), 'isasc': arguments.get('isasc', False)}
        for key, value in param_mapping.items():
            if value is not None and value != '':
                if key == 'isasc' and value == True:
                    payload[key] = 'true'
                elif key == 'isasc' and value == False:
                    payload[key] = 'false'
                else:
                    payload[key] = value
        url = f'''{get_project_api_uri('wealth', 'choose_company')}'''
        header = {}
        response = await http_execute_async(url, 'POST', payload, header)
        logger.info('Application event')
        if response and (response.get('code') == 0 or response.get('code') == '0'):
            query_content = response.get('content') or {}
            query_result = query_content.get('VALUE_LIST1') or []
            count_num = query_content.get('NUM_TOTAL_COUNT') or None
            if query_result and len(query_result) > 0:
                company_list = []
                for i in query_result:
                    company_item = {}
                    if i.get('orgname'):
                        company_item['基金公司名称'] = i.get('orgname')
                    if i.get('fund_company_id'):
                        company_item['基金公司ID'] = i.get('fund_company_id')
                    if i.get('mngscale'):
                        company_item['管理规模'] = i.get('mngscale')
                    if i.get('mngavgyear'):
                        company_item['经理平均任职年限'] = i.get('mngavgyear')
                    if i.get('mngnum'):
                        company_item['基金经理数量'] = i.get('mngnum')
                    if i.get('fdnum'):
                        company_item['基金数量'] = i.get('fdnum')
                    company_list.append(company_item)
                if isinstance(count_num, int) and count_num > 10:
                    total_count = count_num
                    text = f'''共筛选出 {total_count} 家符合条件的基金公司, 前{len(query_result)}家为:\n{company_list}'''
                else:
                    total_count = len(query_result)
                    text = f'''共筛选出 {total_count} 家符合条件的基金公司:\n{company_list}'''
                return (text, None)
            else:
                return ('未找到符合条件的基金公司', None)
        else:
            logger.error('Application event')
            return (_ERROR_MESSAGE, None)
    except (TokenInvalidError, UpstreamError):
        raise
    except Exception as e:
        logger.error('Application event')
        return (_ERROR_MESSAGE, None)
