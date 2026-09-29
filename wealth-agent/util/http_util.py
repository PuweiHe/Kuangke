from config import require_external_services
from typing import Optional, Dict, Any
from config.logger import logger as log
import json
import httpx
import time
from .clients import get_http_client
from util.token_context import get_token
from model.exceptions import TokenInvalidError
from util.card_util import get_request_id

async def http_execute_async(url: str, method: str, data=None, headers=None, is_token=False):
    require_external_services()
    client = get_http_client()
    try:
        method = method.upper()
        start_time = time.time()
        request_id = get_request_id()
        from util.mysql_util import insert_agent_log
        if headers is None:
            headers = {}
        context_token = get_token()
        log.debug('Application event')
        if context_token and 'Authorization' not in headers and (not is_token):
            headers['Authorization'] = context_token
            log.debug('Application event')
        if method == 'GET':
            resp = await client.get(url, params=data, headers=headers)
            end_time = time.time()
            log_str = f'请求方式: {method} | 请求地址: {url} | request_id: {request_id} | 请求头: {headers} | params参数: {json.dumps(data, ensure_ascii=False)} | 耗时: {end_time - start_time:.2f}s'
            log.info('Application event')
            pass
        elif method == 'POST':
            resp = await client.post(url, json=data, headers=headers)
            end_time = time.time()
            log_str = f'请求方式: {method} | 请求地址: {url} | request_id: {request_id} | 请求头: {headers} | body参数: {json.dumps(data, ensure_ascii=False)} | 耗时: {end_time - start_time:.2f}s'
            log.info('Application event')
            pass
        else:
            raise ValueError(f'Unsupported HTTP method: {method}')
        resp_data = resp.json()
        if resp_data and resp_data.get('code') == '10000013':
            error_msg = resp_data.get('msg', 'token无效')
            log.error('Application event')
            raise TokenInvalidError(code='10000013', msg=error_msg)
        if resp.json() and resp.json().get('code') and (resp.json().get('code') == 500):
            log.info('Application event')
        result = resp.json()
        pass
        if result is None or result == []:
            log.warning('Application event')
        return result
    except httpx.TimeoutException:
        log.error('Application event')
    except httpx.HTTPStatusError as e:
        log.error('Application event')
    except httpx.RequestError as e:
        log.error('Application event')
    except ValueError as e:
        log.error('Application event')
    except TokenInvalidError:
        raise
    except Exception:
        log.exception('Application event')
    return []
