"""
create_products_table Migration

Sprint 18.2: Create products table migration using Alembic.

This migration creates the products table with all necessary columns,
indexes, and constraints for PostgreSQL.
"""

from typing import Any, Dict

from alembic import op
import sqlalchemy as sa
from sqlalchemy import DateTime

revision = "df60e0e2c075"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create the products table.

    Creates products table with:
    - id (primary key, auto-increment)
    - name (product name, not null)
    - sku (stock keeping unit, unique, indexed)
    - price (product price, not null)
    - created_at (timezone-aware timestamp)
    - updated_at (timezone-aware timestamp)
    - deleted_at (soft delete, nullable)

    PostgreSQL compatible types:
    - VARCHAR for string columns
    - NUMERIC for price (PostgreSQL recommended for financial data)
    - TIMESTAMP WITH TIME ZONE for datetime columns
    """

    op.create_table(
        "products",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "sku",
            sa.String(length=50),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "price",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            onupdate=sa.func.now(),
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        comment="Products table for e-commerce",
    )

    op.create_index(
        "ix_products_sku",
        "products",
        ["sku"],
        unique=True,
    )


def downgrade() -> None:
    """
    Drop the products table.

    This reverses the upgrade operation by removing the products table.
    """

    op.drop_index("ix_products_sku", "products")

    op.drop_table("products")
