from typing import Any, List, Dict
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到基金经理筛选结果'

@tool('choose_manager_tool', args_schema={'type': 'object', 'properties': {'ttlMngNum': {'type': 'string', 'description': '管理基金数量，规则举例：等于5时填 5~5 ，大于5时填 5~ ，小于5时填 ~5 ， 大于5小于8时填 5~8'}, 'mngDays': {'type': 'string', 'description': '从业年限 (天)，规则举例：等于5天时填 5~5 ，大于5天时填 5~ ，小于5天时填 ~5 ， 大于5天小于8天时填 5~8'}, 'mngScale': {'type': 'string', 'description': '管理规模(元), 规则举例：等于5万时填 50000~50000 ，大于5万时填 50000~ ，小于5万时填 ~50000 ， 大于5万小于8万时填 50000~80000'}, 'oneYearCumlRet': {'type': 'string', 'description': '近一年收益率，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%小于8%时填 5~8'}, 'orgName': {'type': 'array', 'description': '基金公司名称'}, 'mngName': {'type': 'array', 'description': '基金经理姓名'}, 'anlZed': {'type': 'string', 'description': '总任职年化回报，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%小于8%时填 5~8'}, 'pageNum': {'type': 'number', 'default': 1, 'description': '页码，默认为1'}, 'pageSize': {'type': 'number', 'default': 10, 'description': '每页数量，默认为10'}, 'orderBy': {'type': 'string', 'description': '排序字段, 必须为已有筛选指标'}, 'isasc': {'type': 'boolean', 'description': '排序方式，True-升序 False-降序', 'enum': [True, False]}}, 'required': ['pageNum', 'pageSize']})
async def choose_manager_tool(**kwargs):
    """Choose manager tool. Use validated tool arguments and return adapter results."""
    arguments = kwargs
    choose_result, card = await get_choose_mng(arguments)
    if choose_result and card:
        store_card(card)
        return [[choose_result], None]
    elif isinstance(choose_result, str) and card is None:
        return [[choose_result], None]
    else:
        return [[_ERROR_MESSAGE], None]

async def get_choose_mng(arguments: dict) -> Any:
    """Get choose mng. Use validated tool arguments and return adapter results."""
    try:
        payload = {}
        param_mapping = {'ttlMngNum': arguments.get('ttlMngNum'), 'mngDays': arguments.get('mngDays'), 'mngScale': arguments.get('mngScale'), 'oneYearCumlRet': arguments.get('oneYearCumlRet'), 'orgName': arguments.get('orgName'), 'mngName': arguments.get('mngName'), 'anlZed': arguments.get('anlZed'), 'pageNum': arguments.get('pageNum', 1), 'pageSize': arguments.get('pageSize', 10), 'orderBy': arguments.get('orderBy'), 'isasc': arguments.get('isasc')}
        for key, value in param_mapping.items():
            if value is not None and value != '':
                if key == 'isasc' and value == True:
                    payload[key] = 'true'
                elif key == 'isasc' and value == False:
                    payload[key] = 'false'
                elif key == 'orgName' and isinstance(value, list):
                    payload[key] = ','.join(value)
                elif key == 'mngName' and isinstance(value, list):
                    payload[key] = ','.join(value)
                else:
                    payload[key] = value
        url = f'''{get_project_api_uri('wealth', 'choose_manager')}'''
        header = {}
        response = await http_execute_async(url, 'POST', payload, header)
        logger.info('Application event')
        if response and (response.get('code') == 0 or response.get('code') == '0'):
            query_content = response.get('content') or {}
            query_result = query_content.get('VALUE_LIST1') or []
            count_num = query_content.get('NUM_TOTAL_COUNT') or None
            if query_result and len(query_result) > 0:
                mng_list = []
                for i in query_result:
                    mng_item = {}
                    if i.get('mngname'):
                        mng_item['基金经理'] = i.get('mngname')
                    if i.get('fund_manager_id'):
                        mng_item['基金经理ID'] = i.get('fund_manager_id')
                    if i.get('orgname'):
                        mng_item['所属基金公司'] = i.get('orgname')
                    if i.get('fund_company_id'):
                        mng_item['所属基金公司ID'] = i.get('fund_company_id')
                    if i.get('ttlmngnum'):
                        mng_item['管理基金数量'] = i.get('ttlmngnum')
                    if i.get('mngdays'):
                        mng_item['从业年限 (天)'] = i.get('mngdays')
                    if i.get('mngscale'):
                        mng_item['管理规模'] = i.get('mngscale')
                    if i.get('oneYearCumlRet'):
                        mng_item['近一年收益'] = f'''{i.get('oneYearCumlRet')}%'''
                    if i.get('anlzed'):
                        mng_item['总任职年化回报'] = f'''{i.get('anlzed')}%'''
                    mng_list.append(mng_item)
                if isinstance(count_num, int) and count_num > 10:
                    total_count = count_num
                    text = f'''共筛选出 {total_count} 名符合条件的基金经理, 前{len(query_result)}名为:\n{mng_list}'''
                else:
                    total_count = len(query_result)
                    text = f'''共筛选出 {total_count} 名符合条件的基金经理:\n{mng_list}'''
                return (text, None)
            else:
                return ('未找到符合条件的基金经理', None)
        else:
            logger.error('Application event')
            return (_ERROR_MESSAGE, None)
    except TokenInvalidError:
        raise
    except Exception as e:
        logger.error('Application event')
        return (_ERROR_MESSAGE, None)
