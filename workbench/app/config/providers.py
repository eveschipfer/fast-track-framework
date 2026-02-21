"""
Domain Provider Registry

This is the single place to declare which domain providers the application
should load. The RouteServiceProvider reads DOMAIN_PROVIDERS and delegates
to each entry — it never knows the internals of any domain.

Adding a new domain:
    1. Create app/providers/my_domain_service_provider.py
    2. Append MyDomainServiceProvider to DOMAIN_PROVIDERS below.
    3. Done — no other file needs to change (OCP satisfied).

Order matters: providers are registered and booted top-to-bottom, so place
providers with shared dependencies before the ones that depend on them.
"""

from app.providers.product_service_provider import ProductServiceProvider
from app.providers.user_service_provider import UserServiceProvider
from app.providers.auth_domain_service_provider import AuthDomainServiceProvider

from jtc.core import ServiceProvider

# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN_PROVIDERS
# List of ServiceProvider subclasses that own individual domain registrations.
# ─────────────────────────────────────────────────────────────────────────────
DOMAIN_PROVIDERS: list[type[ServiceProvider]] = [
    ProductServiceProvider,
    UserServiceProvider,
    AuthDomainServiceProvider,
]
