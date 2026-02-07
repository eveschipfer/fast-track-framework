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

from jtc.core import Container, ServiceProvider
from jtc.auth import AuthManager
from jtc.auth.guards import JwtGuard


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
        print("🔐 AuthServiceProvider: Registering authentication services...")

        # Register AuthManager as singleton
        container.register(AuthManager, scope="singleton")

        # Initialize AuthManager with Container
        from workbench.config.settings import settings
        AuthManager.initialize(container, default_guard="api")

        # Create JwtGuard with UserProvider and JWT secret
        # Note: UserProvider will be created and registered below
        jwt_secret = settings.auth.jwt_secret

        # Register JwtGuard (will be initialized after UserProvider)
        container.register(JwtGuard, scope="singleton")

        print("  ✓ AuthManager registered (Singleton)")
        print("  ✓ JwtGuard registered (Singleton)")

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
        print("🔐 AuthServiceProvider: Booting authentication services...")

        # Resolve AppSettings to get auth configuration
        from workbench.config.settings import AppSettings, settings

        # Create UserProvider (placeholder - will be implemented fully in future)
        # For now, we'll use a simple implementation that uses repository pattern
        from jtc.auth.user_provider import DatabaseUserProvider

        user_provider = DatabaseUserProvider(container)

        # Register UserProvider
        container.register(type(user_provider), instance=user_provider, scope="singleton")

        # Get JwtGuard from Container
        jwt_guard = container.resolve(JwtGuard)

        # Initialize JwtGuard with UserProvider
        JwtGuard.__init__(jwt_guard, user_provider, settings.auth.jwt_secret)

        # Register JwtGuard in AuthManager
        AuthManager.register("api", jwt_guard)
        AuthManager.register("jwt", jwt_guard)

        print("  ✓ UserProvider registered (DatabaseUserProvider)")
        print("  ✓ JwtGuard initialized with UserProvider")
        print("  ✓ Guards registered in AuthManager (api, jwt)")
