"""
Service Providers

This module contains service providers that bootstrap and configure
various framework services.

Providers:
    - QueueProvider: Initializes queue system with jobs and schedules

Educational Note:
    The provider pattern is common in Laravel and other frameworks.
    Providers are responsible for "bootstrapping" services - setting
    up configuration, registering dependencies, and initializing resources.
"""

from .queue_provider import QueueProvider

__all__ = [
    "QueueProvider",
]
