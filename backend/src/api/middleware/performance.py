"""Performance logging middleware.

Logs execution time for all requests and warns about slow operations.
Threshold: 500ms for slow query warnings.
"""
import time
import logging
from fastapi import Request
from typing import Callable

logger = logging.getLogger("reel_filter.performance")

# Slow query threshold in seconds
SLOW_QUERY_THRESHOLD = 0.5  # 500ms


async def performance_middleware(request: Request, call_next: Callable):
    """
    Performance monitoring middleware.
    - Logs execution time for all requests
    - Warns about requests exceeding 500ms threshold
    - Adds timing headers to responses
    """
    start_time = time.perf_counter()

    response = await call_next(request)

    # Calculate execution time
    duration = time.perf_counter() - start_time
    duration_ms = duration * 1000

    # Add timing header
    response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

    # Log performance metrics
    path = request.url.path
    method = request.method
    status = response.status_code

    if duration > SLOW_QUERY_THRESHOLD:
        # Slow request warning
        logger.warning(
            f"SLOW REQUEST: {method} {path} - {duration_ms:.1f}ms "
            f"(threshold: {SLOW_QUERY_THRESHOLD * 1000:.0f}ms) "
            f"Status: {status}"
        )
    else:
        logger.debug(
            f"Request: {method} {path} - {duration_ms:.1f}ms - Status: {status}"
        )

    return response
