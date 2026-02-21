"""
Auth Service Provider (Sprint 10)

This service provider registers authentication services in the Container.

Architecture:
    - AuthManager: Singleton (main auth entry point)
    - JwtGuard: JWT authentication driver
    - UserProvider: Database user lookup

Sprint 10 Changes:
    - Replaced hardcoded get_current_user() with modular AuthManager
    - Added auth configuration to AppSettings
    - Registered guards for multi-driver support
"""

import logging

from jtc.core import Container, ServiceProvider
from jtc.auth import AuthManager
from jtc.auth.guards import JwtGuard

log = logging.getLogger(__name__)


class AuthServiceProvider(ServiceProvider):
    """
    Authentication Service Provider.

    This provider initializes and registers all authentication services:
    - AuthManager (Singleton)
    - Default Guard (JwtGuard)
    - UserProvider (for database lookup)

    Educational Note:
        This is the Service Provider Pattern from Sprint 5.2.
        Two-phase boot:
        1. register(): Register services in Container
        2. boot(): Bootstrap services (configure, connect, etc.)
    """

    def register(self, container: Container) -> None:
        """
        Register authentication services in Container.

        Args:
            container: IoC Container instance

        Services Registered:
            - AuthManager: Singleton
            - JwtGuard: Singleton (default API guard)
        """
        log.info("🔐 AuthServiceProvider: registering authentication services…")

        # Register AuthManager as singleton
        container.register(AuthManager, scope="singleton")

        # Initialize AuthManager with Container
        from workbench.config.settings import settings
        AuthManager.initialize(container, default_guard="api")

        # Register JwtGuard — initialized with UserProvider in boot()
        container.register(JwtGuard, scope="singleton")

        log.debug("  ↳ AuthManager registered (singleton)")
        log.debug("  ↳ JwtGuard registered (singleton)")

    def boot(self, container: Container) -> None:
        """
        Bootstrap authentication services.

        This method configures and initializes guards after
        all dependencies are registered.

        Args:
            container: IoC Container instance

        Bootstrap Actions:
            - Resolve UserProvider
            - Initialize JwtGuard with UserProvider
            - Register JwtGuard in AuthManager
        """
        log.info("🔐 AuthServiceProvider: booting authentication services…")

        from workbench.config.settings import settings
        from jtc.auth.user_provider import DatabaseUserProvider, UserProvider

        user_provider = DatabaseUserProvider(container)

        # Override both abstract and concrete so JwtGuard can resolve either
        container.override_instance(UserProvider, user_provider)
        container.override_instance(DatabaseUserProvider, user_provider)

        jwt_guard = container.resolve(JwtGuard)
        JwtGuard.__init__(jwt_guard, user_provider, settings.auth.jwt_secret)

        AuthManager.register("api", jwt_guard)
        AuthManager.register("jwt", jwt_guard)

        log.debug("  ↳ DatabaseUserProvider configured")
        log.debug("  ↳ JwtGuard initialized and registered as 'api' + 'jwt'")
        log.info("✅ AuthServiceProvider: authentication infrastructure ready")
