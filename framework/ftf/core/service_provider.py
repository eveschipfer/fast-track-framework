"""
Service Provider Base Class

Inspired by Laravel's Service Provider pattern, this module provides
a base class for organizing application bootstrapping and service
registration logic.

Service Providers are the central place to configure your application.
They allow you to:
- Register bindings in the IoC container (register method)
- Bootstrap services after all providers have registered (boot method)

Example:
    class AppServiceProvider(ServiceProvider):
        def register(self, container: Container) -> None:
            # Register services in the container
            container.register(MyService, scope="singleton")

        def boot(self, container: Container) -> None:
            # Bootstrap services (runs after all register() methods)
            # Access container to resolve and configure services
            pass
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ftf.core.container import Container


class ServiceProvider(ABC):
    """
    Base class for service providers.

    Service providers follow a two-phase initialization:
    1. Register phase: Register bindings in the container
    2. Boot phase: Bootstrap services after all providers have registered

    This pattern ensures that all services are registered before any
    bootstrapping logic runs, avoiding dependency resolution issues.
    """

    def register(self, container: "Container") -> None:
        """
        Register services in the IoC container.

        This method runs during the registration phase, before boot().
        Use this to bind interfaces to implementations or register
        singleton services.

        Args:
            container: The IoC container instance

        Example:
            def register(self, container: Container) -> None:
                container.register(DatabaseEngine, scope="singleton")
                container.register(UserRepository, scope="transient")
        """
        pass  # Default implementation does nothing

    def boot(self, container: "Container") -> None:
        """
        Bootstrap services after all providers have registered.

        This method runs during the boot phase, after all register()
        methods have completed. Use this to perform initialization
        logic that depends on registered services.

        Args:
            container: The IoC container instance

        Example:
            def boot(self, container: Container) -> None:
                db = container.resolve(DatabaseEngine)
                db.configure_pool(max_connections=10)
        """
        pass  # Default implementation does nothing


class DeferredServiceProvider(ServiceProvider):
    """
    A service provider that can defer registration until needed.

    Deferred providers are not registered immediately when the application
    boots. Instead, they are registered only when one of their provided
    services is requested from the container.

    This improves boot performance by avoiding unnecessary registrations.

    Attributes:
        provides: List of service types this provider can provide
    """

    provides: list[type] = []

    def __init__(self) -> None:
        """Initialize the deferred service provider."""
        if not self.provides:
            raise ValueError(
                f"{self.__class__.__name__} must define 'provides' attribute"
            )
