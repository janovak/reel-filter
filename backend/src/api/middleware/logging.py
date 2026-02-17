"""Logging middleware"""
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


async def logging_middleware(request: Request, call_next: Callable):
    """
    Logging middleware - logs all requests and responses with execution time.
    """
    # Start timer
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
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
