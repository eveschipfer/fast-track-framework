"""
Service Providers Package

This package contains all service providers for the workbench application.
Service providers are the central place to configure your application,
register services in the IoC container, and bootstrap application features.

Provider Hierarchy:
    Infrastructure (registered by config/app.py):
        - AppServiceProvider:        Application settings singleton
        - AuthServiceProvider:       JWT guards, AuthManager (infrastructure)
        - RouteServiceProvider:      Domain orchestrator (reads DOMAIN_PROVIDERS)

    Domain (registered by RouteServiceProvider via app/config/providers.py):
        - ProductServiceProvider:    Product repository, service, controller, routes
        - UserServiceProvider:       User repository, service, controller, routes
        - AuthDomainServiceProvider: Auth HTTP layer (service, controller, /api/auth)
"""

from .app_service_provider import AppServiceProvider
from .auth_domain_service_provider import AuthDomainServiceProvider
from .auth_service_provider import AuthServiceProvider
from .product_service_provider import ProductServiceProvider
from .route_service_provider import RouteServiceProvider
from .user_service_provider import UserServiceProvider

__all__ = [
    "AppServiceProvider",
    "AuthDomainServiceProvider",
    "AuthServiceProvider",
    "ProductServiceProvider",
    "RouteServiceProvider",
    "UserServiceProvider",
]
