"""
Application Service Provider

This is the main service provider for the application. It handles
registration and bootstrapping of core application services.

Similar to Laravel's AppServiceProvider, this is where you would:
- Register singleton services (caching, logging, etc.)
- Bind interfaces to implementations
- Configure application-level services

Example:
    class AppServiceProvider(ServiceProvider):
        def register(self, container: Container) -> None:
            # Register services in the container
            container.register(CacheManager, scope="singleton")
            container.register(LogManager, scope="singleton")

        def boot(self, container: Container) -> None:
            # Bootstrap services (runs after all providers registered)
            cache = container.resolve(CacheManager)
            cache.configure(driver="redis")
"""

from ftf.core import Container, ServiceProvider


class AppServiceProvider(ServiceProvider):
    """
    Application Service Provider.

    This provider is responsible for registering and bootstrapping
    core application services.
    """

    def register(self, container: Container) -> None:
        """
        Register services in the IoC container.

        This method runs during the registration phase, before boot().
        Use this to bind interfaces to implementations.

        Args:
            container: The IoC container instance

        Example:
            def register(self, container: Container) -> None:
                container.register(CacheDriver, RedisDriver, scope="singleton")
                container.register(QueueDriver, RedisQueueDriver, scope="singleton")
        """
        # Currently empty - services will be registered here in future sprints
        print("📝 AppServiceProvider: Registering application services...")  # noqa: T201

    def boot(self, container: Container) -> None:
        """
        Bootstrap services after all providers have registered.

        This method runs during the boot phase, after all register()
        methods have completed. Use this for initialization logic that
        depends on registered services.

        Args:
            container: The IoC container instance

        Example:
            def boot(self, container: Container) -> None:
                # Configure database connection pool
                db = container.resolve(DatabaseEngine)
                db.configure_pool(max_connections=20)
        """
        # Currently empty - bootstrap logic will be added here
        print("🔧 AppServiceProvider: Bootstrapping application services...")  # noqa: T201
