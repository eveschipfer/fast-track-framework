"""
Fast Track Framework - Application Entry Point

This module provides the main application bootstrap and entry point.

Usage:
    Development server:
        $ uvicorn ftf.main:app --reload --host 0.0.0.0 --port 8000

    Production server:
        $ uvicorn ftf.main:app --host 0.0.0.0 --port 8000 --workers 4

Architecture Overview:
    1. Initialize FastTrackFramework (extends FastAPI + Container)
    2. Add scoped middleware for request-level dependency management
    3. Register services in the container
    4. Include routers (controllers)

This demonstrates the full integration of:
- IoC Container (Sprint 1.2)
- FastAPI Integration (Sprint 2.1)
- Dependency Injection in routes
- Request-scoped lifecycle management
"""

from ftf.http.app import FastTrackFramework, ScopedMiddleware
from ftf.http.controllers.welcome_controller import MessageService, router

# ============================================================================
# APPLICATION BOOTSTRAP
# ============================================================================

# Create application instance
# This initializes both FastAPI and the IoC Container
app = FastTrackFramework(
    title="Fast Track Framework",
    description="A Laravel-inspired micro-framework built on FastAPI",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# MIDDLEWARE SETUP
# ============================================================================

# Add scoped middleware for request-level dependency management
# This ensures scoped dependencies are created per-request and cleaned up
app.add_middleware(ScopedMiddleware)

# ============================================================================
# SERVICE REGISTRATION
# ============================================================================

# Register services in the container
# Scope options:
#   - singleton: One instance for entire application (DB pools, configs)
#   - scoped: One instance per request (DB sessions, auth context)
#   - transient: New instance every time (DTOs, services)

# MessageService: transient scope (new instance per injection)
# In a real app, you might use singleton for stateless services
app.register(MessageService, scope="transient")

# Example of other registrations (commented for reference):
# app.register(Database, PostgresDatabase, scope="singleton")
# app.register(DatabaseSession, scope="scoped")
# app.register(UserRepository, scope="transient")
# app.register(AuthService, scope="scoped")

# ============================================================================
# ROUTER REGISTRATION
# ============================================================================

# Include routers (controllers)
app.include_router(router)

# Example of multiple routers (commented for reference):
# app.include_router(user_router, prefix="/api/v1/users", tags=["users"])
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Run development server
    # Note: In production, use a process manager like systemd or supervisord
    uvicorn.run(
        "ftf.main:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=True,  # Auto-reload on code changes (development only)
        log_level="info",
    )
