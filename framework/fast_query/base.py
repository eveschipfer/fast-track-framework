"""
SQLAlchemy Declarative Base

Base class for all database models using SQLAlchemy 2.0 style.

All models should inherit from Base to be tracked by Alembic for migrations.

Example:
    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, mapped_column
    from fast_query import Base

    class User(Base):
        __tablename__ = "users"

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))
        email: Mapped[str] = mapped_column(String(100), unique=True)

        def __repr__(self) -> str:
            return f"User(id={self.id}, name={self.name})"

WHY MAPPED TYPES:
    - Type safety: Full MyPy support
    - Modern: SQLAlchemy 2.0 recommended pattern
    - IDE support: Autocomplete and type checking
    - Clear: Explicit column types visible in code
"""

from typing import Any

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all database models.

    Provides:
        - Declarative base for SQLAlchemy ORM
        - Metadata tracking for Alembic migrations
        - Type annotation support (SQLAlchemy 2.0 style)

    Usage:
        1. Create model by inheriting from Base
        2. Define __tablename__ class attribute
        3. Use Mapped[] type hints for columns
        4. Use mapped_column() for column definitions

    Example:
        >>> class Product(Base):
        ...     __tablename__ = "products"
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     name: Mapped[str] = mapped_column(String(200))
        ...     price: Mapped[float] = mapped_column(Numeric(10, 2))
        ...     created_at: Mapped[datetime] = mapped_column(
        ...         DateTime, default=lambda: datetime.now(timezone.utc)
        ...     )

    Type Annotations:
        - Mapped[int]: Integer column
        - Mapped[str]: String column (needs String() for length)
        - Mapped[bool]: Boolean column
        - Mapped[datetime]: DateTime column
        - Mapped[Optional[str]]: Nullable string column

    See: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html
    """

    # Custom type mappings can be added here if needed
    # Example: Map Python types to SQLAlchemy column types
    type_annotation_map: dict[type, Any] = {
        # Add custom mappings here
        # str: String(255),
        # datetime: DateTime(timezone=True),
    }
