"""Uniform error responses: {"error": {"code": "...", "message": "..."}}. The frontend translates by code."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.errors")


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, extra: dict | None = None, headers: dict | None = None):
        super().__init__(message)
        self.status_code, self.code, self.message, self.extra, self.headers = status_code, code, message, extra, headers


def err(status_code: int, code: str, message: str, **extra) -> AppError:
    return AppError(status_code, code, message, extra or None)


def _body(code: str, message: str, extra: dict | None = None) -> dict:
    b: dict = {"error": {"code": code, "message": message}}
    if extra:
        b["error"].update(extra)
    return b


_STATUS_CODES = {401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 429: "RATE_LIMITED"}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(_body(exc.code, exc.message, exc.extra), status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        code = _STATUS_CODES.get(exc.status_code, "HTTP_ERROR")
        msg = exc.detail if isinstance(exc.detail, str) else "Request could not be completed."
        return JSONResponse(_body(code, msg), status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        fields = [
            {"field": ".".join(str(p) for p in e["loc"] if p not in ("body", "query", "path")), "code": e["type"], "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(_body("VALIDATION_ERROR", "Some fields are invalid.", {"fields": fields}), status_code=422)

    @app.exception_handler(OperationalError)
    async def _db_down(_: Request, exc: OperationalError):
        logger.exception("Database unavailable")
        return JSONResponse(_body("SERVICE_UNAVAILABLE", "The service is temporarily unavailable. Please try again shortly."), status_code=503)

    @app.exception_handler(SQLAlchemyError)
    async def _db(_: Request, exc: SQLAlchemyError):
        logger.exception("Database error")
        return JSONResponse(_body("SERVER_ERROR", "Something went wrong on our side. Please try again."), status_code=500)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        logger.exception("Unhandled error")  # stack trace goes to logs only, never to the client
        return JSONResponse(_body("SERVER_ERROR", "Something went wrong on our side. Please try again."), status_code=500)
