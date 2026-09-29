import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from config.prompt import get_pre_agent_prompt
from config import get_project_client_config, get_project_api_uri
from util.http_util import http_execute_async
from config.logger import logger as log
from util.mysql_util import insert_agent_log
from model.ChatBody import ChatBody
from model.exceptions import EntityConflictError, TokenInvalidError
import json, re
_pre_model_cache: dict[str, ChatOpenAI] = {}
_pre_agent_cache: dict[str, Any] = {}

async def query_single_entity(entity: str) -> None | dict[str, str | None] | dict[str, str] | dict[str, str | list[Any]]:
    try:
        url = get_project_api_uri('wealth', 'search_entity')
        header = {}
        payload = {'name': entity}
        response = await http_execute_async(url, 'POST', payload, header)
        if response['code'] == 0 or response['code'] == '0':
            content_list = response.get('content') or []
            if len(content_list) == 0:
                return {'entity': entity, 'status': 'not_found', 'data': None}
            elif len(content_list) == 1:
                entity_type = content_list[0].get('type', '')
                if entity_type == '产品':
                    prod_code_qry = content_list[0].get('prod_code', '')
                    if prod_code_qry:
                        return {'entity': entity, 'status': 'success', 'data': f'{entity}(基金代码：{prod_code_qry})'}
                    else:
                        return {'entity': entity, 'status': 'no_code', 'data': entity}
                elif entity_type == '公司':
                    company_id = content_list[0].get('prod_code', '')
                    if company_id:
                        return {'entity': entity, 'status': 'success', 'data': f'{entity} 是家基金公司,基金公司ID为{company_id}'}
                    else:
                        return {'entity': entity, 'status': 'no_code', 'data': entity}
            else:
                entity_options = []
                for item in content_list:
                    if item.get('type') == '产品':
                        fund_dict = {'基金简称': item.get('short_name_exchange', ''), '基金代码': item.get('prod_code', ''), '基金全称': item.get('full_name', '')}
                        entity_options.append(fund_dict)
                    elif item.get('type') == '公司':
                        company_dict = {'基金公司全称': item.get('full_name', ''), '基金公司ID': item.get('prod_code', '')}
                        entity_options.append(company_dict)
                return {'entity': entity, 'status': 'multiple', 'data': entity_options}
        else:
            return {'entity': entity, 'status': 'error', 'data': None}
    except TokenInvalidError:
        raise
    except Exception as e:
        log.error('Application event')
        return {'entity': entity, 'status': 'exception', 'data': None}

async def query_entities_with_concurrency(entities: List[str], max_concurrent: int=3) -> tuple[List[str], Optional[List[Dict]]]:
    if not entities:
        return ([], None)
    semaphore = asyncio.Semaphore(max_concurrent)

    async def query_with_semaphore(entity: str):
        async with semaphore:
            return await query_single_entity(entity)
    tasks = [query_with_semaphore(entity) for entity in entities]
    results = await asyncio.gather(*tasks)
    result_list = []
    multiple_results_list = []
    for result in results:
        if result['status'] == 'multiple':
            multiple_results_list.append(result)
        elif result['status'] == 'success':
            result_list.append(result['data'])
        elif result['status'] in ['not_found', 'no_code']:
            continue
        else:
            continue
    return (result_list, multiple_results_list if multiple_results_list else None)

async def recognize_and_query_entities(chat_body: ChatBody, question: str) -> Optional[List[str]]:
    try:
        product_id = chat_body.product_id
        pre_model_key = f'pre_{product_id}'
        if pre_model_key not in _pre_model_cache:
            _pre_model_cache[pre_model_key] = ChatOpenAI(base_url=get_project_client_config(product_id, 'base_url'), model=get_project_client_config(product_id, 'model'), api_key=get_project_client_config(product_id, 'api_key'), temperature=0, streaming=False)
        pre_model = _pre_model_cache[pre_model_key]
        pre_agent_key = f'pre_agent_{product_id}'
        if pre_agent_key not in _pre_agent_cache:
            _pre_agent_cache[pre_agent_key] = create_agent(model=pre_model, system_prompt=get_pre_agent_prompt())
        pre_agent = _pre_agent_cache[pre_agent_key]
        messages = {'messages': [{'role': 'user', 'content': question}]}
        pre_model_result = await pre_agent.ainvoke(messages)
        pre_entities_str = pre_model_result['messages'][-1].text
        log.info('Application event')
        try:
            match = re.search('\\{([^}]*)\\}', pre_entities_str)
            if match:
                pre_entities_json_str = '{' + match.group(1) + '}'
            else:
                log.info('Application event')
                return None
            pre_entities_json = json.loads(pre_entities_json_str)
            if not isinstance(pre_entities_json, dict):
                log.info('Application event')
                return None
        except Exception as e:
            log.error('Application event')
            return None
        pre_entities_list = pre_entities_json.get('entities') or []
        if not isinstance(pre_entities_list, list) or len(pre_entities_list) == 0:
            log.info('Application event')
            return None
        log.info('Application event')
        pass
        result_list, multiple_results_list = await query_entities_with_concurrency(pre_entities_list, max_concurrent=3)
        if multiple_results_list:
            conflicts = [{'entity_name': r['entity'], 'options': r['data']} for r in multiple_results_list]
            raise EntityConflictError(conflicts=conflicts)
        log.info('Application event')
        pass
        return result_list
    except EntityConflictError:
        raise
    except TokenInvalidError:
        raise
    except Exception as e:
        log.error('Application event')
        pass
        return None
