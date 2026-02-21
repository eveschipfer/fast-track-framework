"""
ProductServiceProvider

Owns the full lifecycle of the Product domain:
    register() — binds ProductRepository, ProductService, ProductController
                 into the IoC container (scoped lifetime).
    boot()     — mounts the /products router on the application.

OCP: extending the application with a new domain never requires touching
     this file — create a new provider and add it to DOMAIN_PROVIDERS.
SRP: this file knows only about Product-related wiring.
"""

import logging

from jtc.core import Container, ServiceProvider
from jtc.http import FastTrackFramework

log = logging.getLogger(__name__)


class ProductServiceProvider(ServiceProvider):
    """Registers all Product domain services and mounts the /products router."""

    def register(self, container: Container) -> None:
        from app.repositories.product_repository import ProductRepository
        from app.services.product_service import ProductService
        from app.http.controllers.product_controller import ProductController

        container.register(ProductRepository, scope="scoped")
        container.register(ProductService, scope="scoped")
        container.register(ProductController, scope="scoped")

        log.debug("ProductServiceProvider: registered Repository, Service, Controller")

    def boot(self, container: Container) -> None:
        from app.http.controllers.product_controller import router as product_router

        app = container.resolve(FastTrackFramework)
        app.include_router(product_router, prefix="/api", tags=["Products"])

        log.info("✅ ProductServiceProvider: /api/products mounted")
