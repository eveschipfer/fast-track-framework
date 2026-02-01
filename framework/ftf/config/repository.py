"""
Configuration Repository

This module provides the central configuration management system for Fast Track Framework,
inspired by Laravel's config system. Configurations are stored as Python files in the
workbench/config/ directory and can be accessed using dot notation.

Key Features:
- Load configuration from Python files (not JSON/YAML)
- Dot notation access: config.get("app.name")
- Singleton pattern: Single config instance per application
- Dynamic loading: Import config files at runtime
- Type-safe: Strict MyPy compatibility
- Graceful defaults: Handle missing keys elegantly

Why Python files?
- Allows using os.getenv() and logic in config
- Type-safe with IDE autocomplete
- Can compute values at load time
- More powerful than static JSON/YAML

Example:
    # workbench/config/app.py
    import os

    return {
        "name": os.getenv("APP_NAME", "FastTrack"),
        "env": os.getenv("APP_ENV", "production"),
        "providers": [
            AppServiceProvider,
            RouteServiceProvider,
        ]
    }

    # Usage
    from ftf.config import config

    app_name = config("app.name")  # "FastTrack"
    env = config("app.env", "local")  # With default
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any


class ConfigRepository:
    """
    Configuration Repository with dot notation access.

    This class manages all application configuration by loading Python files
    from the workbench/config/ directory and providing a unified interface
    for accessing configuration values.

    The repository follows the Singleton pattern to ensure a single source
    of truth for configuration across the application.

    Attributes:
        _configs: Internal storage for all loaded configurations
        _instance: Singleton instance

    Example:
        >>> config = ConfigRepository()
        >>> app_name = config.get("app.name")
        >>> db_driver = config.get("database.default", "sqlite")
    """

    _instance: "ConfigRepository | None" = None
    _configs: dict[str, dict[str, Any]]

    def __new__(cls) -> "ConfigRepository":
        """
        Ensure only one instance exists (Singleton pattern).

        Returns:
            ConfigRepository: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configs = {}
        return cls._instance

    def load_from_directory(self, config_path: str | Path) -> None:
        """
        Load all Python configuration files from a directory.

        This method scans the specified directory for .py files (excluding __init__.py)
        and dynamically imports them. Each config file must return a dictionary.

        Args:
            config_path: Path to the config directory (e.g., "workbench/config")

        Raises:
            FileNotFoundError: If config directory doesn't exist
            ValueError: If a config file doesn't return a dict

        Example:
            >>> config = ConfigRepository()
            >>> config.load_from_directory("workbench/config")
            # Loads app.py, database.py, cache.py, etc.
        """
        config_dir = Path(config_path)

        if not config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {config_dir}")

        # Find all .py files (exclude __init__.py)
        config_files = [
            f for f in config_dir.glob("*.py") if f.name != "__init__.py"
        ]

        for config_file in config_files:
            # Extract config name from filename (e.g., "app.py" -> "app")
            config_name = config_file.stem

            # Load the config module dynamically
            config_dict = self._load_config_module(config_file)

            # Store in internal dict
            self._configs[config_name] = config_dict

    def _load_config_module(self, config_file: Path) -> dict[str, Any]:
        """
        Dynamically load a Python config file and extract its return value.

        Config files must return a dictionary. This allows for dynamic configuration
        using os.getenv(), conditionals, and other Python logic.

        Args:
            config_file: Path to the config file

        Returns:
            dict: The configuration dictionary

        Raises:
            ValueError: If the config file doesn't return a dict
            Exception: If the config file has syntax errors

        Example:
            # workbench/config/app.py
            import os

            return {
                "name": os.getenv("APP_NAME", "FastTrack"),
                "debug": os.getenv("APP_DEBUG", "false") == "true",
            }
        """
        # Create a unique module name to avoid conflicts
        module_name = f"config.{config_file.stem}"

        # Load the module using importlib
        spec = importlib.util.spec_from_file_location(module_name, config_file)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load config file: {config_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise ValueError(f"Error loading config file {config_file}: {e}") from e

        # Config files must have a 'config' dict or return a dict
        # Check for 'config' variable first (preferred)
        if hasattr(module, "config"):
            config_dict = module.config
        # Fall back to checking for a direct return (not standard Python, so we look for __dict__)
        # Since Python modules don't have returns, we'll use a convention:
        # The config file should define a 'config' variable
        else:
            # Look for all non-private variables and build a dict
            config_dict = {
                key: value
                for key, value in module.__dict__.items()
                if not key.startswith("_") and key not in ["os", "Path", "sys"]
            }

        if not isinstance(config_dict, dict):
            raise ValueError(
                f"Config file {config_file} must define a 'config' dict variable"
            )

        return config_dict

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Dot notation allows accessing nested configuration values:
        - "app.name" -> configs["app"]["name"]
        - "database.connections.mysql.host" -> configs["database"]["connections"]["mysql"]["host"]

        Args:
            key: Configuration key in dot notation
            default: Default value if key doesn't exist

        Returns:
            Any: The configuration value or default

        Example:
            >>> config.get("app.name")
            "FastTrack"
            >>> config.get("app.debug", False)
            False
            >>> config.get("database.connections.mysql.host", "localhost")
            "localhost"
        """
        # Split the key by dots
        parts = key.split(".")

        # First part is the config file name
        config_name = parts[0]

        # Check if config file was loaded
        if config_name not in self._configs:
            return default

        # Start with the config dict
        value: Any = self._configs[config_name]

        # Traverse the nested structure
        for part in parts[1:]:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        This method allows runtime modification of configuration values.
        Useful for testing or dynamic configuration changes.

        Args:
            key: Configuration key in dot notation
            value: The value to set

        Example:
            >>> config.set("app.debug", True)
            >>> config.get("app.debug")
            True
        """
        parts = key.split(".")
        config_name = parts[0]

        # Ensure config dict exists
        if config_name not in self._configs:
            self._configs[config_name] = {}

        # Navigate to the nested location
        current = self._configs[config_name]

        # Create nested dicts as needed
        for part in parts[1:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]

        # Set the final value
        if len(parts) > 1:
            current[parts[-1]] = value
        else:
            # Setting top-level config (e.g., "app")
            self._configs[config_name] = value

    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.

        Args:
            key: Configuration key in dot notation

        Returns:
            bool: True if key exists, False otherwise

        Example:
            >>> config.has("app.name")
            True
            >>> config.has("app.nonexistent")
            False
        """
        return self.get(key, object()) is not object()

    def all(self, config_name: str | None = None) -> dict[str, Any]:
        """
        Get all configuration values.

        Args:
            config_name: Optional config file name to get specific config
                        If None, returns all configs

        Returns:
            dict: All configuration values

        Example:
            >>> config.all("app")
            {"name": "FastTrack", "env": "production", ...}
            >>> config.all()
            {"app": {...}, "database": {...}, ...}
        """
        if config_name:
            return self._configs.get(config_name, {})
        return self._configs.copy()

    def flush(self) -> None:
        """
        Clear all loaded configurations.

        Useful for testing when you need to reload configs.

        Example:
            >>> config.flush()
            >>> config.get("app.name")  # None
        """
        self._configs.clear()
