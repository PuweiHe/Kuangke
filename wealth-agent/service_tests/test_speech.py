"""Speech completion is bounded and sends a final frame even for short audio."""

import json
import threading
import unittest
from unittest.mock import patch
from services.xunfei_iat import XunfeiIAT


class SpeechTests(unittest.TestCase):
    def test_short_audio_sends_final_frame_and_closes(self):
        sent = []
        closed = threading.Event()

        class Socket:
            def __init__(self, url, **callbacks):
                self.callbacks = callbacks

            def send(self, frame):
                sent.append(json.loads(frame)["data"]["status"])
                if sent[-1] == 2:
                    self.callbacks["on_message"](
                        self,
                        json.dumps(
                            {
                                "code": 0,
                                "data": {"status": 2, "result": {"ws": [{"cw": [{"w": "hello"}]}]}},
                            }
                        ),
                    )

            def run_forever(self, **kwargs):
                self.callbacks["on_open"](self)
                closed.wait(1)

            def close(self):
                closed.set()

        with patch("services.xunfei_iat.websocket.WebSocketApp", Socket):
            result = XunfeiIAT("test", "test", "test").recognize(b"audio", timeout_seconds=0.5)
        self.assertEqual(result, "hello")
        self.assertEqual(sent, [0, 2])
        self.assertTrue(closed.is_set())

    def test_empty_audio_is_rejected_before_connection(self):
        with self.assertRaises(ValueError):
            XunfeiIAT("test", "test", "test").recognize(b"")

    def test_partial_transcript_is_not_success_on_early_close(self):
        class Socket:
            def __init__(self, url, **callbacks):
                self.callbacks = callbacks

            def run_forever(self, **kwargs):
                self.callbacks["on_message"](
                    self,
                    json.dumps(
                        {
                            "code": 0,
                            "data": {"status": 1, "result": {"ws": [{"cw": [{"w": "partial"}]}]}},
                        }
                    ),
                )
                self.callbacks["on_close"](self, None, None)

            def close(self):
                pass

        with patch("services.xunfei_iat.websocket.WebSocketApp", Socket):
            with self.assertRaises(RuntimeError):
                XunfeiIAT("test", "test", "test").recognize(b"audio")

    def test_timeout_closes_connection(self):
        closed = threading.Event()

        class Socket:
            def __init__(self, url, **callbacks):
                pass

            def run_forever(self, **kwargs):
                closed.wait(1)

            def close(self):
                closed.set()

        with patch("services.xunfei_iat.websocket.WebSocketApp", Socket):
            with self.assertRaises(TimeoutError):
                XunfeiIAT("test", "test", "test").recognize(b"audio", timeout_seconds=0.01)
        self.assertTrue(closed.is_set())
