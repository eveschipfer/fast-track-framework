"""
Database Configuration

This file contains all database connection settings for the application.
Multiple connections can be defined, and you can switch between them
at runtime.

Connection Types:
    - sqlite: Lightweight, file-based database (good for development/testing)
    - mysql: MySQL/MariaDB connections
    - postgresql: PostgreSQL connections

Usage:
    from ftf.config import config

    # Get default connection
    default = config("database.default")  # "sqlite"

    # Get specific connection settings
    host = config("database.connections.mysql.host")
    port = config("database.connections.mysql.port")
"""

import os

# Database Configuration Dictionary
config = {
    # Default Database Connection
    # Options: "sqlite", "mysql", "postgresql"
    # This connection will be used by default when no connection is specified
    "default": os.getenv("DB_CONNECTION", "sqlite"),
    # Database Connections
    # Define all available database connections here
    # Each connection can have different settings
    "connections": {
        # SQLite Connection
        # File-based database, no server required
        # Perfect for development and testing
        "sqlite": {
            "driver": "sqlite",
            "database": os.getenv("DB_DATABASE", "workbench.db"),
            # SQLite options
            "prefix": "",  # Table name prefix
            "foreign_key_constraints": True,  # Enforce foreign keys
        },
        # MySQL Connection
        # Requires MySQL server running
        "mysql": {
            "driver": "mysql",
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "3306")),
            "database": os.getenv("DB_DATABASE", "workbench"),
            "username": os.getenv("DB_USERNAME", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "prefix": "",
            # Connection pool settings
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
        },
        # PostgreSQL Connection
        # Requires PostgreSQL server running
        "postgresql": {
            "driver": "postgresql",
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_DATABASE", "workbench"),
            "username": os.getenv("DB_USERNAME", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "charset": "utf8",
            "prefix": "",
            "schema": "public",
            # Connection pool settings
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
        },
    },
    # Migration Settings
    "migrations": {
        "table": "migrations",  # Table to track migrations
        "directory": "migrations",  # Directory containing migration files
    },
    # Redis Connection (for cache, queue, sessions)
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", ""),
        "database": int(os.getenv("REDIS_DB", "0")),
        # Connection pool
        "pool_size": 10,
        "decode_responses": True,
    },
}
