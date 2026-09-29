from typing import Any, List, Dict
import asyncio
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到筛选结果'
_CUST_STATUS_MAP = {'0': '正常', '1': '冻结', '2': '挂失', '3': '销户', '6': '休眠', 'A': '不合格司法冻结', 'C': '中登休眠', 'E': '中登不合格', 'G': '内部休眠', 'J': '内部不合格', 'F': '系统锁定', 'L': '未激活', 'g': '解约'}
_AGE_MAP = {'0': '40后', '1': '50后', '2': '60后', '3': '70后', '4': '80后', '5': '90后', '6': '00后', '7': '40前'}

@tool('choose_customer_tool', args_schema={'type': 'object', 'properties': {'user_code': {'type': 'string', 'description': '当前用户账号'}, 'age_code': {'type': 'string', 'description': '年龄，规则如下：0-40后 1-50后 2-60后 3-70后 4-80后 5-90后 6-00后 7-40前', 'enum': ['0', '1', '2', '3', '4', '5', '6', '7']}, 'rsk_pref_code': {'type': 'string', 'description': '风险偏好, 规则如下： 0-低风险偏好 1-较低风险偏好 2-中等风险偏好 3-较高风险偏好 4-高风险偏好 9-未知', 'enum': ['0', '1', '2', '3', '4', '5', '6', '7', '9']}, 'fund_adv_sign_status': {'type': 'string', 'description': '基金投顾签约状态，规则如下: 0-未签约 1-已签约', 'enum': ['0', '1']}, 'cust_st_code': {'type': 'string', 'description': '客户状态代码，规则如下：0-正常 1-冻结 2-挂失 3-销户 6-休眠 A-不合格司法冻结 C-中登休眠 E-中登不合格 G-内部休眠 J-内部不合格 F-系统锁定 L-未激活 g-解约', 'enum': ['0', '1', '2', '3', '6', 'A', 'C', 'E', 'G', 'J', 'F', 'L', 'g']}, 'vld_cust_ind': {'type': 'string', 'description': '有效客户标志，规则如下：0-无效，1-有效', 'enum': ['0', '1']}, 'brd_pref_code': {'type': 'string', 'description': '品种偏好代码, 规则如下:  0-股基交易型 1-债券交易型 2-产品投资型 3-混合型', 'enum': ['0', '1', '2', '3']}, 'pref_idy_code': {'type': 'string', 'description': '偏好行业代码, 规则如下：6230000000-日常消费 6235000000-医疗保健 6255000000-公用事业 6245000000-信息技术 6240000000-金融 6215000000-材料 6210000000-能源 6220000000-工业 6225000000-可选消费 6250000000-电信服务 6260000000-房地产', 'enum': ['6230000000', '6235000000', '6255000000', '6245000000', '6240000000', '6215000000', '6210000000', '6220000000', '6225000000', '6250000000', '6260000000']}, 'pref_pd_tp_code': {'type': 'string', 'description': '偏好产品类型代码, 规则如下：1-权益类 2-类固定收益类 3-挂钩浮动收益类 4-现金管理类 6-其他', 'enum': ['1', '2', '3', '4', '6']}, 'cust_rsk_grd_code': {'type': 'string', 'description': '客户风险等级代码, 规则如下：5-C5(积极型) 6-C4(相对积极型) 7-C3(稳健型) 8-C2(相对保守型) 9-C1(保守型) A-C1(最低风险等级) x-自定义风险等级 0-未评级'}, 'ast_peak_val_365': {'type': 'string', 'description': '365自然日净资产峰值，规则如下：大于5000元时填 5000~ ，小于5000元时填 ~5000 ， 大于5000元小于8000元时填 5000~8000'}, 'tot_ast_peak_val': {'type': 'string', 'description': '峰值总资产，规则如下：大于5000元时填 5000~ ，小于5000元时填 ~5000 ， 大于5000元小于8000元时填 5000~8000'}, 'tot_ast_peak_dt': {'type': 'string', 'description': '峰值总资产日期，规则如下：在2025年3月27日之后时填 20250327~，在2025年3月27日之前时填 ~20250327 ，在2025年1月1日到2025年3月31日之间时填  20250101~20250331'}, 'ly_ast_peak_val': {'type': 'string', 'description': '近12月净资产峰值，规则如下：大于5000元时填 5000~ ，小于5000元时填 ~5000 ， 大于5000元小于8000元时填 5000~8000'}, 'ma_of_scr_mkt_val': {'type': 'string', 'description': '场内证券市值，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'ms_stk_fnd_txn_num': {'type': 'string', 'description': '股基交易量，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'ast': {'type': 'string', 'description': '资产，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'lby': {'type': 'string', 'description': '负债，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'net_ast': {'type': 'string', 'description': '净资产，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'fnd_bal': {'type': 'string', 'description': '资金余额，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'mrgn_bal': {'type': 'string', 'description': '两融余额，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'fnc_bal': {'type': 'string', 'description': '融资余额，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'shrhlr_age': {'type': 'string', 'description': '股龄，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'pd_code': {'type': 'string', 'description': '保有的产品代码，例如：040001'}, 'hold_amt': {'type': 'string', 'description': '保有金额，规则如下：大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}, 'pageNum': {'type': 'string', 'default': '1', 'description': '页码，默认为1'}, 'pageSize': {'type': 'string', 'default': '10', 'description': '每页数量，默认为10'}, 'orderBy': {'type': 'string', 'description': '排序字段'}, 'isasc': {'type': 'boolean', 'description': '排序方式，True-升序 False-降序', 'enum': [True, False]}}, 'required': ['user_code']})
async def choose_customer_tool(**kwargs):
    """Choose customer tool. Use validated tool arguments and return adapter results."""
    arguments = kwargs
    fund_result, card = await get_choose_customer_info(arguments)
    if fund_result and card:
        store_card(card)
        return [[fund_result], None]
    elif isinstance(fund_result, str) and card is None:
        return [[fund_result], None]
    else:
        return [[_ERROR_MESSAGE], None]

async def get_choose_customer_info(arguments: dict) -> Any:
    """Get choose customer info. Use validated tool arguments and return adapter results."""
    try:
        hold_amt = arguments.get('hold_amt')
        pd_code = arguments.get('pd_code')
        if hold_amt and (not pd_code or pd_code == ''):
            return ('请用户补充保有产品的代码，只提供保有金额无法进行筛选', None)
        payload = {}
        param_mapping = {'user_code': arguments.get('user_code'), 'age_code': arguments.get('age_code'), 'rsk_pref_code': arguments.get('rsk_pref_code'), 'fund_adv_sign_status': arguments.get('fund_adv_sign_status'), 'cust_st_code': arguments.get('cust_st_code'), 'vld_cust_ind': arguments.get('vld_cust_ind'), 'brd_pref_code': arguments.get('brd_pref_code'), 'pref_idy_code': arguments.get('pref_idy_code'), 'pref_pd_tp_code': arguments.get('pref_pd_tp_code'), 'cust_rsk_grd_code': arguments.get('cust_rsk_grd_code'), 'ast_peak_val_365': arguments.get('ast_peak_val_365'), 'tot_ast_peak_val': arguments.get('tot_ast_peak_val'), 'tot_ast_peak_dt': arguments.get('tot_ast_peak_dt'), 'ly_ast_peak_val': arguments.get('ly_ast_peak_val'), 'ma_of_scr_mkt_val': arguments.get('ma_of_scr_mkt_val'), 'ms_stk_fnd_txn_num': arguments.get('ms_stk_fnd_txn_num'), 'ast': arguments.get('ast'), 'lby': arguments.get('lby'), 'net_ast': arguments.get('net_ast'), 'fnd_bal': arguments.get('fnd_bal'), 'mrgn_bal': arguments.get('mrgn_bal'), 'fnc_bal': arguments.get('fnc_bal'), 'shrhlr_age': arguments.get('shrhlr_age'), 'pd_code': arguments.get('pd_code'), 'hold_amt': arguments.get('hold_amt'), 'NUM_PAGE_NO': arguments.get('pageNum'), 'NUM_PAGE_SIZE': arguments.get('pageSize'), 'orderBy': arguments.get('orderBy'), 'isasc': arguments.get('isasc')}
        for key, value in param_mapping.items():
            if value is not None and value != '':
                if key == 'isasc' and value == True:
                    payload[key] = 'true'
                elif key == 'isasc' and value == False:
                    payload[key] = 'false'
                else:
                    payload[key] = value
        url = f'''{get_project_api_uri('wealth', 'choose_cust')}'''
        header = {}
        response = await http_execute_async(url, 'POST', payload, header)
        logger.info('Application event')
        if response and (response.get('code') == 0 or response.get('code') == '0'):
            query_content = response.get('content') or {}
            query_result = query_content.get('VALUE_LIST1') or []
            if query_result and len(query_result) > 0:
                cust_list = []
                for i in query_result:
                    cust_item = {}
                    if i.get('client_name'):
                        cust_item['客户名称'] = i.get('client_name')
                    if i.get('hs_cust_id'):
                        cust_item['客户号'] = i.get('hs_cust_id')
                    if i.get('fund_account'):
                        cust_item['资金账号'] = i.get('fund_account')
                    if i.get('cust_st_code'):
                        cust_item['客户状态'] = _CUST_STATUS_MAP.get(str(i.get('cust_st_code')), '--')
                    if i.get('age_code'):
                        cust_item['年龄段'] = _AGE_MAP.get(str(i.get('age_code')), '--')
                    cust_list.append(cust_item)
                total_count = len(query_result)
                text = f'''共筛选出 {total_count} 个符合条件的客户:\n{cust_list}'''
                card_data = query_result
                card = {'card_id': 'CUSTOMER004', 'consumer_data_card': card_data}
                return (text, card)
            else:
                return ('告诉用户: 未找到符合条件的客户', None)
        else:
            logger.error('Application event')
            return (_ERROR_MESSAGE, None)
    except TokenInvalidError:
        raise
    except Exception as e:
        logger.error('Application event')
        return (_ERROR_MESSAGE, None)
