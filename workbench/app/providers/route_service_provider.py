"""
Route Service Provider

This provider is responsible for registering all application routes.
Similar to Laravel's RouteServiceProvider, it loads route definitions
and configures route groups, middleware, and prefixes.

The boot() method is where route registration happens, because:
1. It runs after all providers have registered their services
2. It can resolve to FastTrackFramework app from the container
3. Route registration is a bootstrapping concern, not a service registration

Example:
    class RouteServiceProvider(ServiceProvider):
        def boot(self, container: Container) -> None:
            # Resolve to app from container
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
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.product_repository import ProductRepository


class RouteServiceProvider(ServiceProvider):
    """
    Route Service Provider.

    This provider is responsible for registering all application routes
    with FastTrackFramework application instance.

    Priority:
        100: Register after core services (AppServiceProvider, DatabaseServiceProvider)
    """

    priority: int = 100

    def register(self, container: Container) -> None:
        """
        Register services in IoC container.

        Route providers typically don't register services, but this one
        registers ProductRepository and ProductService for dependency injection.

        Args:
            container: The IoC container instance
        """
        # Register ProductRepository for DI
        # This allows services to inject ProductRepository via Container
        container.register(ProductRepository, scope="scoped")

        # Register ProductService for DI (JTC Design Pattern)
        # This allows controllers to inject ProductService via Inject()
        # Service layer sits between controllers and repositories
        from app.http.controllers.product_controller import ProductService
        container.register(ProductService, scope="scoped")

    def boot(self, container: Container) -> None:
        """
        Bootstrap routes by registering them with the application.

        This method:
        1. Resolves to FastTrackFramework app instance from the container
        2. Imports ProductController router
        3. Registers router with prefix="/api" and tags=["Products"]

        Args:
            container: The IoC container instance
        """
        print("🛣️  RouteServiceProvider: Registering routes...")  # noqa: T201

        # Resolve to FastTrackFramework app instance from the container
        app = container.resolve(FastTrackFramework)

        # Import ProductController router
        # Note: Use 'app' prefix since that's the package name in workbench/
        from app.http.controllers.product_controller import router as product_router

        # Register Product router with /api prefix
        # This creates routes like /api/products, /api/products/{id}, etc.
        app.include_router(
            product_router,
            prefix="/api",
            tags=["Products"],
        )

        print("✅ RouteServiceProvider: Product routes registered at /api/products")  # noqa: T201
        print("✅ RouteServiceProvider: All routes registered successfully")  # noqa: T201
