"""
Product Model

This module defines a Product model for database operations.
Sprint 18.2: Full PostgreSQL CRUD Implementation with UUID support.

Entity Details:
    - id: UUID (primary key)
    - name: String (max 100)
    - slug: String (max 100, unique, indexed)
    - description: Text (nullable)
    - price: Decimal (precision 10, scale 2)
    - stock: Integer (default 0)
    - created_at: Datetime (auto-generated)
    - updated_at: Datetime (auto-generated)
    - deleted_at: Datetime (soft delete support)
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, Text, Numeric, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from fast_query import Base, SoftDeletesMixin, TimestampMixin

if TYPE_CHECKING:
    pass


class Product(Base, TimestampMixin, SoftDeletesMixin):
    """
    Product model with UUID primary key.

    This model includes automatic timestamp management (created_at, updated_at)
    and soft delete functionality (deleted_at).

    Sprint 18.2:
        - Uses SQLAlchemy 2.0 syntax (Mapped, mapped_column)
        - UUID primary key for distributed systems
        - PostgreSQL compatible types (Numeric for price)
        - Timezone-aware datetimes (datetime.now(UTC))
        - Type-safe with full MyPy support

    Attributes:
        id: UUID primary key (auto-generated)
        name: Product name (required)
        slug: URL-friendly identifier (unique, indexed)
        description: Product description (optional, text)
        price: Product price (required, decimal with 2 decimal places)
        stock: Current stock quantity (default 0)
        created_at: Timestamp when product was created
        updated_at: Timestamp when product was last updated
        deleted_at: Soft delete timestamp (null if not deleted)

    Table:
        products

    Example:
        >>> from uuid import uuid4
        >>> product = Product(
        ...     id=uuid4(),
        ...     name="Widget Pro",
        ...     slug="widget-pro",
        ...     description="Premium widget for professionals",
        ...     price=99.99,
        ...     stock=100
        ... )
        >>> await repo.create(product)
    """

    __tablename__ = "products"

    # Primary Key: UUID for distributed systems
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        comment="Unique product identifier (UUID)"
    )

    # Name: Product name
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Product name"
    )

    # Slug: URL-friendly identifier
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="URL-friendly product identifier"
    )

    # Description: Detailed product information
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Product description"
    )

    # Price: Decimal for financial accuracy
    price: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
        comment="Product price (decimal with 2 places)"
    )

    # Stock: Current inventory count
    stock: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Current stock quantity"
    )
