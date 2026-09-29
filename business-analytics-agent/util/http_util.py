"""Bounded synchronous tools run in the agent executor, not the event loop."""

import requests
from config import require_external_services


class UpstreamError(RuntimeError):
    pass


def http_execute_general(url, method, token, data):
    require_external_services()
    if method not in {"GET", "POST"}:
        raise ValueError("Unsupported HTTP method")
    try:
        response = requests.request(
            method,
            url,
            headers={"Authorization": token},
            timeout=(5, 20),
            allow_redirects=False,
            **({"params": data} if method == "GET" else {"json": data}),
        )
        if response.status_code not in range(200, 300):
            raise UpstreamError("Data service rejected the request")
        result = response.json()
        if not isinstance(result, dict):
            raise UpstreamError("Data service returned an invalid object")
        return result
    except (requests.RequestException, ValueError) as exc:
        raise UpstreamError("Data service request failed") from exc


def http_execute(url, method, token, data):
    result = http_execute_general(url, method, token, data)
    if result.get("code") != 200 or "data" not in result:
        raise UpstreamError("Data service reported a failed operation")
    return result["data"]
