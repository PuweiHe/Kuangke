from config import require_external_services
import asyncio
import hmac
import json
import hashlib
import base64
import time
import ssl
import websocket
from datetime import datetime
from threading import Thread
from wsgiref.handlers import format_date_time
from time import mktime
from urllib.parse import urlencode
STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2

class XunfeiIAT:

    def __init__(self, app_id: str, api_key: str, api_secret: str, language: str='zh_cn', accent: str='mandarin'):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.language = language
        self.accent = accent

    def _create_url(self) -> str:
        host = 'iat-api.xfyun.cn'
        url = f'wss://{host}/v2/iat'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f'host: {host}\n'
        signature_origin += f'date: {date}\n'
        signature_origin += 'GET /v2/iat HTTP/1.1'
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'), digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256",headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        v = {'authorization': authorization, 'date': date, 'host': host}
        return url + '?' + urlencode(v)

    def recognize(self, audio_data: bytes, sample_rate: int=16000) -> str:
        result_text = ''
        result_ready = asyncio.Event()

        def on_message(ws, message):
            nonlocal result_text
            try:
                data = json.loads(message)
                code = data.get('code', 0)
                if code != 0:
                    pass
                    result_ready.set()
                    return
                if 'data' in data:
                    result_data = data['data']['result']['ws']
                    for i in result_data:
                        for w in i.get('cw', []):
                            result_text += w.get('w', '')
            except Exception as e:
                pass
            finally:
                if data.get('data', {}).get('status') == 2:
                    result_ready.set()

        def on_error(ws, error):
            pass
            result_ready.set()

        def on_close(ws, a, b):
            pass

        def on_open(ws):

            def run():
                frame_size = 8000
                status = STATUS_FIRST_FRAME
                business_args = {'domain': 'iat', 'language': self.language, 'accent': self.accent, 'vinfo': 1, 'vad_eos': 10000}
                common_arge = {'app_id': self.app_id}
                chunks = [audio_data[i:i + frame_size] for i in range(0, len(audio_data), frame_size)]
                for idx, chunk in enumerate(chunks):
                    is_last = idx == len(chunks) - 1
                    if status == STATUS_FIRST_FRAME:
                        d = {'common': common_arge, 'business': business_args, 'data': {'status': 0, 'format': f'audio/L16;rate={sample_rate}', 'audio': str(base64.b64encode(chunk), 'utf-8'), 'encoding': 'raw'}}
                        ws.send(json.dumps(d))
                        status = STATUS_CONTINUE_FRAME
                    elif is_last:
                        d = {'data': {'status': 2, 'format': f'audio/L16;rate={sample_rate}', 'audio': str(base64.b64encode(chunk), 'utf-8'), 'encoding': 'raw'}}
                        ws.send(json.dumps(d))
                        time.sleep(1)
                        ws.close()
                    else:
                        d = {'data': {'status': 1, 'format': f'audio/L16;rate={sample_rate}', 'audio': str(base64.b64encode(chunk), 'utf-8'), 'encoding': 'raw'}}
                        ws.send(json.dumps(d))
                    time.sleep(0.04)
            Thread(target=run, daemon=True).start()
        ws_url = self._create_url()
        ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        ws.run_forever(sslopt={'cert_reqs': ssl.CERT_REQUIRED})
        if not result_ready.is_set():
            result_ready.wait(timeout=30)
        return result_text

async def recognize_speech(app_id: str, api_key: str, api_secret: str, audio_data: bytes, sample_rate: int=16000, language: str='zh_cn', accent: str='mandarin') -> str:
    require_external_services()
    client = XunfeiIAT(app_id, api_key, api_secret, language, accent)
    return await asyncio.to_thread(client.recognize, audio_data, sample_rate)
