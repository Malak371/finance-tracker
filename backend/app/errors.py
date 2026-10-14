"""Consistent JSON error responses.

Every error the API returns has the shape:

    {"error": {"code": "not_found", "message": "Expense not found", "details": [...]}}

`details` is only present for validation errors and lists one entry per invalid field.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    422: "validation_error",
    429: "too_many_requests",
}


def error_body(status_code: int, message: str, details: list | None = None) -> dict:
    error = {"code": ERROR_CODES.get(status_code, "error"), "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error}


def _field_path(loc: tuple) -> str:
    # ("body", "amount") -> "amount"; ("query", "month") -> "month"
    parts = [str(part) for part in loc if part not in ("body", "query", "path")]
    return ".".join(parts) or "request"


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.status_code, message),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": _field_path(err["loc"]), "message": err["msg"].removeprefix("Value error, ")}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=422, content=error_body(422, "Some fields are invalid", details))


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    # Unique constraints back up the explicit checks in the routes (e.g. two concurrent requests).
    return JSONResponse(status_code=409, content=error_body(409, "This conflicts with existing data"))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.exception("Unhandled error on %s %s (request %s)", request.method, request.url.path, request_id)
    body = error_body(500, "Something went wrong on our side")
    # Lets a user quote the ID when reporting a problem, and it matches the access log line.
    body["error"]["request_id"] = request_id
    headers = {"X-Request-ID": request_id} if request_id else None
    return JSONResponse(status_code=500, content=body, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
