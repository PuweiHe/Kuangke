"""Authenticated data requests with explicit failures and no payload logging."""

import httpx
from config import require_external_services
from model.exceptions import TokenInvalidError
from util.clients import get_http_client
from util.token_context import get_token


class UpstreamError(RuntimeError):
    pass


async def http_execute_async(url, method, data=None, headers=None, is_token=False):
    require_external_services()
    if method.upper() not in {"GET", "POST"}:
        raise ValueError("Unsupported HTTP method")
    headers = dict(headers or {})
    if get_token() and not is_token:
        headers.setdefault("Authorization", get_token())
    try:
        response = await get_http_client().request(
            method.upper(),
            url,
            headers=headers,
            **({"params": data} if method.upper() == "GET" else {"json": data}),
        )
        if response.status_code in {401, 403}:
            raise TokenInvalidError("10000013", "Data service rejected credentials")
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise UpstreamError("Data service returned an invalid object")
        if str(result.get("code")) == "10000013":
            raise TokenInvalidError("10000013", "Data service rejected credentials")
        if str(result.get("code")) not in {"0", "200"}:
            raise UpstreamError("Data service reported a failed operation")
        return result
    except (httpx.HTTPError, ValueError) as exc:
        raise UpstreamError("Data service request failed") from exc
