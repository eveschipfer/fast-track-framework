"""
Application Service Provider (Sprint 7 - Modernized)

This is main service provider for application. It handles
registration and bootstrapping of core application services.

Sprint 7 Changes:
    - Now registers AppSettings in Container for type-safe injection
    - Enables dependency injection of settings throughout application

Similar to Laravel's AppServiceProvider, this is where you would:
- Register singleton services (caching, logging, etc.)
- Bind interfaces to implementations
- Configure application-level services

Example:
    from workbench.config.settings import AppSettings, settings

    class AppServiceProvider(ServiceProvider):
        def register(self, container: Container) -> None:
            # Register settings for type-safe injection
            container.override_instance(AppSettings, settings)

            # Register other services
            container.register(CacheManager, scope="singleton")
            container.register(LogManager, scope="singleton")

        def boot(self, container: Container) -> None:
            # Bootstrap services (runs after all providers registered)
            cache = container.resolve(CacheManager)
            cache.configure(driver="redis")
"""

from jtc.core import Container, ServiceProvider


class AppServiceProvider(ServiceProvider):
    """
    Application Service Provider (Sprint 7).

    This provider is responsible for registering and bootstrapping
    core application services, including the new type-safe
    AppSettings configuration system.

    Sprint 7 Features:
        - Registers AppSettings in Container for DI
        - Enables type-safe config injection throughout app
    """

    priority: int = 50  # Boot before RouteServiceProvider (100)

    def register(self, container: Container) -> None:
        """
        Register services in IoC container (Sprint 7 updated).

        This method runs during the registration phase, before boot().
        Use this to bind interfaces to implementations.

        Args:
            container: The IoC container instance

        Sprint 7 Changes:
            - Now registers AppSettings for type-safe DI
            - Settings can be injected via: settings: AppSettings

        Example:
            def register(self, container: Container) -> None:
                # Register settings (Sprint 7) - pre-constructed instance
                from workbench.config.settings import AppSettings, settings
                container.override_instance(AppSettings, settings)

                # Register other services
                container.register(CacheDriver, RedisDriver, scope="singleton")
                container.register(QueueDriver, RedisQueueDriver, scope="singleton")
        """
        # Sprint 7: Register AppSettings for type-safe injection
        # This enables: settings: AppSettings in any service/route
        from workbench.config.settings import AppSettings, settings
        container.override_instance(AppSettings, settings)

        print("📝 AppServiceProvider: Registering application services...")  # noqa: T201
        print("⚙️  AppSettings registered for type-safe DI")  # noqa: T201

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

