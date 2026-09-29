from util.http_util import UpstreamError
import pandas
from datetime import datetime
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from config.logger import logger
from config import get_project_api_uri
from util.http_util import http_execute
future_list = ['平衡计分卡', '主营收入', '考核利润', '直接代买收入', '代销产品收入', '直接代买收入市场份额', '代销产品收入市场份额', '新开客户数', '新开有效户', '总客户数', '总有效户', '股基交易量', 'A股交易量', 'A股交易量当地市场份额', '新开交易型资产', '总交易型资产', '前台员工数', '产品销售额']
http_search_all_business_list = ['股基交易量', 'A股交易量']

@tool('business_management_tool', args_schema={'type': 'object', 'properties': {'branch_company': {'type': 'object', 'properties': {'company_code': {'type': 'string', 'default': None, 'description': '公司code、机构代码'}, 'company_name': {'type': 'string', 'default': None, 'description': '分公司名称', 'examples': []}, 'company_scope': {'type': 'boolean', 'default': False, 'description': '是否只查询分公司。如果只查询分公司,不查询营业部，该字段填写True;如果查询营业部该字段填写False;当scope参数为True时,该字段填写False;当business_name参数不为None时，该字段填写False。'}}}, 'business_department': {'type': 'object', 'description': '营业部', 'properties': {'scope': {'type': 'boolean', 'default': False, 'description': '是否查询所有的营业部。如果查询所有的营业部，该字段填写True, 如果查询部分营业部，该字段填写False, 当business_code参数不为None时，该字段填写False。'}, 'business_code': {'type': 'string', 'default': None, 'description': '营业部code、营业部代码'}, 'business_name': {'type': 'string', 'default': None, 'description': '营业部名称', 'examples': []}}}, 'indicator_name': {'type': 'string', 'default': 'None', 'description': '经营管理筛选指标名称', 'enum': future_list}, 'balancedScorecard_list': {'type': 'array', 'description': '筛选平衡计分卡评价列表', 'items': {'type': 'object', 'properties': {'card_year': {'type': 'string', 'default': None, 'description': '年份日期, 日期格式：YYYY, 当用户进行区间查询时，用~连接: YYYY~YYYY', 'examples': []}, 'balancedScorecardEvaluation': {'type': 'string', 'default': None, 'description': '平衡计分卡评价', 'examples': []}, 'balancedScorecardRankingN': {'type': 'string', 'default': None, 'description': '平衡计分卡排名，如果不指定则不填'}, 'sec': {'type': 'string', 'default': None, 'description': '分组'}}}}, 'financial_info': {'type': 'object', 'description': '财务指标', 'properties': {'mainIncome_info': {'type': 'object', 'description': '主营收入信息', 'properties': {'mainIncome': {'type': 'string', 'default': None, 'description': '主营收入'}, 'mainIncomeSysRankN': {'type': 'string', 'default': None, 'description': '主营收入系统排名'}, 'mainIncomeGroupRankN': {'type': 'string', 'default': None, 'description': '主营收入同组排名'}}}, 'assessmentProfit_info': {'type': 'object', 'description': '考核利润信息', 'properties': {'assessmentProfit': {'type': 'string', 'default': None, 'description': '考核利润，单位: 元，例如：1亿元应填为100000000, 50万元应填为500000'}, 'assessmentProfitSysRankN': {'type': 'string', 'default': None, 'description': '考核利润系统排名'}, 'assessmentProfitGroupRankN': {'type': 'string', 'default': None, 'description': '考核利润同组排名'}}}, 'directCommission_info': {'type': 'object', 'description': '直接代买收入信息', 'properties': {'directCommission': {'type': 'string', 'default': None, 'description': '直接代买收入'}, 'directCommissionSysRankN': {'type': 'string', 'default': None, 'description': '直接代买系统排序'}, 'directCommissionGroupRankN': {'type': 'string', 'default': None, 'description': '直接代买同组排序'}}}, 'distributionIncome_info': {'type': 'object', 'description': '代销产品收入信息', 'properties': {'distributionIncome': {'type': 'string', 'default': None, 'description': '代销产品收入'}, 'distributionIncomeSysRankN': {'type': 'string', 'default': None, 'description': '代销产品收入系统排序'}, 'distributionIncomeGroupRankN': {'type': 'string', 'default': None, 'description': '代销产品收入同组排序'}}}}}, 'customer_size_info': {'type': 'object', 'description': '客户规模', 'properties': {'newCustomers_info': {'type': 'object', 'description': '新开客户数信息', 'properties': {'newCustomers': {'type': 'string', 'default': None, 'description': '新开客户数'}, 'newCustomersSysRankN': {'type': 'string', 'default': None, 'description': '新开客户数系统排名'}, 'newCustomersGroupRankN': {'type': 'string', 'default': None, 'description': '新开客户数同组排名'}}}, 'newValidCustomers_info': {'type': 'object', 'description': '新开有效户信息', 'properties': {'newValidCustomers': {'type': 'string', 'default': None, 'description': '新开有效户'}, 'newValidSysRankN': {'type': 'string', 'default': None, 'description': '新开有效户系统排名'}, 'newValidGroupRankN': {'type': 'string', 'default': None, 'description': '新开有效户同组排名'}}}, 'totalCustomers_info': {'type': 'object', 'description': '总客户数信息', 'properties': {'totalCustomers': {'type': 'string', 'default': None, 'description': '总客户数'}, 'totalCustomersSysRankN': {'type': 'string', 'default': None, 'description': '总客户数系统排序'}, 'totalCustomersGroupRankN': {'type': 'string', 'default': None, 'description': '总客户数同组排序'}}}, 'totalValidCustomers_info': {'type': 'object', 'description': '总有效户信息', 'properties': {'totalValidCustomers': {'type': 'string', 'default': None, 'description': '总有效户'}, 'totalValidSysRankN': {'type': 'string', 'default': None, 'description': '总有效户系统排序'}, 'totalValidGroupRankN': {'type': 'string', 'default': None, 'description': '总有效户同组排序'}}}}}, 'transaction_info': {'type': 'object', 'description': '交易量', 'properties': {'fundStockVol_info': {'type': 'object', 'description': '股基交易量信息', 'properties': {'fundStockVol': {'type': 'string', 'default': None, 'description': '股基交易量'}, 'fundStockSysRankN': {'type': 'string', 'default': None, 'description': '股基交易量系统排名'}, 'fundStockGroupRankN': {'type': 'string', 'default': None, 'description': '股基交易量同组排名'}}}, 'ashareVol_info': {'type': 'object', 'description': 'A股交易量信息', 'properties': {'ashareVol': {'type': 'string', 'default': None, 'description': 'A股交易量'}, 'ashareSysRankN': {'type': 'string', 'default': None, 'description': 'A股交易量系统排名'}, 'ashareGroupRankN': {'type': 'string', 'default': None, 'description': 'A股交易量同组排名'}, 'ashareMktShare_info': {'type': 'string', 'default': None, 'description': 'A股交易量当地市场份额'}, 'ashareShRank_info': {'type': 'string', 'default': None, 'description': 'A股交易量沪市排名'}, 'ashareSzRank_info': {'type': 'string', 'default': None, 'description': 'A股交易量深市排名'}}}}}, 'asset_info': {'type': 'object', 'description': '资产类型', 'properties': {'newTradingAsset_info': {'type': 'object', 'description': '新开交易型资产', 'properties': {'newTradingAsset': {'type': 'string', 'default': None, 'description': '新开交易型资产, 单位：亿元，需要将 亿元 转换为 元 ，即补8个零'}, 'newAssetSysRankN': {'type': 'string', 'default': None, 'description': '新开交易型资产系统排名'}, 'newAssetGroupRankN': {'type': 'string', 'default': None, 'description': '新开交易型资产同组排名'}}}, 'totalTradingAsset_info': {'type': 'object', 'description': '总交易型资产', 'properties': {'totalTradingAsset': {'type': 'string', 'default': None, 'description': '总交易型资产, 单位：亿元，需要将 亿元 转换为 元 ，即补8个零'}, 'totalAssetSysRankN': {'type': 'string', 'default': None, 'description': '总交易型资产系统排名'}, 'totalAssetGroupRankN': {'type': 'string', 'default': None, 'description': '总交易型资产同组排名'}}}}}, 'employee_info': {'type': 'object', 'description': '前台员工数信息', 'properties': {'staffCnt': {'type': 'string', 'default': None, 'description': '前台员工数'}, 'sysRankN': {'type': 'string', 'default': None, 'description': '前台员工数系统排名'}, 'groupRankN': {'type': 'string', 'default': None, 'description': '前台员工数同组排名'}}}, 'sales_info': {'type': 'object', 'description': '资产类型', 'properties': {'sales': {'type': 'string', 'default': None, 'description': '产品销售额'}, 'salesSysRankN': {'type': 'string', 'default': None, 'description': '产品销售额系统排名'}, 'salesGroupRankN': {'type': 'string', 'default': None, 'description': '产品销售额同组排名'}}}, 'year': {'type': 'array', 'description': '年份日期', 'items': {'type': 'string', 'description': '年份日期, 日期格式：YYYY, 当用户进行区间查询时，用~连接: YYYY~YYYY', 'examples': []}}}, 'required': ['branch_company', 'business_department', 'indicator_name']})
def business_management_tool(config: RunnableConfig, **kwargs):
    """Business management tool. Use validated tool arguments and return adapter results."""
    token = config.get('configurable').get('agent_extends').get('token')
    result = summary_info(token, kwargs)
    if 'function_response' in result:
        function_response = result['function_response']
        card = {'card_id': result.get('card_id'), 'consumer_data_card': result.get('tool_resp')}
        return [[function_response], card]
    else:
        return [result]

def summary_info(token, kwargs):
    branch_company = kwargs.get('branch_company', {})
    company_scope = branch_company.get('company_scope')
    company_code = branch_company.get('company_code', None)
    company_name = branch_company.get('company_name', None)
    business_department = kwargs.get('business_department', {})
    scope = business_department.get('scope')
    business_code = business_department.get('business_code', None)
    business_name = business_department.get('business_name', None)
    balanced_scorecard_list = kwargs.get('balancedScorecard_list', None)
    indicator_name = kwargs.get('indicator_name', None)
    financial_info = kwargs.get('financial_info', None)
    customer_size_info = kwargs.get('customer_size_info', None)
    transaction_info = kwargs.get('transaction_info', None)
    asset_info = kwargs.get('asset_info', None)
    employee_info = kwargs.get('employee_info', None)
    sales_info = kwargs.get('sales_info', None)
    year = kwargs.get('year', None)
    branch_path = 'ORG'
    all_company_and_bus_flag = False
    check_result = check_restrictive_conditions(indicator_name)
    if check_result:
        return check_result
    if indicator_name is None:
        return '无法查询到详细的指标信息，请用户提供正确的指标名称'
    if (company_code and business_code) is None and company_scope and scope:
        return f'''未查询到分公司或营业部ID和名称，请重新提供明确的分公司或营业部名称'''
    basic_params = {}
    if scope:
        branch_path = 'STORE'
        if company_code is None and company_name is None:
            all_company_and_bus_flag = True
        else:
            basic_params['parentOrgCode'] = company_code
            basic_params['parentOrgName'] = company_name
    elif business_name or business_code:
        if business_code is None:
            return f'''未查询到营业部ID，请重新提供明确的营业部名称'''
        branch_path = 'STORE'
        basic_params['orgCode'] = business_code
        basic_params['orgName'] = business_name
    elif company_code or company_name:
        if company_code is None:
            return f'''未查询到机构ID，请重新提供明确的机构名称'''
        basic_params['orgCode'] = company_code
        basic_params['orgName'] = company_name
    else:
        all_company_and_bus_flag = True
    result = {}
    if year is None:
        current_year = datetime.now().year
        year = [current_year - 2, current_year - 1, current_year]
    if '平衡计分卡' == indicator_name and balanced_scorecard_list:
        result['function_response'] = []
        show_info_list = []
        branch_list = []
        answer = []
        sec = None
        if all_company_and_bus_flag:
            for scorecard_item in balanced_scorecard_list:
                indicator_params = {'year': scorecard_item.get('card_year'), 'balancedScorecardEvaluation': scorecard_item.get('balancedScorecardEvaluation'), 'balancedScorecardRankingN': scorecard_item.get('balancedScorecardRankingN'), 'grouping': scorecard_item.get('sec')}
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_performance') + f'''/{branch_path}''', 'GET', token, indicator_params)
                if response and len(response) > 0:
                    if len(response) > 10:
                        answer.append(f'''一共有{len(response)}条数据符合条件，由于数据量过多，只为您展示数据的前十条。''')
                        response = response[:10]
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')}, \n                            评价日期:{res.get('year')},平衡计分卡评价:{res.get('balancedScorecardEvaluation')}:平衡计分卡排名 {res.get('balancedScorecardRanking')}, 分组:{res.get('grouping')}, 成立时间:{res.get('setupDate')}, \n                            机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
        elif basic_params.get('parentOrgCode'):
            try:
                sec_params = {'orgCode': basic_params.get('parentOrgCode')}
                response = http_execute(get_project_api_uri('operations', 'mge_org_info') + f'''/ORG''', 'GET', token, sec_params)
                if response and len(response) > 0:
                    sec = response.get('grouping')
            except UpstreamError:
                raise
            except Exception as e:
                logger.error('Application event')
            branch_list.append({'orgCode': basic_params.get('parentOrgCode'), 'orgName': basic_params.get('parentOrgName'), 'grouping': sec})
            for scorecard_item in balanced_scorecard_list:
                indicator_params = {'parentOrgCode': basic_params.get('parentOrgCode'), 'year': scorecard_item.get('card_year'), 'balancedScorecardEvaluation': scorecard_item.get('balancedScorecardEvaluation'), 'balancedScorecardRankingN': scorecard_item.get('balancedScorecardRankingN'), 'grouping': scorecard_item.get('sec')}
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_performance') + f'''/{branch_path}''', 'GET', token, indicator_params)
                if response and len(response) > 0:
                    show_info_list = show_info_list + response
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')}, \n                            评价日期:{res.get('year')},平衡计分卡评价:{res.get('balancedScorecardEvaluation')}:平衡计分卡排名 {res.get('balancedScorecardRanking')}, 分组:{res.get('grouping')}, 成立时间:{res.get('setupDate')}, \n                            机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
                        branch_list.append({'orgCode': res.get('orgCode'), 'orgName': res.get('orgName'), 'grouping': res.get('grouping')})
        else:
            for scorecard_item in balanced_scorecard_list:
                params = {'orgCode': basic_params.get('orgCode'), 'year': scorecard_item.get('card_year'), 'balancedScorecardEvaluation': scorecard_item.get('balancedScorecardEvaluation'), 'balancedScorecardRankingN': scorecard_item.get('balancedScorecardRankingN'), 'grouping': scorecard_item.get('sec')}
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_performance') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    show_info_list = show_info_list + response
                    for res in response:
                        sec = res.get('grouping')
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')}, \n                                评价日期:{res.get('year')},平衡计分卡评价:{res.get('balancedScorecardEvaluation')}:平衡计分卡排名 {res.get('balancedScorecardRanking')}, 分组:{res.get('grouping')}, 成立时间:{res.get('setupDate')}, \n                                机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
            branch_list.append({'orgCode': basic_params.get('orgCode'), 'orgName': basic_params.get('orgName'), 'grouping': sec})
        result['function_response'] = str(answer)
        if not all_company_and_bus_flag:
            df = pandas.DataFrame(branch_list)
            branch_list = df.drop_duplicates().to_dict(orient='records')
            if company_scope:
                result['card_id'] = 'OPRMGT1002'
            elif scope:
                result['card_id'] = 'OPRMGT100201'
            else:
                result['card_id'] = 'OPRMGT100202'
            result['tool_resp'] = {'card': 'balancedScoreCard', 'showInfoList': show_info_list, 'branchList': branch_list}
        return result
    financial_list = ['主营收入', '考核利润', '直接代买收入', '代销产品收入']
    if indicator_name in financial_list:
        result['function_response'] = []
        show_info_list = []
        branch_list = []
        answer = []
        params = {}
        if financial_info:
            mainIncome_info = financial_info.get('mainIncome_info', None)
            assessmentProfit_info = financial_info.get('assessmentProfit_info', None)
            directCommission_info = financial_info.get('directCommission_info', None)
            distributionIncome_info = financial_info.get('distributionIncome_info', None)
            if '主营收入' in indicator_name and mainIncome_info:
                params['mainIncome'] = mainIncome_info.get('mainIncome', None)
                params['mainIncomeSysRankN'] = mainIncome_info.get('mainIncomeSysRankN', None)
                params['mainIncomeGroupRankN'] = mainIncome_info.get('mainIncomeGroupRankN', None)
            if '考核利润' in indicator_name and assessmentProfit_info:
                params['assessmentProfit'] = assessmentProfit_info.get('assessmentProfit', None)
                params['assessmentProfitSysRankN'] = assessmentProfit_info.get('assessmentProfitSysRankN', None)
                params['assessmentProfitGroupRankN'] = assessmentProfit_info.get('assessmentProfitGroupRankN', None)
            if '直接代买收入' in indicator_name and directCommission_info:
                params['directCommission'] = directCommission_info.get('directCommission', None)
                params['directCommissionSysRankN'] = directCommission_info.get('directCommissionSysRankN', None)
                params['directCommissionGroupRankN'] = directCommission_info.get('directCommissionGroupRankN', None)
            if '代销产品收入' in indicator_name and distributionIncome_info:
                params['distributionIncome'] = distributionIncome_info.get('distributionIncome', None)
                params['distributionIncomeSysRankN'] = distributionIncome_info.get('distributionIncomeSysRankN', None)
                params['distributionIncomeGroupRankN'] = distributionIncome_info.get('distributionIncomeGroupRankN', None)
        sec = None
        if all_company_and_bus_flag:
            for year_item in year:
                params['year'] = year_item
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_financial') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                年度:{res.get('year')}, 分组:{res.get('grouping')}, 主营收入:{res.get('mainIncome')},主营收入系统排名:{res.get('mainIncomeSysRank')},主营收入系统占比:{res.get('mainIncomeSysRatio')},主营收入同组排名:{res.get('mainIncomeGroupRank')},主营收入同组占比:{res.get('mainIncomeGroupRatio')},\n                                考核利润:{res.get('assessmentProfit')},考核利润系统排名:{res.get('assessmentProfitSysRank')},考核利润系统占比:{res.get('assessmentProfitSysRatio')},考核利润同组排名:{res.get('assessmentProfitGroupRank')},考核利润同组占比:{res.get('assessmentProfitGroupRatio')},\n                                直接代买收入:{res.get('directCommission')},直接代买收入系统排名:{res.get('directCommissionSysRank')},直接代买收入系统占比:{res.get('directCommissionSysRatio')},直接代买收入同组排名:{res.get('directCommissionGroupRank')},直接代买收入同组占比:{res.get('directCommissionGroupRatio')},\n                                代销产品收入:{res.get('distributionIncome')},代销产品收入系统排名:{res.get('distributionIncomeSysRank')},代销产品收入系统占比:{res.get('distributionIncomeSysRatio')},代销产品收入同组排名:{res.get('distributionIncomeGroupRank')},代销产品收入同组占比:{res.get('distributionIncomeGroupRatio')},\n                                机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
        elif basic_params.get('parentOrgCode'):
            try:
                sec_params = {'orgCode': basic_params.get('parentOrgCode')}
                response = http_execute(get_project_api_uri('operations', 'mge_org_info') + f'''/ORG''', 'GET', token, sec_params)
                if response and len(response) > 0:
                    sec = response.get('grouping')
            except UpstreamError:
                raise
            except Exception as e:
                logger.error('Application event')
            branch_list.append({'orgCode': basic_params.get('parentOrgCode'), 'orgName': basic_params.get('parentOrgName'), 'grouping': sec})
            for year_item in year:
                params['year'] = year_item
                params['parentOrgCode'] = basic_params.get('parentOrgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_financial') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    show_info_list = show_info_list + response
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                年度:{res.get('year')}, 分组:{res.get('grouping')}, 主营收入:{res.get('mainIncome')},主营收入系统排名:{res.get('mainIncomeSysRank')},主营收入系统占比:{res.get('mainIncomeSysRatio')},主营收入同组排名:{res.get('mainIncomeGroupRank')},主营收入同组占比:{res.get('mainIncomeGroupRatio')},\n                                考核利润:{res.get('assessmentProfit')},考核利润系统排名:{res.get('assessmentProfitSysRank')},考核利润系统占比:{res.get('assessmentProfitSysRatio')},考核利润同组排名:{res.get('assessmentProfitGroupRank')},考核利润同组占比:{res.get('assessmentProfitGroupRatio')},\n                                直接代买收入:{res.get('directCommission')},直接代买收入系统排名:{res.get('directCommissionSysRank')},直接代买收入系统占比:{res.get('directCommissionSysRatio')},直接代买收入同组排名:{res.get('directCommissionGroupRank')},直接代买收入同组占比:{res.get('directCommissionGroupRatio')},\n                                代销产品收入:{res.get('distributionIncome')},代销产品收入系统排名:{res.get('distributionIncomeSysRank')},代销产品收入系统占比:{res.get('distributionIncomeSysRatio')},代销产品收入同组排名:{res.get('distributionIncomeGroupRank')},代销产品收入同组占比:{res.get('distributionIncomeGroupRatio')},\n                                机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
                        branch_list.append({'orgCode': res.get('orgCode'), 'orgName': res.get('orgName'), 'grouping': res.get('grouping')})
        else:
            for year_item in year:
                params['year'] = year_item
                params['orgCode'] = basic_params.get('orgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_financial') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    show_info_list = show_info_list + response
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                    年度:{res.get('year')}, 分组:{res.get('grouping')}, 主营收入:{res.get('mainIncome')},主营收入系统排名:{res.get('mainIncomeSysRank')},主营收入系统占比:{res.get('mainIncomeSysRatio')},主营收入同组排名:{res.get('mainIncomeGroupRank')},主营收入同组占比:{res.get('mainIncomeGroupRatio')},\n                                    考核利润:{res.get('assessmentProfit')},考核利润系统排名:{res.get('assessmentProfitSysRank')},考核利润系统占比:{res.get('assessmentProfitSysRatio')},考核利润同组排名:{res.get('assessmentProfitGroupRank')},考核利润同组占比:{res.get('assessmentProfitGroupRatio')},\n                                    直接代买收入:{res.get('directCommission')},直接代买收入系统排名:{res.get('directCommissionSysRank')},直接代买收入系统占比:{res.get('directCommissionSysRatio')},直接代买收入同组排名:{res.get('directCommissionGroupRank')},直接代买收入同组占比:{res.get('directCommissionGroupRatio')},\n                                    代销产品收入:{res.get('distributionIncome')},代销产品收入系统排名:{res.get('distributionIncomeSysRank')},代销产品收入系统占比:{res.get('distributionIncomeSysRatio')},代销产品收入同组排名:{res.get('distributionIncomeGroupRank')},代销产品收入同组占比:{res.get('distributionIncomeGroupRatio')},\n                                    机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
                        branch_list.append({'orgCode': res.get('orgCode'), 'orgName': res.get('orgName'), 'grouping': res.get('grouping')})
        result['function_response'] = str(answer)
        if not all_company_and_bus_flag:
            df = pandas.DataFrame(branch_list)
            branch_list = df.drop_duplicates().to_dict(orient='records')
            if '考核利润' == indicator_name and len(show_info_list) > 0:
                if company_scope:
                    result['card_id'] = 'OPRMGT1003'
                elif scope:
                    result['card_id'] = 'OPRMGT100301'
                else:
                    result['card_id'] = 'OPRMGT100302'
                result['tool_resp'] = {'card': 'assessmentProfitCard', 'showInfoList': show_info_list, 'branchList': branch_list}
            if '主营收入' == indicator_name and len(show_info_list) > 0:
                if company_scope:
                    result['card_id'] = 'OPRMGT1004'
                elif scope:
                    result['card_id'] = 'OPRMGT100401'
                else:
                    result['card_id'] = 'OPRMGT100402'
                result['tool_resp'] = {'card': 'mainIncomeCard', 'showInfoList': show_info_list, 'branchList': branch_list}
            if '直接代买收入' == indicator_name and len(show_info_list) > 0:
                if company_scope:
                    result['card_id'] = 'OPRMGT1005'
                elif scope:
                    result['card_id'] = 'OPRMGT100501'
                else:
                    result['card_id'] = 'OPRMGT100502'
                result['tool_resp'] = {'card': 'directCommissionCard', 'showInfoList': show_info_list, 'branchList': branch_list}
            if '代销产品收入' == indicator_name and len(show_info_list) > 0:
                if company_scope:
                    result['card_id'] = 'OPRMGT1006'
                elif scope:
                    result['card_id'] = 'OPRMGT100601'
                else:
                    result['card_id'] = 'OPRMGT100602'
                result['tool_resp'] = {'card': 'distributionIncomeCard', 'showInfoList': show_info_list, 'branchList': branch_list}
        return result
    customer_info_list = ['新开客户数', '新开有效户', '总客户数', '总有效户']
    if indicator_name in customer_info_list:
        result['function_response'] = []
        show_info_list = []
        branch_list = []
        answer = []
        params = {}
        if customer_size_info:
            newCustomers_info = customer_size_info.get('newCustomers_info', None)
            newValidCustomers_info = customer_size_info.get('newValidCustomers_info', None)
            totalCustomers_info = customer_size_info.get('totalCustomers_info', None)
            totalValidCustomers_info = customer_size_info.get('totalValidCustomers_info', None)
            if '新开客户数' in indicator_name and newCustomers_info:
                params['newCustomers'] = newCustomers_info.get('newCustomers', None)
                params['newCustomersSysRankN'] = newCustomers_info.get('newCustomersSysRankN', None)
                params['newCustomersGroupRankN'] = newCustomers_info.get('newCustomersGroupRankN', None)
            if '新开有效户' in indicator_name and newValidCustomers_info:
                params['newValidCustomers'] = newValidCustomers_info.get('newValidCustomers', None)
                params['newValidSysRankN'] = newValidCustomers_info.get('newValidSysRankN', None)
                params['newValidGroupRankN'] = newValidCustomers_info.get('newValidGroupRankN', None)
            if '总客户数' in indicator_name and totalCustomers_info:
                params['totalCustomers'] = totalCustomers_info.get('totalCustomers', None)
                params['totalCustomersSysRankN'] = totalCustomers_info.get('totalCustomersSysRankN', None)
                params['totalCustomersGroupRankN'] = totalCustomers_info.get('totalCustomersGroupRankN', None)
            if '总有效户' in indicator_name and totalValidCustomers_info:
                params['totalValidCustomers'] = totalValidCustomers_info.get('totalValidCustomers', None)
                params['totalValidSysRankN'] = totalValidCustomers_info.get('totalValidSysRankN', None)
                params['totalValidGroupRankN'] = totalValidCustomers_info.get('totalValidGroupRankN', None)
        sec = None
        if all_company_and_bus_flag:
            for year_item in year:
                params['year'] = year_item
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_customer_size') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                    年度:{res.get('year')},分组:{res.get('grouping')}；新开客户数:{res.get('newCustomers')},新开客户数系统排名:{res.get('newCustomersSysRank')},新开客户数系统占比:{res.get('newCustomersSysRatio')},\n                                    新开客户数同组排名:{res.get('newCustomersGroupRank')},新开客户数同组占比:{res.get('newCustomersGroupRatio')}；新开有效户:{res.get('newValidCustomers')},\n                                    新开有效户系统排名:{res.get('newValidSysRank')},新开有效户系统占比:{res.get('newValidSysRatio')},新开有效户同组排名:{res.get('newValidGroupRank')},\n                                    新开有效户同组占比:{res.get('newValidGroupRatio')}；总客户数:{res.get('totalCustomers')},总客户数系统排名:{res.get('totalCustomersSysRank')},总客户数系统占比:{res.get('totalCustomersSysRatio')},\n                                    总客户数同组排名:{res.get('totalCustomersGroupRank')},总客户数同组占比:{res.get('totalCustomersGroupRatio')}；总有效户:{res.get('totalValidCustomers')},总有效户系统排名:{res.get('totalValidSysRank')},\n                                    总有效户系统占比:{res.get('totalValidSysRatio')},总有效户同组排名:{res.get('totalValidGroupRank')},总有效户同组占比:{res.get('totalValidGroupRatio')},\n                                    机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
        elif basic_params.get('parentOrgCode'):
            try:
                sec_params = {'orgCode': basic_params.get('parentOrgCode')}
                response = http_execute(get_project_api_uri('operations', 'mge_org_info') + f'''/ORG''', 'GET', token, sec_params)
                if response and len(response) > 0:
                    sec = response.get('grouping')
            except UpstreamError:
                raise
            except Exception as e:
                logger.error('Application event')
            branch_list.append({'orgCode': basic_params.get('parentOrgCode'), 'orgName': basic_params.get('parentOrgName'), 'grouping': sec})
            for year_item in year:
                params['year'] = year_item
                params['parentOrgCode'] = basic_params.get('parentOrgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_customer_size') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    if '新开有效户' == indicator_name or '总有效户' == indicator_name:
                        show_info_list = show_info_list + response
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                    年度:{res.get('year')},分组:{res.get('grouping')}；新开客户数:{res.get('newCustomers')},新开客户数系统排名:{res.get('newCustomersSysRank')},新开客户数系统占比:{res.get('newCustomersSysRatio')},\n                                    新开客户数同组排名:{res.get('newCustomersGroupRank')},新开客户数同组占比:{res.get('newCustomersGroupRatio')}；新开有效户:{res.get('newValidCustomers')},\n                                    新开有效户系统排名:{res.get('newValidSysRank')},新开有效户系统占比:{res.get('newValidSysRatio')},新开有效户同组排名:{res.get('newValidGroupRank')},\n                                    新开有效户同组占比:{res.get('newValidGroupRatio')}；总客户数:{res.get('totalCustomers')},总客户数系统排名:{res.get('totalCustomersSysRank')},总客户数系统占比:{res.get('totalCustomersSysRatio')},\n                                    总客户数同组排名:{res.get('totalCustomersGroupRank')},总客户数同组占比:{res.get('totalCustomersGroupRatio')}；总有效户:{res.get('totalValidCustomers')},总有效户系统排名:{res.get('totalValidSysRank')},\n                                    总有效户系统占比:{res.get('totalValidSysRatio')},总有效户同组排名:{res.get('totalValidGroupRank')},总有效户同组占比:{res.get('totalValidGroupRatio')},\n                                    机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
                        branch_list.append({'orgCode': res.get('orgCode'), 'orgName': res.get('orgName'), 'grouping': res.get('grouping')})
        else:
            for year_item in year:
                params['year'] = year_item
                params['orgCode'] = basic_params.get('orgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_customer_size') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                        年度:{res.get('year')},分组:{res.get('grouping')}；新开客户数:{res.get('newCustomers')},新开客户数系统排名:{res.get('newCustomersSysRank')},新开客户数系统占比:{res.get('newCustomersSysRatio')},\n                                        新开客户数同组排名:{res.get('newCustomersGroupRank')},新开客户数同组占比:{res.get('newCustomersGroupRatio')}；新开有效户:{res.get('newValidCustomers')},\n                                        新开有效户系统排名:{res.get('newValidSysRank')},新开有效户系统占比:{res.get('newValidSysRatio')},新开有效户同组排名:{res.get('newValidGroupRank')},\n                                        新开有效户同组占比:{res.get('newValidGroupRatio')}；总客户数:{res.get('totalCustomers')},总客户数系统排名:{res.get('totalCustomersSysRank')},总客户数系统占比:{res.get('totalCustomersSysRatio')},\n                                        总客户数同组排名:{res.get('totalCustomersGroupRank')},总客户数同组占比:{res.get('totalCustomersGroupRatio')}；总有效户:{res.get('totalValidCustomers')},总有效户系统排名:{res.get('totalValidSysRank')},\n                                        总有效户系统占比:{res.get('totalValidSysRatio')},总有效户同组排名:{res.get('totalValidGroupRank')},总有效户同组占比:{res.get('totalValidGroupRatio')},\n                                        机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
                        branch_list.append({'orgCode': res.get('orgCode'), 'orgName': res.get('orgName'), 'grouping': res.get('grouping')})
                    if '新开有效户' == indicator_name or '总有效户' == indicator_name:
                        show_info_list = show_info_list + response
        result['function_response'] = str(answer)
        if not all_company_and_bus_flag:
            df = pandas.DataFrame(branch_list)
            branch_list = df.drop_duplicates().to_dict(orient='records')
            if '新开有效户' == indicator_name and len(show_info_list) > 0:
                if company_scope:
                    result['card_id'] = 'OPRMGT1007'
                elif scope:
                    result['card_id'] = 'OPRMGT100701'
                else:
                    result['card_id'] = 'OPRMGT100702'
                result['tool_resp'] = {'card': 'newValidCustomersCard', 'showInfoList': show_info_list, 'branchList': branch_list}
            elif '总有效户' == indicator_name and len(show_info_list) > 0:
                if company_scope:
                    result['card_id'] = 'OPRMGT1008'
                elif scope:
                    result['card_id'] = 'OPRMGT100801'
                else:
                    result['card_id'] = 'OPRMGT100802'
                result['tool_resp'] = {'card': 'totalValidCustomersCard', 'showInfoList': show_info_list, 'branchList': branch_list}
        return result
    transaction_info_list = ['股基交易量', 'A股交易量', 'A股交易量当地市场份额']
    if indicator_name in transaction_info_list:
        result['function_response'] = []
        answer = []
        params = {}
        if transaction_info:
            fundStockVol_info = transaction_info.get('fundStockVol_info', None)
            ashareVol_info = transaction_info.get('ashareVol_info', None)
            if fundStockVol_info:
                params['fundStockVol'] = fundStockVol_info.get('fundStockVol', None)
                params['fundStockSysRankN'] = fundStockVol_info.get('fundStockSysRankN', None)
                params['fundStockGroupRankN'] = fundStockVol_info.get('fundStockGroupRankN', None)
            if ashareVol_info:
                params['ashareVol'] = ashareVol_info.get('ashareVol', None)
                params['ashareSysRankN'] = ashareVol_info.get('ashareSysRankN', None)
                params['ashareGroupRankN'] = ashareVol_info.get('ashareGroupRankN', None)
                params['ashareMktShareN'] = ashareVol_info.get('ashareMktShare', None)
                params['ashareShRankN'] = ashareVol_info.get('ashareShRankN', None)
                params['ashareSzRankN'] = ashareVol_info.get('ashareSzRankN', None)
        if basic_params.get('parentOrgCode') or all_company_and_bus_flag:
            for year_item in year:
                params['year'] = year_item
                if basic_params.get('parentOrgCode'):
                    params['parentOrgCode'] = basic_params.get('parentOrgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_transaction') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                年度:{res.get('year')},分组:{res.get('grouping')},股基交易量:{res.get('fundStockVol')},股基交易量系统排名:{res.get('fundStockSysRank')},\n                                股基交易量系统占比:{res.get('fundStockSysRatio')},股基交易量同组排名:{res.get('fundStockGroupRank')},股基交易量同组占比:{res.get('fundStockGroupRatio')},\n                                A股交易量:{res.get('ashareVol')},A股交易量系统排名:{res.get('ashareSysRank')},A股交易量系统占比:{res.get('ashareSysRatio')},A股交易量同组排名:{res.get('ashareGroupRank')},\n                                A股交易量同组占比:{res.get('ashareGroupRatio')},A股交易量当地市场份额:{res.get('ashareMktShare')},A股交易量沪市排名:{res.get('ashareShRank')},\n                                A股交易量深市排名:{res.get('ashareSzRank')},机构负责人:{res.get('orgLeader')},机构负责人ID:{res.get('leaderStaffId')}\n                                ''')
        else:
            for year_item in year:
                params['year'] = year_item
                params['orgCode'] = basic_params.get('orgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_transaction') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                    年度:{res.get('year')},分组:{res.get('grouping')},股基交易量:{res.get('fundStockVol')},股基交易量系统排名:{res.get('fundStockSysRank')},\n                                    股基交易量系统占比:{res.get('fundStockSysRatio')},股基交易量同组排名:{res.get('fundStockGroupRank')},股基交易量同组占比:{res.get('fundStockGroupRatio')},\n                                    A股交易量:{res.get('ashareVol')},A股交易量系统排名:{res.get('ashareSysRank')},A股交易量系统占比:{res.get('ashareSysRatio')},A股交易量同组排名:{res.get('ashareGroupRank')},\n                                    A股交易量同组占比:{res.get('ashareGroupRatio')},A股交易量当地市场份额:{res.get('ashareMktShare')},A股交易量沪市排名:{res.get('ashareShRank')},\n                                    A股交易量深市排名:{res.get('ashareSzRank')},机构负责人:{res.get('orgLeader')},机构负责人ID:{res.get('leaderStaffId')}\n                                    ''')
        result['function_response'] = str(answer)
        return result
    asset_info_list = ['新开交易型资产', '总交易型资产']
    if indicator_name in asset_info_list:
        result['function_response'] = []
        show_info_list = []
        branch_list = []
        answer = []
        params = {}
        if asset_info:
            newTradingAsset_info = asset_info.get('newTradingAsset_info', None)
            totalTradingAsset_info = asset_info.get('totalTradingAsset_info', None)
            if newTradingAsset_info:
                params['newTradingAsset'] = newTradingAsset_info.get('newTradingAsset', None)
                params['newAssetSysRankN'] = newTradingAsset_info.get('newAssetSysRankN', None)
                params['newAssetGroupRankN'] = newTradingAsset_info.get('newAssetGroupRankN', None)
            if totalTradingAsset_info:
                params['totalTradingAsset'] = totalTradingAsset_info.get('totalTradingAsset', None)
                params['totalAssetSysRankN'] = totalTradingAsset_info.get('totalAssetSysRankN', None)
                params['totalAssetGroupRankN'] = totalTradingAsset_info.get('totalAssetGroupRankN', None)
        sec = None
        if all_company_and_bus_flag:
            for year_item in year:
                params['year'] = year_item
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_asset') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                    年度:{res.get('year')},分组:{res.get('grouping')},新开交易型资产:{res.get('newTradingAsset')},新开交易型资产系统排名:{res.get('newAssetSysRank')},\n                                    新开交易型资产系统占比:{res.get('newAssetSysRatio')},新开交易型资产同组排名:{res.get('newAssetGroupRank')},新开交易型资产同组占比:{res.get('newAssetGroupRatio')},\n                                    总交易型资产:{res.get('totalTradingAsset')},总交易型资产系统排名:{res.get('totalAssetSysRank')},总交易型资产系统占比:{res.get('totalAssetSysRatio')},\n                                    总交易型资产同组排名:{res.get('totalAssetGroupRank')},总交易型资产同组占比:{res.get('totalAssetGroupRatio')},机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}\n                                    ''')
        elif basic_params.get('parentOrgCode'):
            try:
                sec_params = {'orgCode': basic_params.get('parentOrgCode')}
                response = http_execute(get_project_api_uri('operations', 'mge_org_info') + f'''/ORG''', 'GET', token, sec_params)
                if response and len(response) > 0:
                    sec = response.get('grouping')
            except UpstreamError:
                raise
            except Exception as e:
                logger.error('Application event')
            branch_list.append({'orgCode': basic_params.get('parentOrgCode'), 'orgName': basic_params.get('parentOrgName'), 'grouping': sec})
            for year_item in year:
                params['year'] = year_item
                params['parentOrgCode'] = basic_params.get('parentOrgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_asset') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                    年度:{res.get('year')},分组:{res.get('grouping')},新开交易型资产:{res.get('newTradingAsset')},新开交易型资产系统排名:{res.get('newAssetSysRank')},\n                                    新开交易型资产系统占比:{res.get('newAssetSysRatio')},新开交易型资产同组排名:{res.get('newAssetGroupRank')},新开交易型资产同组占比:{res.get('newAssetGroupRatio')},\n                                    总交易型资产:{res.get('totalTradingAsset')},总交易型资产系统排名:{res.get('totalAssetSysRank')},总交易型资产系统占比:{res.get('totalAssetSysRatio')},\n                                    总交易型资产同组排名:{res.get('totalAssetGroupRank')},总交易型资产同组占比:{res.get('totalAssetGroupRatio')},机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}\n                                    ''')
                        branch_list.append({'orgCode': res.get('orgCode'), 'orgName': res.get('orgName'), 'grouping': res.get('grouping')})
                    if '新开交易型资产' == indicator_name or '总交易型资产' == indicator_name:
                        show_info_list = show_info_list + response
        else:
            for year_item in year:
                params['year'] = year_item
                params['orgCode'] = basic_params.get('orgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_asset') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                        年度:{res.get('year')},分组:{res.get('grouping')},新开交易型资产:{res.get('newTradingAsset')},新开交易型资产系统排名:{res.get('newAssetSysRank')},\n                                        新开交易型资产系统占比:{res.get('newAssetSysRatio')},新开交易型资产同组排名:{res.get('newAssetGroupRank')},新开交易型资产同组占比:{res.get('newAssetGroupRatio')},\n                                        总交易型资产:{res.get('totalTradingAsset')},总交易型资产系统排名:{res.get('totalAssetSysRank')},总交易型资产系统占比:{res.get('totalAssetSysRatio')},\n                                        总交易型资产同组排名:{res.get('totalAssetGroupRank')},总交易型资产同组占比:{res.get('totalAssetGroupRatio')},机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}\n                                        ''')
                        branch_list.append({'orgCode': res.get('orgCode'), 'orgName': res.get('orgName'), 'grouping': res.get('grouping')})
                    if '新开交易型资产' == indicator_name or '总交易型资产' == indicator_name:
                        show_info_list = show_info_list + response
        if not all_company_and_bus_flag:
            df = pandas.DataFrame(branch_list)
            branch_list = df.drop_duplicates().to_dict(orient='records')
        result['function_response'] = str(answer)
        if '新开交易型资产' == indicator_name and len(show_info_list) > 0:
            if company_scope:
                result['card_id'] = 'OPRMGT1010'
            elif scope:
                result['card_id'] = 'OPRMGT101001'
            else:
                result['card_id'] = 'OPRMGT101002'
            result['tool_resp'] = {'card': 'newTradingAssetCard', 'showInfoList': show_info_list, 'branchList': branch_list}
        if '总交易型资产' == indicator_name and len(show_info_list) > 0:
            if company_scope:
                result['card_id'] = 'OPRMGT1011'
            elif scope:
                result['card_id'] = 'OPRMGT101101'
            else:
                result['card_id'] = 'OPRMGT101102'
            result['tool_resp'] = {'card': 'totalTradingAssetCard', 'showInfoList': show_info_list, 'branchList': branch_list}
        return result
    employee_info_list = ['前台员工数']
    if indicator_name in employee_info_list:
        result['function_response'] = []
        show_info_list = []
        branch_list = []
        answer = []
        params = {}
        if employee_info:
            params['staffCnt'] = employee_info.get('staffCnt', None)
            params['sysRankN'] = employee_info.get('sysRankN', None)
            params['groupRankN'] = employee_info.get('groupRankN', None)
        if basic_params.get('parentOrgCode') or all_company_and_bus_flag:
            for year_item in year:
                params['year'] = year_item
                if basic_params.get('parentOrgCode'):
                    params['parentOrgCode'] = basic_params.get('parentOrgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_employee') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                    日期:{res.get('year')},分组:{res.get('grouping')},前台员工数:{res.get('staffCnt')},前台员工数系统排名:{res.get('sysRank')},\n                                    前台员工数系统占比:{res.get('sysRatio')},前台员工数同组排名:{res.get('groupRank')},前台员工数同组占比:{res.get('groupRatio')},\n                                    机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
        else:
            for year_item in year:
                params['year'] = year_item
                params['orgCode'] = basic_params.get('orgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_employee') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                        日期:{res.get('year')},分组:{res.get('grouping')},前台员工数:{res.get('staffCnt')},前台员工数系统排名:{res.get('sysRank')},\n                                        前台员工数系统占比:{res.get('sysRatio')},前台员工数同组排名:{res.get('groupRank')},前台员工数同组占比:{res.get('groupRatio')},\n                                        机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
        result['function_response'] = str(answer)
        return result
    sales_info_list = ['产品销售额']
    if indicator_name in sales_info_list:
        result['function_response'] = []
        show_info_list = []
        branch_list = []
        answer = []
        params = {}
        if sales_info:
            params['sales'] = sales_info.get('sales', None)
            params['salesSysRankN'] = sales_info.get('salesSysRankN', None)
            params['salesGroupRankN'] = sales_info.get('salesGroupRankN', None)
        if basic_params.get('parentOrgCode') or all_company_and_bus_flag:
            for year_item in year:
                params['year'] = year_item
                if basic_params.get('parentOrgCode'):
                    params['parentOrgCode'] = basic_params.get('parentOrgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_sales') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                    日期:{res.get('year')},分组:{res.get('grouping')},产品销售额:{res.get('sales')}元 ,产品销售额系统排名:{res.get('salesSysRank')},\n                                    产品销售额系统占比:{res.get('salesSysRatio')},产品销售额同组排名:{res.get('salesGroupRank')},产品销售额同组占比:{res.get('salesGroupRatio')},\n                                    机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
        else:
            for year_item in year:
                params['year'] = year_item
                params['orgCode'] = basic_params.get('orgCode')
                response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_sales') + f'''/{branch_path}''', 'GET', token, params)
                if response and len(response) > 0:
                    for res in response:
                        answer.append(f'''机构名称(最新): {res.get('orgName')}, 机构代码: {res.get('orgCode')},上级机构名称:{res.get('parentOrgCode')},上级机构代码:{res.get('parentOrgName')},\n                                        日期:{res.get('year')},分组:{res.get('grouping')},产品销售额:{res.get('sales')}元 ,产品销售额系统排名:{res.get('salesSysRank')},\n                                        产品销售额系统占比:{res.get('salesSysRatio')},产品销售额同组排名:{res.get('salesGroupRank')},产品销售额同组占比:{res.get('salesGroupRatio')},\n                                        机构负责人:{res.get('orgLeader')}, 机构负责人ID:{res.get('leaderStaffId')}''')
        result['function_response'] = str(answer)
        return result
    else:
        return result

def check_restrictive_conditions(indicator_name):
    market_share_index_list = ['直接代买收入市场份额', '代销产品收入市场份额']
    if indicator_name in market_share_index_list:
        function_response = f'''固定回复用户：由于暂未接入该指标的分公司维度数据，所以无法查询指标值。但是直接代买收入市场份额、代销产品收入市场份额两个指标的系统排名、系统占比、同组排名、同组占比与直接代买收入、代销产品收入的相同，您可直接查询以上两个指标即可。'''
        return function_response
    else:
        return None
