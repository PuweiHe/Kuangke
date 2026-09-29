"""Environment-only configuration for a generalized portfolio service."""
import json
import os
from pathlib import Path

def external_services_enabled():
    return os.getenv('ENABLE_EXTERNAL_SERVICES', 'false').lower() == 'true'

def require_external_services():
    if not external_services_enabled():
        raise RuntimeError('External services are disabled. Use the synthetic demo or configure adapters explicitly.')

def get_configuration(module, key=None):
    if module == 'application':
        value = {'app': {'host': '127.0.0.1', 'port': int(os.getenv('PORT', '8000'))}, 'redis': {'host': os.getenv('REDIS_HOST', '127.0.0.1'), 'port': int(os.getenv('REDIS_PORT', '6379')), 'db': 0, 'password': os.getenv('REDIS_PASSWORD', ''), 'max_connections': 10}}
        return value.get(key) if key else value
    if module == 'api':
        require_external_services()
        base = os.environ['DATA_API_BASE_URL'].rstrip('/')
        endpoints = json.loads(os.getenv('DATA_API_PATHS_JSON', '{}'))
        return {'base_url': base, 'prefix': '', 'apis': endpoints, 'token': os.getenv('DATA_API_TOKEN', ''), 'http_local_url': base, 'http_url': base, 'es_query_url': os.getenv('SEARCH_API_URL', ''), 'detection_analysis_url': os.getenv('ENTITY_API_URL', ''), 'sandbox': os.getenv('SANDBOX_URL', '')}
    raise ValueError('Unknown configuration module')

def get_configuration_from_filepath(filepath, key=None):
    value = json.loads(Path(filepath).read_text())
    return value.get(key) if key else value

def get_project_api_uri(project, api_name):
    cfg = get_configuration('api', project)
    path = cfg['apis'].get(api_name)
    if not isinstance(path, str) or not path.startswith('/') or path.startswith('//'):
        raise ValueError('Configure a relative API path for ' + api_name)
    return cfg['base_url'] + path

def get_project_client_config(model_name, key):
    require_external_services()
    names = {'base_url': 'LLM_BASE_URL', 'api_key': 'LLM_API_KEY', 'model': 'LLM_MODEL'}
    if model_name == 'xunfei':
        names = {'app_id': 'SPEECH_APP_ID', 'api_key': 'SPEECH_API_KEY', 'api_secret': 'SPEECH_API_SECRET'}
    return os.environ[names[key]]

def get_project_token(project, api_name):
    require_external_services()
    return os.getenv('DATA_API_TOKEN', '')
