import json
import dirtyjson
from config.logger import logger

def loads(params: str):
    if params is None:
        pass
    if not isinstance(params, str):
        return params
    try:
        return json.loads(params)
    except Exception as e:
        logger.info('Application event')
    try:
        return json.loads(params.replace("'", '"'))
    except Exception as e:
        logger.error('Application event')
    return json.loads(json.dumps(dirtyjson.loads(params)))

def dumps(data=None, beautiful=False, default=None, ensure_ascii=False):
    if data is None:
        pass
    if isinstance(data, str):
        return data
    try:
        if beautiful:
            return json.dumps(data, indent=4, default=default, ensure_ascii=ensure_ascii)
        else:
            return json.dumps(data, default=default, ensure_ascii=ensure_ascii)
    except Exception as e:
        if beautiful:
            return json.dumps(data.__dict__, indent=4, default=default, ensure_ascii=ensure_ascii)
        else:
            return json.dumps(data.__dict__, default=default, ensure_ascii=ensure_ascii)
