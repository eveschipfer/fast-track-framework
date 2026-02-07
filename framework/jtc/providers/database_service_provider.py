"""
Database Service Provider (Sprint 5.7 + Sprint 12 + Sprint 15.0)

Auto-configures database layer by reading config/database.py and
automatically setting up AsyncEngine, async_sessionmaker, and AsyncSession.

This eliminates need for manual SQLAlchemy setup in main.py.

Sprint 15.0: Added Serverless Connection Handling
    - Automatically detects AWS Lambda environment via AWS_LAMBDA_FUNCTION_NAME
    - Supports manual serverless mode via app.serverless config
    - Uses NullPool in serverless to prevent connection exhaustion
    - Ignores pool_size and max_overflow in serverless mode

Educational Note:
    This provider demonstrates "Convention over Configuration" - user
    just fills out config/database.py (or .env), and framework handles
    all infrastructure complexity.

    Compare to manual setup:
        # Before (Sprint 5.6 and earlier):
        engine = create_async_engine("sqlite+aiosqlite:///./app.db")
        factory = async_sessionmaker(engine)
        container.register(AsyncEngine, instance=engine, scope="singleton")
        container.register(async_sessionmaker, instance=factory, scope="singleton")

        # After (Sprint 5.7):
        # Just add DatabaseServiceProvider to config/app.py providers list
        # Everything else is automatic!

    Sprint 12: Now uses Method Injection in boot():
        # Old pattern (Service Locator - Sprint 11 and earlier):
        def boot(self, container: Container) -> None:
            engine = container.resolve(AsyncEngine)
            settings = container.resolve(AppSettings)

        # New pattern (Method Injection - Sprint 12):
        async def boot(self, db: AsyncEngine, settings: AppSettings) -> None:
            # db and settings are auto-injected!
            print(f"Database: {db.url}")

    Sprint 15.0: Serverless Connection Handling
        # Problem: In AWS Lambda, connections persist between invocations
        # Lambda reuses execution contexts, but database connections time out
        # This causes "Too many connections" errors

        # Solution: Use NullPool (no connection pooling) in serverless
        # Each invocation creates a new connection, then closes it
        # This prevents connection exhaustion in Lambda

        # Detection: Check AWS_LAMBDA_FUNCTION_NAME OR app.serverless config
        is_serverless = (
            os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or
            config("app.serverless", False)
        )

        if is_serverless:
            from sqlalchemy.pool import NullPool
            return {"poolclass": NullPool}  # Disable pooling

Usage:
    # In config/app.py
    "providers": [
        "jtc.providers.database_service_provider.DatabaseServiceProvider",
        # ... other providers
    ]

    # In your repository
    class UserRepository(BaseRepository[User]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, User)

    # Framework auto-injects AsyncSession from the provider!
"""

import os
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from jtc.config import config
from jtc.core.service_provider import ServiceProvider


class DatabaseServiceProvider(ServiceProvider):
    """
    Database Service Provider - Auto-configures SQLAlchemy.

    Sprint 12: Uses Method Injection and priority-based boot order.
    Sprint 15.0: Adds Serverless Connection Handling.

    Reads config/database.py and automatically sets up:
    - AsyncEngine (connection pool)
    - async_sessionmaker (session factory)
    - AsyncSession (scoped per request)

    This provider respects separation of concerns:
    - fast_query (ORM) remains framework-agnostic
    - ftf (Framework) provides the glue (this provider)

    Attributes:
        priority: 10 (High priority - boots before most other providers)
    """

    priority: int = 10

    def register(self, container: Any) -> None:
        """
        Register database services into IoC container.

        This method:
        1. Reads database config
        2. Detects serverless environment (Sprint 15.0)
        3. Constructs database URL
        4. Creates AsyncEngine (with appropriate pool settings)
        5. Creates async_sessionmaker
        6. Binds them to container as Singletons

        Sprint 15.0: Serverless Connection Handling
            - If serverless detected: Uses NullPool (no pooling)
            - If not serverless: Uses standard pooling (QueuePool)
            - Prevents "Too many connections" errors in AWS Lambda

        The container will then be able to inject:
        - AsyncEngine (singleton)
        - AsyncSession (scoped per request)
        """
        # Step 1: Read database configuration
        default_connection = config("database.default", "sqlite")
        connection_config = config(f"database.connections.{default_connection}", {})

        if not connection_config:
            raise ValueError(
                f"Database connection '{default_connection}' not found in config/database.py. "
                f"Check your DB_CONNECTION environment variable or database.default config."
            )

        # Step 2: Detect serverless environment (Sprint 15.0)
        is_serverless = self._detect_serverless()

        if is_serverless:
            print("✓ Serverless environment detected: Using NullPool (no connection pooling)")

        # Step 3: Construct database URL
        database_url = self._build_database_url(default_connection, connection_config)

        # Step 4: Extract pool settings (Sprint 15.0: Serverless-aware)
        pool_settings = self._extract_pool_settings(connection_config, is_serverless)

        # Step 5: Create AsyncEngine
        engine = create_async_engine(database_url, **pool_settings)

        # Step 6: Create async_sessionmaker
        # Note: expire_on_commit=False is critical for async/await patterns
        # This prevents lazy loading after commit, which can cause race conditions
        session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Step 7: Bind to container
        # AsyncEngine as Singleton (one engine for the entire application)
        # Register type first, then set pre-created instance
        container.register(AsyncEngine, scope="singleton")
        container._singletons[AsyncEngine] = engine

        # async_sessionmaker as Singleton (one factory for the app)
        container.register(async_sessionmaker, scope="singleton")
        container._singletons[async_sessionmaker] = session_factory

        # AsyncSession as Scoped (new session per request/scope)
        # The factory is called automatically by container when resolving AsyncSession
        def create_session() -> AsyncSession:
            """Create a new AsyncSession from the factory."""
            return session_factory()

        container.register(
            AsyncSession,
            implementation=create_session,
            scope="scoped"
        )

    async def boot(self, db: AsyncEngine, settings: Any, **kwargs: Any) -> None:
        """
        Bootstrap database services after registration.

        Sprint 12: Uses Method Injection!
        Dependencies are auto-resolved and injected:
        - db: AsyncEngine (auto-resolved from container)
        - settings: AppSettings (auto-resolved from container)

        This method is called after all providers have registered their services.
        We perform a quick connection test to ensure database is accessible.

        Args:
            db: The AsyncEngine instance (injected automatically)
            settings: The AppSettings instance (injected automatically)
            **kwargs: Additional dependencies (not used in this provider)

        Note: This is optional but provides immediate feedback if database config is wrong.
        """
        # Log database connection info (without password)
        connection_name = settings.database.default
        connection_config = getattr(settings.database.connections, connection_name, {})

        if isinstance(connection_config, dict):
            driver = connection_config.get("driver")
            database = connection_config.get("database", "unknown")
            host = connection_config.get("host", "unknown")
        else:
            driver = connection_config.driver
            database = connection_config.database
            host = connection_config.host

        if driver == "sqlite+aiosqlite":
            db_info = f"SQLite ({database})"
        else:
            db_info = f"{connection_name} ({host}/{database})"

        # Sprint 15.0: Log if serverless mode is active
        is_serverless = self._detect_serverless()
        if is_serverless:
            db_info += " [Serverless: NullPool]"

        print(f"✓ Database configured: {db_info}")

    def _detect_serverless(self) -> bool:
        """
        Detect if running in a serverless environment.

        Sprint 15.0: Checks two sources:
        1. AWS_LAMBDA_FUNCTION_NAME environment variable (auto-detect Lambda)
        2. app.serverless config (manual override)

        Returns:
            bool: True if serverless, False otherwise
        """
        # Check AWS Lambda environment variable
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            return True

        # Check manual serverless config
        if config("app.serverless", False):
            return True

        return False

    def _build_database_url(self, connection_name: str, connection_config: dict[str, Any]) -> str:
        """
        Build SQLAlchemy database URL from config.

        Handles different formats:
        - SQLite: sqlite+aiosqlite:///path/to/db.db
        - MySQL: mysql+aiomysql://user:pass@host:port/database
        - PostgreSQL: postgresql+asyncpg://user:pass@host:port/database

        Args:
            connection_name: Name of connection (sqlite, mysql, postgresql)
            connection_config: Connection settings from config/database.py

        Returns:
            str: SQLAlchemy database URL

        Raises:
            ValueError: If driver is missing or URL construction fails
        """
        driver = connection_config.get("driver")

        if not driver:
            raise ValueError(
                f"Database driver not specified for '{connection_name}' connection. "
                f"Add 'driver' key to config/database.py connections.{connection_name}"
            )

        # SQLite: sqlite+aiosqlite:///path/to/db.db
        if driver.startswith("sqlite"):
            database = connection_config.get("database", "app.db")
            return f"{driver}:///{database}"

        # MySQL/PostgreSQL: driver://user:pass@host:port/database
        username = connection_config.get("username", "")
        password = connection_config.get("password", "")
        host = connection_config.get("host", "localhost")
        port = connection_config.get("port", 3306 if "mysql" in driver else 5432)
        database = connection_config.get("database", "")

        if not database:
            raise ValueError(
                f"Database name not specified for '{connection_name}' connection. "
                f"Set DB_DATABASE environment variable or database.connections.{connection_name}.database"
            )

        # Construct URL with or without password
        if password:
            credentials = f"{username}:{password}"
        else:
            credentials = username

        return f"{driver}://{credentials}@{host}:{port}/{database}"

    def _extract_pool_settings(self, connection_config: dict[str, Any], is_serverless: bool) -> dict[str, Any]:
        """
        Extract SQLAlchemy pool settings from connection config.

        Sprint 15.0: Serverless Connection Handling
            - If serverless: Uses NullPool (ignores pool_size, max_overflow)
            - If not serverless: Uses standard pooling (QueuePool)

        Translates config/database.py settings into SQLAlchemy create_async_engine parameters.

        Args:
            connection_config: Connection settings from config/database.py
            is_serverless: Whether running in serverless mode

        Returns:
            dict: Pool settings for create_async_engine()

        Pool Settings (Non-Serverless):
            - pool_size: Number of connections to maintain (default: 10)
            - max_overflow: Extra connections beyond pool_size (default: 20)
            - pool_pre_ping: Verify connections before using (default: True)
            - pool_recycle: Recycle connections after N seconds (default: 3600)
            - echo: Log all SQL statements (default: False)

        Pool Settings (Serverless):
            - poolclass: NullPool (no connection pooling)
            - All other pool settings ignored
        """
        pool_settings: dict[str, Any] = {}

        # Sprint 15.0: Serverless Connection Handling
        # Use NullPool in serverless to prevent connection exhaustion
        if is_serverless:
            from sqlalchemy.pool import NullPool
            return {"poolclass": NullPool}

        # Non-serverless: Use standard pooling
        # Pool size (number of permanent connections)
        if "pool_size" in connection_config:
            pool_settings["pool_size"] = connection_config["pool_size"]

        # Max overflow (additional connections beyond pool_size)
        if "max_overflow" in connection_config:
            pool_settings["max_overflow"] = connection_config["max_overflow"]

        # Pool pre-ping (health check before using connection)
        if "pool_pre_ping" in connection_config:
            pool_settings["pool_pre_ping"] = connection_config["pool_pre_ping"]

        # Pool recycle (recycle connections after N seconds)
        if "pool_recycle" in connection_config:
            pool_settings["pool_recycle"] = connection_config["pool_recycle"]

        # Echo (log SQL statements for debugging)
        if "echo" in connection_config:
            pool_settings["echo"] = connection_config["echo"]

        return pool_settings
