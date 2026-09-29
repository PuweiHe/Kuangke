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
from threading import Thread, Event
from wsgiref.handlers import format_date_time
from time import mktime
from urllib.parse import urlencode

STATUS_FIRST_FRAME = 0
STATUS_CONTINUE_FRAME = 1
STATUS_LAST_FRAME = 2


class XunfeiIAT:
    def __init__(
        self,
        app_id: str,
        api_key: str,
        api_secret: str,
        language: str = "zh_cn",
        accent: str = "mandarin",
    ):
        self.app_id = app_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.language = language
        self.accent = accent

    def _create_url(self) -> str:
        host = "iat-api.xfyun.cn"
        url = f"wss://{host}/v2/iat"
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: {host}\n"
        signature_origin += f"date: {date}\n"
        signature_origin += "GET /v2/iat HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode("utf-8")
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256",headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
        v = {"authorization": authorization, "date": date, "host": host}
        return url + "?" + urlencode(v)

    def recognize(
        self, audio_data: bytes, sample_rate: int = 16000, timeout_seconds: float = 30
    ) -> str:
        if not audio_data or len(audio_data) > 2 * 1024 * 1024:
            raise ValueError("Audio must contain at most 2 MiB")
        done = Event()
        completed = Event()
        fragments = []
        errors = []

        def fail():
            errors.append("Speech provider failed")
            done.set()

        def on_message(ws, message):
            try:
                payload = json.loads(message)
                if payload.get("code", 0) != 0:
                    fail()
                    return
                data = payload["data"]
                for segment in data.get("result", {}).get("ws", []):
                    fragments.extend(item["w"] for item in segment.get("cw", []))
                if data.get("status") == 2:
                    completed.set()
                    done.set()
            except (ValueError, KeyError, TypeError, AttributeError):
                fail()

        def on_open(ws):
            def send():
                try:
                    for index, offset in enumerate(range(0, len(audio_data), 8000)):
                        if done.is_set():
                            return
                        frame = {
                            "data": {
                                "status": 0 if index == 0 else 1,
                                "format": f"audio/L16;rate={sample_rate}",
                                "audio": base64.b64encode(
                                    audio_data[offset : offset + 8000]
                                ).decode(),
                                "encoding": "raw",
                            }
                        }
                        if index == 0:
                            frame.update(
                                common={"app_id": self.app_id},
                                business={
                                    "domain": "iat",
                                    "language": self.language,
                                    "accent": self.accent,
                                },
                            )
                        ws.send(json.dumps(frame))
                        time.sleep(0.04)
                    ws.send(
                        json.dumps(
                            {
                                "data": {
                                    "status": 2,
                                    "format": f"audio/L16;rate={sample_rate}",
                                    "audio": "",
                                    "encoding": "raw",
                                }
                            }
                        )
                    )
                except Exception:
                    fail()

            Thread(target=send, daemon=True).start()

        ws = websocket.WebSocketApp(
            self._create_url(),
            on_message=on_message,
            on_error=lambda *_: fail(),
            on_close=lambda *_: done.set(),
            on_open=on_open,
        )
        worker = Thread(
            target=lambda: ws.run_forever(sslopt={"cert_reqs": ssl.CERT_REQUIRED}), daemon=True
        )
        worker.start()
        try:
            if not done.wait(timeout_seconds):
                raise TimeoutError("Speech provider timed out")
            if errors or not completed.is_set() or not fragments:
                raise RuntimeError("Speech provider did not return a transcript")
            return "".join(fragments)
        finally:
            ws.close()
            worker.join(timeout=2)


async def recognize_speech(
    app_id: str,
    api_key: str,
    api_secret: str,
    audio_data: bytes,
    sample_rate: int = 16000,
    language: str = "zh_cn",
    accent: str = "mandarin",
) -> str:
    require_external_services()
    client = XunfeiIAT(app_id, api_key, api_secret, language, accent)
    return await asyncio.to_thread(client.recognize, audio_data, sample_rate)
