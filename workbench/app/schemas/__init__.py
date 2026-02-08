"""
Product Schemas Package

This package contains Pydantic V2 schemas for Product CRUD operations.

Exports:
    - ProductCreate: Create new product schema
    - ProductUpdate: Update existing product schema (partial)
    - ProductResponse: Product response schema
    - ProductListResponse: Paginated product list response

Usage:
    from app.schemas import (
        ProductCreate,
        ProductUpdate,
        ProductResponse,
        ProductListResponse
    )

    # Create product
    @app.post("/products", response_model=ProductResponse)
    async def create(payload: ProductCreate):
        product = await repo.create(payload.model_dump())
        return product

    # List products
    @app.get("/products", response_model=list[ProductResponse])
    async def list():
        return await repo.all()
"""

from .product_schema import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

__all__ = [
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    "ProductListResponse",
]
