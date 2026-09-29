from util.http_util import UpstreamError
import pandas
from datetime import datetime
from config.logger import logger
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from config import get_project_api_uri
from util.http_util import http_execute

@tool('branch_company_info_tool', args_schema={'type': 'object', 'properties': {'company_code': {'type': 'string', 'default': None, 'description': '分公司代码'}, 'company_name': {'type': 'string', 'default': None, 'description': '分公司名称', 'examples': []}, 'company_scope': {'type': 'boolean', 'default': False, 'description': '是否只查询分公司。如果查询只分公司,该字段填写True;如果查询营业部该字段填写False; 当business_name参数不为None时，该字段填写False。'}, 'business_code': {'type': 'string', 'default': None, 'description': '营业部代码'}, 'business_name': {'type': 'string', 'default': None, 'description': '营业部名称', 'examples': []}, 'scope': {'type': 'boolean', 'default': False, 'description': '是否查询所有的营业部。如果查询所有的营业部，该字段填写True, 如果查询部分营业部，该字段填写False, 当business_name参数不为None时，该字段填写False。'}, 'screening': {'type': 'boolean', 'default': False, 'description': '是否筛选条件。如果是筛选所有的营业部，该字段填写True。'}, 'info_list': {'type': 'object', 'description': '基本信息', 'properties': {'orgType': {'type': 'string', 'default': None, 'description': '机构性质'}, 'orgTypeCode': {'type': 'string', 'default': None, 'description': '机构性质代码'}, 'setupDate': {'type': 'string', 'default': None, 'description': '成立时间'}, 'grouping': {'type': 'string', 'default': None, 'description': '组别、SEC分组'}, 'orgLeader': {'type': 'string', 'default': None, 'description': '机构负责人'}, 'leaderStaffId': {'type': 'string', 'default': None, 'description': '机构负责人ID'}}}}, 'required': ['company_code', 'company_name', 'company_scope', 'business_code', 'business_name', 'scope', 'info_list']})
def branch_company_info_tool(config: RunnableConfig, **kwargs):
    """Branch company info tool. Use validated tool arguments and return adapter results."""
    token = config.get('configurable').get('agent_extends').get('token')
    result = summary_info(token, kwargs)
    if 'function_response' in result:
        function_response = result['function_response']
        card = {'card_id': 'OPRMGT1001', 'consumer_data_card': result.get('tool_resp')}
        return [[function_response], card]
    else:
        return [result]

def summary_info(token, kwargs):
    company_scope = kwargs.get('company_scope', False)
    company_code = kwargs.get('company_code', None)
    company_name = kwargs.get('company_name', None)
    business_code = kwargs.get('business_code', None)
    business_name = kwargs.get('business_name', None)
    scope = kwargs.get('scope', None)
    screening = kwargs.get('screening', None)
    info_list = kwargs.get('info_list', None)
    branch_path = 'ORG'
    all_company_and_bus_flag = False
    if (company_code and business_code) is None and company_scope and scope:
        return f'''未查询到分公司或营业部ID和名称，请重新提供明确的分公司或营业部名称'''
    params = {}
    if scope:
        branch_path = 'STORE'
        if company_code is None and company_name is None:
            all_company_and_bus_flag = True
        else:
            params['parentOrgCode'] = company_code
            params['parentOrgName'] = company_name
    elif business_name or business_code:
        branch_path = 'STORE'
        params['orgCode'] = business_code
        params['orgName'] = business_name
    elif company_name or company_code:
        params['orgCode'] = company_code
        params['orgName'] = company_name
    else:
        all_company_and_bus_flag = True
    if info_list:
        for key, value in info_list.items():
            if value:
                params[key] = value
    result = {}
    answer = []
    branch_list = []
    show_info_list = []
    sec = None
    if all_company_and_bus_flag or screening:
        response = http_execute(get_project_api_uri('operations', 'mge_org_list') + f'''/{branch_path}''', 'GET', token, params)
        if response is None or response == '' or len(response) == 0:
            return f'''复述给用户：未查询到机构的详细信息，您可以换一个其他的名称继续查询～'''
        for res in response:
            answer.append(f'''机构代码:{res.get('orgCode')},机构名称(最新):{res.get('orgName')},上级机构代码:{res.get('parentOrgCode')},\n                    上级机构名称:{res.get('parentOrgName')},机构性质:{res.get('orgType')},机构性质代码:{res.get('orgTypeCode')},\n                    成立时间:{res.get('setupDate')},营业状态:{res.get('isOperating')},绩效组别:{res.get('grouping')},机构负责人:{res.get('orgLeader')},\n                    机构负责人ID:{res.get('leaderStaffId')}''')
    elif params.get('parentOrgCode'):
        try:
            sec_params = {'orgCode': params.get('parentOrgCode')}
            response = http_execute(get_project_api_uri('operations', 'mge_org_info') + f'''/ORG''', 'GET', token, sec_params)
            if response and len(response) > 0:
                sec = response.get('grouping')
        except UpstreamError:
            raise
        except Exception:
            logger.error('Application event')
        branch_list.append({'orgCode': params.get('parentOrgCode'), 'orgName': params.get('parentOrgName'), 'grouping': sec})
        try:
            response = http_execute(get_project_api_uri('operations', 'mge_org_list') + f'''/{branch_path}''', 'GET', token, params)
            if response is None or response == '' or len(response) == 0:
                return f'''复述给用户：未查询到{params.get('parentOrgName')}(ID: {params.get('parentOrgCode')})的详细信息，您可以换一个其他的名称继续查询～'''
            for res in response:
                answer.append(f'''机构代码:{res.get('orgCode')},机构名称(最新):{res.get('orgName')},上级机构代码:{res.get('parentOrgCode')},\n                    上级机构名称:{res.get('parentOrgName')},机构性质:{res.get('orgType')},机构性质代码:{res.get('orgTypeCode')},\n                    成立时间:{res.get('setupDate')},营业状态:{res.get('isOperating')},绩效组别:{res.get('grouping')},机构负责人:{res.get('orgLeader')},\n                    机构负责人ID:{res.get('leaderStaffId')}''')
            params = {'parentOrgCode': params.get('parentOrgCode'), 'grouping': params.get('grouping'), 'year': datetime.now().year}
            response = http_execute(get_project_api_uri('operations', 'mge_quota_filter_performance') + f'''/{branch_path}''', 'GET', token, params)
            if response and len(response) > 0:
                show_info_list = show_info_list + response
                for res in response:
                    branch_list.append({'orgCode': res.get('orgCode'), 'orgName': res.get('orgName'), 'grouping': res.get('grouping')})
        except UpstreamError:
            raise
        except Exception:
            logger.error('Application event')
    else:
        res = http_execute(get_project_api_uri('operations', 'mge_org_info') + f'''/{branch_path}''', 'GET', token, params)
        if res is None or len(res) == 0 or res == '':
            return f'''复述给用户：未查询到{params.get('orgName')}(ID: {params.get('orgCode')})的详细信息，您可以换一个其他的名称继续查询～'''
        else:
            answer.append(f'''机构代码:{res.get('orgCode')},机构名称(最新):{res.get('orgName')},上级机构代码:{res.get('parentOrgCode')},\n                    上级机构名称:{res.get('parentOrgName')},机构性质:{res.get('orgType')},机构性质代码:{res.get('orgTypeCode')},\n                    成立时间:{res.get('setupDate')},营业状态:{res.get('isOperating')},绩效组别:{res.get('grouping')},机构负责人:{res.get('orgLeader')},\n                    机构负责人ID:{res.get('leaderStaffId')}''')
    result['function_response'] = str(answer)
    if not all_company_and_bus_flag:
        if params.get('parentOrgCode') and len(answer) > 0 and branch_list:
            df = pandas.DataFrame(branch_list)
            branch_list = df.drop_duplicates().to_dict(orient='records')
            result['tool_resp'] = {'card': 'basicInfoCard', 'showInfoList': show_info_list, 'branchList': branch_list}
    return result
