"""
Fast Track Framework - HTTP Module

This module provides FastAPI integration with the IoC Container.

Public API:
    FastTrackFramework: Main application kernel with DI integration
    Inject: Dependency injection parameter for FastAPI routes
    scoped_middleware: Middleware for request-scoped dependency management
"""

from .app import FastTrackFramework, scoped_middleware
from .params import Inject

__all__ = [
    "FastTrackFramework",
    "Inject",
    "scoped_middleware",
]
