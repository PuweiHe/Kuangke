from config import require_external_services
import requests
from config import get_configuration
from config.logger import logger as log
import json

def http_execute(url, method, token, data):
    require_external_services()
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'Connection': 'keep-alive', 'Authorization': token}
    try:
        if method == 'GET':
            response = requests.get(url, params=data, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
        else:
            log.warning('Application event')
            return None
    except Exception as e:
        log.error('Application event')
        return None
    if response.status_code != 200:
        log.warning('Application event')
        return None
    try:
        result = response.json()
    except Exception as e:
        log.error('Application event')
        return None
    result_data = result.get('data')
    if result_data is None or result_data == [] or result.get('code') != 200:
        log.warning('Application event')
    return result_data

def http_execute_general(url, method, token, data):
    require_external_services()
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'Connection': 'keep-alive', 'Authorization': token}
    if method == 'GET':
        response = requests.get(url, params=data, headers=headers)
        data = response.json()
        if data is None or data == []:
            log.warning('Application event')
        return data
    if method == 'POST':
        response = requests.post(url, headers=headers, data=json.dumps(data))
        data = response.json()
        if data is None or data == []:
            log.warning('Application event')
        return data
    return None
