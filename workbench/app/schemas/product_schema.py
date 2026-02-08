"""
Product Schemas

This module defines Pydantic V2 schemas for Product CRUD operations.
Sprint 18.2: Complete Request/Response DTOs with validation.

Schemas Defined:
    - ProductCreate: Create new product
    - ProductUpdate: Update existing product (partial)
    - ProductResponse: Product data in API responses
    - ProductListResponse: Paginated product list response

Validation:
    - All required fields validated
    - Price must be greater than 0
    - Stock cannot be negative
    - Slug must be alphanumeric with hyphens
    - Name length: 1-100 characters
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    """
    Schema for creating a new Product.

    Validates incoming product data before it reaches the controller.
    All fields are required for creation.

    Attributes:
        name: Product name (1-100 characters)
        slug: URL-friendly identifier (unique)
        description: Product description (optional)
        price: Product price (must be > 0)
        stock: Initial stock quantity (default 0, cannot be negative)

    Validation Rules:
        - name: Required, 1-100 characters
        - slug: Required, 1-100 characters, unique
        - description: Optional, text
        - price: Required, decimal, must be > 0
        - stock: Optional, integer, must be >= 0

    Example:
        >>> payload = ProductCreate(
        ...     name="Widget Pro",
        ...     slug="widget-pro",
        ...     description="Premium widget for professionals",
        ...     price=99.99,
        ...     stock=100
        ... )
        >>> await repo.create(payload.model_dump())
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Product name",
        examples=["Widget Pro"]
    )

    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-friendly identifier (lowercase, alphanumeric, hyphens only)",
        examples=["widget-pro", "premium-widget-2024"]
    )

    description: str | None = Field(
        None,
        description="Product description (optional)",
        examples=["Premium widget for professionals"],
        max_length=5000
    )

    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Product price (must be greater than 0)",
        examples=[99.99, 149.50]
    )

    stock: int = Field(
        default=0,
        ge=0,
        description="Initial stock quantity (default 0, cannot be negative)",
        examples=[100, 50, 0]
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_serialization_defaults_required=True
    )


class ProductUpdate(BaseModel):
    """
    Schema for updating an existing Product.

    All fields are optional to support partial updates.
    Only provided fields will be updated.

    Attributes:
        name: Product name (optional, 1-100 characters)
        slug: URL-friendly identifier (optional, unique)
        description: Product description (optional)
        price: Product price (optional, must be > 0)
        stock: Stock quantity (optional, must be >= 0)

    Validation Rules:
        - All fields are optional
        - Same validation rules as ProductCreate
        - Unchanged fields preserve existing values

    Example:
        >>> payload = ProductUpdate(
        ...     price=89.99,
        ...     stock=150
        ... )
        >>> await repo.update(product_id, payload.model_dump(exclude_unset=True))
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Product name",
        examples=["Widget Pro"]
    )

    slug: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-friendly identifier (lowercase, alphanumeric, hyphens only)",
        examples=["widget-pro", "premium-widget-2024"]
    )

    description: str | None = Field(
        None,
        description="Product description (optional)",
        examples=["Premium widget for professionals"],
        max_length=5000
    )

    price: Decimal | None = Field(
        None,
        gt=0,
        decimal_places=2,
        description="Product price (must be greater than 0)",
        examples=[99.99, 149.50]
    )

    stock: int | None = Field(
        None,
        ge=0,
        description="Stock quantity (default 0, cannot be negative)",
        examples=[100, 50, 0]
    )

    model_config = ConfigDict(
        extra="forbid"
    )


class ProductResponse(BaseModel):
    """
    Schema for Product API responses.

    Transforms database model to API response format.
    Includes timestamps in ISO 8601 format.

    Attributes:
        id: UUID primary key
        name: Product name
        slug: URL-friendly identifier
        description: Product description (optional)
        price: Product price
        stock: Current stock quantity
        created_at: Creation timestamp (ISO 8601)
        updated_at: Last update timestamp (ISO 8601, optional)

    Example:
        >>> response = ProductResponse(
        ...     id="550e8400-e29b-41d4-a716-446655440100",
        ...     name="Widget Pro",
        ...     slug="widget-pro",
        ...     description="Premium widget for professionals",
        ...     price=Decimal("99.99"),
        ...     stock=100,
        ...     created_at=datetime.now(UTC),
        ...     updated_at=datetime.now(UTC)
        ... )
    """

    id: str = Field(
        ...,
        description="Product UUID",
        examples=["550e8400-e29b-41d4-a716-446655440100"]
    )

    name: str = Field(
        ...,
        description="Product name",
        examples=["Widget Pro"]
    )

    slug: str = Field(
        ...,
        description="URL-friendly identifier",
        examples=["widget-pro"]
    )

    description: str | None = Field(
        None,
        description="Product description",
        examples=["Premium widget for professionals"]
    )

    price: Decimal = Field(
        ...,
        description="Product price",
        examples=[Decimal("99.99"), Decimal("149.50")]
    )

    stock: int = Field(
        ...,
        description="Current stock quantity",
        examples=[100, 50, 0]
    )

    created_at: datetime = Field(
        ...,
        description="Creation timestamp (ISO 8601)",
        examples=[datetime.now(UTC)]
    )

    updated_at: datetime | None = Field(
        None,
        description="Last update timestamp (ISO 8601)",
        examples=[datetime.now(UTC)]
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ProductListResponse(BaseModel):
    """
    Schema for paginated product list response.

    Wraps a list of products with metadata.

    Attributes:
        data: List of products
        total: Total number of products
        page: Current page number
        per_page: Items per page

    Example:
        >>> response = ProductListResponse(
        ...     data=[product1, product2],
        ...     total=100,
        ...     page=1,
        ...     per_page=15
        ... )
    """

    data: list[ProductResponse] = Field(
        ...,
        description="List of products"
    )

    total: int = Field(
        ...,
        ge=0,
        description="Total number of products",
        examples=[100]
    )

    page: int = Field(
        ...,
        ge=1,
        description="Current page number",
        examples=[1]
    )

    per_page: int = Field(
        ...,
        ge=1,
        description="Items per page",
        examples=[15]
    )

    model_config = ConfigDict(
        from_attributes=True
    )
