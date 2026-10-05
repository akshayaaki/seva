"""
Janseva AI — FastAPI Application Entry Point
Production-ready API with authentication, CORS, rate limiting, and health checks.
"""
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import time

from app.config import get_settings
from app.routes import auth, complaints, incidents, admin

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if get_settings().environment == "development"
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        structlog.get_config()["wrapper_class"]._default_level
        if hasattr(structlog.get_config().get("wrapper_class", object), "_default_level")
        else 0
    ),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info(
        "app_starting",
        environment=settings.environment,
        supabase_url=settings.supabase_url[:30] + "...",
    )

    # Initialize Sentry if configured
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=0.1,
            environment=settings.environment,
        )
        logger.info("sentry_initialized")

    yield  # App is running

    logger.info("app_shutting_down")


# Create FastAPI application
app = FastAPI(
    title="Janseva AI",
    description="AI-powered municipal grievance and field-operations platform. "
                "From citizen voice to civic action.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response: Response = await call_next(request)
    duration = time.time() - start

    if duration > 2.0:  # Log slow requests
        logger.warning(
            "slow_request",
            method=request.method,
            path=request.url.path,
            duration_ms=round(duration * 1000),
            status=response.status_code,
        )

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    logger.error(
        "unhandled_error",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if str(exc) else "An internal error occurred. Please try again."},
    )


# =============================================================================
# ROUTES
# =============================================================================

app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(incidents.router)
app.include_router(admin.router)


# =============================================================================
# HEALTH CHECKS
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "janseva-ai-backend",
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """
    Readiness check — verifies database and essential services.
    Returns 503 if any critical service is unreachable.
    """
    from app.database import get_supabase_admin

    services = {}

    # Check database
    try:
        supabase = get_supabase_admin()
        supabase.table("municipalities").select("id").limit(1).execute()
        services["database"] = "connected"
    except Exception as e:
        services["database"] = f"error: {str(e)[:100]}"

    # Check Gemini AI
    try:
        from app.config import get_settings
        s = get_settings()
        if s.gemini_api_key and s.gemini_api_key != "your-gemini-api-key":
            services["ai"] = "configured"
        else:
            services["ai"] = "not_configured"
    except Exception:
        services["ai"] = "error"

    # Check geocoding
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.nominatim_url}/status")
            services["geocoding"] = "available" if resp.status_code == 200 else "degraded"
    except Exception:
        services["geocoding"] = "unavailable"

    all_ok = all(
        v in ("connected", "configured", "available")
        for v in services.values()
        if v != "not_configured"  # Allow optional services
    )

    status_code = 200 if services.get("database") == "connected" else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_ok else "degraded",
            "version": "1.0.0",
            "database": services.get("database", "unknown"),
            "services": services,
        },
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "Janseva AI",
        "tagline": "From citizen voice to civic action.",
        "version": "1.0.0",
        "docs": "/docs",
    }
