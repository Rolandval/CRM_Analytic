"""
Centralised exception hierarchy and FastAPI exception handlers.

All domain exceptions inherit from CRMException so callers can catch
a single base class when needed.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


# ── Base ──────────────────────────────────────────────────────────────────────

class CRMException(Exception):
    """Root exception for all CRM-related errors."""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(message)


# ── 400 Bad Request ───────────────────────────────────────────────────────────

class ValidationError(CRMException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "VALIDATION_ERROR"


class InvalidPhoneNumber(ValidationError):
    error_code = "INVALID_PHONE"


# ── 401 Unauthorized ──────────────────────────────────────────────────────────

class AuthenticationError(CRMException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "AUTHENTICATION_ERROR"


class InvalidCredentials(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"


class TokenExpired(AuthenticationError):
    error_code = "TOKEN_EXPIRED"


# ── 403 Forbidden ─────────────────────────────────────────────────────────────

class PermissionDenied(CRMException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "PERMISSION_DENIED"


# ── 404 Not Found ─────────────────────────────────────────────────────────────

class NotFoundError(CRMException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"


class UserNotFound(NotFoundError):
    error_code = "USER_NOT_FOUND"


class CallNotFound(NotFoundError):
    error_code = "CALL_NOT_FOUND"


# ── 409 Conflict ──────────────────────────────────────────────────────────────

class ConflictError(CRMException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "CONFLICT"


# ── 422 Unprocessable ─────────────────────────────────────────────────────────

class UnprocessableError(CRMException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "UNPROCESSABLE"


# ── 503 External Service ──────────────────────────────────────────────────────

class ExternalServiceError(CRMException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "EXTERNAL_SERVICE_ERROR"


class UnitalkAPIError(ExternalServiceError):
    error_code = "UNITALK_API_ERROR"


# ── FastAPI handlers ──────────────────────────────────────────────────────────

def _error_response(exc: CRMException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CRMException)
    async def crm_exception_handler(request: Request, exc: CRMException):
        return _error_response(exc)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        from core.logging import get_logger
        logger = get_logger(__name__)
        logger.error("unhandled_exception", exc_info=exc, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "detail": None,
            },
        )
