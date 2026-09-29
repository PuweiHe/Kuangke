from util.http_util import UpstreamError
from typing import Any, List, Dict
import asyncio
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到客户信息'
_GENDER_MAP = {'0': '男', '1': '女', '2': '非自然人', '3': '未知'}
_AGE_MAP = {'0': '40后', '1': '50后', '2': '60后', '3': '70后', '4': '80后', '5': '90后', '6': '00后', '7': '40前'}
_RISK_PREF_MAP = {'0': '低风险偏好', '1': '较低风险偏好', '2': '中等风险偏好', '3': '较高风险偏好', '4': '高风险偏好', '9': '未知'}
_ADV_SIGN_MAP = {'0': '未签约', '1': '已签约'}
_CUST_STATUS_MAP = {'0': '正常', '1': '冻结', '2': '挂失', '3': '销户', '6': '休眠', 'A': '不合格司法冻结', 'C': '中登休眠', 'E': '中登不合格', 'G': '内部休眠', 'J': '内部不合格', 'F': '系统锁定', 'L': '未激活', 'g': '解约'}
_VLD_CUST_MAP = {'0': '否', '1': '是'}
_BRD_PREF_MAP = {'0': '股基交易型', '1': '债券交易型', '2': '产品投资型', '3': '混合型'}
_PREF_IDY_MAP = {'6230000000': '日常消费', '6235000000': '医疗保健', '6255000000': '公用事业', '6245000000': '信息技术', '6240000000': '金融', '6215000000': '材料', '6210000000': '能源', '6220000000': '工业', '6225000000': '可选消费', '6250000000': '电信服务', '6260000000': '房地产'}
_PREF_PD_MAP = {'1': '权益类', '2': '类固定收益类', '3': '挂钩浮动收益类', '4': '现金管理类', '6': '其他'}
_RISK_GRD_MAP = {'5': 'C5-积极型', '6': 'C4-相对积极型', '7': 'C3-稳健型', '8': 'C2-相对保守型', '9': 'C1-相对保守型', 'A': 'C1-最低风险等级', 'x': '自定义风险等级', '0': '未评级'}
_MKT_TP_MAP = {'XSHE': '深交所', 'XSHG': '上交所', 'CTS': '场外多金|公募', 'OTC': 'OTC渠道', 'ADV': '基金投顾'}

@tool('query_customer_info_tool', args_schema={'type': 'object', 'properties': {'user_code': {'type': 'string', 'description': '当前用户账号'}, 'customer_code_or_name': {'type': 'string', 'description': '需要查询的客户号或者客户名称，prefer客户号'}, 'account_id': {'type': 'string', 'description': '需要查询的资金账号'}, 'feature': {'type': 'string', 'description': '需要查询的信息特征', 'enum': ['基本信息', '资产信息', '持仓信息']}}, 'required': ['user_code']})
async def query_customer_info_tool(**kwargs):
    """Query customer info tool. Use validated tool arguments and return adapter results."""
    arguments = kwargs
    cust_result, card = await get_cust_info(arguments)
    if cust_result and card:
        store_card(card)
        return [[cust_result], None]
    elif isinstance(cust_result, str) and card is None:
        return [[cust_result], None]
    else:
        return [[_ERROR_MESSAGE], None]

async def get_cust_info(arguments: dict) -> Any:
    cust_item = arguments.get('customer_code_or_name', '')
    feature = arguments.get('feature', None)
    user_code = arguments.get('user_code')
    if not user_code:
        from util.adapter_identity import get_data_api_user_id
        user_code = get_data_api_user_id()
    account_id = arguments.get('account_id', '')
    try:
        if account_id:
            url = f'''{get_project_api_uri('wealth', 'search_cust')}'''
            header = {}
            pay_load = {'user_code': user_code, 'account_id': account_id}
            response = await http_execute_async(url, 'POST', pay_load, header)
            logger.info('Application event')
            if response['code'] == 0 or response['code'] == '0':
                query_result = response.get('content') or {}
                query_content = query_result.get('VALUE_LIST1') or []
            else:
                return ('无法查询到客户，请用户提供正确资金账号。', None)
            if len(query_content) == 1:
                cust_code = query_content[0].get('hs_cust_id')
                cust_name = query_content[0].get('client_name')
                cust_account = query_content[0].get('fund_account')
            elif len(query_content) > 1:
                cust_list = []
                for i in query_content:
                    cust_str_item = f'''客户姓名: {i.get('client_name')}, 客户编号: {i.get('hs_cust_id')}, 资金账号: {i.get('fund_account')}'''
                    cust_list.append(cust_str_item)
                cust_str = '\n'.join(cust_list)
                return (f'''告诉用户：根据{account_id} 查询到{len(cust_list)}个客户: {cust_str}，让用户选择需要查询哪一位客户。''', None)
            else:
                return ('无法查询到客户，请用户提供正确客户名称。', None)
        elif contains_chinese(cust_item):
            url = f'''{get_project_api_uri('wealth', 'search_cust')}'''
            header = {}
            pay_load = {'user_code': user_code, 'cust_name': cust_item}
            response = await http_execute_async(url, 'POST', pay_load, header)
            logger.info('Application event')
            if response['code'] == 0 or response['code'] == '0':
                query_result = response.get('content') or {}
                query_content = query_result.get('VALUE_LIST1') or []
            else:
                return ('无法查询到客户，请用户提供正确客户名称名称。', None)
            if len(query_content) == 1:
                cust_code = query_content[0].get('hs_cust_id')
                cust_name = query_content[0].get('client_name')
                cust_account = query_content[0].get('fund_account')
            elif len(query_content) > 1:
                cust_list = []
                for i in query_content:
                    cust_str_item = f'''客户姓名: {i.get('client_name')}, 客户编号: {i.get('hs_cust_id')}, 资金账号: {i.get('fund_account')}'''
                    cust_list.append(cust_str_item)
                cust_str = '\n'.join(cust_list)
                return (f'''告诉用户：根据{cust_item} 查询到{len(cust_list)}个客户: {cust_str}，让用户选择需要查询哪一位客户。''', None)
            else:
                return ('无法查询到客户，请用户提供正确客户名称。', None)
        elif cust_item.isalnum():
            url = f'''{get_project_api_uri('wealth', 'search_cust')}'''
            header = {}
            pay_load = {'user_code': user_code, 'cust_id': cust_item}
            response = await http_execute_async(url, 'POST', pay_load, header)
            logger.info('Application event')
            if response['code'] == 0 or response['code'] == '0':
                query_result = response.get('content') or {}
                query_content = query_result.get('VALUE_LIST1') or []
            else:
                return ('无法查询到客户，请用户提供正确客户名称。', None)
            if len(query_content) == 1:
                cust_code = query_content[0].get('hs_cust_id')
                cust_name = query_content[0].get('client_name')
                cust_account = query_content[0].get('fund_account')
            elif len(query_content) > 1:
                cust_list = []
                for i in query_content:
                    cust_str_item = f'''客户姓名: {i.get('client_name')}, 客户编号: {i.get('hs_cust_id')}, 资金账号: {i.get('fund_account')}'''
                    cust_list.append(cust_str_item)
                cust_str = '\n'.join(cust_list)
                return (f'''告诉用户：根据{cust_item} 查询到{len(cust_list)}个客户: {cust_str}，让用户选择需要查询哪一位客户。''', None)
            else:
                return ('无法查询到客户，请用户提供正确客户名称。', None)
        else:
            return ('告诉用户：你没有提供正确基金名称或者基金代码，请提供正确的基金名称或基金代码进行查询。', None)
        if cust_code:
            if feature == '基本信息' or feature is None:
                url = f'''{get_project_api_uri('wealth', 'cust_info')}'''
                header = {}
                pay_load = {'cust_id': cust_code}
                response = await http_execute_async(url, 'POST', pay_load, header)
                logger.info('Application event')
                if response['code'] == 0 or response['code'] == '0':
                    query_content = response.get('content') or []
                else:
                    return ('无法查询到该客户，请用户提供正确客户姓名或客户号。', None)
                if len(query_content) >= 1:
                    q = query_content[0]
                    cust_name = q.get('client_name')
                    hs_cust_id = q.get('hs_cust_id')
                    gnd_code = str(q.get('gnd_code', ''))
                    gender = _GENDER_MAP.get(gnd_code, '--')
                    age_code = str(q.get('age_code', ''))
                    age = _AGE_MAP.get(age_code, '--')
                    rsk_pref_code = str(q.get('rsk_pref_code', ''))
                    risk_prefer = _RISK_PREF_MAP.get(rsk_pref_code, '--')
                    fund_adv_sign_status = str(q.get('fund_adv_sign_status', ''))
                    cust_adv_sign_status = _ADV_SIGN_MAP.get(fund_adv_sign_status, '--')
                    cust_st_code = str(q.get('cust_st_code', ''))
                    cust_status = _CUST_STATUS_MAP.get(cust_st_code, '--')
                    vld_cust_ind = str(q.get('vld_cust_ind', ''))
                    vld_cust = _VLD_CUST_MAP.get(vld_cust_ind, '--')
                    brd_pref_code = str(q.get('brd_pref_code', ''))
                    brd_pref = _BRD_PREF_MAP.get(brd_pref_code, '--')
                    pref_idy_code = str(q.get('pref_idy_code', ''))
                    pref_idy = _PREF_IDY_MAP.get(pref_idy_code, '--')
                    pref_pd_tp_code = str(q.get('pref_pd_tp_code', ''))
                    pref_pd_tp = _PREF_PD_MAP.get(pref_pd_tp_code, '--')
                    cust_rsk_grd_code = str(q.get('cust_rsk_grd_code', ''))
                    cust_rsk_grd = _RISK_GRD_MAP.get(cust_rsk_grd_code, '--')
                    text = f'''客户的基本信息如下：\n客户姓名：{cust_name}, 客户号：{hs_cust_id}, 性别：{gender}, 年龄段：{age}, 风险偏好：{risk_prefer}, 客户状态：{cust_status}, 是否有效：{vld_cust}, 投资品种偏好：{brd_pref}, 投资偏好行业：{pref_idy}, 偏好产品类型：{pref_pd_tp}, 风险等级：{cust_rsk_grd}, 签约状态: {cust_adv_sign_status}'''
                    card_data = query_content
                    card = {'card_id': 'CUSTOMER001', 'consumer_data_card': {'title': {'cust_code': hs_cust_id, 'cust_name': cust_name, 'cust_account': cust_account, 'gnd_code': gnd_code}, 'content': card_data}}
                    return (text, card)
                else:
                    return ('无法查询到客户，请用户提供正确客户名称或客户ID', None)
            elif feature == '资产信息':
                url = f'''{get_project_api_uri('wealth', 'cust_asset')}'''
                header = {}
                pay_load = {'cust_id': cust_code}
                response = await http_execute_async(url, 'POST', pay_load, header)
                logger.info('Application event')
                if response['code'] == 0 or response['code'] == '0':
                    query_content = response.get('content') or []
                else:
                    return ('无法查询到该客户，请用户提供正确客户姓名或客户号。', None)
                if len(query_content) >= 1:
                    hs_cust_id = query_content[0].get('hs_cust_id')
                    statc_dt = query_content[0].get('statc_dt')
                    ast_peak_val_365 = query_content[0].get('ast_peak_val_365')
                    tot_ast_peak_val = query_content[0].get('tot_ast_peak_val')
                    tot_ast_peak_dt = query_content[0].get('tot_ast_peak_dt')
                    ly_ast_peak_val = query_content[0].get('ly_ast_peak_val')
                    ma_of_scr_mkt_val = query_content[0].get('ma_of_scr_mkt_val')
                    ast = query_content[0].get('ast')
                    lby = query_content[0].get('lby')
                    net_ast = query_content[0].get('net_ast')
                    fnd_bal = query_content[0].get('fnd_bal')
                    mrgn_bal = query_content[0].get('mrgn_bal')
                    gnd_code = query_content[0].get('gnd_code')
                    ms_stk_fnd_txn_num = query_content[0].get('ms_stk_fnd_txn_num')
                    text = f'''该客户的资产信息如下：\n客户姓名：{cust_name}, 客户号：{hs_cust_id}, 统计日期：{statc_dt}, 365自然日净资产峰值：{ast_peak_val_365}, 峰值总资产：{tot_ast_peak_val}(日期：{tot_ast_peak_dt}), 近12月资产峰值：{ly_ast_peak_val}, 场内证券市值: {ma_of_scr_mkt_val}, 资产: {ast}, 负债: {lby}, 净资产: {net_ast}, 股基交易量: {ms_stk_fnd_txn_num}, 资金余额: {fnd_bal}, 两融余额: {mrgn_bal}'''
                    card_data = query_content
                    card = {'card_id': 'CUSTOMER002', 'consumer_data_card': {'title': {'cust_code': hs_cust_id, 'cust_name': cust_name, 'cust_account': cust_account, 'gnd_code': gnd_code}, 'content': card_data}}
                    return (text, card)
                else:
                    return ('无法查询到客户，请用户提供正确客户名称或客户ID', None)
            elif feature == '持仓信息':
                url = f'''{get_project_api_uri('wealth', 'cust_hold')}'''
                header = {}
                pay_load = {'cust_id': cust_code}
                response = await http_execute_async(url, 'POST', pay_load, header)
                logger.info('Application event')
                if response['code'] == 0 or response['code'] == '0':
                    query_content = response.get('content') or []
                else:
                    return ('无法查询到该客户的持仓信息，请用户提供正确客户姓名或客户号。', None)
                if len(query_content) >= 1:
                    gnd_code_01 = '--'
                    asset_list = []
                    for i in query_content:
                        gnd_code_01 = i.get('gnd_code')
                        pd_name = i.get('pd_name')
                        pd_code = i.get('pd_code')
                        mkt_tp_code = i.get('mkt_tp_code_new')
                        mkt_tp = _MKT_TP_MAP.get(mkt_tp_code, '--')
                        hold_amt = i.get('hold_amt')
                        hold_share = i.get('hold_share')
                        pd_item = {'产品名称': pd_name, '产品代码': pd_code, '市场类型': mkt_tp, '产品保有金额': hold_amt, '产品保有份额': hold_share}
                        asset_list.append(pd_item)
                    text = f'''客户{cust_name}(客户号: {cust_code})的持仓信息如下：\n{asset_list}'''
                    card_data = query_content
                    card = {'card_id': 'CUSTOMER003', 'consumer_data_card': {'title': {'cust_code': cust_code, 'cust_name': cust_name, 'cust_account': cust_account, 'gnd_code': gnd_code_01}, 'content': card_data}}
                    return (text, card)
                else:
                    return ('无法查询到该客户的持仓信息，请用户提供正确客户姓名或客户号。', None)
            else:
                return (f'''你所填的值，不是符合要求的enum值, 请根据用户需求重新填写''', None)
        else:
            return ('你没有提供正确客户姓名或者客户号，请提供正确的客户姓名或客户号进行查询。', None)
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
