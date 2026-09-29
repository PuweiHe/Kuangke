import asyncio
from typing import Any, List, Dict
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到基金比较结果'
period_list = ['成立以来', '近3年', '近5年', '近1个月', '近1周', '近1年', '近2周', '近2年', '近3个月', '近6个月', '今年以来']
period_map = {'成立以来': 'ETD', '近3年': '3Y', '近5年': '5Y', '近1个月': '1M', '近1周': '1W', '近1年': '1Y', '近2周': '2W', '近2年': '2Y', '近3个月': '3M', '近6个月': '6M', '今年以来': 'YTD'}

@tool('compare_funds_tool', args_schema={'type': 'object', 'properties': {'funds_list': {'type': 'array', 'description': '需要比较的基金名称或代码列表，至少2只，prefer基金代码'}, 'time_period': {'type': 'string', 'description': '时间段', 'default': '近1年', 'enum': period_list}}, 'required': ['funds_list']})
async def compare_funds_tool(**kwargs):
    """Compare funds tool. Use validated tool arguments and return adapter results."""
    arguments = kwargs
    compare_result, card = await compare_funds(arguments)
    if compare_result and card:
        store_card(card)
        return [[compare_result], card]
    elif isinstance(compare_result, str) and card is None:
        return [[compare_result], None]
    else:
        return [[_ERROR_MESSAGE], None]

async def compare_funds(arguments: dict) -> Any:
    funds_list = arguments.get('funds_list', []) or []
    time_period = arguments.get('time_period', '近1年')
    try:
        if len(funds_list) > 0:
            fund_code_list = []
            for fund_item in funds_list:
                if contains_chinese(fund_item):
                    if fund_item.endswith('基金'):
                        define_fund_name = fund_item.replace('基金', '')
                    elif fund_item.endswith('产品'):
                        define_fund_name = fund_item.replace('产品', '')
                    else:
                        define_fund_name = fund_item
                    response = await search_prd_api(define_fund_name)
                    if response['code'] == 0 or response['code'] == '0':
                        query_result = response.get('content') or []
                    else:
                        return ('无法查询到该基金，直接告知用户: 请用户提供正确基金名称。', None)
                    if len(query_result) == 1:
                        sub_fund_code = query_result[0].get('sub_prod_id')
                        fund_code_list.append(sub_fund_code)
                    elif len(query_result) > 1:
                        fund_list = []
                        for i in query_result:
                            fund_dict = {}
                            if i.get('short_name'):
                                fund_dict['基金简称'] = i.get('short_name')
                            if i.get('prod_code_qry'):
                                fund_dict['基金代码'] = i.get('prod_code_qry')
                            fund_list.append(fund_dict)
                        text = f'''根据{fund_item}查出来{len(query_result)}个结果，\n{fund_list}, 请选择你想查询的基金代码。'''
                        return (text, None)
                    else:
                        es_query_url = get_configuration('api', 'wealth')['es_query_url']
                        header = {'Content-Type': 'application/json'}
                        payload = {'name': define_fund_name}
                        response = await http_execute_async(es_query_url, 'POST', payload, header, True)
                        logger.info('Application event')
                        if response.get('result'):
                            if response['result'].get('match_stage') != 'rule_low_confidence':
                                fund_code = response['result'].get('fund_code')
                                fund_name = response['result'].get('short_name')
                                full_name = response['result'].get('full_name')
                                fund_type = response['result'].get('fund_type')
                                sub_fund_code = response['result'].get('product_id')
                                fund_code_list.append(sub_fund_code)
                                is_es = True
                            else:
                                return ('无法查询到该基金，直接告知用户: 请用户提供正确基金名称。', None)
                        else:
                            return ('无法查询到该基金，直接告知用户: 请用户提供正确基金名称。', None)
                elif fund_item.replace('.', '').isalnum():
                    response = await search_prd_api(fund_item)
                    if response['code'] == 0 or response['code'] == '0':
                        query_result = response.get('content') or []
                    else:
                        return ('无法查询到该基金，直接告知用户: 请用户提供正确基金代码。', None)
                    if len(query_result) == 1:
                        sub_fund_code = query_result[0].get('sub_prod_id')
                        fund_code_list.append(sub_fund_code)
                    elif len(query_result) > 1:
                        fund_list = []
                        for i in query_result:
                            fund_dict = {}
                            if i.get('short_name'):
                                fund_dict['基金简称'] = i.get('short_name')
                            if i.get('prod_code_qry'):
                                fund_dict['基金代码'] = i.get('prod_code_qry')
                            fund_list.append(fund_dict)
                        text = f'''根据{fund_item}查出来{len(query_result)}个结果，\n{fund_list}, 请选择你想查询的基金代码。'''
                        return (text, None)
                    else:
                        return ('无法查询到该基金，直接告知用户: 请用户提供正确基金代码。', None)
                else:
                    return ('你没有提供正确基金名称或者基金代码，请提供正确的基金名称或基金代码进行查询。', None)
            if len(fund_code_list) > 0:
                sub_prod_id_list = ','.join(fund_code_list)
                final_result = ''
                baseinfo_result = await compare_fund_baseinfo(sub_prod_id_list)
                final_result += baseinfo_result + '\n'
                perform_result = await compare_fund_perform(sub_prod_id_list, time_period)
                final_result += perform_result + '\n'
                manager_result = await compare_fund_manager(fund_code_list)
                final_result += manager_result + '\n'
                company_result = await compare_fund_company(fund_code_list)
                final_result += company_result + '\n'
                return (final_result, None)
            else:
                return (_ERROR_MESSAGE, None)
        else:
            return (_ERROR_MESSAGE, None)
    except TokenInvalidError:
        raise
    except Exception as e:
        logger.error('Application event')
        return (_ERROR_MESSAGE, None)

async def compare_fund_baseinfo(sub_prod_ids: str):
    url = f'''{get_project_api_uri('wealth', 'compare_fund_baseinfo')}'''
    header = {}
    payload = {'sub_prod_id': sub_prod_ids}
    response = await http_execute_async(url, 'POST', payload, header)
    logger.info('Application event')
    if response and (response.get('code') == 0 or response.get('code') == '0'):
        query_content = response.get('content') or {}
        query_result = query_content.get('VALUE_LIST1') or []
        if len(query_result) > 0:
            compare_base_info_result = []
            for i in query_result:
                market_cap_original = i.get('market_cap', '--')
                if market_cap_original and market_cap_original != '--':
                    market_cap = f'''{float(market_cap_original):.2f}亿'''
                else:
                    market_cap = '--'
                special_original = i.get('special', '--')
                if special_original and special_original != '--':
                    special = f'''{special_original}基金'''
                else:
                    special = '--'
                base_info_result = {'基金简称': i.get('short_name'), '基金代码': i.get('prod_code'), '基金规模': market_cap, '特殊标识': special, '基金一级分类': i.get('group_by_type_1'), '基金二级分类': i.get('group_by_type_2'), '基金成立时间': i.get('establish_date').split('T')[0], '管理费率': i.get('fee_rate_gl'), '托管费率': i.get('fee_rate_tg')}
                compare_base_info_result.append(base_info_result)
            text = f'''基金基本信息比较: \n{compare_base_info_result}'''
            return text
        else:
            return '暂时无法获取到基金基本信息比较结果'
    else:
        return '暂时无法获取到基金基本信息比较结果'

async def compare_fund_perform(sub_prod_ids: str, time_period: str='近1年'):
    url = f'''{get_project_api_uri('wealth', 'compare_fund_perform')}'''
    header = {}
    time_period_str = period_map.get(time_period)
    payload = {'time_period': time_period_str, 'sub_prod_id': sub_prod_ids}
    response = await http_execute_async(url, 'POST', payload, header)
    logger.info('Application event')
    if response and (response.get('code') == 0 or response.get('code') == '0'):
        query_content = response.get('content') or {}
        query_result = query_content.get('VALUE_LIST1') or []
        if len(query_result) > 0:
            compare_perform_result = []
            for i in query_result:
                sharpe_ratio_org = i.get('sharp_ratio')
                if sharpe_ratio_org and isinstance(sharpe_ratio_org, float):
                    sharpe_ratio = round(sharpe_ratio_org, 2)
                else:
                    sharpe_ratio = '--'
                mdd_org = i.get('mdd')
                mdd = f'''{mdd_org:.2%}''' if mdd_org is not None else '--'
                roi_org = i.get('roi')
                roi = f'''{roi_org}%''' if roi_org is not None else '--'
                perform_info_result = {'基金全称': i.get('full_name'), '基金代码': i.get('prod_code'), f'''{time_period}夏普比率''': sharpe_ratio, f'''{time_period}最大回撤''': mdd, f'''{time_period}收益率''': roi}
                compare_perform_result.append(perform_info_result)
            text = f'''基金业绩信息比较: \n{compare_perform_result}'''
            return text
        else:
            return '暂时无法获取到基金业绩信息比较结果'
    else:
        return '暂时无法获取到基金业绩信息比较结果'

async def compare_fund_manager(sub_prod_ids: list):
    url = f'''{get_project_api_uri('wealth', 'compare_fund_mng')}'''
    header = {}
    fund_ids = ','.join(sub_prod_ids)
    payload = {'sub_prod_id': fund_ids}
    response = await http_execute_async(url, 'POST', payload, header)
    logger.info('Application event')
    if response and (response.get('code') == 0 or response.get('code') == '0'):
        query_content = response.get('content') or {}
        query_result = query_content.get('VALUE_LIST1') or []
        if query_result:
            order_map = {sid: idx for idx, sid in enumerate(sub_prod_ids)}
            query_result.sort(key=lambda x: order_map.get(str(x.get('sub_prod_id')), len(sub_prod_ids)))
            fund_manager_map = {}
            fund_name_map = {}
            for item in query_result:
                fund_id = str(item.get('sub_prod_id'))
                if fund_id not in fund_manager_map:
                    fund_manager_map[fund_id] = []
                    fund_name_map[fund_id] = item.get('short_name_exchange')
                annual_roi = item.get('annual_roi')
                annual_return = f'''{annual_roi}%''' if annual_roi else '--'
                manager_info = {'基金经理姓名': item.get('fund_manager_name', '--'), '基金经理ID': item.get('fund_manager_id', '--'), '管理规模(元)': item.get('market_cap', '--'), '管理年限': item.get('manage_years', '--'), '总任职年化回报': annual_return}
                fund_manager_map[fund_id].append(manager_info)
            compare_mng_info_result = []
            for fund_id in sub_prod_ids:
                fund_id_str = str(fund_id)
                managers = fund_manager_map.get(fund_id_str, [])
                fund_name = fund_name_map.get(fund_id_str, '--')
                if managers:
                    compare_mng_info_result.append({fund_name: managers})
            text = f'''基金经理比较: \n{compare_mng_info_result}'''
            return text
        else:
            return '暂时无法获取到基金经理比较结果'
    else:
        return '暂时无法获取到基金经理比较结果'

async def compare_fund_company(sub_prod_ids: list):
    url = f'''{get_project_api_uri('wealth', 'compare_fund_org')}'''
    header = {}
    fund_ids = ','.join(sub_prod_ids)
    payload = {'sub_prod_id': fund_ids}
    response = await http_execute_async(url, 'POST', payload, header)
    logger.info('Application event')
    if response and (response.get('code') == 0 or response.get('code') == '0'):
        query_content = response.get('content') or {}
        query_result = query_content.get('VALUE_LIST1') or []
        if query_result:
            order_map = {sid: idx for idx, sid in enumerate(sub_prod_ids)}
            query_result.sort(key=lambda x: order_map.get(str(x.get('sub_prod_id')), len(sub_prod_ids)))
            compare_company_result = []
            for item in query_result:
                company_info = {'基金公司全称': item.get('full_name', '--'), '基金公司简称': item.get('short_name', '--'), '基金公司ID': item.get('fund_company_id'), '管理规模(元)': item.get('market_cap', '--'), '管理基金总数': item.get('fund_number', '--'), '成立日期': item.get('establish_date', '--')}
                compare_company_result.append(company_info)
            text = f'''基金公司比较: \n{compare_company_result}'''
            return text
        else:
            return '暂时无法获取到基金公司比较结果'
    else:
        return '暂时无法获取到基金公司比较结果'

def contains_chinese(text):
    for ch in text:
        if '一' <= ch <= '鿿':
            return True
    return False

async def search_prd_api(key: str, user_id: str | None = None) -> Dict[str, Any]:
    """Search prd api. Use validated tool arguments and return adapter results."""
    url = get_project_api_uri('wealth', 'search_prd')
    header = {}
    from util.adapter_identity import get_data_api_user_id
    payload = {'key': key, 'userId': user_id or get_data_api_user_id()}
    response = await http_execute_async(url, 'POST', payload, header)
    logger.info('Application event')
    return response
