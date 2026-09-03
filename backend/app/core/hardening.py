"""Production HTTP hardening: security headers, body limits, structured errors.

Every response leaving the service carries the same security headers and every error
leaves as the same JSON envelope, so clients never see a stack trace or an unhandled
exception body and operators can correlate a failure by request id.
"""

import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import Settings

logger = logging.getLogger("sentinel_aegis.api")

REQUEST_ID_HEADER = "x-request-id"

# Spelled numerically: Starlette renamed these constants and the old aliases warn.
HTTP_413_CONTENT_TOO_LARGE = 413
HTTP_422_UNPROCESSABLE_CONTENT = 422

# A JSON API that never inlines scripts or frames itself: lock the page down entirely.
_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Content-Security-Policy", _CONTENT_SECURITY_POLICY)
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=()",
        )
        response.headers.setdefault("Cache-Control", "no-store")
        # HSTS only over TLS: sending it on plain HTTP is meaningless and can strand
        # local development on an unreachable https origin.
        if self.settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={self.settings.hsts_max_age_seconds}; includeSubDomains",
            )
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects oversized bodies before they are buffered or parsed."""

    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        declared = request.headers.get("content-length")
        if declared is not None:
            try:
                if int(declared) > self.max_bytes:
                    return self._too_large(request)
            except ValueError:
                return error_response(
                    request,
                    status.HTTP_400_BAD_REQUEST,
                    "invalid_content_length",
                    "Content-Length header is not a valid integer.",
                )
        return await call_next(request)

    def _too_large(self, request: Request) -> JSONResponse:
        return error_response(
            request,
            HTTP_413_CONTENT_TOO_LARGE,
            "request_too_large",
            f"Request body exceeds the {self.max_bytes} byte limit.",
        )


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Gives every request a correlation id and echoes it back to the caller."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or f"req-{id(request):x}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers.setdefault(REQUEST_ID_HEADER, request_id)
        return response


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
) -> JSONResponse:
    payload: dict[str, object] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", None),
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def install_hardening(app: FastAPI, settings: Settings) -> None:
    """Install CORS, headers, body limits, and structured error handling.

    Middleware runs in reverse registration order, so request context is added first
    and therefore the request id is available to every layer below it.
    """
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=settings.cors_allow_credentials,
            allow_methods=settings.cors_allow_methods,
            allow_headers=settings.cors_allow_headers,
        )

    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=settings.max_request_bytes)
    if settings.security_headers_enabled:
        app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    app.add_middleware(RequestContextMiddleware)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        response = error_response(
            request,
            exc.status_code,
            _code_for_status(exc.status_code),
            str(exc.detail),
        )
        for key, value in (exc.headers or {}).items():
            response.headers[key] = value
        return response

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            request,
            HTTP_422_UNPROCESSABLE_CONTENT,
            "validation_error",
            "Request validation failed.",
            details=_safe_validation_details(exc),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Log the cause for operators; return nothing internal to the caller.
        logger.exception(
            "unhandled_error",
            extra={"request_id": getattr(request.state, "request_id", None)},
            exc_info=exc,
        )
        return error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "The request could not be completed.",
        )


def _code_for_status(status_code: int) -> str:
    return {
        400: "bad_request",
        401: "unauthenticated",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        413: "request_too_large",
        422: "validation_error",
        429: "rate_limited",
    }.get(status_code, "error")


def _safe_validation_details(exc: RequestValidationError) -> list[dict[str, str]]:
    """Report where validation failed without echoing the submitted values back."""
    return [
        {
            "location": ".".join(str(part) for part in error.get("loc", ())),
            "message": str(error.get("msg", "invalid value")),
            "type": str(error.get("type", "value_error")),
        }
        for error in exc.errors()
    ]
