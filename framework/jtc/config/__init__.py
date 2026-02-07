"""
Fast Track Framework - Configuration Module

This module provides centralized configuration management inspired by Laravel's config system.
Configurations are loaded from Python files in workbench/config/ and accessed via dot notation.

Public API:
    ConfigRepository: Singleton repository for managing configurations
    config: Global helper function for easy config access

Example:
    >>> from jtc.config import config
    >>> app_name = config("app.name")
    >>> db_host = config("database.connections.mysql.host", "localhost")

Configuration Files:
    Config files are Python modules that define a 'config' dictionary:

    # workbench/config/app.py
    import os
    from app.providers import AppServiceProvider, RouteServiceProvider

    config = {
        "name": os.getenv("APP_NAME", "FastTrack"),
        "env": os.getenv("APP_ENV", "production"),
        "debug": os.getenv("APP_DEBUG", "false") == "true",
        "providers": [
            AppServiceProvider,
            RouteServiceProvider,
        ]
    }

Usage Patterns:
    # Get config value
    app_name = config("app.name")

    # Get with default
    debug_mode = config("app.debug", False)

    # Check if key exists
    if config_repository.has("app.name"):
        ...

    # Get all values from a config file
    app_config = config_repository.all("app")
"""

from typing import Any

from .repository import ConfigRepository

# Create singleton instance
_config_repository = ConfigRepository()


def config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value using dot notation.

    This is a global helper function that provides convenient access to
    the ConfigRepository singleton. It's the primary way to access
    configuration values in the application.

    Args:
        key: Configuration key in dot notation (e.g., "app.name")
        default: Default value if key doesn't exist

    Returns:
        Any: The configuration value or default

    Example:
        >>> from jtc.config import config
        >>> app_name = config("app.name")
        "FastTrack"
        >>> db_driver = config("database.default", "sqlite")
        "sqlite"
        >>> providers = config("app.providers", [])
        [AppServiceProvider, RouteServiceProvider]
    """
    return _config_repository.get(key, default)


def get_config_repository() -> ConfigRepository:
    """
    Get the singleton ConfigRepository instance.

    This function provides access to the repository for advanced operations
    like loading config directories, setting values, or checking key existence.

    Returns:
        ConfigRepository: The singleton instance

    Example:
        >>> from jtc.config import get_config_repository
        >>> repo = get_config_repository()
        >>> repo.load_from_directory("workbench/config")
        >>> repo.has("app.name")
        True
    """
    return _config_repository


__all__ = [
    "ConfigRepository",
    "config",
    "get_config_repository",
]
