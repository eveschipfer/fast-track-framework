"""
Fast Track Framework - Database Module

This module provides database integration with SQLAlchemy AsyncEngine
and Repository Pattern (NOT Active Record).

Public API:
    create_engine: Create singleton AsyncEngine for connection pooling
    get_engine: Get existing AsyncEngine instance
    get_session: Async context manager for manual session usage
    AsyncSessionFactory: Factory for creating AsyncSession instances
    Base: SQLAlchemy declarative base for models
    BaseRepository: Generic repository with CRUD operations
    QueryBuilder: Fluent query builder for complex queries

WHY REPOSITORY PATTERN:
    - Explicit dependencies (testable)
    - Works in all contexts (HTTP, CLI, jobs, tests)
    - Manual transaction control
    - Type-safe with full MyPy support
    - Avoids Active Record anti-pattern in async Python

See: src/ftf/exercises/sprint_1_2_active_record_trap.py for rationale
"""

from .base import Base
from .engine import create_engine, get_engine
from .query_builder import QueryBuilder
from .repository import BaseRepository
from .session import AsyncSessionFactory, get_session

__all__ = [
    # Engine
    "create_engine",
    "get_engine",
    # Session
    "get_session",
    "AsyncSessionFactory",
    # Models
    "Base",
    # Repository
    "BaseRepository",
    # Query Builder
    "QueryBuilder",
]
