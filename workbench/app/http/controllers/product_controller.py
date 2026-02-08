"""
Product Controller - JTC Design Pattern

This controller demonstrates the Fast Track Framework (jtc) design:
1. Service Layer (ProductService) - Business logic and data transformation
2. Router Setup (APIRouter) - Route configuration with tags
3. Route Handlers - Thin controllers using Inject() for DI

Architecture:
    Request → Route Handler → Service → Repository → Database

The controller is responsible for:
- HTTP concerns (request/response)
- Route definitions
- Delegating to service layer

The service is responsible for:
- Business logic
- Data validation and transformation
- Coordinating repository operations
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Response, status

from jtc.http import Inject

from app.repositories.product_repository import ProductRepository
from app.schemas import ProductResponse
from app.http.requests.store_product_request import StoreProductRequest
from app.http.requests.update_product_request import UpdateProductRequest
from fast_query import CursorPaginator, RecordNotFound
from jtc.validation import Validate


# ============================================================================
# SERVICE LAYER
# ============================================================================


class ProductService:
    """
    Product Service - Business logic layer.

    This service encapsulates all product-related business logic,
    acting as a bridge between controllers and repositories.

    Design Pattern (JTC Framework):
        - Service receives Repository via dependency injection
        - Service handles business logic and data transformation
        - Service is registered in Container with 'scoped' lifetime
        - Controllers inject Service, not Repository directly

    Why Services?
        - Single Responsibility: Controllers handle HTTP, Services handle logic
        - Testability: Services can be tested without HTTP layer
        - Reusability: Same service can be used by multiple controllers
        - Domain Logic: Business rules live in one place
    """

    def __init__(self, repo: ProductRepository):
        """
        Initialize ProductService with injected repository.

        Args:
            repo: ProductRepository (injected automatically by Container)
        """
        self.repo = repo

    async def get_all_products(self) -> list[dict[str, Any]]:
        """
        Get all products.

        Returns:
            List of product dictionaries
        """
        products = await self.repo.all()
        return [ProductResponse.model_validate(product).model_dump() for product in products]

    async def get_paginated_products(
        self, per_page: int = 15, cursor: str | None = None
    ) -> dict[str, Any]:
        """
        Get cursor-paginated products.

        Uses O(1) cursor pagination (WHERE id > :cursor) instead of
        O(n) offset pagination (COUNT + OFFSET). Single query, no COUNT.

        Args:
            per_page: Items per page (default: 15, max: 100)
            cursor: Last product ID from previous page (None for first page)

        Returns:
            Dictionary with 'data' (serialized products) and 'meta' (cursor info)
        """
        paginator: CursorPaginator = await self.repo.query().cursor_paginate(
            per_page=per_page, cursor=cursor, cursor_column="id"
        )

        return {
            "data": [
                ProductResponse.model_validate(product).model_dump()
                for product in paginator.items
            ],
            "meta": {
                "per_page": paginator.per_page,
                "next_cursor": paginator.next_cursor,
                "has_more_pages": paginator.has_more_pages,
                "count": paginator.count,
            },
        }

    async def create_product(self, data: StoreProductRequest) -> dict[str, Any]:
        """
        Create a new product.

        Args:
            data: Validated product creation data (includes unique slug check)

        Returns:
            Created product dictionary
        """
        from app.models import Product

        # Create Product instance from validated data
        product = Product(**data.model_dump())

        # Persist to database
        product = await self.repo.create(product)
        return ProductResponse.model_validate(product).model_dump()

    async def get_product_by_id(self, product_id: str) -> dict[str, Any]:
        """
        Get product by ID.

        Args:
            product_id: Product UUID

        Returns:
            Product dictionary

        Raises:
            HTTPException: 404 if product not found
        """
        try:
            product = await self.repo.find_or_fail(product_id)
            return ProductResponse.model_validate(product).model_dump()
        except RecordNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )

    async def get_product_by_slug(self, slug: str) -> dict[str, Any]:
        """
        Get product by slug.

        Args:
            slug: Product slug

        Returns:
            Product dictionary

        Raises:
            HTTPException: 404 if product not found
        """
        product = await self.repo.find_by_slug(slug)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with slug '{slug}' not found"
            )
        return ProductResponse.model_validate(product).model_dump()

    async def update_product(self, product_id: str, data: UpdateProductRequest) -> dict[str, Any]:
        """
        Update product (full update).

        Args:
            product_id: Product UUID
            data: Update data (includes unique slug check)

        Returns:
            Updated product dictionary

        Raises:
            HTTPException: 404 if product not found
        """
        try:
            # Get existing product (raises if not found)
            product = await self.repo.find_or_fail(product_id)

            # Set product ID for unique validation (exclude current product)
            data.set_product_id(product_id)

            # Update all fields with new data
            update_data = data.model_dump(exclude_unset=False)
            for key, value in update_data.items():
                if not key.startswith('_'):  # Skip private attributes
                    setattr(product, key, value)

            # Commit changes
            product = await self.repo.update(product)
            return ProductResponse.model_validate(product).model_dump()
        except RecordNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )

    async def partial_update_product(self, product_id: str, data: UpdateProductRequest) -> dict[str, Any]:
        """
        Partially update product (PATCH).

        Args:
            product_id: Product UUID
            data: Partial update data (includes unique slug check)

        Returns:
            Updated product dictionary

        Raises:
            HTTPException: 404 if product not found
        """
        try:
            # Get existing product
            product = await self.repo.find_or_fail(product_id)

            # Set product ID for unique validation (exclude current product)
            data.set_product_id(product_id)

            # Update only provided fields (exclude_unset=True)
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if not key.startswith('_'):  # Skip private attributes
                    setattr(product, key, value)

            # Commit changes
            product = await self.repo.update(product)
            return ProductResponse.model_validate(product).model_dump()
        except RecordNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )

    async def delete_product(self, product_id: str) -> None:
        """
        Delete product.

        Args:
            product_id: Product UUID

        Raises:
            HTTPException: 404 if product not found
        """
        try:
            await self.repo.find_or_fail(product_id)
            await self.repo.delete(product_id)
        except RecordNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )

    async def search_products(self, query: str) -> list[dict[str, Any]]:
        """
        Search products by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching products
        """
        products = await self.repo.search(query)
        return [ProductResponse.model_validate(product).model_dump() for product in products]

    async def get_low_stock_products(self, threshold: int = 10) -> list[dict[str, Any]]:
        """
        Get products with low stock.

        Args:
            threshold: Stock threshold (default: 10)

        Returns:
            List of low-stock products
        """
        products = await self.repo.low_stock(threshold)
        return [ProductResponse.model_validate(product).model_dump() for product in products]


# ============================================================================
# ROUTER SETUP
# ============================================================================

# Create router (will be included in main app via RouteServiceProvider)
router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={
        404: {"description": "Product not found"},
        422: {"description": "Validation error"},
    },
)


# ============================================================================
# ROUTE HANDLERS
# ============================================================================


@router.get("/")
async def index(
    per_page: int = Query(15, ge=1, le=100, description="Items per page (max 100)"),
    cursor: str | None = Query(None, description="Cursor (last product ID from previous page)"),
    service: ProductService = Inject(ProductService)
) -> dict[str, Any]:
    """
    List products with cursor pagination.

    Uses O(1) cursor-based pagination instead of offset-based.
    Pass the `next_cursor` from the previous response to get the next page.

    Args:
        per_page: Items per page (default: 15, minimum: 1, maximum: 100)
        cursor: Last product ID from previous page (omit for first page)
        service: ProductService (injected via Container)

    Returns:
        Paginated response with 'data' and 'meta' keys

    Example:
        First page:  GET /api/products?per_page=15
        Next page:   GET /api/products?per_page=15&cursor=550e8400-e29b-41d4-a716-446655440100
        Response: {
            "data": [ ... ],
            "meta": {
                "per_page": 15,
                "next_cursor": "660f9500-f30c-52e5-b827-557766551211",
                "has_more_pages": true,
                "count": 15
            }
        }
    """
    return await service.get_paginated_products(per_page=per_page, cursor=cursor)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def store(
    payload: StoreProductRequest = Validate(StoreProductRequest),
    service: ProductService = Inject(ProductService)
) -> dict[str, Any]:
    """
    Create a new product.

    Args:
        payload: Product creation data (validated by FormRequest with unique slug check)
        service: ProductService (injected via Container)

    Returns:
        Created product

    Raises:
        422: Validation error (duplicate slug, invalid price, etc.)

    Example:
        POST /api/products
        Body: {
            "name": "Widget Pro",
            "slug": "widget-pro",
            "description": "Premium widget",
            "price": 99.99,
            "stock": 100
        }
    """
    return await service.create_product(payload)


@router.get("/{id}", response_model=ProductResponse)
async def show(
    id: str,
    service: ProductService = Inject(ProductService)
) -> dict[str, Any]:
    """
    Get product by ID.

    Args:
        id: Product UUID
        service: ProductService (injected via Container)

    Returns:
        Product details

    Raises:
        HTTPException: 404 if product not found
    """
    return await service.get_product_by_id(id)


@router.get("/slug/{slug}", response_model=ProductResponse)
async def show_by_slug(
    slug: str,
    service: ProductService = Inject(ProductService)
) -> dict[str, Any]:
    """
    Get product by slug.

    Args:
        slug: Product slug (URL-friendly identifier)
        service: ProductService (injected via Container)

    Returns:
        Product details

    Raises:
        HTTPException: 404 if product not found

    Example:
        GET /api/products/slug/widget-pro
    """
    return await service.get_product_by_slug(slug)


@router.put("/{id}", response_model=ProductResponse)
async def update(
    id: str,
    payload: UpdateProductRequest = Validate(UpdateProductRequest),
    service: ProductService = Inject(ProductService)
) -> dict[str, Any]:
    """
    Update product (full update - PUT).

    Replaces all product fields with provided data.

    Args:
        id: Product UUID
        payload: Complete product update data (validated with unique slug check)
        service: ProductService (injected via Container)

    Returns:
        Updated product

    Raises:
        404: Product not found
        422: Validation error (duplicate slug, invalid price, etc.)
    """
    return await service.update_product(id, payload)


@router.patch("/{id}", response_model=ProductResponse)
async def partial_update(
    id: str,
    payload: UpdateProductRequest = Validate(UpdateProductRequest),
    service: ProductService = Inject(ProductService)
) -> dict[str, Any]:
    """
    Partially update product (PATCH).

    Updates only the fields provided in the request.

    Args:
        id: Product UUID
        payload: Partial product update data (validated with unique slug check)
        service: ProductService (injected via Container)

    Returns:
        Updated product

    Raises:
        404: Product not found
        422: Validation error (duplicate slug, invalid price, etc.)

    Example:
        PATCH /api/products/550e8400-e29b-41d4-a716-446655440100
        Body: {"price": 89.99}  # Only update price
    """
    return await service.partial_update_product(id, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    id: str,
    service: ProductService = Inject(ProductService)
) -> Response:
    """
    Delete product.

    Permanently removes product from database.

    Args:
        id: Product UUID
        service: ProductService (injected via Container)

    Returns:
        Empty response with 204 status

    Raises:
        HTTPException: 404 if product not found
    """
    await service.delete_product(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/search/query", response_model=list[ProductResponse])
async def search(
    query: str = Query(..., min_length=1, description="Search query"),
    service: ProductService = Inject(ProductService)
) -> list[dict[str, Any]]:
    """
    Search products.

    Searches product names and descriptions for the given query.

    Args:
        query: Search term (minimum 1 character)
        service: ProductService (injected via Container)

    Returns:
        List of matching products

    Example:
        GET /api/products/search/query?query=widget
    """
    return await service.search_products(query)


@router.get("/inventory/low-stock", response_model=list[ProductResponse])
async def low_stock(
    threshold: int = Query(10, ge=0, description="Stock threshold"),
    service: ProductService = Inject(ProductService)
) -> list[dict[str, Any]]:
    """
    Get low stock products.

    Returns products with stock below the specified threshold.

    Args:
        threshold: Stock threshold (default: 10, minimum: 0)
        service: ProductService (injected via Container)

    Returns:
        List of low-stock products

    Example:
        GET /api/products/inventory/low-stock?threshold=5
    """
    return await service.get_low_stock_products(threshold)
