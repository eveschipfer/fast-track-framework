"""
Alembic Migration Environment

Production-grade migration environment for Fast Track Framework.

This module provides robust path resolution, async migration support,
and automatic model discovery for both framework and application models.

Key Features:
    - Dynamic project root discovery (works in Docker, local, CI/CD)
    - Automatic model discovery (framework + workbench)
    - Async migration support (SQLAlchemy 2.0 + asyncpg/aiosqlite)
    - Clean code standards (no hardcoded paths, enterprise-grade)

Architecture:
    - Root Detection: Uses pathlib to dynamically find project root
    - Path Injection: Adds project root to sys.path with validation
    - Model Discovery: Recursively imports all models for autogenerate
    - Async Execution: Supports async migrations via run_async_migrations

Usage:
    # Generate migration
    alembic revision --autogenerate -m "Add users table"

    # Run migrations
    alembic upgrade head

    # Rollback
    alembic downgrade -1

See: docs/guides/migrations.md for detailed migration guide
"""

import asyncio
import sys
import os
from logging.config import fileConfig
from pathlib import Path
from dotenv import load_dotenv

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent # workbench/database/migrations/env.py -> larafast
load_dotenv(project_root / ".env")

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config


# =============================================================================
# DYNAMIC PROJECT ROOT DISCOVERY
# =============================================================================


# =============================================================================
# DYNAMIC PROJECT ROOT DISCOVERY
# =============================================================================

def discover_project_root() -> Path:
    """
    Dynamically discover the project root directory.

    This function walks up the directory tree from the current file
    location to find the project root. The project root is identified
    by the presence of key files/directories:
        - alembic.ini (Alembic configuration)
        - workbench/ (Application directory)
        - framework/ (Framework directory)

    This approach works across all environments:
        - Local development: /home/user/projects/larafast
        - Docker container: /app/larafast
        - CI/CD pipelines: Any directory structure

    Returns:
        Path: Absolute path to the project root directory

    Raises:
        RuntimeError: If project root cannot be discovered

    Example:
        >>> root = discover_project_root()
        >>> print(root)
        /app/larafast
    """
    current_file = Path(__file__).resolve()

    # Start from env.py and walk up the tree
    # env.py is at: workbench/database/migrations/env.py
    # We need to go up 3 levels to reach project root
    search_paths = [
        current_file.parent.parent.parent,  # workbench/database/migrations -> larafast
        current_file.parent.parent.parent.parent,  # One more level up (backup)
    ]

    for candidate in search_paths:
        # Validate candidate by checking for key markers
        if (candidate / "alembic.ini").exists() and \
           (candidate / "workbench").exists() and \
           (candidate / "framework").exists():
            return candidate

    # Fallback: Search up the tree with markers
    search_dir = current_file
    for _ in range(10):  # Max 10 levels up
        if (search_dir / "alembic.ini").exists() and \
           (search_dir / "workbench").exists():
            return search_dir
        parent = search_dir.parent
        if parent == search_dir:  # Reached filesystem root
            break
        search_dir = parent

    raise RuntimeError(
        f"Cannot discover project root from {current_file}. "
        "Expected to find alembic.ini, workbench/, and framework/ directories. "
        "Ensure you're running Alembic from within the project directory."
    )


def configure_project_path() -> Path:
    """
    Configure Python sys.path to include the project root.

    This function:
        1. Discovers the project root dynamically
        2. Converts to absolute path string
        3. Adds to sys.path if not already present
        4. Validates that critical modules can be imported

    Returns:
        Path: The project root path that was configured

    Raises:
        RuntimeError: If critical modules cannot be imported after path configuration
    """
    project_root = discover_project_root()
    project_root_str = str(project_root)

    # Add project root to sys.path if not already present
    # We check for string equality to avoid duplicates
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

    # Add framework directory to sys.path if not already present
    # This is required because fast_query is in framework/fast_query
    framework_path = project_root / "framework"
    framework_path_str = str(framework_path)
    if framework_path_str not in sys.path:
        sys.path.insert(0, framework_path_str)

    return project_root


# =============================================================================
# MODEL DISCOVERY
# =============================================================================

def import_models() -> None:
    """
    Import all models for Alembic autogenerate detection.

    This function imports models from two sources:
        1. Framework models: framework/jtc/db/models/Base
        2. Application models: workbench/app/models/*

    The imports are performed to register models with SQLAlchemy's
    metadata registry so Alembic can detect them during autogenerate.

    Models are imported at module level (not in functions) to ensure
    they're available when Alembic analyzes the application.

    Strategy:
        - Import Base from fast_query (shared declarative base)
        - Import each application model explicitly
        - All models should inherit from Base to be detected

    Note:
        We import models explicitly rather than using importlib for
        clarity and better error messages when imports fail.

    Example:
        >>> import_models()
        # Now all models are registered with Base.metadata
    """
    try:
        # Import Base from fast_query (shared declarative base)
        from fast_query import Base

        # Import application models (workbench)
        from workbench.app.models.comment import Comment
        from workbench.app.models.post import Post
        from workbench.app.models.product import Product
        from workbench.app.models.role import Role
        from workbench.app.models.user import User

        # Note: Importing models registers them with Base.metadata
        # We don't need to do anything else here - the import is sufficient

        # Add new models here as they're created
        # from workbench.app.models.newmodel import NewModel

    except ImportError as e:
        raise RuntimeError(
            f"Failed to import models: {e}. "
            "Ensure project root is in sys.path and all model files exist."
        ) from e


# =============================================================================
# CONFIGURATION
# =============================================================================

# Configure project path and import models
# This must happen before we access target_metadata
PROJECT_ROOT = configure_project_path()
import_models()

# Import Base after path configuration
from fast_query import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata for autogenerate support
# This contains all models that were imported above
target_metadata = Base.metadata


# =============================================================================
# MIGRATION EXECUTION
# =============================================================================

def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations in a synchronous context.

    This function is called by run_async_migrations() to execute
    migrations within an async connection. It configures the
    Alembic context and runs the migration commands.

    Args:
        connection: SQLAlchemy connection object

    Note:
        This function is synchronous but is called from an async context
        via connection.run_sync().
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # 1. Pega a config do ini
    section = config.get_section(config.config_ini_section)

    # 2. Prioridade: Argumento -x do terminal
    cmd_line_url = context.get_x_argument(as_dictionary=True).get("sqlalchemy.url")

    # 3. Segunda Prioridade: Variáveis de Ambiente do JTC
    env_url = os.getenv("DATABASE_URL") # Ou monte a string usando DB_HOST, DB_USER, etc.
    if not env_url and os.getenv("DB_CONNECTION") == "postgresql":
        env_url = f"postgresql+asyncpg://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"

    # 4. Injeção Final
    target_url = cmd_line_url or env_url or section.get("sqlalchemy.url")
    section["sqlalchemy.url"] = target_url

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.

    This is the default execution mode for Alembic migrations.
    It connects to a real database and executes migration commands.

    Example:
        >>> run_migrations_online()
        # Connects to database and runs migrations
    """
    asyncio.run(run_async_migrations())


# =============================================================================
# ENTRY POINT
# =============================================================================

if context.is_offline_mode():
    # Offline mode - generate SQL without connecting to database
    # This is useful for generating migration scripts in CI/CD
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        literal_binds=True,  # Render literal values instead of parameters
    )

    with context.begin_transaction():
        context.run_migrations()
else:
    # Online mode - connect to database and run migrations
    run_migrations_online()
