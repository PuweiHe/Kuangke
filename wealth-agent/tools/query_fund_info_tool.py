from util.http_util import UpstreamError
from util.adapter_identity import get_data_api_user_id
from typing import Any, List, Dict
import asyncio
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from config import get_configuration
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到基金产品信息'

@tool('query_fund_info_tool', args_schema={'type': 'object', 'properties': {'fund_code_or_name': {'type': 'string', 'description': '基金名称或者基金代码，prefer基金代码'}, 'feature': {'type': 'string', 'description': '查询的基金信息特征', 'enum': ['基本信息', '业绩信息', '持仓信息', '基金经理', '净值信息', '盈利概率']}}, 'required': ['fund_code_or_name']})
async def query_fund_info_tool(**kwargs):
    """Query fund info tool. Use validated tool arguments and return adapter results."""
    arguments = kwargs
    fund_result, card = await get_fund_info(arguments)
    if fund_result and card:
        store_card(card)
        return [[fund_result], None]
    elif isinstance(fund_result, str) and card is None:
        return [[fund_result], None]
    else:
        return [[_ERROR_MESSAGE], None]

async def get_fund_info(arguments: dict) -> Any:
    fund_item = arguments.get('fund_code_or_name', '')
    feature = arguments.get('feature', None)
    is_es = False
    try:
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
                fund_code = query_result[0].get('prod_code_qry')
                fund_name = query_result[0].get('short_name')
                fund_type = query_result[0].get('prod_type')
                sub_fund_code = query_result[0].get('sub_prod_id')
            elif len(query_result) > 1:
                fund_list = []
                for i in query_result:
                    fund_dict = {}
                    if i.get('short_name'):
                        fund_dict['基金简称'] = i.get('short_name')
                    if i.get('prod_code_qry'):
                        fund_dict['基金代码'] = i.get('prod_code_qry')
                    fund_list.append(fund_dict)
                text = f'''根据 {fund_item} 查出来{len(query_result)}个结果，\n{fund_list}, 请选择你想查询的基金代码。'''
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
                fund_code = query_result[0].get('prod_code_qry')
                fund_name = query_result[0].get('short_name')
                fund_type = query_result[0].get('prod_type')
                sub_fund_code = query_result[0].get('sub_prod_id')
            elif len(query_result) > 1:
                fund_list = []
                for i in query_result:
                    fund_dict = {}
                    if i.get('short_name'):
                        fund_dict['基金简称'] = i.get('short_name')
                    if i.get('prod_code_qry'):
                        fund_dict['基金代码'] = i.get('prod_code_qry')
                    fund_list.append(fund_dict)
                text = f'''根据 {fund_item} 查出来{len(query_result)}个结果，\n{fund_list}, 请选择你想查询的基金代码。'''
                return (text, None)
            else:
                return ('无法查询到该基金，直接告知用户: 请用户提供正确基金代码。', None)
        else:
            return ('你没有提供正确基金名称或者基金代码，请提供正确的基金名称或基金代码进行查询。', None)
        if sub_fund_code:
            if feature == '基本信息' or feature is None:
                base_url = get_project_api_uri('wealth', 'query_prd_info')
                chart_url = get_project_api_uri('wealth', 'query_prd_chart')
                base_info_url = get_project_api_uri('wealth', 'query_prd_baseinfo')
                header = {}
                stk_code = str(sub_fund_code)

                async def fetch_basic_info():
                    url = f'''{base_url}'''
                    pay_load = {'stkCode': stk_code, 'type': '1', 'jobModeCode': 200, 'userId': get_data_api_user_id()}
                    resp = await http_execute_async(url, 'POST', pay_load, header)
                    logger.info('Application event')
                    return resp

                async def fetch_roi_nav():
                    url = f'''{chart_url}'''
                    pay_load = {'stkCode': stk_code, 'type': '2', 'jobModeCode': 200, 'userId': get_data_api_user_id()}
                    resp = await http_execute_async(url, 'POST', pay_load, header)
                    logger.info('Application event')
                    return resp

                async def fetch_max_down():
                    url = f'''{chart_url}'''
                    pay_load = {'stkCode': stk_code, 'type': '72', 'jobModeCode': 200, 'userId': get_data_api_user_id()}
                    resp = await http_execute_async(url, 'POST', pay_load, header)
                    logger.info('Application event')
                    return resp

                async def get_basic_info():
                    url = f'''{base_info_url}'''
                    pay_load = {'sub_prod_id': str(sub_fund_code)}
                    resp = await http_execute_async(url, 'POST', pay_load, header)
                    logger.info('Application event')
                    return resp
                response, response2, response3, response4 = await asyncio.gather(fetch_basic_info(), fetch_roi_nav(), fetch_max_down(), get_basic_info(), return_exceptions=True)
                if response['code'] != 0 and response['code'] != '0':
                    return ('无法查询到该基金基本信息，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                query_content = response.get('content') or {}
                query_result = query_content.get('list1') or []
                if len(query_result) != 1:
                    return ('无法查询到该基金基本信息，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                prod_type_idx = query_result[0].get('prod_type_idx')
                invest_strategy = query_result[0].get('invest_strategy')
                fund_company = query_result[0].get('fund_company')
                risk_level = query_result[0].get('risk_level')
                short_name = query_result[0].get('short_name')
                establish_date = query_result[0].get('establish_date')
                if response2['code'] != 0 and response2['code'] != '0':
                    return ('无法查询到该基金基本信息，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                query_content2 = response2.get('content') or {}
                query_result2 = query_content2.get('list1') or []
                if len(query_result2) == 1:
                    annual_roi = query_result2[0].get('annual_roi')
                    latest_annual_roi = f'''{annual_roi}%''' if annual_roi else '--'
                else:
                    annual_roi = None
                    latest_annual_roi = '--'
                    logger.error('Application event')
                if response3['code'] != 0 and response3['code'] != '0':
                    return ('无法查询到该基金基本信息，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                query_content3 = response3.get('content') or {}
                query_result3 = query_content3.get('list1') or []
                if len(query_result3) >= 1:
                    max_down = '--'
                    mdd = None
                    for i in query_result3:
                        if i.get('statc_interval') == 'ETD':
                            mdd = i.get('mdd')
                            if mdd:
                                max_down = f'''{mdd}%'''
                            break
                else:
                    max_down = '--'
                    mdd = None
                    logger.error('Application event')
                if response4['code'] != 0 and response4['code'] != '0':
                    return ('无法查询到该基金基本信息，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                query_content4 = response4.get('content') or {}
                query_result4 = query_content4.get('VALUE_LIST1') or []
                if len(query_result4) != 1:
                    return ('无法查询到基金基本信息，请用户提供正确基金名称或基金代码', None)
                prod_nav = query_result4[0].get('prod_nav', '--')
                net_date = query_result4[0].get('net_date', '--')
                daily_change = query_result4[0].get('daily_change', '--')
                fee_rate_gl = query_result4[0].get('fee_rate_gl', '--')
                fee_rate_tg = query_result4[0].get('fee_rate_tg', '--')
                group_by_type_1 = query_result4[0].get('group_by_type_1', '--')
                group_by_type_2 = query_result4[0].get('group_by_type_2', '--')
                fund_manager = query_result4[0].get('fund_manager', '--')
                fee_rate_sg = query_result4[0].get('fee_rate_sg', '--')
                fee_rate_sh = query_result4[0].get('fee_rate_sh', '--')
                stock_ratio_original = query_result4[0].get('stock_ratio', '--')
                if stock_ratio_original and stock_ratio_original != '--':
                    stock_ratio = f'''{stock_ratio_original}%'''
                else:
                    stock_ratio = '--'
                bond_ratio_original = query_result4[0].get('bond_ratio', '--')
                if bond_ratio_original and bond_ratio_original != '--':
                    bond_ratio = f'''{bond_ratio_original}%'''
                else:
                    bond_ratio = '--'
                market_cap_original = query_result4[0].get('market_cap', '--')
                if market_cap_original and market_cap_original != '--':
                    market_cap = f'''{float(market_cap_original):.2f}亿'''
                else:
                    market_cap = '--'
                iss_stat_xet = query_result4[0].get('iss_stat_xet', '--')
                accrued_nav = query_result4[0].get('accrued_nav', '--')
                if is_es:
                    text = f'''根据 {fund_item} 匹配到最相似的基金为{fund_name}(基金代码: {fund_code})，该基金的基本信息如下：\n基金简称称：{short_name}(基金代码：{fund_code})，基金类型：{prod_type_idx}，投资策略：{invest_strategy}，基金经理：{fund_manager}，基金公司：{fund_company}，基金风险等级：{risk_level}, 成立以来年化收益率：{latest_annual_roi}, 最新净值：{prod_nav}(最近净值日期：{net_date}), 累计净值:{accrued_nav}, 日涨跌幅：{daily_change}, 成立以来最大回撤：{max_down}, 管理费率:{fee_rate_gl}, 托管费率:{fee_rate_tg}, 申购费率:{fee_rate_sg}, 赎回费率:{fee_rate_sh}, 基金一级分类：{group_by_type_1}, 基金二级分类：{group_by_type_2}, 股票仓位{stock_ratio}, 债券仓位：{bond_ratio}, 基金规模：{market_cap}, 运行状态: {iss_stat_xet}'''
                else:
                    text = f'''基金的基本信息如下：\n基金名称：{short_name}(基金代码：{fund_code})，基金类型：{prod_type_idx}，投资策略：{invest_strategy}，基金经理：{fund_manager}，基金公司：{fund_company}，基金风险等级：{risk_level}, 成立以来年化收益率：{latest_annual_roi}, 最新净值：{prod_nav}(最近净值日期：{net_date}), 累计净值:{accrued_nav}, 日涨跌幅：{daily_change}, 成立以来最大回撤：{max_down}, 管理费率:{fee_rate_gl}, 托管费率:{fee_rate_tg}, 申购费率:{fee_rate_sg}, 赎回费率:{fee_rate_sh}, 基金一级分类：{group_by_type_1}, 基金二级分类：{group_by_type_2}, 股票仓位{stock_ratio}, 债券仓位：{bond_ratio}, 基金规模：{market_cap}, 运行状态: {iss_stat_xet}'''
                card_data = {'short_name': short_name, 'prod_code': fund_code, 'sub_prod_id': sub_fund_code, 'prod_type_idx': prod_type_idx, 'invest_strategy': invest_strategy, 'establish_date': establish_date, 'annual_roi': annual_roi, 'prod_nav': prod_nav, 'max_down': mdd, 'prod_type': fund_type}
                card = {'card_id': 'FUND001', 'consumer_data_card': card_data}
                return (text, card)
            elif feature == '业绩信息':
                card_data = {'short_name': fund_name, 'prod_code': fund_code, 'prod_type': fund_type, 'sub_prod_id': sub_fund_code}
                stk_code = str(sub_fund_code)
                is_private = fund_type == '2' or fund_type == 2

                async def fetch_nav_list():
                    if is_private:
                        url = f'''{get_project_api_uri('wealth', 'query_prd_chart')}'''
                        pay_load = {'stkCode': stk_code, 'type': '9', 'jobModeCode': 200, 'userId': get_data_api_user_id()}
                    else:
                        url = f'''{get_project_api_uri('wealth', 'query_prd_net')}'''
                        pay_load = {'stkCode': stk_code, 'type': '204', 'jobModeCode': 200, 'userId': get_data_api_user_id()}
                    resp = await http_execute_async(url, 'POST', pay_load, {})
                    logger.info('Application event')
                    return resp

                async def fetch_return_line():
                    url = f'''{get_project_api_uri('wealth', 'query_prd_line')}'''
                    pay_load = {'userId': get_data_api_user_id(), 'subProdId': stk_code, 'indexId': '56664484', 'jobModeCode': 200, 'dateOption': 5, 'figOption': 1, 'periodOption': 1}
                    resp = await http_execute_async(url, 'POST', pay_load, {})
                    logger.info('Application event')
                    return resp

                async def fetch_performance():
                    if is_private:
                        url = f'''{get_project_api_uri('wealth', 'query_prd_chart')}'''
                        pay_load = {'stkCode': stk_code, 'type': '54', 'jobModeCode': 200, 'userId': get_data_api_user_id()}
                    else:
                        url = f'''{get_project_api_uri('wealth', 'query_prd_net')}'''
                        pay_load = {'stkCode': stk_code, 'type': '54', 'jobModeCode': 200, 'userId': get_data_api_user_id()}
                    resp = await http_execute_async(url, 'POST', pay_load, {})
                    logger.info('Application event')
                    return resp
                nav_resp, line_resp, perf_resp = await asyncio.gather(fetch_nav_list(), fetch_return_line(), fetch_performance(), return_exceptions=True)
                if nav_resp['code'] != 0 and nav_resp['code'] != '0':
                    return (' 无法查询到该基金净值列表，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                nav_list = (nav_resp.get('content') or {}).get('list1') or []
                if len(nav_list) < 1:
                    nav_list = []
                    logger.error('Application event')
                card_data['nav_list'] = nav_list
                if line_resp['code'] != 0 and line_resp['code'] != '0':
                    return (' 无法查询到该基金收益率曲线数据，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                value_list = (line_resp.get('content') or {}).get('valueList') or []
                if len(value_list) < 1:
                    value_list = []
                    logger.error('Application event')
                card_data['return_list'] = value_list
                if perf_resp['code'] != 0 and perf_resp['code'] != '0':
                    return ('无法查询到该基金业绩信息，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                perf_list = (perf_resp.get('content') or {}).get('list1') or []
                if len(perf_list) < 1:
                    return (' 无法查询到该基金业绩信息，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                return_list = []
                for i in perf_list:
                    if i.get('roi') and i.get('statc_interval'):
                        return_percent = f'''{float(i['roi']) * 100:.2f}%'''
                        return_str = f'''{i['statc_interval']}收益率: {return_percent}'''
                        if i.get('roi_rank') and i.get('rank_prod_num'):
                            return_str += f'''(同类排名：{i['roi_rank']}/{i['rank_prod_num']})'''
                        return_list.append(return_str)
                    i['prod_code'] = fund_code
                if is_es:
                    text = f'''根据 {fund_item} 匹配到最相似的基金为{fund_name}(基金代码: {fund_code})，该基金业绩信息如下：\n{return_list}'''
                else:
                    text = f'''基金业绩信息如下：\n{return_list}'''
                card_data['return_tabel'] = perf_list
                card = {'card_id': 'FUND002', 'consumer_data_card': card_data}
                return (text, card)
            elif feature == '持仓信息':
                results = await asyncio.gather(get_asset_info(sub_fund_code), get_prd_top_stock(sub_fund_code), return_exceptions=True)
                asset_result = results[0]
                if not isinstance(asset_result, Exception) and isinstance(asset_result, tuple):
                    asset_info, asset_card_data = asset_result
                    if not (isinstance(asset_info, list) and len(asset_info) >= 1):
                        asset_info = []
                        asset_card_data = None
                else:
                    logger.warning('Application event')
                    asset_info = []
                    asset_card_data = None
                stock_result = results[1]
                if not isinstance(stock_result, Exception) and isinstance(stock_result, tuple):
                    stock_info, stock_card_data = stock_result
                    if not (isinstance(stock_info, list) and len(stock_info) >= 1):
                        stock_info = []
                        stock_card_data = None
                else:
                    logger.warning('Application event')
                    stock_info = []
                    stock_card_data = None
                if asset_info or stock_info:
                    if is_es:
                        text = f'''根据 {fund_item} 匹配到最相似的基金为{fund_name}(基金代码: {fund_code})，该基金持仓信息如下：\n 产品大类信息：{asset_info}\n 持仓股票信息：{stock_info}'''
                    else:
                        text = f'''基金持仓信息如下：\n 产品大类信息：{asset_info}\n 持仓股票信息：{stock_info}'''
                    card_data = {'short_name': fund_name, 'prod_code': fund_code, 'sub_prod_id': sub_fund_code, 'asset_list': asset_card_data, 'stock_list': stock_card_data, 'prod_type': fund_type}
                    card = {'card_id': 'FUND003', 'consumer_data_card': card_data}
                    return (text, card)
                else:
                    return ('告诉用户：无法查询到基金持仓信息，请用户提供正确基金代码', None)
            elif feature == '基金经理':
                manager_result = await get_fund_manager(sub_fund_code)
                if isinstance(manager_result, list) and len(manager_result) > 0:
                    if is_es:
                        text = f'''根据 {fund_item} 匹配到最相似的基金为{fund_name}(基金代码: {fund_code})，该基金的基金经理如下: \n{manager_result}'''
                    else:
                        text = f'''该基金的基金经理如下: \n{manager_result}'''
                    return (text, None)
                else:
                    return ('无法查询到该基金的基金经理信息，直接告知用户: 未找到基金经理相关信息，请用户提供正确基金代码。', None)
            elif feature == '净值信息':
                base_info_url = get_project_api_uri('wealth', 'query_prd_baseinfo')
                header = {}
                stk_code = str(sub_fund_code)
                url = f'''{base_info_url}'''
                pay_load = {'sub_prod_id': str(sub_fund_code)}
                resp = await http_execute_async(url, 'POST', pay_load, header)
                logger.info('Application event')
                if resp['code'] != 0 and resp['code'] != '0':
                    return ('无法查询到该基金净值信息，直接告知用户: 请用户提供正确基金名称或基金代码。', None)
                query_content = resp.get('content') or {}
                query_result = query_content.get('VALUE_LIST1') or []
                if len(query_result) != 1:
                    return ('无法查询到基金净值信息，请用户提供正确基金名称或基金代码', None)
                prod_nav = query_result[0].get('prod_nav', '--')
                net_date = query_result[0].get('net_date', '--')
                accrued_nav = query_result[0].get('accrued_nav', '--')
                short_name = query_result[0].get('short_name')
                fund_code = query_result[0].get('prod_code')
                fund_manager = query_result[0].get('fund_manager')
                if is_es:
                    text = f'''根据 {fund_item} 匹配到最相似的基金为{fund_name}(基金代码: {fund_code})，该基金的净值信息如下：\n基金简称：{short_name}(基金代码：{fund_code})，基金经理：{fund_manager}, 最新净值：{prod_nav}(最近净值日期：{net_date}), 累计净值:{accrued_nav}'''
                else:
                    text = f'''基金的净值信息如下：\n基金简称：{short_name}(基金代码：{fund_code})，基金经理：{fund_manager}, 最新净值：{prod_nav}(最近净值日期：{net_date}), 累计净值:{accrued_nav}'''
                return (text, None)
            elif feature == '盈利概率':
                winrate_result = await get_win_rate(sub_fund_code)
                if isinstance(winrate_result, list) and len(winrate_result) > 0:
                    if is_es:
                        text = f'''根据 {fund_item} 匹配到最相似的基金为{fund_name}(基金代码: {fund_code})，该基金的盈利概率如下: \n{winrate_result}'''
                    else:
                        text = f'''该基金的盈利概率如下: \n{winrate_result}'''
                    return (text, None)
                else:
                    return ('无法查询到该基金的盈利概率信息', None)
            else:
                return (f'''你所填的值，不是符合要求的enum值, 请根据用户需求重新填写''', None)
        else:
            return ('你没有提供正确基金名称或者基金代码，请提供正确的基金名称或基金代码进行查询。', None)
    except (TokenInvalidError, UpstreamError):
        raise
    except Exception as e:
        logger.error('Application event')
        return (_ERROR_MESSAGE, None)

async def get_asset_info(fund_code: str):
    asset_url = f'''{get_project_api_uri('wealth', 'query_prd_class')}'''
    header = {}
    payload = {'sub_prod_id': fund_code}
    response = await http_execute_async(asset_url, 'POST', payload, header)
    logger.info('Application event')
    if response['code'] == 0 or response['code'] == '0':
        query_content = response.get('content') or {}
        query_result1 = query_content.get('VALUE_LIST1') or []
        query_result2 = query_content.get('VALUE_LIST2') or []
    else:
        return ('告诉用户: 无法查询到基金大类配置新，请用户提供正确基金代码。', None)
    if len(query_result1) >= 1:
        TYPE_MAP = {'bond': '债券', 'stock': '股票', 'fund': '基金', 'mm': '货币市场工具', 'warran': '权证', 'cash': '现金', 'other': '其他'}
        ratio_map = {i2.get('type_name', '').strip(): i2.get('changeinvestpct', '--') for i2 in query_result2}
        asset_type_list = []
        for item in query_result1:
            raw_type = item.get('type_name', '').strip()
            type_name = TYPE_MAP.get(raw_type, raw_type)
            change_ratio = ratio_map.get(raw_type, '--')
            asset_type_list.append({'资产类别': type_name, '资产占比': f'''{item.get('ratio', '--')}%''', '较上期变化': f'''{change_ratio}%'''})
        return (asset_type_list, query_content)
    else:
        return (None, None)

async def get_prd_top_stock(fund_code: str):
    stock_url = f'''{get_project_api_uri('wealth', 'query_prd_top_stock')}'''
    header = {}
    payload = {'sub_prod_id': fund_code}
    response = await http_execute_async(stock_url, 'POST', payload, header)
    logger.info('Application event')
    if response['code'] == 0 or response['code'] == '0':
        query_content = response.get('content') or []
    else:
        return ('无法查询到该基金的持仓股票信息，直接告知用户: 未找到相关信息，请用户提供正确基金代码。', None)
    if len(query_content) >= 1:
        stock_list = []
        for item in query_content:
            stock_list.append({'股票名称': item.get('hold_prod_name'), '股票代码': item.get('ticker'), '持仓占比': f'''{item.get('nav_pc', '--')}%'''})
        return (stock_list, query_content)
    else:
        return (None, None)

async def get_fund_manager(fund_code: str):
    fund_manager_url = f'''{get_project_api_uri('wealth', 'fund_manager')}'''
    header = {}
    payload = {'sub_prod_id': fund_code}
    response = await http_execute_async(fund_manager_url, 'POST', payload, header)
    logger.info('Application event')
    if response['code'] == 0 or response['code'] == '0':
        query_content = response.get('content') or []
    else:
        return '无法查询到该基金的基金经理信息'
    if len(query_content) >= 1:
        manager_list = []
        for item in query_content:
            manager_list.append({'基金经理姓名': item.get('fund_manager_name'), '基金经理ID': item.get('fund_manager_id'), '任职日期': item.get('start_date'), '任职年化回报': f'''{item.get('annual_roi', '--')}%'''})
        return manager_list
    else:
        return '无法查询到该基金的基金经理信息'

async def get_win_rate(fund_code: str):
    fund_winrate_url = f'''{get_project_api_uri('wealth', 'fund_winrate')}'''
    header = {}
    payload = {'id': fund_code}
    response = await http_execute_async(fund_winrate_url, 'POST', payload, header)
    logger.info('Application event')
    if response['code'] == 0 or response['code'] == '0':
        query_content = response.get('content') or []
    else:
        return '无法查询到该基金的基金经理信息'
    if len(query_content) >= 1:
        winrate_list = []
        for item in query_content:
            winrate_list.append({'本基金盈利概率(%)': item.get('fundsuccess_percent'), '盈利 > 10% 概率(%)': item.get('fundsuccess_levelonepercent'), '盈利 5% ~ 10% 概率(%)': item.get('undsuccess_leveltwopercent'), '盈利 0 ~ 5% 概率(%)': item.get('fundsuccess_levelthreepercent'), '本基金亏损概率(%)': item.get('fundfail_percent'), '亏损 >-10% 概率(%)': item.get('fundfail_levelonepercent'), '亏损 -5% ~ -10% 概率(%)': item.get('fundfail_leveltwopercent'), '亏损 -5% ~ 0 概率(%)': item.get('fundfail_levelthreepercent')})
        return winrate_list
    else:
        return '无法查询到该基金的盈利概率信息'

def contains_chinese(text):
    for ch in text:
        if '一' <= ch <= '鿿':
            return True
    return False

async def search_prd_api(key: str, user_id: str | None = None) -> Dict[str, Any]:
    """Search prd api. Use validated tool arguments and return adapter results."""
    url = get_project_api_uri('wealth', 'search_prd')
    header = {}
    payload = {'key': key, 'userId': user_id or get_data_api_user_id()}
    response = await http_execute_async(url, 'POST', payload, header)
    logger.info('Application event')
    return response
