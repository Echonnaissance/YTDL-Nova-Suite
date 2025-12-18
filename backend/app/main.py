"""
FastAPI Application Entry Point
Main application file that sets up the FastAPI app, middleware, and routes
"""
from app.api.routes import settings as settings_router
from app.api.routes import downloads
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Any, cast
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os
import sys
import logging
import time

from app.config import settings, init_directories
from app.core.database import init_db
from app.services.download_queue import get_download_queue
from app.core.exceptions import (
    YouTubeDownloaderException,
    InvalidURLError,
    DownloadNotFoundError,
    QueueFullError,
    ServiceUnavailableError,
    YTDLPError,
    FFmpegError,
    DownloadError
)

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

# SECURITY: Log rotation to prevent disk fill
log_handler = RotatingFileHandler(
    "app.log",
    maxBytes=10 * 1024 * 1024,  # 10 MB per file
    backupCount=5  # Keep 5 backup files
)
log_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        log_handler
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("[*] Starting Universal Media Downloader API...")
    print(f"[*] Version: {settings.APP_VERSION}")
    print(f"[*] Debug Mode: {settings.DEBUG}")

    # Initialize directories
    init_directories()
    print(f"[*] Download directory: {settings.DOWNLOAD_DIR}")

    # Initialize database
    init_db()

    # Start download queue
    download_queue = get_download_queue()
    await download_queue.start()

    # Check for external tools
    ytdlp_exists = os.path.exists(settings.YTDLP_PATH)
    ffmpeg_exists = os.path.exists(settings.FFMPEG_PATH)

    print(f"[*] yt-dlp available: {ytdlp_exists}")
    print(f"[*] FFmpeg available: {ffmpeg_exists}")

    if not ytdlp_exists:
        print("[!] WARNING: yt-dlp.exe not found! Downloads will not work.")
        print(f"    Expected location: {settings.YTDLP_PATH}")

    if not ffmpeg_exists:
        print("[!] WARNING: ffmpeg.exe not found! Video processing may fail.")
        print(f"    Expected location: {settings.FFMPEG_PATH}")

    print("[+] Application startup complete!\n")

    yield

    # Shutdown
    print("\n[*] Shutting down YouTube Downloader API...")

    # Stop download queue
    download_queue = get_download_queue()
    await download_queue.stop()

    print("[+] Shutdown complete!")


# Create rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.RATE_LIMIT_ENABLED
)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional universal media downloader API",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Attach limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, cast(
    Any, _rate_limit_exceeded_handler))


# ============================================================================
# Middleware
# ============================================================================

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


# Request Size Validation Middleware
@app.middleware("http")
async def validate_request_size(request: Request, call_next):
    """
    Validate request size to prevent memory exhaustion attacks

    SECURITY: Check Content-Length header to reject oversized requests early.
    Note: Uvicorn also enforces --limit-request-line and body limits at the server level.
    """
    content_length = request.headers.get("content-length")

    if content_length:
        try:
            content_length_int = int(content_length)
            if content_length_int > settings.MAX_REQUEST_SIZE:
                client_host = request.client.host if request.client else "unknown"
                logger.warning(
                    f"Request too large from {client_host}: "
                    f"{content_length_int} bytes (max: {settings.MAX_REQUEST_SIZE})"
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "error": "RequestTooLarge",
                        "detail": f"Request body too large. Maximum size: {settings.MAX_REQUEST_SIZE} bytes"
                    }
                )
        except ValueError:
            pass  # Invalid Content-Length header

    return await call_next(request)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for security monitoring"""
    start_time = time.time()

    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} "
        f"({process_time:.3f}s)"
    )

    return response


# Rate Limiting Middleware
app.add_middleware(SlowAPIMiddleware)

# CORS Middleware - allows frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(YouTubeDownloaderException)
async def youtube_downloader_exception_handler(
    request: Request,
    exc: YouTubeDownloaderException
):
    """Handle custom application exceptions with appropriate HTTP status codes"""
    # Determine appropriate status code based on exception type
    if isinstance(exc, (InvalidURLError, DownloadNotFoundError)):
        # Client errors - bad request
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, QueueFullError):
        # Too many requests
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, ServiceUnavailableError):
        # External service unavailable
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif isinstance(exc, (YTDLPError, FFmpegError, DownloadError)):
        # Server/processing errors
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    else:
        # Default to 500 for unknown YouTubeDownloaderException types
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    if settings.DEBUG:
        # In debug mode, return detailed error
        import traceback
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "detail": str(exc),
                "traceback": traceback.format_exc()
            }
        )
    else:
        # In production, return generic error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "detail": "An unexpected error occurred"
            }
        )


# ============================================================================
# Root Routes
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/api/docs",
        "message": "Welcome to Universal Media Downloader API! Visit /api/docs for documentation."
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "ytdlp_available": os.path.exists(settings.YTDLP_PATH),
        "ffmpeg_available": os.path.exists(settings.FFMPEG_PATH),
        "database_ok": True  # TODO: Add actual DB health check
    }


# ============================================================================
# API Routes
# ============================================================================

# Import and include routers

app.include_router(downloads.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
# app.include_router(queue.router, prefix="/api")  # TODO: Create queue routes
# app.include_router(history.router, prefix="/api")  # TODO: Create history routes


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print(f"""
    ============================================================
              Universal Media Downloader API - Dev Server
    ============================================================
      API Documentation: http://localhost:{settings.PORT}/api/docs
      ReDoc: http://localhost:{settings.PORT}/api/redoc
      Health Check: http://localhost:{settings.PORT}/api/health
    ============================================================
    """)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
