"""fix_products_table_structure

Revision ID: 3865ba6a9637
Revises: df60e0e2c075
Create Date: 2026-02-07 20:53:32.794484

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3865ba6a9637'
down_revision: Union[str, None] = 'df60e0e2c075'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix products table structure to match Product model.

    Changes:
    - Drop old table with wrong structure
    - Recreate with correct columns:
      - id: VARCHAR(36) for UUID (not INTEGER)
      - slug: VARCHAR(100) instead of sku VARCHAR(50)
      - Add description: TEXT (nullable)
      - Add stock: INTEGER (default 0)
    """

    # Drop old table (and its index if exists)
    op.drop_index("ix_products_sku", "products", if_exists=True)
    op.drop_table("products")

    # Recreate with correct structure
    op.create_table(
        "products",
        sa.Column(
            "id",
            sa.String(length=36),
            primary_key=True,
            comment="Unique product identifier (UUID)"
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            comment="Product name"
        ),
        sa.Column(
            "slug",
            sa.String(length=100),
            nullable=False,
            unique=True,
            comment="URL-friendly product identifier"
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Product description"
        ),
        sa.Column(
            "price",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Product price (decimal with 2 places)"
        ),
        sa.Column(
            "stock",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Current stock quantity"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Timestamp when product was created"
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            onupdate=sa.func.now(),
            comment="Timestamp when product was last updated"
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Soft delete timestamp"
        ),
        comment="Products table with UUID support"
    )

    # Create index on slug (unique)
    op.create_index(
        "ix_products_slug",
        "products",
        ["slug"],
        unique=True
    )


def downgrade() -> None:
    """
    Revert to old table structure (INTEGER id, sku field).
    """

    # Drop new table
    op.drop_index("ix_products_slug", "products")
    op.drop_table("products")

    # Recreate old structure
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
    )

    op.create_index(
        "ix_products_sku",
        "products",
        ["sku"],
        unique=True,
    )
