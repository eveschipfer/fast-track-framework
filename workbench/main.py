"""
Workbench Application Entry Point

This is the main entry point for the Fast Track Framework workbench application.
The workbench is a sample application that demonstrates how to use the framework
with the Service Provider pattern (Sprint 5.2).

Architecture:
    - Service Providers handle service registration and bootstrapping
    - Routes are defined in workbench/routes/ (similar to Laravel's routes/)
    - Application configuration is centralized in providers

Service Provider Pattern (Sprint 5.2):
    1. register() phase: All providers register their services
    2. boot() phase: All providers bootstrap (configure, mount routes, etc.)

This pattern ensures:
    - Clear separation of concerns
    - Predictable initialization order
    - Easy testing and modularity
    - Laravel-like developer experience

Usage:
    uvicorn workbench.main:app --reload
"""

from ftf.http import FastTrackFramework

# Import service providers
from app.providers import AppServiceProvider, RouteServiceProvider

# Import app models (registers them with SQLAlchemy)
from app.models import Comment, Post, Role, User  # noqa: F401


def create_app() -> FastTrackFramework:
    """
    Application factory function.

    This function creates and configures the FastTrackFramework application
    instance using the Service Provider pattern.

    Returns:
        FastTrackFramework: Configured application instance

    Example:
        >>> app = create_app()
        >>> # App is fully configured with all providers registered and booted
    """
    # Create application instance
    app = FastTrackFramework()

    # Register service providers (Phase 1: Registration)
    # The register() method on each provider is called immediately
    app.register_provider(AppServiceProvider)
    app.register_provider(RouteServiceProvider)

    # Providers will be booted automatically during app startup
    # The boot() method on each provider is called in order

    return app


# Create the application instance
# This is what uvicorn will load when running the server
app = create_app()


# Optional: Keep health endpoint at root level for infrastructure monitoring
# These are common endpoints that don't belong in /api
@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint with API information.

    Returns:
        dict: API metadata and welcome message
    """
    return {
        "message": "Fast Track Framework - Workbench Application",
        "version": "5.2.0",
        "framework": "ftf",
        "description": "A Laravel-inspired micro-framework built on FastAPI",
        "architecture": "Service Provider Pattern (Sprint 5.2)",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Health check endpoint for infrastructure monitoring.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}
