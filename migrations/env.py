"""
Alembic Migration Environment for Fast Track Framework

This module configures Alembic to work with:
- SQLAlchemy 2.0 async engine
- Auto-discovery of models from ftf.models
- Async migration execution

Usage:
    # Create migration
    alembic revision --autogenerate -m "Add users table"

    # Apply migrations
    alembic upgrade head

    # Rollback one migration
    alembic downgrade -1

    # Show current revision
    alembic current

    # Show migration history
    alembic history
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Base for metadata
from ftf.database import Base

# Import all models for auto-discovery
# This ensures Alembic can detect all tables
from ftf.models import *  # noqa: F401, F403

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with an established connection.

    Args:
        connection: SQLAlchemy connection to use for migrations
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async engine.

    In this scenario we need to create an async Engine and associate
    a connection with the context.
    """
    # Get configuration section
    configuration = config.get_section(config.config_ini_section, {})

    # Create async engine
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Run migrations synchronously within async connection
        await connection.run_sync(do_run_migrations)

    # Dispose engine
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    This uses an async engine for migration execution.
    """
    asyncio.run(run_async_migrations())


# Determine mode and run migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
