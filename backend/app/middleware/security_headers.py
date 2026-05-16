from collections.abc import Awaitable, Callable

from fastapi import Request, Response


async def add_security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
