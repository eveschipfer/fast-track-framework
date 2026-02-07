"""
Route Service Provider

This provider is responsible for registering all application routes.
Similar to Laravel's RouteServiceProvider, it loads route definitions
and configures route groups, middleware, and prefixes.

The boot() method is where route registration happens, because:
1. It runs after all providers have registered their services
2. It can resolve the FastTrackFramework app from the container
3. Route registration is a bootstrapping concern, not a service registration

Example:
    class RouteServiceProvider(ServiceProvider):
        def boot(self, container: Container) -> None:
            # Resolve the app from the container
            app = container.resolve(FastTrackFramework)

            # Import and register API routes
            from workbench.routes.api import api_router
            app.include_router(api_router, prefix="/api", tags=["API"])

            # Import and register web routes
            from workbench.routes.web import web_router
            app.include_router(web_router, prefix="/web", tags=["Web"])
"""

from jtc.core import Container, ServiceProvider
from jtc.http import FastTrackFramework


class RouteServiceProvider(ServiceProvider):
    """
    Route Service Provider.

    This provider is responsible for registering all application routes
    with the FastTrackFramework application instance.
    """

    def register(self, container: Container) -> None:
        """
        Register services in the IoC container.

        Route providers typically don't register services, so this
        method is left empty. All route registration happens in boot().

        Args:
            container: The IoC container instance
        """
        # Route providers don't typically register services
        pass

    def boot(self, container: Container) -> None:
        """
        Bootstrap routes by registering them with the application.

        This method:
        1. Resolves the FastTrackFramework app from the container
        2. Imports the API router from workbench.routes.api
        3. Registers the router with prefix="/api" and tags=["API"]

        Args:
            container: The IoC container instance
        """
        print("🛣️  RouteServiceProvider: Registering routes...")  # noqa: T201

        # Resolve the FastTrackFramework app instance from the container
        app = container.resolve(FastTrackFramework)

        # Import API routes
        from workbench.routes.api import api_router

        # Register API router with /api prefix
        app.include_router(
            api_router,
            prefix="/api",
            tags=["API"],
        )

        print("✅ RouteServiceProvider: API routes registered at /api")  # noqa: T201
