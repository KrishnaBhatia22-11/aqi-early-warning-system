import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

limiter = Limiter(key_func=get_remote_address)


def _has_valid_api_key(request: Request) -> bool:
    api_key = request.headers.get("X-API-Key")
    valid_keys = os.environ.get("VALID_API_KEYS", "")
    if not valid_keys:
        return False
    return api_key in valid_keys.split(",")
