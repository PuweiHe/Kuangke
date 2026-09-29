from config import require_external_services
import requests
from config import get_configuration, get_project_token
from config.logger import logger as log
import httpx
from .clients import get_http_client
import traceback

def http_execute_local(url, method, body):
    require_external_services()
    url_prefix = get_configuration('api', 'wealth')['http_local_url']
    url = url_prefix + url
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'Connection': 'keep-alive', 'Authorization': get_project_token('wealth', 'token')}
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
            data = response.json().get('data')
        elif method == 'POST':
            response = requests.post(url, data=body, headers=headers)
            data = response.json().get('data')
        else:
            raise ValueError(f'Unsupported HTTP method: {method}')
        if response.json() and response.json().get('code') and (response.json().get('code') == 500):
            log.info('Application event')
        return data
    except Exception as e:
        log.error('Application event')
        return ''

def http_execute_local_post(url, method, body):
    require_external_services()
    url_prefix = get_configuration('api', 'wealth')['http_local_url']
    url = url_prefix + url
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'Connection': 'keep-alive', 'Authorization': get_project_token('wealth', 'token')}
    if method == 'POST':
        response = requests.post(url, data=body, headers=headers)
        data = response.json().get('data')
        if data is None or data == []:
            log.error('Application event')
        return data

async def http_execute_local_async(url: str, method: str, data=None):
    require_external_services()
    client = get_http_client()
    url_prefix = get_configuration('api', 'wealth')['http_local_url']
    url = url_prefix + url
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'Connection': 'keep-alive', 'Authorization': get_project_token('wealth', 'token')}
    try:
        method = method.upper()
        if method == 'GET':
            resp = await client.get(url, params=data, headers=headers)
        elif method == 'POST':
            resp = await client.post(url, data=data, headers=headers)
        else:
            raise ValueError(f'Unsupported HTTP method: {method}')
        if resp.json() and resp.json().get('code') and (resp.json().get('code') == 500):
            log.info('Application event')
        resp.raise_for_status()
        result = resp.json()
        res_data = result.get('data')
        if res_data is None or res_data == [] or res_data == {} or (res_data == ''):
            return ''
        return res_data
    except httpx.TimeoutException:
        log.error('Application event')
    except httpx.HTTPStatusError as e:
        log.error('Application event')
    except httpx.RequestError as e:
        log.error('Application event')
    except ValueError as e:
        log.error('Application event')
    except Exception:
        log.exception('Application event')
    return []
