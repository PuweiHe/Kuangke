from util.http_util import UpstreamError
from typing import Any, List, Dict
import asyncio
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到基金经理信息'

@tool('query_manager_info_tool', args_schema={'type': 'object', 'properties': {'manager_name_or_ID': {'type': 'string', 'description': '基金经理姓名or基金经理ID, prefer基金经理ID'}, 'feature': {'type': 'string', 'description': '查询的基金经理的信息特征', 'enum': ['基本信息', '在管产品', '业绩信息']}}, 'required': ['manager_name_or_ID']})
async def query_manager_info_tool(**kwargs):
    """Query manager info tool. Use validated tool arguments and return adapter results."""
    arguments = kwargs
    manager_result, card = await get_manager_info(arguments)
    if manager_result and card:
        store_card(card)
        return [[manager_result], None]
    elif isinstance(manager_result, str) and card is None:
        return [[manager_result], None]
    else:
        return [[_ERROR_MESSAGE], None]

async def get_manager_info(arguments: dict) -> Any:
    manager_item = arguments.get('manager_name_or_ID', '')
    feature = arguments.get('feature', None)
    try:
        if contains_chinese(manager_item):
            if manager_item.endswith('经理'):
                define_mng_name = manager_item.replace('经理', '')
            else:
                define_mng_name = manager_item
            response = await search_mng_api(define_mng_name)
            if response['code'] == 0 or response['code'] == '0':
                query_result = response.get('content') or []
            else:
                return ('无法查询到该基金经理，直接告知用户: 请用户提供正确基金经理姓名。', None)
            if len(query_result) == 1:
                mng_id = query_result[0].get('fund_manager_id')
                mng_name = query_result[0].get('fund_manager_name')
                company_name = query_result[0].get('full_name')
            elif len(query_result) > 1:
                mng_list = []
                for i in query_result:
                    mng_dict = {}
                    if i.get('fund_manager_name'):
                        mng_dict['基金经理姓名'] = i.get('fund_manager_name')
                    if i.get('fund_manager_id'):
                        mng_dict['基金经理ID'] = i.get('fund_manager_id')
                    if i.get('company_name'):
                        mng_dict['所属基金公司'] = i.get('company_name')
                    mng_list.append(mng_dict)
                text = f'根据{manager_item}查出来{len(query_result)}个结果，\n{mng_list}, 请选择你想查询的基金经理'
                return (text, None)
            else:
                return ('无法查询到该基金经理，直接告知用户: 请用户提供正确基金经理姓名。', None)
        elif manager_item.isalnum():
            response = await search_mng_api(manager_item)
            if response['code'] == 0 or response['code'] == '0':
                query_result = response.get('content') or []
            else:
                return ('无法查询到该基金经理，直接告知用户: 请用户提供正确基金经理ID', None)
            if len(query_result) == 1:
                mng_id = query_result[0].get('fund_manager_id')
                mng_name = query_result[0].get('fund_manager_name')
                company_name = query_result[0].get('full_name')
            elif len(query_result) > 1:
                mng_list = []
                for i in query_result:
                    mng_dict = {}
                    if i.get('fund_manager_name'):
                        mng_dict['基金经理姓名'] = i.get('fund_manager_name')
                    if i.get('fund_manager_id'):
                        mng_dict['基金经理ID'] = i.get('fund_manager_id')
                    if i.get('company_name'):
                        mng_dict['所属基金公司'] = i.get('company_name')
                    mng_list.append(mng_dict)
                text = f'根据{manager_item}查出来{len(query_result)}个结果，\n{mng_list}, 请选择你想查询的基金经理'
                return (text, None)
            else:
                return ('无法查询到该基金经理，直接告知用户: 请用户提供正确基金经理ID', None)
        else:
            return ('你没有提供正确基金经理姓名或者基金经理ID，请提供正确的基金经理姓名或基金经理ID进行查询。', None)
        if mng_id:
            if feature == '基本信息' or feature is None:
                base_info_url = get_project_api_uri('wealth', 'manager_baseinfo')
                header = {}
                manager_id = str(mng_id)
                url = f'{base_info_url}'
                pay_load = {'id': manager_id}
                response = await http_execute_async(url, 'POST', pay_load, header)
                logger.info('Application event')
                if response['code'] != 0 and response['code'] != '0':
                    return ('无法查询到该基金经理基本信息，直接告知用户: 请用户提供正确基金姓名或基金经理ID。', None)
                query_result = response.get('content') or []
                if len(query_result) != 1:
                    return ('无法查询到该基金经理基本信息，直接告知用户: 请用户提供正确基金姓名或基金经理ID', None)
                market_cap = query_result[0].get('market_cap')
                if market_cap:
                    mng_market_cap = f'{market_cap}元'
                else:
                    mng_market_cap = '--'
                typical_prod_name = query_result[0].get('representative_fund', '--')
                typical_prod_code_org = query_result[0].get('representative_fund_code')
                if typical_prod_code_org:
                    typical_prod_code = typical_prod_code_org.split('.')[0]
                else:
                    typical_prod_code = '--'
                manager_name = query_result[0].get('fund_manager_name', '--')
                manager_id_str = query_result[0].get('fund_manager_id', '--')
                fund_num = query_result[0].get('fund_num')
                annual_roi = query_result[0].get('annual_roi')
                if annual_roi:
                    annual_return = f'{annual_roi}%'
                else:
                    annual_return = '--'
                manage_years = query_result[0].get('manage_years')
                rewards = query_result[0].get('rewards')
                text = f'该基金经理基本信息如下：\n基金经理姓名：{manager_name}(基金经理ID: {manager_id_str}), 代表产品: {typical_prod_name}(产品代码: {typical_prod_code}), 管理规模: {mng_market_cap}, 管理年限：{manage_years}, 管理基金数量：{fund_num}, 总任职年化回报：{annual_return}, 获奖记录：{rewards}'
                return (text, None)
            elif feature == '在管产品':
                manager_product_url = get_project_api_uri('wealth', 'manager_product')
                header = {}
                manager_id = str(mng_id)
                url = f'{manager_product_url}'
                pay_load = {'id': manager_id}
                response = await http_execute_async(url, 'POST', pay_load, header)
                logger.info('Application event')
                if response['code'] != 0 and response['code'] != '0':
                    return ('无法查询到该基金经理的管理产品，直接告知用户: 请用户提供正确基金姓名或基金经理ID。', None)
                query_result = response.get('content') or []
                if len(query_result) < 1:
                    return ('无法查询到该基金经理的管理产品，直接告知用户: 请用户提供正确基金姓名或基金经理ID', None)
                product_list = []
                for item in query_result:
                    fund_name = item.get('short_name_exchange', '--')
                    prod_code = item.get('prod_code', '--')
                    prod_type1 = item.get('group_by_type_1', '--')
                    start_date = item.get('start_date', '--')
                    leave_date = item.get('leave_date') or '在职'
                    product_dict = {'基金名称': fund_name, '基金代码': prod_code, '一级分类': prod_type1, '任职产品起始日期': start_date, '离职产品日': leave_date}
                    product_list.append(product_dict)
                text = f'该基金管理的所有产品如下：\n{product_list}'
                return (text, None)
            elif feature == '业绩信息':
                manager_perform_url = get_project_api_uri('wealth', 'manager_perform')
                header = {}
                manager_id = str(mng_id)
                url = f'{manager_perform_url}'
                pay_load = {'manager_id': manager_id}
                response = await http_execute_async(url, 'POST', pay_load, header)
                logger.info('Application event')
                if response['code'] != 0 and response['code'] != '0':
                    return ('无法查询到该基金经理的业绩信息，直接告知用户: 请用户提供正确基金姓名或基金经理ID。', None)
                query_result = response.get('content') or []
                if len(query_result) < 1:
                    return ('无法查询到该基金经理的业绩信息，直接告知用户: 请用户提供正确基金姓名或基金经理ID', None)
                perform_list = []
                for item in query_result:
                    if item.get('statc_interval') == '1Y':
                        indicator = '近一年收益率'
                        total_num = item.get('total_number', '--')
                        roi_rank = item.get('roi_rank', '--')
                        roi_avg = item.get('roi_avg')
                        roi_avg_value = f'{roi_avg:.2%}' if roi_avg is not None else '--'
                        roi = item.get('roi')
                        roi_value = f'{roi}%' if roi is not None else '--'
                        perform_dict = {indicator: roi_value, '同类均值': roi_avg_value, '同类排名': f'{roi_rank}/{total_num}'}
                        perform_list.append(perform_dict)
                    elif item.get('statc_interval') == '3Y':
                        indicator = '近三年收益率'
                        total_num = item.get('total_number', '--')
                        roi_rank = item.get('roi_rank', '--')
                        roi_avg = item.get('roi_avg')
                        roi_avg_value = f'{roi_avg:.2%}' if roi_avg is not None else '--'
                        roi = item.get('roi')
                        roi_value = f'{roi}%' if roi is not None else '--'
                        perform_dict = {indicator: roi_value, '同类均值': roi_avg_value, '同类排名': f'{roi_rank}/{total_num}'}
                        perform_list.append(perform_dict)
                    elif item.get('statc_interval') == 'YTD':
                        indicator = '今年以来收益率'
                        total_num = item.get('total_number', '--')
                        roi_rank = item.get('roi_rank', '--')
                        roi_avg = item.get('roi_avg')
                        roi_avg_value = f'{roi_avg:.2%}' if roi_avg is not None else '--'
                        roi = item.get('roi')
                        roi_value = f'{roi}%' if roi is not None else '--'
                        perform_dict = {indicator: roi_value, '同类均值': roi_avg_value, '同类排名': f'{roi_rank}/{total_num}'}
                        perform_list.append(perform_dict)
                    elif item.get('statc_interval') == 'ETD':
                        indicator = '从业以来收益率'
                        total_num = item.get('total_number', '--')
                        roi_rank = item.get('roi_rank', '--')
                        roi_avg = item.get('roi_avg')
                        roi_avg_value = f'{roi_avg:.2%}' if roi_avg is not None else '--'
                        roi = item.get('roi')
                        roi_value = f'{roi}%' if roi is not None else '--'
                        perform_dict = {indicator: roi_value, '同类均值': roi_avg_value, '同类排名': f'{roi_rank}/{total_num}'}
                        perform_list.append(perform_dict)
                    else:
                        continue
                text = f'该基金的业绩信息如下：\n{perform_list}'
                return (text, None)
            else:
                return (f'你所填的值，不是符合要求的enum值, 请根据用户需求重新填写', None)
        else:
            return ('你没有提供正确基金经理姓名或者基金经理ID，请提供正确的基金经理姓名或者基金经理ID进行查询。', None)
    except (TokenInvalidError, UpstreamError):
        raise
    except Exception as e:
        logger.error('Application event')
        return (_ERROR_MESSAGE, None)

def contains_chinese(text):
    for ch in text:
        if '一' <= ch <= '鿿':
            return True
    return False

async def search_mng_api(key: str) -> Dict[str, Any]:
    """Search mng api. Use validated tool arguments and return adapter results."""
    url = get_project_api_uri('wealth', 'search_manager')
    header = {}
    payload = {'item': key}
    response = await http_execute_async(url, 'POST', payload, header)
    logger.info('Application event')
    return response
