"""
Configuration Repository (Sprint 7 - Modernized)

This module provides central configuration management system for Fast Track Framework,
now powered by Pydantic Settings for type-safe configuration.

SPRINT 7 MIGRATION:
    Before: Dictionary-based config loaded from Python files
    After: Pydantic Settings with automatic environment variable loading

Key Features:
- Type-safe configuration with Pydantic validation
- Dot notation access: config("app.name") - backward compatible
- Singleton pattern: Single config instance per application
- Duck typing: __getitem__ allows dict-like access on Pydantic models
- Automatic environment variable loading via pydantic-settings
- Full backward compatibility with existing code

Architecture (Sprint 7+):
    Pydantic Settings (Type-Safe)
        ↓
    BaseModelConfig (Duck Typing Adapter)
        ↓
    config() Helper (Legacy Compatibility)

Why This Migration?
    - Type Safety: Compile-time checking of config keys
    - Validation: Invalid values caught at startup
    - IDE Support: Autocomplete on all config fields
    - Backward Compatible: Duck typing preserves legacy code

Example:
    # Type-safe direct access (recommended)
    from workbench.config.settings import settings

    app_name = settings.app.name
    debug_mode = settings.app.debug

    # Legacy dot notation (still works!)
    from jtc.config import config

    app_name = config("app.name")  # Internally uses settings
    env = config("app.env", "local")  # With default

    # Dict-style access via Duck Typing
    settings.app["name"]  # Works like a dict!
"""

import functools
from typing import Any


class ConfigRepository:
    """
    Configuration Repository with Pydantic Settings backend (Sprint 7).

    This class provides a unified interface for accessing configuration
    values through modern Pydantic Settings system while maintaining
    full backward compatibility with legacy code.

    Architecture:
        Pydantic Settings (Type-Safe) → ConfigRepository (Legacy Proxy) → Application

    The repository follows Singleton pattern to ensure a single source
    of truth for configuration across application.

    Attributes:
        _instance: Singleton instance
        _settings: Reference to global settings instance
        _overrides: Runtime configuration overrides (for testing)

    Example:
        >>> from jtc.config import config
        >>> app_name = config("app.name")  # Uses Pydantic under hood
        >>> db_driver = config("database.default", "sqlite")
    """

    _instance: "ConfigRepository | None" = None
    _settings: Any = None
    _overrides: dict[str, Any] = {}

    def __new__(cls) -> "ConfigRepository":
        """
        Ensure only one instance exists (Singleton pattern).

        Returns:
            ConfigRepository: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Import settings here to avoid circular imports at module level
            from workbench.config.settings import settings
            cls._instance._settings = settings
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation (Sprint 7 modernized).

        This method uses functools.reduce and getattr to navigate Pydantic
        settings object, supporting arbitrary nesting depth while maintaining
        backward compatibility with existing code.

        Navigation Algorithm:
            - "app.name" → settings.app.name
            - "database.connections.mysql.host" → settings.database.connections.mysql.host
            - If key exists in overrides, returns override value
            - If any intermediate value is None, returns default

        Args:
            key: Configuration key in dot notation
            default: Default value if key doesn't exist or is None

        Returns:
            Any: The configuration value or default

        Example:
            >>> config.get("app.name")
            "Fast Track Framework"
            >>> config.get("app.debug", False)
            False
            >>> config.get("database.connections.mysql.host", "localhost")
            "localhost"

        Educational Note:
            functools.reduce() allows us to navigate nested attributes
            dynamically without knowing depth at compile time.

            functools.reduce(getattr, [obj, "a", "b", "c"], default)
            # Equivalent to: obj.a.b.c (but with None checking)
        """
        # Check overrides first (highest priority)
        if key in self._overrides:
            return self._overrides[key]

        # Split key by dots
        parts = key.split(".")

        if not parts:
            return default

        # Start with settings object
        obj = self._settings

        # Navigate through nested attributes using reduce
        # functools.reduce applies getattr() recursively: getattr(getattr(obj, 'a'), 'b')
        # We also check if intermediate value is not None
        try:
            result = functools.reduce(
                lambda acc, part: getattr(acc, part, None) if acc is not None else None,
                parts,
                obj
            )
        except AttributeError:
            return default

        # Return result or default if None
        return result if result is not None else default

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation (for runtime overrides).

        Since Pydantic models are immutable by default, this stores runtime
        overrides in a separate dictionary. Overrides have higher priority
        than Pydantic settings.

        Use Cases:
            - Testing: Override configuration values without touching .env
            - Feature Flags: Enable/disable features at runtime
            - Dynamic Configuration: Change settings without restart

        Args:
            key: Configuration key in dot notation
            value: The value to set

        Example:
            >>> config.set("app.debug", True)
            >>> config.get("app.debug")
            True
            >>> config.flush()  # Clear all overrides
            >>> config.get("app.debug")  # Back to original value

        Educational Note:
            Pydantic Settings are designed to be immutable after initialization
            (loaded from environment). This method provides a mutable overlay
            for special cases like testing without breaking the type-safety
            guarantees of the underlying Pydantic model.
        """
        self._overrides[key] = value

    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.

        This method checks both Pydantic settings and runtime overrides.

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
        Get all configuration values as dict.

        This method converts Pydantic models to dictionaries using model_dump(),
        making it compatible with code that expects dictionary access.

        Args:
            config_name: Optional config section name
                        If None, returns all configs

        Returns:
            dict: All configuration values

        Example:
            >>> config.all("app")
            {"name": "Fast Track Framework", "env": "production", ...}
            >>> config.all()
            {"app": {...}, "database": {...}, ...}

        Educational Note:
            Pydantic's model_dump() method converts the model to a dictionary,
            preserving all nested structure and types. This provides full backward
            compatibility with code that expects dictionary-based configuration.
        """
        from pydantic import BaseModel

        # If specific config section requested
        if config_name:
            section = functools.reduce(
                lambda acc, part: getattr(acc, part, None) if acc is not None else None,
                config_name.split("."),
                self._settings
            )
            if section is not None and isinstance(section, BaseModel):
                return section.model_dump()
            return {}

        # Return all configuration as nested dict
        return self._settings.model_dump()

    def flush(self) -> None:
        """
        Clear all runtime configuration overrides.

        This does NOT reset Pydantic settings (which are loaded from
        environment variables at startup). It only clears overrides set via
        config.set().

        Useful for testing when you need to reset configuration state.

        Example:
            >>> config.set("app.debug", True)
            >>> config.get("app.debug")
            True
            >>> config.flush()
            >>> config.get("app.debug")  # Back to original value from .env

        Educational Note:
            Pydantic Settings cannot be "reloaded" during runtime because
            they're designed to be loaded once at application startup from
            environment variables. This method provides a way to reset the
            mutable override layer without restarting the application.
        """
        self._overrides.clear()
