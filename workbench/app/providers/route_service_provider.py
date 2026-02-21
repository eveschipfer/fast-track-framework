"""
RouteServiceProvider — Generic Domain Orchestrator

Responsibilities (and only these):
    register() — iterate over DOMAIN_PROVIDERS and delegate registration.
    boot()     — configure the router, then iterate over DOMAIN_PROVIDERS
                 and delegate boot.

This provider is intentionally domain-agnostic.  It does not know about
Product, User, Auth, or any future domain.  Adding a new domain only
requires updating app/config/providers.py — this file never changes.

Principles applied:
    OCP — open for extension (add to DOMAIN_PROVIDERS), closed for
          modification (this file stays the same).
    SRP — sole responsibility is orchestrating the provider lifecycle;
          each domain owns its own wiring.

Priority 100 — runs after DatabaseServiceProvider (infrastructure) and
AppServiceProvider (settings), so AsyncSession and AppSettings are
available when domain providers register.
"""

import logging

from jtc.core import Container, ServiceProvider
from jtc.http import FastTrackFramework

log = logging.getLogger(__name__)


class RouteServiceProvider(ServiceProvider):
    """
    Generic orchestrator that delegates to domain-specific providers.

    Domain providers are declared in app/config/providers.DOMAIN_PROVIDERS.
    Instances are created fresh each time to avoid cross-request state.
    """

    priority: int = 100

    def register(self, container: Container) -> None:
        """Instantiate each domain provider and run its register() phase."""
        from app.config.providers import DOMAIN_PROVIDERS

        log.info("🛣️  RouteServiceProvider: registering %d domain provider(s)…",
                 len(DOMAIN_PROVIDERS))

        for provider_class in DOMAIN_PROVIDERS:
            provider = provider_class()
            provider.register(container)
            log.debug("  ↳ %s.register() done", provider_class.__name__)

    def boot(self, container: Container) -> None:
        """Disable slash redirects, then run each domain provider's boot()."""
        from app.config.providers import DOMAIN_PROVIDERS

        app = container.resolve(FastTrackFramework)
        app.router.redirect_slashes = False

        log.info("🛣️  RouteServiceProvider: booting %d domain provider(s)…",
                 len(DOMAIN_PROVIDERS))

        for provider_class in DOMAIN_PROVIDERS:
            provider = provider_class()
            provider.boot(container)
            log.debug("  ↳ %s.boot() done", provider_class.__name__)

        log.info("✅ RouteServiceProvider: all domain routes mounted")
