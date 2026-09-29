import base64
import io
import os
import uuid
import datetime
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from e2b_code_interpreter import Sandbox
from minio import Minio
from dotenv import load_dotenv
from config.logger import logger as log
load_dotenv()
E2B_API_KEY = os.environ.get('E2B_API_KEY')
MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT')
MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY')
MINIO_BUCKET = os.environ.get('MINIO_BUCKET')
MINIO_PUBLIC_BASE = os.environ.get('MINIO_PUBLIC_BASE')
MINIO_SECURE = os.environ.get('MINIO_SECURE', 'false').lower() == 'true'
_minio_client = None

def _get_storage_client():
    global _minio_client
    from config import require_external_services
    require_external_services()
    if _minio_client is None:
        if not all([MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET]):
            raise RuntimeError('Object storage is not configured')
        _minio_client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=MINIO_SECURE)
    return _minio_client
STYLE_PREAMBLE = "\nimport matplotlib\nimport matplotlib.pyplot as plt\nplt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei']\nplt.rcParams['axes.unicode_minus'] = False\nplt.rcParams['axes.prop_cycle'] = plt.cycler(color=['#ED7B2F', '#5B8FF9', '#5AD8A6', '#F6BD16', '#E8684A'])\nplt.rcParams['figure.figsize'] = (10, 6)\nplt.rcParams['figure.dpi'] = 120\nplt.rcParams['axes.spines.top'] = False\nplt.rcParams['axes.spines.right'] = False\nplt.rcParams['axes.grid'] = True\nplt.rcParams['grid.alpha'] = 0.3\n"

def _upload_to_minio(img_bytes: bytes, ext: str='png') -> str:
    """ upload to minio. Use validated tool arguments and return adapter results."""
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    key = f'reports/{ts}{uuid.uuid4().hex}.{ext}'
    _get_storage_client().put_object(bucket_name=MINIO_BUCKET, object_name=key, data=io.BytesIO(img_bytes), length=len(img_bytes), part_size=10 * 1024 * 1024, content_type=f'image/{ext}')
    return f'{MINIO_PUBLIC_BASE}/{MINIO_BUCKET}/{key}'

@tool('sandbox_tool', args_schema={'type': 'object', 'properties': {'language': {'type': 'string', 'default': 'python', 'description': '程序语言类型'}, 'code': {'type': 'string', 'description': "待执行的Python代码。必须包含print()输出结果或生成图表。可调用库：math, numpy, pandas, matplotlib, seaborn。示例：'import numpy as np; x = np.linspace(0,10,100); y = np.sin(x); plt.plot(x,y)'"}, 'output_type': {'type': 'string', 'enum': ['plot', 'text'], 'description': "输出类型：'plot'返回图表base64，'text'返回print()内容。默认根据代码自动判断"}}, 'required': ['code']})
def sandbox_tool(config: RunnableConfig, **kwargs) -> dict:
    """Sandbox tool. Use validated tool arguments and return adapter results."""
    from config import require_external_services
    require_external_services()
    arguments = kwargs
    code = arguments.get('code')
    output_type = arguments.get('output_type')
    if not code:
        return [{'function_response': '未提供可执行代码'}]
    try:
        with Sandbox.create(api_key=E2B_API_KEY) as sandbox:
            execution = sandbox.run_code(STYLE_PREAMBLE + '\n' + code)
            error = execution.error
            results = execution.results
            stdout = ''.join(execution.logs.stdout) if execution.logs and execution.logs.stdout else ''
            text_output = execution.text or stdout
            image_b64_list = [r.png for r in results if getattr(r, 'png', None)]
    except Exception as e:
        log.error('Application event')
        return [{'function_response': f'代码执行失败: {e}'}]
    if error:
        err = f'{error.name}: {error.value}'
        log.warning('Application event')
        return [{'function_response': f'代码运行出错: {err}'}]
    image_urls = []
    for b64 in image_b64_list:
        try:
            image_urls.append(_upload_to_minio(base64.b64decode(b64), 'png'))
        except Exception as e:
            log.error('Application event')
    result = {}
    if image_urls:
        md = ' '.join((f'![chart]({u})' for u in image_urls))
        result['function_response'] = '直接在页面上通过 markdown 的方式 ![name](url) 直接加载图片的链接 ' + md
    else:
        result['function_response'] = str(text_output)
    return [result]
