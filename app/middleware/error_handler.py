from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Union, Dict, Any, Type, Callable
import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    async def __call__(self, request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, RequestValidationError):
            return await self.handle_validation_error(request, exc)
        elif isinstance(exc, StarletteHTTPException):
            return await self.handle_http_error(request, exc)
        else:
            return await self.handle_internal_error(request, exc)

    async def handle_validation_error(
        self,
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            f"Validation error: {str(exc)} - "
            f"URL: {request.url} - "
            f"Method: {request.method}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "body": exc.body
            }
        )

    async def handle_http_error(
        self,
        request: Request,
        exc: StarletteHTTPException
    ) -> JSONResponse:
        logger.warning(
            f"HTTP error {exc.status_code}: {exc.detail} - "
            f"URL: {request.url} - "
            f"Method: {request.method}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        )

    async def handle_internal_error(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        logger.error(
            f"Internal error: {str(exc)} - "
            f"URL: {request.url} - "
            f"Method: {request.method}",
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(exc) if request.app.debug else "An unexpected error occurred"
            }
        )

def get_error_handler() -> Dict[Union[int, Type[Exception]], Callable]:
    """Get error handlers for FastAPI app"""
    handler = ErrorHandler()
    return {
        RequestValidationError: handler.handle_validation_error,
        StarletteHTTPException: handler.handle_http_error,
        Exception: handler.handle_internal_error
    }
