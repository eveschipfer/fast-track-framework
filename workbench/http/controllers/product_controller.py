"""
Product Controller

Sprint 18.2: PostgreSQL Product CRUD Implementation.
"""

from typing import Any, Optional

from fastapi import APIRouter, status, Depends
from pydantic import EmailStr

from fast_query import RecordNotFound
from app.repositories.product_repository import ProductRepository
from app.http.requests.product_request import ProductCreate, ProductUpdate
from app.models import Product

api_router = APIRouter(prefix="/products", tags=["products"])


def get_product_repository(
    repo: ProductRepository = Depends(ProductRepository),
) -> ProductRepository:
    """
    Dependency injection for ProductRepository.
    
    FastAPI/Starlette dependency injection.
    """
    return repo


@api_router.post("", status_code=status.HTTP_201_CREATED)
async def create(
    request: ProductCreate,
    repo: ProductRepository = Depends(get_product_repository),
) -> dict[str, Any]:
    """
    Create a new Product.

    Validates incoming data, creates product in database,
    and returns the created product with timestamps.

    Args:
        request: Validated product creation data
        repo: Product repository (injected via dependency injection)

    Returns:
        dict: Created product with id, timestamps, and message

    Raises:
        HTTPException: 422 if validation fails
    """
    # Create product from request data
    product = await repo.create({
        "name": request.name,
        "sku": request.sku,
        "price": request.price,
    })

    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "price": product.price,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
        "message": "Product created successfully",
    }


@api_router.get("")
async def index(
    repo: ProductRepository = Depends(get_product_repository),
) -> list[dict[str, Any]]:
    """
    List all products.

    Returns a paginated or complete list of products
    depending on query parameters.

    Args:
        repo: Product repository (injected via dependency injection)

    Returns:
        list: List of product dictionaries

    Example:
        GET /products -> [{"id": 1, "name": "Widget", ...}, ...]
    """
    products = await repo.all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "price": p.price,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        }
        for p in products
    ]


@api_router.get("/{product_id}")
async def show(
    product_id: int,
    repo: ProductRepository = Depends(get_product_repository),
) -> dict[str, Any]:
    """
    Get a single product by ID.

    Returns product details or 404 if not found.

    Args:
        product_id: Primary key of the product
        repo: Product repository (injected via dependency injection)

    Returns:
        dict: Product details

    Raises:
        HTTPException: 404 if product not found

    Example:
        GET /products/1 -> {"id": 1, "name": "Widget", ...}
        GET /products/999 -> {"detail": "Product not found"}
    """
    product = await repo.find_or_fail(product_id)

    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "price": product.price,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
    }


@api_router.put("/{product_id}")
async def update(
    product_id: int,
    request: ProductUpdate,
    repo: ProductRepository = Depends(get_product_repository),
) -> dict[str, Any]:
    """
    Update an existing product.

    Validates incoming data, updates product in database,
    and returns the updated product with timestamps.

    Args:
        product_id: Primary key of the product
        request: Validated product update data (all fields optional)
        repo: Product repository (injected via dependency injection)

    Returns:
        dict: Updated product details

    Raises:
        HTTPException: 404 if product not found
        HTTPException: 422 if validation fails
    """
    # Check product exists
    product = await repo.find_or_fail(product_id)

    # Build update data (only include non-None fields)
    update_data: dict[str, Any] = {
        "name": request.name,
        "sku": request.sku,
        "price": request.price,
    }
    if request.model_config.extra is None or "forbid":
        update_data = {k: v for k, v in update_data.items() if v is not None}

    await repo.update(product_id, update_data)

    return {
        "id": product.id,
        "name": product.name,
        "sku": product.sku,
        "price": product.price,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat(),
        "message": "Product updated successfully",
    }


@api_router.delete("/{product_id}")
async def destroy(
    product_id: int,
    repo: ProductRepository = Depends(get_product_repository),
) -> dict[str, Any]:
    """
    Delete a product (soft delete).

    Deletes a product by ID. If the model has SoftDeletesMixin,
    this sets deleted_at instead of removing the record.

    Args:
        product_id: Primary key of the product
        repo: Product repository (injected via dependency injection)

    Returns:
        dict: Success message

    Raises:
        HTTPException: 404 if product not found

    Example:
        DELETE /products/1 -> {"message": "Product deleted successfully"}
        DELETE /products/999 -> {"detail": "Product not found"}
    """
    product = await repo.find_or_fail(product_id)
    await repo.delete(product_id)

    return {
        "message": "Product deleted successfully",
    }
