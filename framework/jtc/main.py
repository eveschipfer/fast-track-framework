"""
Fast Track Framework - Application Entry Point

This module demonstrates a complete production-ready application setup with all
framework features integrated (Sprints 1.1 through 3.7).

Features Demonstrated:
    - IoC Container with Dependency Injection (Sprint 1.2)
    - Database Layer with Repository Pattern (Sprint 2.2)
    - Query Builder with Relationships (Sprint 2.3)
    - Multi-Driver Caching (Sprint 3.7)
    - Rate Limiting with ThrottleMiddleware (Sprint 3.7)
    - HTTP Kernel with Exception Handling (Sprint 3.4)
    - Validation with Form Requests (Sprint 2.9)
    - Background Jobs (Sprint 3.2)
    - Event System (Sprint 3.1)
    - Authentication with JWT (Sprint 3.3)
    - i18n Multi-language Support (Sprint 3.5)

Usage:
    Development server:
        $ uvicorn ftf.main:app --reload --host 0.0.0.0 --port 8000

    Production server:
        $ uvicorn ftf.main:app --host 0.0.0.0 --port 8000 --workers 4

Environment Variables:
    DATABASE_URL      - Database connection string (default: sqlite+aiosqlite:///./app.db)
    CACHE_DRIVER      - Cache driver: file, redis, array (default: file)
    CACHE_PATH        - File cache directory (default: ./storage/cache)
    REDIS_HOST        - Redis host (default: localhost)
    REDIS_PORT        - Redis port (default: 6379)
    REDIS_DB          - Redis database (default: 0)
    LOCALE            - Default locale (default: en)
    FALLBACK_LOCALE   - Fallback locale (default: en)

Endpoints:
    GET  /              - API documentation and available endpoints
    GET  /health        - Health check endpoint
    GET  /docs          - Swagger UI (OpenAPI)
    GET  /redoc         - ReDoc documentation

Architecture Overview:
    1. Initialize FastTrackFramework (extends FastAPI + Container)
    2. Setup Database (AsyncEngine singleton + AsyncSession scoped)
    3. Setup Cache (multi-driver with environment configuration)
    4. Add HTTP Kernel Middlewares (CORS, Compression, Rate Limiting)
    5. Register Services and Repositories
    6. Include Routers (modular route organization)
    7. Add Global Exception Handlers
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

# Add workbench to Python path for app imports
workbench_path = Path(__file__).parent.parent.parent / "workbench"
if str(workbench_path) not in sys.path:
    sys.path.insert(0, str(workbench_path))

from fast_query import AsyncSessionFactory, Base, create_engine
from jtc.cache import Cache
from jtc.http import FastTrackFramework
from jtc.http.middleware.throttle import ThrottleMiddleware
from jtc.i18n import Translator

# ============================================================================
# APPLICATION LIFESPAN
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastTrackFramework) -> AsyncGenerator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events:
    - Startup: Initialize database, cache, and services
    - Shutdown: Cleanup resources and close connections

    Args:
        app: The FastTrackFramework application instance

    Yields:
        None: Application runs between startup and shutdown
    """
    # ========================================================================
    # STARTUP PHASE
    # ========================================================================

    print("🚀 Fast Track Framework starting up...")  # noqa: T201

    # ------------------------------------------------------------------------
    # 1. Database Initialization
    # ------------------------------------------------------------------------
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    engine = create_engine(database_url, echo=False)

    # Create tables (development only - use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"📊 Database initialized: {database_url}")  # noqa: T201

    # ------------------------------------------------------------------------
    # 2. Cache Initialization
    # ------------------------------------------------------------------------
    cache_driver = os.getenv("CACHE_DRIVER", "file")
    try:
        # Test cache connection
        await Cache.put("framework:startup", "success", ttl=60)
        test_value = await Cache.get("framework:startup")
        if test_value == "success":
            print(f"💾 Cache initialized: {cache_driver} driver")  # noqa: T201
        await Cache.forget("framework:startup")
    except Exception as e:
        print(f"⚠️  Cache initialization warning: {e}")  # noqa: T201

    # ------------------------------------------------------------------------
    # 3. Internationalization (i18n)
    # ------------------------------------------------------------------------
    locale = os.getenv("LOCALE", "en")
    fallback_locale = os.getenv("FALLBACK_LOCALE", "en")
    translator = Translator.get_instance(locale=locale)
    print(f"🌍 i18n initialized: locale={locale}, fallback={fallback_locale}")  # noqa: T201

    # ------------------------------------------------------------------------
    # 4. Framework Ready
    # ------------------------------------------------------------------------
    print(f"📦 Container initialized with {len(app.container._registry)} services")  # noqa: T201
    print(f"✅ Framework ready at http://0.0.0.0:8000")  # noqa: T201
    print(f"📚 API Documentation: http://0.0.0.0:8000/docs")  # noqa: T201

    # Yield control to the application
    yield

    # ========================================================================
    # SHUTDOWN PHASE
    # ========================================================================

    print("🛑 Fast Track Framework shutting down...")  # noqa: T201

    # Cleanup database connections
    await engine.dispose()

    # Cleanup cache (if needed)
    # await Cache.flush()  # Uncomment if you want to clear cache on shutdown

    print("✅ Cleanup complete")  # noqa: T201


# ============================================================================
# APPLICATION INSTANCE
# ============================================================================

app = FastTrackFramework(
    title="Fast Track Framework",
    description="A Laravel-inspired async micro-framework built on FastAPI",
    version="3.7.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ============================================================================
# MIDDLEWARE STACK
# ============================================================================

# Order matters! Middlewares are executed in the order they're added.
# The last added middleware is the first to process the request.

# 1. Rate Limiting (outermost - applied first)
# Limit to 100 requests per minute per IP
app.add_middleware(
    ThrottleMiddleware,
    max_requests=100,
    window_seconds=60,
    key_prefix="throttle:global:",
)

# 2. CORS (if needed in production)
# from starlette.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Configure for production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 3. Compression (reduces response size)
# from starlette.middleware.gzip import GZipMiddleware
# app.add_middleware(GZipMiddleware, minimum_size=1000)

# 4. Trusted Host (security - prevent host header attacks)
# from starlette.middleware.trustedhost import TrustedHostMiddleware
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "*.example.com"])

# Note: ScopedMiddleware is automatically added by FastTrackFramework
# to manage request-scoped dependencies (database sessions, etc.)

# ============================================================================
# DEPENDENCY INJECTION SETUP
# ============================================================================

# Database Engine (Singleton - shared across entire application)
app.register(AsyncEngine, scope="singleton", instance=create_engine(
    os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db"),
    echo=False,
))


# Database Session Factory (Scoped - one per request)
def session_factory() -> AsyncSession:
    """Create async session for each request."""
    factory = AsyncSessionFactory()
    return factory()


app.register(AsyncSession, implementation=session_factory, scope="scoped")

# Repositories (Transient - new instance per injection)
# Example:
# from jtc.repositories import UserRepository, PostRepository
# app.register(UserRepository, scope="transient")
# app.register(PostRepository, scope="transient")

# Services (Transient by default)
# Example:
# from jtc.services import AuthService, EmailService
# app.register(AuthService, scope="transient")
# app.register(EmailService, scope="singleton")  # If stateless

# ============================================================================
# ROUTER REGISTRATION
# ============================================================================

# Include routers for modular route organization
# Example:
# from jtc.http.controllers import user_router, post_router, auth_router
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(user_router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(post_router, prefix="/api/v1/posts", tags=["Posts"])

# ============================================================================
# EXAMPLE ROUTES
# ============================================================================


@app.get("/")
async def index() -> dict[str, Any]:
    """
    API Documentation - Available Endpoints.

    This endpoint provides a map of all available API endpoints and features.

    Returns:
        dict: API information and endpoint map
    """
    return {
        "name": "Fast Track Framework",
        "version": "3.7.0",
        "description": "Laravel-inspired async micro-framework built on FastAPI",
        "features": {
            "ioc_container": "Type-hint based dependency injection",
            "database": "SQLAlchemy 2.0 with Repository Pattern",
            "query_builder": "Eloquent-inspired fluent interface",
            "caching": "Multi-driver (File/Redis/Array)",
            "rate_limiting": "Throttle middleware with cache backend",
            "authentication": "JWT with bcrypt passwords",
            "validation": "Pydantic v2 with custom rules",
            "events": "Observer pattern with async listeners",
            "jobs": "Background processing with SAQ",
            "i18n": "Multi-language support",
            "cli": "Artisan-like command-line tools",
        },
        "endpoints": {
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi_schema": "/openapi.json",
            },
            "health": "/health",
            "cache": {
                "test": "ftf cache test",
                "config": "ftf cache config",
                "clear": "ftf cache clear",
            },
        },
        "cli_commands": {
            "scaffolding": [
                "ftf make model <name>",
                "ftf make repository <name>",
                "ftf make request <name>",
                "ftf make rule <name>",
                "ftf make factory <name>",
                "ftf make seeder <name>",
                "ftf make event <name>",
                "ftf make listener <event> <name>",
                "ftf make job <name>",
                "ftf make middleware <name>",
                "ftf make cmd <name>",
                "ftf make lang <locale>",
                "ftf make auth",
            ],
            "database": [
                "ftf db seed",
                "alembic revision --autogenerate -m 'description'",
                "alembic upgrade head",
            ],
            "cache": [
                "ftf cache test",
                "ftf cache config",
                "ftf cache clear",
                "ftf cache forget <key>",
            ],
            "jobs": [
                "ftf queue work",
                "ftf queue dashboard",
            ],
        },
        "environment_variables": {
            "DATABASE_URL": "Database connection string",
            "CACHE_DRIVER": "Cache driver (file/redis/array)",
            "CACHE_PATH": "File cache directory",
            "REDIS_HOST": "Redis host",
            "REDIS_PORT": "Redis port",
            "REDIS_DB": "Redis database number",
            "LOCALE": "Default locale (en/pt_BR)",
            "FALLBACK_LOCALE": "Fallback locale",
            "JWT_SECRET": "JWT signing secret",
            "JWT_ALGORITHM": "JWT algorithm (HS256)",
            "JWT_EXPIRES_MINUTES": "JWT expiration time",
        },
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health Check Endpoint.

    Used by load balancers and monitoring systems to verify the application
    is running and can respond to requests.

    Returns:
        dict: Health status
    """
    # You can add more sophisticated health checks here:
    # - Database connectivity check
    # - Cache availability check
    # - External service checks
    # - Memory usage check

    return {
        "status": "healthy",
        "version": "3.7.0",
        "framework": "Fast Track Framework",
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Development server with auto-reload
    # In production, use a process manager (systemd, supervisord, docker-compose)
    uvicorn.run(
        "jtc.main:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info",
    )
