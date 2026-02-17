"""Error handling middleware"""
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from typing import Callable


async def error_handler_middleware(request: Request, call_next: Callable):
    """
    Global error handler middleware.
    Catches exceptions and returns user-friendly JSON error responses.
    """
    try:
        response = await call_next(request)
        return response
    
    except SQLAlchemyError as exc:
        # Database errors
        error_detail = {
            "error": "DatabaseError",
            "message": "A database error occurred. Please try again later.",
            "details": str(exc) if request.app.debug else None
        }
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_detail
        )
    
    except ValueError as exc:
        # Validation errors
        error_detail = {
            "error": "ValidationError",
            "message": str(exc),
        }
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_detail
        )
    
    except Exception as exc:
        # Catch-all for unexpected errors
        error_detail = {
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
            "details": traceback.format_exc() if request.app.debug else None
        }
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_detail
        )
