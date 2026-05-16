from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.config import get_settings

_buckets: dict[str, deque[float]] = defaultdict(deque)


def reset_rate_limits() -> None:
    _buckets.clear()


def rate_limit(scope: str, limit_getter: Callable[[], int]):
    def dependency(request: Request) -> None:
        limit = limit_getter()
        if limit <= 0:
            return
        client_host = request.client.host if request.client else "unknown"
        key = f"{scope}:{client_host}"
        now = time.monotonic()
        window_start = now - 60
        bucket = _buckets[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please retry shortly.",
                headers={"Retry-After": "60"},
            )
        bucket.append(now)

    return dependency


rate_limit_auth = rate_limit("auth", lambda: get_settings().rate_limit_auth_per_minute)
rate_limit_ai = rate_limit("ai", lambda: get_settings().rate_limit_ai_per_minute)
rate_limit_billing = rate_limit("billing", lambda: get_settings().rate_limit_billing_per_minute)
rate_limit_public = rate_limit("public", lambda: get_settings().rate_limit_public_per_minute)
