import httpx
from typing import Optional
_http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    if _http_client is None:
        raise RuntimeError('HTTP 客户端未初始化。请确保在 FastAPI lifespan 中调用了 init_http_clients()')
    return _http_client

async def init_http_clients():
    global _http_client
    _http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0), limits=httpx.Limits(max_connections=200, max_keepalive_connections=100, keepalive_expiry=30), http2=False, follow_redirects=True)

async def close_http_clients():
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
