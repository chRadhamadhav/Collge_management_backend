"""
FastAPI application factory.
Registers routers, exception handlers, static file serving, and startup events.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as api_router
from app.config import get_settings
from app.core.exceptions import AppException
from app.core.logger.logger import configure_logger, logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs setup before serving and cleanup on shutdown."""
    configure_logger(settings.environment)

    # Ensure upload directory exists at startup
    upload_dir = Path(settings.file_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info("College Backend starting up — environment: {}", settings.environment)

    yield

    logger.info("College Backend shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    Called once at import time (by uvicorn or tests).
    """
    app = FastAPI(
        title="College Management API",
        description="Backend for the College Management Flutter app.",
        version="1.0.0",
        lifespan=lifespan,
        # Hide detailed error responses in production
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Static file serving for uploaded files ────────────────────────────────
    # Files are served at /uploads/<filename> — referenced in DB as file_url
    upload_dir = Path(settings.file_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    # ── Domain exception handler ──────────────────────────────────────────────
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """
        Transforms domain exceptions into consistent JSON error responses.
        Stack traces and internal details are never exposed to clients.
        """
        logger.warning(
            "Domain error on {} {}: [{}] {}",
            request.method,
            request.url.path,
            exc.error_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
            },
        )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Render health check endpoint — returns 200 when the server is alive."""
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
