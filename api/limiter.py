import os
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def _has_valid_api_key(request) -> bool:
    """Return True when the request carries a valid API key, exempting it from rate limits."""
    key = request.headers.get("x-api-key")
    if not key:
        return False
    valid = os.environ.get("VALID_API_KEYS", "")
    return key in {k.strip() for k in valid.split(",") if k.strip()}
