"""
Product Request Schemas

Sprint 18.2: Pydantic schemas for Product CRUD operations.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, EmailStr


class ProductCreate(BaseModel):
    """
    Schema for creating a new Product.

    Validates incoming product data before it reaches the controller.
    """

    name: str = Field(..., min_length=1, max_length=100, description="Product name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly identifier (unique)")
    description: str | None = Field(None, description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    stock: int = Field(default=0, ge=0, description="Stock quantity")

    model_config = ConfigDict(
        json_schema_extra="forbid",
    )


class ProductUpdate(BaseModel):
    """
    Schema for updating an existing Product.

    All fields are optional to support partial updates.
    """

    name: str | None = Field(None, min_length=1, max_length=100, description="Product name")
    slug: str | None = Field(None, min_length=1, max_length=100, description="URL-friendly identifier")
    description: str | None = Field(None, description="Product description")
    price: float | None = Field(None, gt=0, description="Product price")
    stock: int | None = Field(None, ge=0, description="Stock quantity")

    model_config = ConfigDict(
        json_schema_extra="forbid",
    )


class ProductResponse(BaseModel):
    """
    Schema for Product API responses.

    Transforms database model to API response format.
    """

    id: str  # UUID as string
    name: str
    slug: str
    description: str | None = None
    price: float
    stock: int
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None  # Soft delete support

    model_config = ConfigDict(
        from_attributes=True,
    )
