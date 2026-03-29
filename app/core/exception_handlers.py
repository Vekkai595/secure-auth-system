from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DomainError
from app.schemas.common import ErrorResponse


def _error_response(request: Request, status_code: int, error: str, message: str):
    payload = ErrorResponse(
        error=error,
        message=message,
        request_id=getattr(request.state, 'request_id', None),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        return _error_response(request, exc.status_code, exc.code, exc.message)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return _error_response(request, 401, 'invalid_token', str(exc))
