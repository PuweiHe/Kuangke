from util.http_util import UpstreamError
from typing import Any, List, Dict
import asyncio
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到基金公司信息'

@tool('query_company_info_tool', args_schema={'type': 'object', 'properties': {'company_name_or_ID': {'type': 'string', 'description': '基金公司名称or基金公司ID, prefer基金公司ID'}, 'feature': {'type': 'string', 'description': '查询的基金公司的信息特征', 'enum': ['基本信息', '产品统计', '股东信息']}}, 'required': ['company_name_or_ID']})
async def query_company_info_tool(**kwargs):
    """Query company info tool. Use validated tool arguments and return adapter results."""
    arguments = kwargs
    company_result, card = await get_company_info(arguments)
    if company_result and card:
        store_card(card)
        return [[company_result], None]
    elif isinstance(company_result, str) and card is None:
        return [[company_result], None]
    else:
        return [[_ERROR_MESSAGE], None]

async def get_company_info(arguments: dict) -> Any:
    company_item = arguments.get('company_name_or_ID', '')
    feature = arguments.get('feature', None)
    try:
        if contains_chinese(company_item):
            define_company_name = company_item
            response = await search_company_api(define_company_name)
            if response['code'] == 0 or response['code'] == '0':
                query_result = response.get('content') or []
            else:
                return ('无法查询到该基金公司，直接告知用户: 请用户提供正确基金公司名称。', None)
            if len(query_result) == 1:
                company_id = query_result[0].get('fund_company_id')
                company_name = query_result[0].get('full_name')
            elif len(query_result) > 1:
                company_list = []
                for i in query_result:
                    company_dict = {}
                    if i.get('full_name'):
                        company_dict['基金公司全称'] = i.get('full_name')
                    if i.get('fund_company_id'):
                        company_dict['基金公司ID'] = i.get('fund_company_id')
                    company_list.append(company_dict)
                text = f'''根据{company_item}查出来{len(query_result)}个结果，\n{company_list}, 请选择你想查询的基金公司'''
                return (text, None)
            else:
                return ('无法查询到该基金公司，直接告知用户: 请用户提供正确基金公司名称。', None)
        elif company_item.isalnum():
            response = await search_company_api(company_item)
            if response['code'] == 0 or response['code'] == '0':
                query_result = response.get('content') or []
            else:
                return ('无法查询到该基金公司，直接告知用户: 请用户提供正确基金公司ID', None)
            if len(query_result) == 1:
                company_id = query_result[0].get('fund_company_id')
                company_name = query_result[0].get('full_name')
            elif len(query_result) > 1:
                company_list = []
                for i in query_result:
                    company_dict = {}
                    if i.get('full_name'):
                        company_dict['基金公司全称'] = i.get('full_name')
                    if i.get('fund_company_id'):
                        company_dict['基金公司ID'] = i.get('fund_company_id')
                    company_list.append(company_dict)
                text = f'''根据{company_item}查出来{len(query_result)}个结果，\n{company_list}, 请选择你想查询的基金公司'''
                return (text, None)
            else:
                return ('无法查询到该基金公司，直接告知用户: 请用户提供正确基金公司ID', None)
        else:
            return ('你没有提供正确基金公司名称或者基金公司ID，请提供正确的基金公司名称或基金公司ID进行查询。', None)
        if company_id:
            if feature == '基本信息' or feature is None:
                base_info_url = get_project_api_uri('wealth', 'company_baseinfo')
                header = {}
                company_id_str = str(company_id)
                url = f'''{base_info_url}'''
                pay_load = {'id': company_id_str}
                response = await http_execute_async(url, 'POST', pay_load, header)
                logger.info('Application event')
                if response['code'] != 0 and response['code'] != '0':
                    return ('无法查询到该基金公司基本信息，直接告知用户: 请用户提供正确基金公司名称或基金公司ID。', None)
                query_result = response.get('content') or []
                if len(query_result) != 1:
                    return ('无法查询到该基金公司基本信息，直接告知用户: 请用户提供正确基金公司名称或基金公司ID', None)
                company_name = query_result[0].get('short_name', '--')
                company_full_name = query_result[0].get('full_name', '--')
                company_id_result = query_result[0].get('fund_company_id', '--')
                market_cap = query_result[0].get('market_cap')
                if market_cap:
                    market_cap_str = f'''{market_cap}'''
                else:
                    market_cap_str = '--'
                mng_num = query_result[0].get('fund_manager_number', '--')
                fd_num = query_result[0].get('fund_number', '--')
                mng_avg_scale = query_result[0].get('man_avg', '--')
                man_avg_year = query_result[0].get('avg_yr', '--')
                establish_date = query_result[0].get('establish_date', '--')
                value = query_result[0].get('layoff_per') or None
                layoff_percent = f'''{value:.2%}''' if value is not None else '--'
                text = f'''该基金公司基本信息如下：\n基金公司名称：{company_name}(基金公司ID: {company_id_result}), 基金公司全称: {company_full_name}, 成立日期：{establish_date}, 管理规模: {market_cap_str}, 基金经理数量：{mng_num}, 基金数量：{fd_num}, 人均任职年限：{man_avg_year}, 人均管理规模：{mng_avg_scale}, 年度离职率：{layoff_percent}'''
                return (text, None)
            elif feature == '产品统计':
                response = await get_product_count(company_id)
                if response['code'] != 0 and response['code'] != '0':
                    return ('无法查询到该基金公司的旗下产品统计信息，直接告知用户: 请用户提供正确基金公司名称或基金公司ID。', None)
                query_result = response.get('content') or []
                if len(query_result) == 0:
                    return ('该基金公司旗下暂无产品', None)
                product_list = []
                type_map = {'stock': '股票基金', 'mix': '混合基金', 'bond': '债券基金', 'currency': '货币基金', 'qdii': 'QDII基金', 'fof': 'FOF基金'}
                for item in query_result:
                    class_name = item.get('type_name', '--')
                    type_name = type_map.get(class_name, '--')
                    cap = f'''{item.get('cap', '--')}亿'''
                    percent = f'''{item.get('percent', '--')}%'''
                    fund_number = item.get('fund_number', '--')
                    product_dict = {'产品类型': type_name, '产品数量': fund_number, '规模': cap, '规模占比': percent}
                    product_list.append(product_dict)
                text = f'''该基金公司旗下各类产品统计信息如下：\n{product_list}'''
                return (text, None)
            elif feature == '股东信息':
                response = await get_stock_holder_info(company_id)
                if response['code'] != 0 and response['code'] != '0':
                    return ('无法查询到该基金公司的股东信息信息，直接告知用户: 请用户提供正确基金公司名称或基金公司ID。', None)
                query_result = response.get('content') or []
                if len(query_result) == 0:
                    return ('暂无法获取到该基金公司的股东信息', None)
                holder_list = []
                for item in query_result:
                    holder_name = item.get('shareholder_name', '--')
                    invest_amount = f'''{item.get('invest_amount', '--')}万'''
                    invest_ratio = item.get('invest_ratio', '--')
                    holder_dict = {'股东名称': holder_name, '持股金额': invest_amount, '持股比例': invest_ratio}
                    holder_list.append(holder_dict)
                text = f'''该基金公司股东信息如下：\n{holder_list}'''
                return (text, None)
            else:
                return (f'''你所填的值，不是符合要求的enum值, 请根据用户需求重新填写''', None)
        else:
            return ('你没有提供正确基金公司名称或者基金公司ID，请提供正确的基金公司名称或者基金公司ID进行查询。', None)
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

async def search_company_api(key: str) -> Dict[str, Any]:
    """Search company api. Use validated tool arguments and return adapter results."""
    url = get_project_api_uri('wealth', 'search_company')
    header = {}
    payload = {'item': key}
    response = await http_execute_async(url, 'POST', payload, header)
    logger.info('Application event')
    return response

async def get_product_count(company_id: str) -> Dict[str, Any]:
    company_product_url = get_project_api_uri('wealth', 'company_product')
    header = {}
    company_id_str = str(company_id)
    url = f'''{company_product_url}'''
    pay_load = {'id': company_id_str}
    response = await http_execute_async(url, 'POST', pay_load, header)
    logger.info('Application event')
    return response

async def get_stock_holder_info(company_id: str) -> Dict[str, Any]:
    company_holder_url = get_project_api_uri('wealth', 'company_holder')
    header = {}
    company_id_str = str(company_id)
    url = f'''{company_holder_url}'''
    pay_load = {'id': company_id_str}
    response = await http_execute_async(url, 'POST', pay_load, header)
    logger.info('Application event')
    return response
