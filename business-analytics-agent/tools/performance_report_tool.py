from util.http_util import UpstreamError
from datetime import datetime, timedelta
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from config import get_project_api_uri
from config.prompt import *
from util.http_util import http_execute
from config.logger import logger
last_yaer = datetime.now().strftime('%Y')

@tool('performance_report_tool', args_schema={'type': 'object', 'properties': {'branch_company': {'type': 'object', 'properties': {'company_code': {'type': 'string', 'default': None, 'description': '公司code、机构代码、上级机构代码', 'examples': []}, 'company_name': {'type': 'string', 'default': None, 'description': '分公司名称', 'examples': []}, 'report_date': {'type': 'string', 'default': last_yaer, 'description': '报告日期, 格式: YYYY; 当用户进行区间查询时，用~连接: YYYY~YYYY', 'examples': []}}}}})
def performance_report_tool(config: RunnableConfig, **kwargs):
    """Performance report tool. Use validated tool arguments and return adapter results."""
    token = config.get('configurable').get('agent_extends').get('token')
    result = summary_info(token, kwargs)
    if 'function_response' in result:
        function_response = result['function_response']
        card = {'card_id': 'DEMO_CARD_1003', 'consumer_data_card': result.get('tool_resp')}
        return [[function_response], card]
    else:
        return [result]

def summary_info(token, kwargs):
    branch_company = kwargs.get('branch_company', {})
    company_code = branch_company.get('company_code', None)
    company_name = branch_company.get('company_name', None)
    report_date = branch_company.get('report_date', last_yaer)
    result = {}
    if company_code is None and company_name is None:
        return '未获取到具体的分公司信息，请用户提供明确的分公司名称或代码~'
    try:
        function_response = f'Report request prepared (file generation requires an external report service). Branch: {company_name}, 机构代码:{company_code}。'
        result['tool_resp'] = {'card': 'reportDownCard', 'report_date': report_date, 'branchList': [{'orgCode': company_code, 'orgName': company_name}]}
        result['function_response'] = function_response
        return result
    except UpstreamError:
        raise
    except Exception as e:
        logger.error('Application event')
        return f'未获取到具体的分公司信息，请用户重新提供正确的分公司名称或代码~'
