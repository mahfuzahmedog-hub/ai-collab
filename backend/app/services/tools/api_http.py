import ipaddress
import re
import logging
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_PRIVATE_IPS = re.compile(r"^(127\.|10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|0\.)", re.IGNORECASE)


def _is_private(url: str) -> bool:
    host = urlparse(url).hostname or ""
    if host == "localhost" or host == "0.0.0.0":
        return True
    try:
        addr = ipaddress.ip_address(host)
        return addr.is_private
    except ValueError:
        return bool(_PRIVATE_IPS.match(host))


async def _request(method: str, url: str, data: dict = None, headers: dict = None, timeout: int = 30) -> dict:
    if _is_private(url):
        return {"status_code": 0, "headers": {}, "body": "", "error": "Blocked request to private/internal IP"}
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as cl:
            r = await cl.request(method, url, json=data, headers=headers)
            body = r.text[:10000]
            return {"status_code": r.status_code, "headers": dict(r.headers), "body": body, "error": None}
    except Exception as e:
        return {"status_code": 0, "headers": {}, "body": "", "error": str(e)}


async def http_get(url: str, headers: dict = None, timeout: int = 30) -> dict:
    return await _request("GET", url, headers=headers, timeout=timeout)


async def http_post(url: str, data: dict = None, headers: dict = None, timeout: int = 30) -> dict:
    return await _request("POST", url, data=data, headers=headers, timeout=timeout)


async def http_put(url: str, data: dict = None, headers: dict = None, timeout: int = 30) -> dict:
    return await _request("PUT", url, data=data, headers=headers, timeout=timeout)


async def http_delete(url: str, headers: dict = None, timeout: int = 30) -> dict:
    return await _request("DELETE", url, headers=headers, timeout=timeout)
