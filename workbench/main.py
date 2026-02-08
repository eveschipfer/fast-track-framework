"""
Workbench Application Entry Point

This is the main entry point for the Fast Track Framework workbench application.
The workbench demonstrates the framework with the Configuration System (Sprint 5.3).

Architecture Evolution:
    Sprint 5.2: Manual provider registration in create_app()
    Sprint 5.3: Automatic provider registration from config/app.py

Configuration System (Sprint 5.3):
    - All settings centralized in workbench/config/*.py
    - Providers auto-registered from config/app.providers
    - Environment-specific configuration via os.getenv()
    - Dot notation access: config("app.name")

The create_app() function is now extremely clean - all configuration
is loaded automatically from workbench/config/*.py files.

Usage:
    uvicorn workbench.main:app --reload
"""

from jtc.config import config
from jtc.http import FastTrackFramework
from jtc.http.middleware import DatabaseSessionMiddleware

# Import app models (registers them with SQLAlchemy)
from app.models import Comment, Post, Product, Role, User  # noqa: F401


def create_app() -> FastTrackFramework:
    """
    Application factory function.

    This function creates and configures the FastTrackFramework application
    instance. With Sprint 5.3, all configuration is loaded automatically:

    1. Config files loaded from workbench/config/*.py
    2. Service providers auto-registered from config("app.providers")
    3. Application bootstraps automatically on first request

    Returns:
        FastTrackFramework: Fully configured application instance

    Example:
        >>> app = create_app()
        >>> # Config loaded, providers registered, ready to serve!

    Sprint 5.2 (Manual):
        app = FastTrackFramework()
        app.register_provider(AppServiceProvider)
        app.register_provider(RouteServiceProvider)

    Sprint 5.3 (Automatic):
        app = FastTrackFramework()
        # Done! Providers loaded from config/app.py
    """
    # Create application instance
    # Sprint 5.3: Config loaded and providers registered automatically
    app = FastTrackFramework()

    # Add database session middleware for proper transaction management
    # This ensures sessions are committed on success, rolled back on error
    app.add_middleware(DatabaseSessionMiddleware)

    # That's it! The framework now:
    # 1. Loads config from workbench/config/*.py
    # 2. Registers providers from config("app.providers")
    # 3. Boots providers on application startup
    # 4. Manages database sessions per request (commit/rollback)

    return app


# Create the application instance
# This is what uvicorn will load when running the server
app = create_app()


# Optional: Keep health endpoint at root level for infrastructure monitoring
# These are common endpoints that don't belong in /api
@app.get("/")
async def root() -> dict[str, str | bool]:
    """
    Root endpoint with API information.

    Now includes configuration-driven values to demonstrate
    the config system working.

    Returns:
        dict: API metadata with config values
    """
    return {
        "message": f"Welcome to {config('app.name', 'Fast Track Framework')}",
        "version": config("app.version", "5.3.0"),
        "environment": config("app.env", "production"),
        "debug": config("app.debug", False),
        "framework": "ftf",
        "architecture": "Service Provider + Configuration System (Sprint 5.3)",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """
    Health check endpoint for infrastructure monitoring.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


@app.get("/config")
async def show_config() -> dict[str, str | int | list[str]]:
    """
    Show current configuration (for debugging).

    WARNING: Do not expose this endpoint in production!
    It may reveal sensitive configuration values.

    Returns:
        dict: Current configuration values
    """
    return {
        "app_name": config("app.name"),
        "environment": config("app.env"),
        "debug": config("app.debug"),
        "version": config("app.version"),
        "locale": config("app.locale"),
        "database_default": config("database.default"),
        "providers_count": len(config("app.providers", [])),
    }
