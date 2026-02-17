"""Logging middleware with search query and filter usage tracking"""
import time
import logging
from fastapi import Request
from typing import Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
search_logger = logging.getLogger("reel_filter.search_analytics")


async def logging_middleware(request: Request, call_next: Callable):
    """
    Logging middleware - logs all requests and responses with execution time.
    Additionally logs search queries and filter usage for analytics.
    """
    # Start timer
    start_time = time.time()

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    # Log search-specific analytics
    if request.url.path == "/api/movies/search" and request.method == "GET":
        _log_search_query(request)

    # Process request
    response = await call_next(request)

    # Calculate execution time
    execution_time = time.time() - start_time

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {execution_time:.3f}s"
    )

    # Add execution time to response headers
    response.headers["X-Process-Time"] = f"{execution_time:.3f}"

    return response


def _log_search_query(request: Request):
    """Log search query parameters for analytics."""
    params = dict(request.query_params)
    if not params:
        return

    # Build analytics log entry
    analytics = {
        "query": params.get("q", ""),
        "filters": {},
    }

    # Track which filters are being used
    filter_fields = [
        "genres", "year_min", "year_max", "mpaa_ratings",
        "imdb_min", "rt_min", "metacritic_min", "awards_min",
        "sex_max", "violence_max", "language_max",
    ]

    active_filters = []
    for field in filter_fields:
        if field in params and params[field]:
            active_filters.append(field)
            analytics["filters"][field] = params[field]

    search_logger.info(
        f"Search: q='{analytics['query']}' "
        f"active_filters=[{', '.join(active_filters)}] "
        f"filter_count={len(active_filters)}"
    )
