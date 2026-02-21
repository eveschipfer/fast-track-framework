"""
UserServiceProvider

Owns the full lifecycle of the User domain:
    register() — binds UserRepository, UserService, UserController (scoped).
    boot()     — mounts the /users router on the application.

SRP: this file knows only about User-related wiring.
OCP: new domains are added via new providers, never by modifying this file.
"""

import logging

from jtc.core import Container, ServiceProvider
from jtc.http import FastTrackFramework

log = logging.getLogger(__name__)


class UserServiceProvider(ServiceProvider):
    """Registers all User domain services and mounts the /users router."""

    def register(self, container: Container) -> None:
        from app.repositories.user_repository import UserRepository
        from app.services.user_service import UserService
        from app.http.controllers.user_controller import UserController

        container.register(UserRepository, scope="scoped")
        container.register(UserService, scope="scoped")
        container.register(UserController, scope="scoped")

        log.debug("UserServiceProvider: registered Repository, Service, Controller")

    def boot(self, container: Container) -> None:
        from app.http.controllers.user_controller import router as user_router

        app = container.resolve(FastTrackFramework)
        app.include_router(user_router, prefix="/api", tags=["Users"])

        log.info("✅ UserServiceProvider: /api/users mounted")
