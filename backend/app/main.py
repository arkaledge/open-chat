"""Main FastAPI application"""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import redis.asyncio as redis

from app.core.config import settings
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.v1 import auth, chat, conversations
from app.services.cache_service import CacheService
from app.services.rag_service import RAGService


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
        if settings.log_format == "json"
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

LLM_REQUEST_COUNT = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["model", "provider"]
)

LLM_TOKEN_COUNT = Counter(
    "llm_tokens_total",
    "Total LLM tokens",
    ["model", "type"]  # type: prompt, completion
)

LLM_COST = Counter(
    "llm_cost_total_usd",
    "Total LLM cost in USD",
    ["model"]
)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""

    # Startup
    logger.info("Starting OpenChat API", version="0.1.0", environment=settings.app_env)

    # Initialize Redis for rate limiting
    redis_client = await redis.from_url(settings.redis_url)
    app.state.redis = redis_client

    # Initialize services
    cache_service = CacheService()
    await cache_service.initialize()
    app.state.cache_service = cache_service

    rag_service = RAGService()
    await rag_service.initialize()
    app.state.rag_service = rag_service

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down OpenChat API")

    if hasattr(app.state, "redis"):
        await app.state.redis.close()

    if hasattr(app.state, "cache_service"):
        await app.state.cache_service.close()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Enterprise AI Assistant Platform - Open Source ChatGPT Alternative",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add rate limiting middleware
@app.on_event("startup")
async def add_rate_limit_middleware():
    if settings.rate_limit_enabled and hasattr(app.state, "redis"):
        app.add_middleware(RateLimitMiddleware, redis_client=app.state.redis)


# Include routers
from app.api.v1 import branches

app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(branches.router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": settings.app_env
    }


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "description": "Enterprise AI Assistant Platform",
        "docs": "/docs" if settings.debug else None
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=exc
    )

    return {
        "error": {
            "message": "An internal error occurred",
            "type": "internal_error"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
