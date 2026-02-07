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
        # Optional: Define boot priority (lower runs first)
        priority = 10

        def register(self, container: Container) -> None:
            # Register services in the container
            container.register(MyService, scope="singleton")

        async def boot(self, db: DatabaseEngine, config: AppSettings) -> None:
            # Sprint 12: Method Injection!
            # Dependencies are automatically resolved and injected.
            await db.connect(config.db.url)
"""

from abc import ABC
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jtc.core.container import Container


class ServiceProvider(ABC):
    """
    Base class for service providers.

    Service providers follow a two-phase initialization:
    1. Register phase: Register bindings in the container
    2. Boot phase: Bootstrap services after all providers have registered

    Attributes:
        priority: Boot order priority (default: 100). Lower numbers boot first.
    """

    # Priority for boot order (Lower = runs first)
    priority: int = 100

    def register(self, container: "Container") -> None:
        """
        Register services in the IoC container.

        This runs BEFORE the boot phase. Only bind services here.
        Do NOT resolve services or perform IO operations in this method.
        """
        pass

    def boot(self) -> Any:
        """
        Bootstrap services after all providers have registered.

        Sprint 12: Supports Method Injection!

        You should override this method with your own signature. The framework
        will inspect your arguments and inject the dependencies automatically.

        Can be synchronous or asynchronous (async def).

        Example:
            async def boot(self, db: AsyncEngine, mailer: Mailer) -> None:
                ...
        """
        pass


class DeferredServiceProvider(ServiceProvider):
    """
    A service provider that can defer registration until needed.

    NOTE: Requires support from the Application Kernel to function correctly.
    """

    provides: list[type] = []

    def __init__(self) -> None:
        if not self.provides:
            raise ValueError(
                f"{self.__class__.__name__} must define 'provides' attribute"
            )