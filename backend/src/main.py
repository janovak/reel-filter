"""FastAPI application entry point"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.database.session import init_db
from src.api.middleware.error_handler import error_handler_middleware
from src.api.middleware.logging import logging_middleware
from src.api.routes import movies, metadata, health


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    print("🚀 Starting up Reel-Filter API...")
    init_db()
    print("✓ Database initialized")
    yield
    # Shutdown
    print("👋 Shutting down Reel-Filter API...")


# Create FastAPI application
app = FastAPI(
    title="Reel-Filter Movie Search API",
    description=(
        "REST API for movie content-aware search. "
        "Filter movies by genre, ratings, awards, and content tolerance thresholds."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware - allow frontend to access API
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(logging_middleware)
app.middleware("http")(error_handler_middleware)

# Register routes
app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(metadata.router, prefix="/api", tags=["metadata"])
app.include_router(health.router, prefix="/api", tags=["health"])


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Reel-Filter API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
