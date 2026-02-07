"""
Application Settings (Sprint 7 - Type-Safe Configuration)

This module replaces the old dictionary-based configuration with Pydantic Settings,
providing compile-time type safety and runtime validation while maintaining full
backward compatibility with the existing config('key') syntax.

Key Improvements:
- Type-safe: All config fields have type hints
- Validation: Pydantic validates values at startup
- IDE Support: Autocomplete on all configuration fields
- Backward Compatible: Duck typing with __getitem__ preserves legacy code
- Environment Variables: Automatic loading from .env via pydantic-settings

Usage:
    from workbench.config.settings import settings

    # Type-safe access (recommended)
    app_name = settings.app.name
    debug_mode = settings.app.debug

    # Legacy dot notation (still works!)
    from ftf.config import config
    app_name = config("app.name")  # Uses settings under the hood

    # Container injection (type-safe)
    from workbench.config.settings import AppSettings

    def my_service(settings: AppSettings):
        app_name = settings.app.name
"""

import os
from functools import reduce
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseModelConfig(BaseModel):
    """
    Base configuration model with dict-like access for backward compatibility.

    This implements Duck Typing to allow Pydantic models to behave like dicts,
    ensuring full backward compatibility with existing code that uses config('key').

    Why __getitem__?
        - Legacy code expects: config("database.connections.mysql.host")
        - Pydantic naturally: settings.database.connections.mysql.host
        - __getitem__ bridges the gap without breaking changes

    Educational Note:
        This is a prime example of the Adapter Pattern. We're adapting
        Pydantic's object-oriented API to work with dict-style access
        patterns that were established before the migration.

    Example:
        >>> model = BaseModelConfig(name="Test", value=123)
        >>> model["name"]  # Works like a dict
        'Test'
        >>> model["value"]
        123
    """

    def __getitem__(self, key: str) -> Any:
        """
        Get attribute by key (dict-like access).

        This enables config("app.name") to work with Pydantic models.

        Args:
            key: Attribute name to retrieve

        Returns:
            Any: The attribute value

        Raises:
            KeyError: If key doesn't exist

        Example:
            >>> settings.app["name"]  # Dict-style access
            "Fast Track Framework"
        """
        if not hasattr(self, key):
            raise KeyError(f"'{self.__class__.__name__}' has no key '{key}'")
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get attribute by key with default value.

        This mimics dict.get() for maximum backward compatibility.

        Args:
            key: Attribute name to retrieve
            default: Default value if key doesn't exist

        Returns:
            Any: The attribute value or default

        Example:
            >>> settings.app.get("missing_key", "default")
            'default'
        """
        return getattr(self, key, default)


class DatabaseConnectionConfig(BaseModelConfig):
    """
    Base configuration for a single database connection.

    All connection types share these settings. Specific driver settings
    are defined in the concrete connection classes.

    Attributes:
        driver: Database driver (e.g., "sqlite+aiosqlite", "mysql+aiomysql")
        pool_pre_ping: Verify connections before using them (health check)
        echo: Log all SQL statements (debug mode)

    Example:
        >>> config = DatabaseConnectionConfig(
        ...     driver="sqlite+aiosqlite",
        ...     database="app.db",
        ...     pool_pre_ping=True
        ... )
    """

    driver: str
    pool_pre_ping: bool = True
    echo: bool = False


class SQLiteConfig(DatabaseConnectionConfig):
    """
    SQLite database configuration.

    SQLite is the default database for development and testing.
    It's file-based, so no server is required.

    Attributes:
        database: Path to SQLite database file (relative to project root)

    Environment Variables:
        DB_DATABASE: Path to database file (default: "workbench/database/app.db")
        DB_ECHO: Enable SQL logging (default: false)

    Example:
        >>> sqlite_config = SQLiteConfig(
        ...     driver="sqlite+aiosqlite",
        ...     database="workbench/database/app.db"
        ... )
    """

    database: str


class MySQLConfig(DatabaseConnectionConfig):
    """
    MySQL/MariaDB database configuration.

    For production deployments using MySQL or MariaDB.

    Attributes:
        host: Database server hostname
        port: Database server port (default: 3306)
        database: Database name
        username: Database user
        password: Database password
        pool_size: Number of permanent connections (default: 10)
        max_overflow: Extra connections beyond pool_size (default: 20)
        pool_recycle: Recycle connections after N seconds (default: 3600)

    Environment Variables:
        DB_HOST: MySQL server host (default: localhost)
        DB_PORT: MySQL server port (default: 3306)
        DB_DATABASE: Database name
        DB_USERNAME: Database user
        DB_PASSWORD: Database password
        DB_POOL_SIZE: Connection pool size (default: 10)
        DB_MAX_OVERFLOW: Max overflow connections (default: 20)
        DB_POOL_RECYCLE: Connection recycle time (default: 3600)
        DB_ECHO: Enable SQL logging (default: false)

    Example:
        >>> mysql_config = MySQLConfig(
        ...     driver="mysql+aiomysql",
        ...     host="localhost",
        ...     port=3306,
        ...     database="fast_track",
        ...     username="app_user",
        ...     password="secret"
        ... )
    """

    host: str = "localhost"
    port: int = 3306
    database: str
    username: str
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600


class PostgreSQLConfig(DatabaseConnectionConfig):
    """
    PostgreSQL database configuration.

    For production deployments using PostgreSQL.

    Attributes:
        host: Database server hostname
        port: Database server port (default: 5432)
        database: Database name
        username: Database user
        password: Database password
        pool_size: Number of permanent connections (default: 10)
        max_overflow: Extra connections beyond pool_size (default: 20)
        pool_recycle: Recycle connections after N seconds (default: 3600)

    Environment Variables:
        DB_HOST: PostgreSQL server host (default: localhost)
        DB_PORT: PostgreSQL server port (default: 5432)
        DB_DATABASE: Database name
        DB_USERNAME: Database user
        DB_PASSWORD: Database password
        DB_POOL_SIZE: Connection pool size (default: 10)
        DB_MAX_OVERFLOW: Max overflow connections (default: 20)
        DB_POOL_RECYCLE: Connection recycle time (default: 3600)
        DB_ECHO: Enable SQL logging (default: false)

    Example:
        >>> postgres_config = PostgreSQLConfig(
        ...     driver="postgresql+asyncpg",
        ...     host="localhost",
        ...     port=5432,
        ...     database="fast_track",
        ...     username="postgres",
        ...     password="secret"
        ... )
    """

    host: str = "localhost"
    port: int = 5432
    database: str
    username: str
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600


class DatabaseConnectionsConfig(BaseModelConfig):
    """
    All database connection configurations.

    This model contains all available database connections.
    The 'default' setting in DatabaseConfig determines which one is used.

    Attributes:
        sqlite: SQLite configuration (development/testing)
        mysql: MySQL configuration (production)
        postgresql: PostgreSQL configuration (production)

    Example:
        >>> connections = DatabaseConnectionsConfig(
        ...     sqlite=SQLiteConfig(driver="sqlite+aiosqlite", database="app.db"),
        ...     mysql=MySQLConfig(...),
        ...     postgresql=PostgreSQLConfig(...)
        ... )
    """

    sqlite: SQLiteConfig
    mysql: MySQLConfig
    postgresql: PostgreSQLConfig


class DatabaseConfig(BaseModelConfig):
    """
    Complete database configuration.

    This model contains all database settings including the default connection
    and all available connection configurations.

    Attributes:
        default: Default connection name (sqlite, mysql, or postgresql)
        connections: All available connection configurations
        migrations: Migration settings
        redis: Redis configuration (for cache, queue, sessions)

    Environment Variables:
        DB_CONNECTION: Default database driver (default: sqlite)
        DB_DATABASE: Database name/path
        DB_HOST: Database host (mysql/postgresql only)
        DB_PORT: Database port (mysql/postgresql only)
        DB_USERNAME: Database username (mysql/postgresql only)
        DB_PASSWORD: Database password (mysql/postgresql only)
        DB_POOL_SIZE: Connection pool size (default: 10)
        DB_MAX_OVERFLOW: Max overflow connections (default: 20)
        DB_POOL_RECYCLE: Connection recycle time (default: 3600)
        DB_ECHO: Enable SQL logging (default: false)
        REDIS_HOST: Redis host (default: localhost)
        REDIS_PORT: Redis port (default: 6379)
        REDIS_PASSWORD: Redis password (default: empty)
        REDIS_DB: Redis database number (default: 0)

    Example:
        >>> db_config = DatabaseConfig(
        ...     default="sqlite",
        ...     connections=DatabaseConnectionsConfig(...)
        ... )
    """

    default: str = Field(default="sqlite", alias="DB_CONNECTION")
    connections: DatabaseConnectionsConfig
    model_config = ConfigDict(populate_by_name=True)


class AuthConfig(BaseModel):
    """
    Authentication settings.

    This model contains authentication configuration including
    JWT secret keys, guard settings, and token expiration.

    Attributes:
        jwt_secret: Secret key for JWT signing
        guards: Default guard to use
        token_expiration: Token expiration time in minutes
        refresh_expiration: Refresh token expiration in days

    Environment Variables:
        AUTH_JWT_SECRET: Secret key for JWT signing (required in production)
        AUTH_GUARDS: Default guard (default: api)
        AUTH_TOKEN_EXPIRATION: Token expiration in minutes (default: 30)
        AUTH_REFRESH_EXPIRATION: Refresh token expiration in days (default: 7)

    Example:
        >>> auth_config = AuthConfig(
        ...     jwt_secret="your-secret-key",
        ...     guards="api",
        ... )
    """

    jwt_secret: str = Field(
        default="INSECURE_DEFAULT_SECRET_KEY_CHANGE_IN_PRODUCTION_DO_NOT_USE_THIS",
        alias="AUTH_JWT_SECRET",
    )
    guards: str = Field(default="api", alias="AUTH_GUARDS")
    token_expiration: int = Field(default=30, alias="AUTH_TOKEN_EXPIRATION")
    refresh_expiration: int = Field(default=7, alias="AUTH_REFRESH_EXPIRATION")


class AppConfig(BaseModelConfig):
    """
    Application core settings.

    This model contains application metadata and runtime settings.

    Attributes:
        name: Application name (used in responses, logs, emails)
        env: Application environment (local, development, staging, production)
        debug: Debug mode (shows detailed errors, NEVER enable in production)
        version: Semantic version for API versioning
        url: Application URL for generating absolute URLs
        timezone: Default timezone for timestamps
        locale: Default language for i18n
        fallback_locale: Fallback language when translation is missing

    Environment Variables:
        APP_NAME: Application name (default: "Fast Track Framework")
        APP_ENV: Environment (default: "production")
        APP_DEBUG: Debug mode (default: false)
        APP_URL: Application URL (default: "http://localhost:8000")
        APP_TIMEZONE: Timezone (default: "UTC")
        APP_LOCALE: Locale (default: "en")

    Example:
        >>> app_config = AppConfig(
        ...     name="Fast Track Framework",
        ...     env="production",
        ...     debug=False
        ... )
    """

    name: str = Field(default="Fast Track Framework", alias="APP_NAME")
    env: str = Field(default="production", alias="APP_ENV")
    debug: bool = Field(default=False, alias="APP_DEBUG")
    version: str = "1.0.0a1"
    url: str = Field(default="http://localhost:8000", alias="APP_URL")
    timezone: str = Field(default="UTC", alias="APP_TIMEZONE")
    locale: str = Field(default="en", alias="APP_LOCALE")
    fallback_locale: str = "en"
    model_config = ConfigDict(populate_by_name=True)


class AppSettings(BaseSettings):
    """
    Main application settings container.

    This is the root settings model that contains all application configuration.
    It automatically loads values from environment variables via pydantic-settings.

    All legacy config('key') calls now route through this Pydantic model,
    providing type safety and validation while maintaining backward compatibility.

    Attributes:
        app: Application configuration (name, env, debug, etc.)
        auth: Authentication configuration (JWT, guards, tokens)
        database: Database configuration (connections, pools, etc.)

    Usage:
        # Type-safe direct access (recommended)
        >>> settings = AppSettings()
        >>> app_name = settings.app.name
        >>> db_driver = settings.database.default

        # Legacy dict-style access (still works via __getitem__)
        >>> settings.app["name"]  # Dict-like access
        "Fast Track Framework"
        >>> settings.database.connections.mysql["host"]
        "localhost"

        # Via config() helper (backward compatible)
        >>> from ftf.config import config
        >>> config("app.name")  # Internally uses settings
        "Fast Track Framework"

        # Container injection (type-safe)
        >>> from workbench.config.settings import AppSettings
        >>> def my_service(settings: AppSettings):
        ...     return settings.app.name

    Pydantic Settings Config:
        - Loads from .env file (if present)
        - Environment variables take precedence over defaults
        - Type validation at startup
        - MyPy/IDE autocomplete support

    Educational Note:
        This migration from dict to Pydantic provides:
        1. Type Safety: Compile-time checking of config keys
        2. Validation: Invalid values caught at startup, not runtime
        3. Documentation: Fields have docs and defaults
        4. Backward Compatibility: Duck typing preserves legacy code

        This is an example of evolutionary architecture - improve the foundation
        without breaking existing code that depends on it.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    app: AppConfig
    database: DatabaseConfig

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize AppSettings with default database connections.

        This method ensures that all three database connection types
        (sqlite, mysql, postgresql) are always available with
        sensible defaults from environment variables.

        Args:
            **kwargs: Additional settings (usually from .env)
        """
        # Set up database connections with environment variables
        connections = DatabaseConnectionsConfig(
            sqlite=SQLiteConfig(
                driver="sqlite+aiosqlite",
                database=os.getenv("DB_DATABASE", "workbench/database/app.db"),
                pool_pre_ping=os.getenv("DB_ECHO", "false").lower() == "true",
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            ),
            mysql=MySQLConfig(
                driver="mysql+aiomysql",
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "3306")),
                database=os.getenv("DB_DATABASE", "fast_track"),
                username=os.getenv("DB_USERNAME", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
                pool_pre_ping=os.getenv("DB_ECHO", "false").lower() == "true",
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            ),
            postgresql=PostgreSQLConfig(
                driver="postgresql+asyncpg",
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_DATABASE", "fast_track"),
                username=os.getenv("DB_USERNAME", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
                pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
                pool_pre_ping=os.getenv("DB_ECHO", "false").lower() == "true",
                echo=os.getenv("DB_ECHO", "false").lower() == "true",
            ),
        )

        database_config = DatabaseConfig(
            default=os.getenv("DB_CONNECTION", "sqlite"),
            connections=connections,
        )

        auth_config = AuthConfig()

        app_config = AppConfig()

        # Merge with provided kwargs
        all_data = {"app": app_config, "auth": auth_config, "database": database_config}
        all_data.update(kwargs)

        super().__init__(**all_data)


# Global settings instance (Singleton pattern)
# This is the single source of truth for application configuration
settings = AppSettings()
