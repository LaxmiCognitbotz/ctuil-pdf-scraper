"""
Helpers - shared utilities for API route handlers.
"""

import logging
import traceback

from fastapi import status
from fastapi.responses import JSONResponse

from app.schemas import APIResponse

logger = logging.getLogger(__name__)

# Standard error response schema for OpenAPI docs
ERROR_RESPONSES = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "Scraper execution failed",
        "model": APIResponse,
    },
}


def handle_scraper(
    service_fn,
    success_message: str,
    error_message: str,
    error_code: str,
):
    """
    Execute a service function and return a standardised response.

    • On success → 200 with APIResponse(status=True)
    • On failure → 500 with APIResponse(status=False) + full error detail
    """
    try:
        result = service_fn()
        return APIResponse.success(message=success_message, data=result)

    except Exception:
        logger.exception("%s  [%s]", error_message, error_code)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIResponse.failure(
                message=error_message,
                error_code=error_code,
                detail=traceback.format_exc(),
            ).model_dump(),
        )
