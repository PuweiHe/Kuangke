from util.http_util import UpstreamError
from typing import Any, List, Dict
from config import get_project_api_uri
from langchain.tools import tool
from util.http_util import http_execute_async
from config.logger import logger
from model.exceptions import TokenInvalidError
from util.card_util import store_card
_ERROR_MESSAGE = '很抱歉，未能获取到筛选结果'
private_prod_type1_bus = ['主观股票多头', '量化股票多头', '量化对冲', '管理期货', '套利策略', '债券型', '宏观策略', '多策略', 'FoF/MoM', '结构化', '其他策略']
public_prod_type1_bus = ['FOF', 'QDII', '股票型', '混合型', '货币市场型', '另类投资', '债券型']
private_prod_type2_bus = ['主动权益', '大中华股票', '海外股票', '沪深300指数增强', 'A500指数增强', '中证500指数增强', '中证1000指数增强', '中证2000指数增强', '小市值指数增强', '中证红利指数增强', '其他指数增强', '量化选股', '市场中性', '股票多空', '灵活对冲', 'T0策略', '主观CTA', '量化CTA', '海外CTA', '商品指数', 'ETF套利', '期权套利', '复合套利', '纯债', '混债', '转债策略', 'REITS', '海外固收', '宏观策略', '多策略', '稳健FOF', '平衡FOF', '积极FOF', '低含权类', '高含权类', '线性类', '股票服务类', '海外其他', '新三板', '定增', '其他']
public_prod_type2_bus = ['股票型FOF基金', '混合型FOF基金', '债券型FOF基金', '国际(QDII)股票型基金', '国际(QDII)混合型基金', '国际(QDII)另类投资基金', '国际(QDII)债券型基金', '被动指数型基金', '普通股票型基金', '增强指数型基金', '灵活配置型基金', '偏股混合型基金', '偏债混合型基金', '平衡混合型基金', '商品型基金', '被动指数型债券基金', '短期纯债型基金', '混合债券型二级基金', '混合债券型一级基金', '可转换债券型基金', '增强指数型债券基金', '中长期纯债型基金']
period_list = ['成立以来', '近3年', '近5年', '近1个月', '近1周', '近1年', '近2周', '近2年', '近3个月', '近6个月', '今年以来']
period_map = {'成立以来': 'ETD', '近3年': '3Y', '近5年': '5Y', '近1个月': '1M', '近1周': '1W', '近1年': '1Y', '近2周': '2W', '近2年': '2Y', '近3个月': '3M', '近6个月': '6M', '今年以来': 'YTD'}
ORDER_BY_NAME_MAP = {'company': '基金公司', 'establish_years': '成立年限', 'short_name': '基金简称', 'full_name': '基金全称', 'risk_level': '风险等级', 'iss_stat_xet': '运作状态', 'prod_type1_bus': '一级分类', 'prod_type2_bus': '二级分类', 'fund_manager': '基金经理', 'establish_date': '成立日期', 'market_cap': '基金规模', 'fee_rate_gl': '管理费率', 'fee_rate_tg': '托管费率', 'special': '特殊标识', 'net_value': '净值', 'roi': '收益率', 'sharp_ratio': '夏普比率', 'vq': '波动率', 'mdd': '最大回撤', 'excess_roi': '超额收益', 'excess_mdd': '超额最大回撤', 'track_sd': '跟踪误差', 'info_ratio': '信息比率', 'roi_rank': '收益率排名', 'mdd_rank': '最大回撤排名', 'sharp_ratio_rank': '夏普比率排名', 'vq_rank': '波动率排名', 'roi_rank_percent': '收益率排名百分位', 'mdd_rank_percent': '最大回撤排名百分位', 'sharp_rank_percent': '夏普比率排名百分位', 'vq_rank_percent': '波动率排名百分位', 'industry': '行业', 'market_cap_style': '市值风格', 'value_develop_style': '价值成长风格', 'other_style': '其他风格', 'PROVISION_TYPE': '产品类型'}
TIME_BASED_ORDER_FIELDS = ['roi', 'sharp_ratio', 'vq', 'mdd', 'excess_roi', 'excess_mdd', 'track_sd', 'info_ratio', 'roi_rank', 'mdd_rank', 'sharp_ratio_rank', 'vq_rank', 'roi_rank_percent', 'mdd_rank_percent', 'sharp_rank_percent', 'vq_rank_percent']

@tool('choose_fund_tool', args_schema={'type': 'object', 'properties': {'company': {'type': 'array', 'description': '基金公司简称'}, 'establish_years': {'type': 'string', 'description': '成立年限，规则举例：等于5年时填 5~5 ，大于5年时填 5~ ，小于5年时填 ~5 ， 大于5年小于8年时填 5~8'}, 'short_name': {'type': 'string', 'description': '产品简称'}, 'full_name': {'type': 'string', 'description': '产品全称'}, 'risk_level': {'type': 'array', 'description': '风险等级，规则举例：R1-低风险  R2-较低风险  R3-中风险  R4-较高风险  R5-高风险', 'enum': ['R1', 'R2', 'R3', 'R4', 'R5']}, 'iss_stat_xet': {'type': 'array', 'description': '产品状态', 'enum': ['运行中', '开放期', '封闭期']}, 'prod_tag': {'type': 'array', 'description': '产品标签  产品标签筛选的基金包含公募和私募，当明确查公募或私募基金时，不要使用该条件', 'enum': ['主观', '主动', '大中华', '海外', '指增', 'QDII债券']}, 'prod_type1': {'type': 'object', 'description': '产品一级分类，当没有明确查公募还是私募时，必须尽可能包含公募和私募分类', 'properties': {'public_prod_type1_bus': {'type': 'array', 'description': '公募产品一级分类', 'enum': public_prod_type1_bus}, 'private_prod_type1_bus': {'type': 'array', 'description': '私募产品一级分类', 'enum': private_prod_type1_bus}}}, 'prod_type2': {'type': 'object', 'description': '产品二级分类，当没有明确查公募还是私募时，必须尽可能包含公募和私募分类', 'properties': {'public_prod_type2_bus': {'type': 'array', 'description': '公募产品二级分类', 'enum': public_prod_type2_bus}, 'private_prod_type2_bus': {'type': 'array', 'description': '私募产品二级分类', 'enum': private_prod_type2_bus}}}, 'fund_manager': {'type': 'array', 'description': '基金经理'}, 'manage_time': {'type': 'string', 'description': '基金经理管理年限, 单位：年，规则举例：等于5年时填 5~5 ，大于5年时填 5~ ，小于5年时填 ~5 ， 大于5年小于8年时填 5~8'}, 'manager_scale': {'type': 'string', 'description': '基金经理管理规模, 单位：元，规则举例：等于5亿元时填 500000000~500000000，大于5亿元时填 500000000~ ，小于5亿元时填 ~500000000 ， 大于5亿元小于8亿元时填 500000000~800000000'}, 'daily_change': {'type': 'string', 'description': '前一日涨跌幅%, 规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%小于8%时填 5~8'}, 'market_cap': {'type': 'string', 'description': '产品规模，单位：元，规则举例：等于5亿元时填 500000000~500000000，大于5亿元时填 500000000~ ，小于5亿元时填 ~500000000 ， 大于5亿元小于8亿元时填 500000000~800000000'}, 'establish_date': {'type': 'string', 'description': '成立日期， 日期格式为：yyyymmdd，规则举例：等于20210607时填20210607~20210607，晚于20210607时填 20210607~ ，早于20210607时时填 ~20210607， 在20210607和20220322之间时填 20210607~20220322'}, 'fee_rate_gl': {'type': 'string', 'description': '管理费率(%), 规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%小于8%时填 5~8'}, 'fee_rate_tg': {'type': 'string', 'description': '托管费率(%), 规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%小于8%时填 5~8'}, 'special_type': {'type': 'string', 'description': '特殊类型', 'enum': ['ETF', 'LOF', 'REITS', 'MRF', 'FOF', 'QDII', 'REG']}, 'stock_ratio': {'type': 'string', 'description': '股票仓位(%), 规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%小于8%时填 5~8'}, 'bond_ratio': {'type': 'string', 'description': '债券仓位(%), 规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%小于8%时填 5~8'}, 'fund_advisor': {'type': 'string', 'description': '投资顾问名称'}, 'maturity_date': {'type': 'string', 'description': '到期日期，日期格式为：yyyymmdd，规则举例：等于20210607时填20210607~20210607，晚于20210607时填 20210607~ ，早于20210607时时填 ~20210607， 在20210607和20220322之间时填 20210607~20220322'}, 'close_operate_time': {'type': 'string', 'description': '封闭期，单位：天，规则举例：等于30天填30~30，大于30天填30~，小于30天填~30，大于30天小于50天填30~50'}, 'book_buy_date': {'type': 'string', 'description': '预约申购日，1-当日 2-当周 3-当月 4-当季度', 'enum': ['1', '2', '3', '4']}, 'book_sell_date': {'type': 'string', 'description': '预约赎回日，1-当日 2-当周 3-当月 4-当季度', 'enum': ['1', '2', '3', '4']}, 'roi': {'type': 'object', 'description': '收益率', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%且小于8%时填 5~8'}}}, 'sharp_ratio': {'type': 'object', 'description': '夏普比率', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于0.75时填 0.75~0.75 ，大于0.75时填 0.75~ ，小于0.75时填 ~0.75 ， 大于0.75且小于1.88时填 0.75~1.88'}}}, 'vq': {'type': 'object', 'description': '波动率', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%且小于8%时填 5~8'}}}, 'mdd': {'type': 'object', 'description': '最大回撤', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%且小于8%时填 5~8'}}}, 'excess_roi': {'type': 'object', 'description': '超额收益率', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%且小于8%时填 5~8'}}}, 'excess_mdd': {'type': 'object', 'description': '超额回撤', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%且小于8%时填 5~8'}}}, 'track_sd': {'type': 'object', 'description': '跟踪误差', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%且小于8%时填 5~8'}}}, 'info_ratio': {'type': 'object', 'description': '信息比率', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于0.5时填 0.5~0.5 ，大于0.5时填 0.5~ ，小于0.5时填 ~0.5 ， 大于0.5且小于0.8时填 0.5~0.8'}}}, 'roi_rank': {'type': 'object', 'description': '收益率_同类排名', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5时填 5~5 ，大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}}}, 'mdd_rank': {'type': 'object', 'description': '最大回撤_同类排名', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5时填 5~5 ，大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}}}, 'sharp_ratio_rank': {'type': 'object', 'description': '夏普比率_同类排名', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5时填 5~5 ，大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}}}, 'vq_rank': {'type': 'object', 'description': '波动率_同类排名', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，规则举例：等于5时填 5~5 ，大于5时填 5~ ，小于5时填 ~5 ， 大于5且小于8时填 5~8'}}}, 'roi_rank_percent': {'type': 'object', 'description': '收益率_排名百分位', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，必须为小数，规则举例：等于5%时填 0.05~0.05 ，排名后60%时填 0.6~ ，排名前5%时填 ~0.05 ， 排名在5%到8%之间时填 0.05~0.08'}}}, 'mdd_rank_percent': {'type': 'object', 'description': '最大回撤_排名百分位', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，必须为小数，规则举例：等于5%时填 0.05~0.05 ，排名后60%时填 0.6~ ，排名前5%时填 ~0.05 ， 排名在5%到8%之间时填 0.05~0.08'}}}, 'sharp_rank_percent': {'type': 'object', 'description': '夏普比率_排名百分位', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，必须为小数，规则举例：等于5%时填 0.05~0.05 ，排名后60%时填 0.6~ ，排名前5%时填 ~0.05 ， 排名在5%到8%之间时填 0.05~0.08'}}}, 'vq_rank_percent': {'type': 'object', 'description': '波动率_排名百分位', 'properties': {'time_period': {'type': 'string', 'description': '时间段', 'enum': period_list}, 'value': {'type': 'string', 'description': '数值，必须为小数，规则举例：等于5%时填 0.05~0.05 ，排名后60%时填 0.6~ ，排名前5%时填 ~0.05 ， 排名在5%到8%之间时填 0.05~0.08'}}}, 'industry': {'type': 'object', 'description': '行业配置', 'properties': {'industry_name': {'type': 'string', 'description': '行业名称', 'enum': period_list}, 'industry_ratio': {'type': 'string', 'description': '行业配置比例，规则举例：等于5%时填 5~5 ，大于5%时填 5~ ，小于5%时填 ~5 ， 大于5%且小于8%时填 5~8'}}}, 'market_cap_style': {'type': 'string', 'description': '市值风格', 'enum': ['大盘', '中盘', '小盘']}, 'value_develop_style': {'type': 'string', 'description': '价值成长风格', 'enum': ['成长', '均衡', '价值']}, 'other_style': {'type': 'string', 'description': '其他风格', 'enum': ['红利', '低波']}, 'provision_type': {'type': 'string', 'description': '业绩报酬方法'}, 'pageNum': {'type': 'number', 'default': 1, 'description': '页码，默认为1'}, 'pageSize': {'type': 'number', 'default': 10, 'description': '每页数量，默认为10'}, 'orderBy': {'type': 'string', 'description': '排序字段，必须为已有筛选指标'}, 'order_time': {'type': 'string', 'description': '排序的时间段，仅当orderBy为带时间段的指标(如roi、sharp_ratio、mdd等)时必须填写，指定按哪个时间段的指标排序', 'enum': period_list}, 'isasc': {'type': 'boolean', 'description': '排序方式，True-升序 False-降序', 'enum': [True, False]}}})
async def choose_fund_tool(**kwargs):
    """Choose fund tool. Use validated tool arguments and return adapter results."""
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
    """Get fund info. Use validated tool arguments and return adapter results."""
    try:
        payload = {}
        prod_tag = arguments.get('prod_tag') or []
        tag_type_list = []
        if isinstance(prod_tag, list) and len(prod_tag) > 0:
            for tag in prod_tag:
                if tag in ['主观', '主动']:
                    tag_type_list += ['主动权益', '普通股票型基金', '灵活配置型基金', '偏股混合型基金']
                elif tag in ['大中华', '海外']:
                    tag_type_list += ['大中华股票', '海外股票', '国际(QDII)股票型基金', '国际(QDII)混合型基金']
                elif tag == '指增':
                    tag_type_list += ['沪深300指数增强', 'A500指数增强', '中证500指数增强', '中证1000指数增强', '中证2000指数增强', '小市值指数增强', '中证红利指数增强', '其他指数增强', '量化选股', '增强指数型基金']
                elif tag in ['海外债券', 'QDII债券']:
                    tag_type_list += ['海外固收', '国际(QDII)债券型基金']
                else:
                    continue
        prod_type1 = arguments.get('prod_type1') or {}
        public_type1 = prod_type1.get('public_prod_type1_bus') or []
        private_type1 = prod_type1.get('private_prod_type1_bus') or []
        prod_type1_bus = list(set(public_type1 + private_type1)) if public_type1 or private_type1 else None
        prod_type2 = arguments.get('prod_type2') or {}
        public_type2 = prod_type2.get('public_prod_type2_bus') or []
        private_type2 = prod_type2.get('private_prod_type2_bus') or []
        prod_type2_bus = list(set(public_type2 + private_type2 + tag_type_list)) if public_type2 or private_type2 or tag_type_list else None
        param_mapping = {'company': arguments.get('company'), 'establish_years': arguments.get('establish_years'), 'short_name': arguments.get('short_name'), 'full_name': arguments.get('full_name'), 'risk_level': arguments.get('risk_level'), 'iss_stat_xet': arguments.get('iss_stat_xet'), 'prod_type1_bus': prod_type1_bus, 'prod_type2_bus': prod_type2_bus, 'fund_manager': arguments.get('fund_manager'), 'manage_time': arguments.get('manage_time'), 'manager_scale': arguments.get('manager_scale'), 'daily_change': arguments.get('daily_change'), 'market_cap': arguments.get('market_cap'), 'establish_date': arguments.get('establish_date'), 'fee_rate_gl': arguments.get('fee_rate_gl'), 'fee_rate_tg': arguments.get('fee_rate_tg'), 'special_type': arguments.get('special_type'), 'stock_ratio': arguments.get('stock_ratio'), 'bond_ratio': arguments.get('bond_ratio'), 'FUND_ADVISOR': arguments.get('fund_advisor'), 'MATURITY_DATE': arguments.get('maturity_date'), 'CLOSE_OPERATE_TIME': arguments.get('close_operate_time'), 'BOOK_BUY_DATE': arguments.get('book_buy_date'), 'BOOK_SELL_DATE': arguments.get('book_sell_date'), 'roi': arguments.get('roi'), 'sharp_ratio': arguments.get('sharp_ratio'), 'vq': arguments.get('vq'), 'mdd': arguments.get('mdd'), 'EXCESS_ROI': arguments.get('excess_roi'), 'EXCESS_MDD': arguments.get('excess_mdd'), 'TRACK_SD': arguments.get('track_sd'), 'INFO_RATIO': arguments.get('info_ratio'), 'roi_rank': arguments.get('roi_rank'), 'mdd_rank': arguments.get('mdd_rank'), 'sharp_ratio_rank': arguments.get('sharp_ratio_rank'), 'vq_rank': arguments.get('vq_rank'), 'roi_rank_percent': arguments.get('roi_rank_percent'), 'mdd_rank_percent': arguments.get('mdd_rank_percent'), 'sharp_rank_percent': arguments.get('sharp_rank_percent'), 'vq_rank_percent': arguments.get('vq_rank_percent'), 'industry': arguments.get('industry'), 'market_cap_style': arguments.get('market_cap_style'), 'value_develop_style': arguments.get('value_develop_style'), 'other_style': arguments.get('other_style'), 'PROVISION_TYPE': arguments.get('provision_type'), 'NUM_PAGE_NO': arguments.get('pageNum', 1), 'NUM_PAGE_SIZE': arguments.get('pageSize', 10), 'orderBy': arguments.get('orderBy'), 'isasc': arguments.get('isasc')}
        for key, value in param_mapping.items():
            if value is not None and value != '':
                if key == 'isasc' and value == True:
                    payload[key] = 'true'
                elif key == 'isasc' and value == False:
                    payload[key] = 'false'
                elif key == 'prod_type1_bus' and isinstance(value, list):
                    payload[key] = ','.join(value)
                elif key == 'prod_type2_bus' and isinstance(value, list):
                    payload[key] = ','.join(value)
                elif key == 'company' and isinstance(value, list):
                    payload[key] = ','.join(value)
                elif key == 'risk_level' and isinstance(value, list):
                    payload[key] = ','.join(value)
                elif key == 'iss_stat_xet' and isinstance(value, list):
                    if '运行中' in value:
                        value = list(set(value) | {'开放期'})
                    payload[key] = ','.join(value)
                elif key == 'fund_manager' and isinstance(value, list):
                    payload[key] = ','.join(value)
                elif key == 'roi' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['int_interval_roi'] = period_map[value['time_period']]
                elif key == 'sharp_ratio' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['int_interval_sharp'] = period_map[value['time_period']]
                elif key == 'roi_rank' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['roi_rank_interval'] = period_map[value['time_period']]
                elif key == 'mdd_rank' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['mdd_rank_interval'] = period_map[value['time_period']]
                elif key == 'sharp_ratio_rank' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['sharp_rank_interval'] = period_map[value['time_period']]
                elif key == 'roi_rank_percent' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['roi_rank_interval'] = period_map[value['time_period']]
                elif key == 'mdd_rank_percent' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['mdd_rank_interval'] = period_map[value['time_period']]
                elif key == 'sharp_rank_percent' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['sharp_rank_interval'] = period_map[value['time_period']]
                elif key == 'vq' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['int_interval_vq'] = period_map[value['time_period']]
                elif key == 'mdd' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['int_interval_mdd'] = period_map[value['time_period']]
                elif key == 'EXCESS_ROI' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['EXCESS_ROI_interval'] = period_map[value['time_period']]
                elif key == 'EXCESS_MDD' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['EXCESS_MDD_interval'] = period_map[value['time_period']]
                elif key == 'TRACK_SD' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['TRACK_SD_interval'] = period_map[value['time_period']]
                elif key == 'INFO_RATIO' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['INFO_RATIO_interval'] = period_map[value['time_period']]
                elif key == 'vq_rank' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['vq_rank_interval'] = period_map[value['time_period']]
                elif key == 'vq_rank_percent' and isinstance(value, dict):
                    payload[key] = value['value']
                    payload['vq_rank_interval'] = period_map[value['time_period']]
                elif key == 'industry' and isinstance(value, dict):
                    payload['industry_name'] = value.get('industry_name')
                    payload['industry_ratio'] = value.get('industry_ratio')
                else:
                    payload[key] = value
        order_time = arguments.get('order_time') or None
        orderBy = arguments.get('orderBy') or None
        if order_time and orderBy in ['roi', 'sharp_ratio', 'vq', 'mdd', 'excess_roi', 'excess_mdd', 'track_sd', 'info_ratio', 'roi_rank', 'mdd_rank', 'sharp_ratio_rank', 'vq_rank', 'roi_rank_percent', 'mdd_rank_percent', 'sharp_rank_percent', 'vq_rank_percent']:
            if orderBy == 'roi':
                payload['int_interval_roi'] = period_map[order_time]
            elif orderBy == 'sharp_ratio':
                payload['int_interval_sharp'] = period_map[order_time]
            elif orderBy == 'vq':
                payload['int_interval_vq'] = period_map[order_time]
            elif orderBy == 'mdd':
                payload['int_interval_mdd'] = period_map[order_time]
            elif orderBy == 'excess_roi':
                payload['int_interval_excess_roi'] = period_map[order_time]
            elif orderBy == 'excess_mdd':
                payload['int_interval_excess_mdd'] = period_map[order_time]
            elif orderBy == 'track_sd':
                payload['int_interval_track_sd'] = period_map[order_time]
            elif orderBy == 'info_ratio':
                payload['int_interval_info_ratio'] = period_map[order_time]
            elif orderBy == 'roi_rank':
                payload['roi_rank_interval'] = period_map[order_time]
            elif orderBy == 'mdd_rank':
                payload['mdd_rank_interval'] = period_map[order_time]
            elif orderBy == 'sharp_ratio_rank':
                payload['sharp_rank_interval'] = period_map[order_time]
            elif orderBy == 'vq_rank':
                payload['vq_rank_interval'] = period_map[order_time]
            elif orderBy == 'roi_rank_percent':
                payload['roi_rank_interval'] = period_map[order_time]
            elif orderBy == 'mdd_rank_percent':
                payload['mdd_rank_interval'] = period_map[order_time]
            elif orderBy == 'sharp_rank_percent':
                payload['sharp_rank_interval'] = period_map[order_time]
            elif orderBy == 'vq_rank_percent':
                payload['vq_rank_interval'] = period_map[order_time]
        url = f'''{get_project_api_uri('wealth', 'choose_fund')}'''
        header = {}
        response = await http_execute_async(url, 'POST', payload, header)
        logger.info('Application event')
        if response and (response.get('code') == 0 or response.get('code') == '0'):
            query_content = response.get('content') or {}
            query_result = query_content.get('VALUE_LIST1') or []
            count_num = query_content.get('NUM_TOTAL_COUNT') or None
            if query_result and len(query_result) > 0:
                fund_list = []
                for i in query_result:
                    fund_item = {}
                    if i.get('short_name'):
                        fund_item['基金名称'] = i.get('short_name')
                    if i.get('prod_code'):
                        fund_item['基金代码'] = i.get('prod_code')
                    if i.get('fund_manager'):
                        fund_item['基金经理'] = i.get('fund_manager')
                    if i.get('establish_years'):
                        fund_item['成立年限'] = i.get('establish_years')
                    if i.get('prod_type'):
                        fund_item['产品类型'] = i.get('prod_type')
                    if i.get('roi'):
                        if payload.get('int_interval_roi'):
                            time_period = next((k for k, v in period_map.items() if v == payload.get('int_interval_roi')), None)
                            fund_item[f'''{time_period}收益率'''] = f'''{round(i.get('roi'), 2)}%'''
                        else:
                            time_period = '今年以来'
                            fund_item[f'''{time_period}收益率'''] = f'''{round(i.get('roi'), 2)}%'''
                    fund_list.append(fund_item)
                orderBy = payload.get('orderBy')
                isasc = payload.get('isasc')
                if orderBy and isasc:
                    field_name = ORDER_BY_NAME_MAP.get(orderBy, orderBy)
                    order_time = arguments.get('order_time')
                    if order_time and orderBy in TIME_BASED_ORDER_FIELDS:
                        sort_desc = f'''{order_time}{field_name}{('升序' if isasc == 'true' else '降序')}'''
                    else:
                        sort_desc = f'''{field_name}{('升序' if isasc == 'true' else '降序')}'''
                else:
                    sort_desc = '今年以来收益率降序'
                if isinstance(count_num, int) and count_num > 10:
                    total_count = count_num
                    text = f'''共筛选出 {total_count} 个符合条件的基金产品, 按{sort_desc}排序, 前10个为:\n{fund_list}'''
                else:
                    total_count = len(query_result)
                    text = f'''共筛选出 {total_count} 个符合条件的基金产品, 按{sort_desc}排序:\n{fund_list}'''
                card_data = query_result
                card = {'card_id': 'FUND004', 'consumer_data_card': card_data}
                return (text, card)
            else:
                return ('未找到符合条件的基金产品', None)
        else:
            logger.error('Application event')
            return (_ERROR_MESSAGE, None)
    except (TokenInvalidError, UpstreamError):
        raise
    except Exception as e:
        logger.error('Application event')
        return (_ERROR_MESSAGE, None)
