"""
AuthDomainServiceProvider

Owns the HTTP layer of the Auth domain:
    register() — binds AuthService, AuthController (scoped).
    boot()     — mounts the /auth router on the application.

Relationship to AuthServiceProvider:
    AuthServiceProvider      (auth_service_provider.py)
        → infrastructure layer: JWT guard, AuthManager, DatabaseUserProvider.
        → runs at app startup (boot registers singleton guards).

    AuthDomainServiceProvider  (this file)
        → HTTP layer: AuthService (login/refresh/me logic),
                      AuthController (HTTP translation),
                      /api/auth routes.
        → scoped per-request.

SRP: this file knows only about the /auth HTTP wiring.
"""

import logging

from jtc.core import Container, ServiceProvider
from jtc.http import FastTrackFramework

log = logging.getLogger(__name__)


class AuthDomainServiceProvider(ServiceProvider):
    """Registers AuthService, AuthController and mounts the /auth router."""

    def register(self, container: Container) -> None:
        from app.services.auth_service import AuthService
        from app.http.controllers.auth_controller import AuthController

        container.register(AuthService, scope="scoped")
        container.register(AuthController, scope="scoped")

        log.debug("AuthDomainServiceProvider: registered AuthService, AuthController")

    def boot(self, container: Container) -> None:
        from app.http.controllers.auth_controller import router as auth_router

        app = container.resolve(FastTrackFramework)
        app.include_router(auth_router, prefix="/api", tags=["Auth"])

        log.info("✅ AuthDomainServiceProvider: /api/auth mounted")
