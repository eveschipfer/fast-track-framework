"""
Database Configuration (Sprint 5.7 + Sprint 15.0)

This file defines all database connections for your application.
The DatabaseServiceProvider reads this config and automatically sets up:
- AsyncEngine (database connection pool)
- async_sessionmaker (session factory)
- AsyncSession (injected into repositories)

Connection Types:
    - sqlite: Lightweight, file-based database (good for development/testing)
    - mysql: MySQL/MariaDB connections with aiomysql driver
    - postgresql: PostgreSQL connections with asyncpg driver

Sprint 15.0: Serverless Connection Handling
    The DatabaseServiceProvider automatically detects serverless environments and
    uses NullPool (no connection pooling) to prevent "Too many connections"
    errors in AWS Lambda and other serverless platforms.

    Detection:
        1. Automatic: AWS_LAMBDA_FUNCTION_NAME environment variable
        2. Manual: app.serverless = True in config/app.py

    Behavior:
        - Serverless: NullPool (no pooling, connections closed after use)
        - Non-Serverless: QueuePool (standard pooling with pool_size/max_overflow)

Usage:
    from ftf.config import config

    # Get default connection
    default = config("database.default")  # "sqlite"

    # Get specific connection settings
    host = config("database.connections.mysql.host")
    port = config("database.connections.mysql.port")

Environment Variables:
    DB_CONNECTION - Default database driver (sqlite, mysql, postgresql)
    DB_HOST - Database host
    DB_PORT - Database port
    DB_DATABASE - Database name
    DB_USERNAME - Database username
    DB_PASSWORD - Database password
    DB_POOL_SIZE - Connection pool size (default: 10, ignored in serverless)
    DB_MAX_OVERFLOW - Max connections beyond pool_size (default: 20, ignored in serverless)
    DB_ECHO - Enable SQL query logging (true/false)
"""

import os

# Database Configuration
# Sprint 5.3: ConfigRepository expects a 'config' variable
# Sprint 5.7: DatabaseServiceProvider reads this for auto-configuration
config = {
    # Default Database Connection
    # Options: "sqlite", "mysql", "postgresql"
    "default": os.getenv("DB_CONNECTION", "sqlite"),

    # Database Connections
    # Each connection uses async drivers for SQLAlchemy 2.0
    "connections": {
        # SQLite Connection (Development/Testing)
        # File-based, no server required
        "sqlite": {
            "driver": "sqlite+aiosqlite",  # Async SQLite driver
            "database": os.getenv("DB_DATABASE", "workbench/database/app.db"),
            # SQLite-specific options
            "pool_pre_ping": True,  # Verify connections before using
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
        },

        # MySQL Connection (Production)
        # Requires MySQL server and aiomysql driver
        "mysql": {
            "driver": "mysql+aiomysql",  # Async MySQL driver
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "database": os.getenv("DB_DATABASE", "fast_track"),
            "username": os.getenv("DB_USERNAME", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            # Connection pool settings
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_pre_ping": True,  # Health checks before queries
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
        },

        # PostgreSQL Connection (Production)
        # Requires PostgreSQL server and asyncpg driver
        "postgresql": {
            "driver": "postgresql+asyncpg",  # Async PostgreSQL driver
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_DATABASE", "fast_track"),
            "username": os.getenv("DB_USERNAME", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            # Connection pool settings
            "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "echo": os.getenv("DB_ECHO", "false").lower() == "true",
        },
    },

    # Migration Settings
    "migrations": {
        "table": "migrations",
        "directory": "migrations",
    },

    # Redis Connection (for cache, queue, sessions)
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", ""),
        "database": int(os.getenv("REDIS_DB", "0")),
        "pool_size": 10,
        "decode_responses": True,
    },
}
