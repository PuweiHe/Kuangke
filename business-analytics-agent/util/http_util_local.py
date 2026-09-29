from config import require_external_services
import requests
from config import get_configuration, get_project_token
from config.logger import logger

def http_execute_local(url, method, body):
    require_external_services()
    url_prefix = get_configuration('api', 'operations')['http_local_url']
    url = url_prefix + url
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'Connection': 'keep-alive', 'Authorization': get_project_token('operations', 'token')}
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
            data = response.json().get('data')
            return data
        if method == 'POST':
            response = requests.post(url, data=body, headers=headers)
            data = response.json().get('data')
            return data
    except Exception as e:
        logger.warning('Application event')

def http_execute_local_post(url, method, body):
    require_external_services()
    url_prefix = get_configuration('api', 'operations')['http_local_url']
    url = url_prefix + url
    headers = {'Content-Type': 'application/json;charset=UTF-8', 'Connection': 'keep-alive', 'Authorization': get_project_token('operations', 'token')}
    try:
        if method == 'POST':
            response = requests.post(url, data=body, headers=headers)
            data = response.json().get('data')
            if data is None or data == []:
                logger.warning('Application event')
            return data
    except Exception as e:
        logger.warning('Application event')
