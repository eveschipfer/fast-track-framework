"""
ProductController — HTTP Handler Layer

Architecture:
    Request → Route function → ProductController method
                → ProductService method (pure domain logic)
                → ProductRepository → Database

Responsibility split:
    ProductService   — domain rules, raises domain exceptions (ProductNotFound …)
    ProductController — HTTP translation: catches domain exceptions, maps them to
                        status codes, and shapes the final HTTP response using
                        BaseController helpers.

This file contains:
    1. ProductController class (inherits BaseController)
    2. APIRouter with route functions that are thin wrappers around controller methods
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from jtc.http import Inject

from fast_query import CursorPage
from app.exceptions.product_exceptions import ProductNotFound
from jtc.http import BaseController
from app.http.requests.store_product_request import StoreProductRequest
from app.http.requests.update_product_request import UpdateProductRequest
from app.limiter import limiter
from app.schemas import ProductResponse
from app.services.product_service import ProductService
from jtc.validation import Validate


# ============================================================================
# CONTROLLER
# ============================================================================


class ProductController(BaseController):
    """
    Handles HTTP concerns for the /products resource.

    Receives ``ProductService`` from the IoC container (scoped lifetime).
    Never imports domain models or repository internals directly — all data
    access flows through the service layer.

    Exception mapping (domain → HTTP):
        ProductNotFound → 404 Not Found
    """

    def __init__(self, service: ProductService) -> None:
        self.service = service

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def index(
        self, per_page: int, cursor: str | None
    ) -> dict[str, Any]:
        """Return a cursor-paginated product list."""
        page: CursorPage[ProductResponse] = await self.service.get_paginated_products(
            per_page=per_page, cursor=cursor
        )
        return self.paginated(page)

    async def show(self, product_id: str) -> ProductResponse:
        """Return a single product by UUID."""
        try:
            return self.ok(await self.service.get_product_by_id(product_id))
        except ProductNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )

    async def show_by_slug(self, slug: str) -> ProductResponse:
        """Return a single product by slug."""
        try:
            return self.ok(await self.service.get_product_by_slug(slug))
        except ProductNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with slug '{slug}' not found",
            )

    async def search(self, query: str) -> list[ProductResponse]:
        """Return products whose name or description matches the query."""
        return self.ok(await self.service.search_products(query))

    async def low_stock(self, threshold: int) -> list[ProductResponse]:
        """Return products with stock below ``threshold``."""
        return self.ok(await self.service.get_low_stock_products(threshold))

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def store(self, payload: StoreProductRequest) -> ProductResponse:
        """Create and return a new product."""
        return self.created(await self.service.create_product(payload))

    async def update(self, product_id: str, payload: UpdateProductRequest) -> ProductResponse:
        """Full replacement update (PUT semantics)."""
        try:
            return self.ok(await self.service.update_product(product_id, payload))
        except ProductNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )

    async def partial_update(
        self, product_id: str, payload: UpdateProductRequest
    ) -> ProductResponse:
        """Partial update (PATCH semantics — only supplied fields changed)."""
        try:
            return self.ok(await self.service.partial_update_product(product_id, payload))
        except ProductNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )

    async def destroy(self, product_id: str) -> Response:
        """Delete a product; returns 204 No Content on success."""
        try:
            await self.service.delete_product(product_id)
            return self.no_content()
        except ProductNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={
        404: {"description": "Product not found"},
        422: {"description": "Validation error"},
    },
)


# ------------------------------------------------------------------
# Route functions — thin wrappers; all logic lives in the controller.
# ------------------------------------------------------------------


@router.get("", response_model=CursorPage[ProductResponse])
async def index(
    per_page: int = Query(15, ge=1, le=100, description="Items per page (max 100)"),
    cursor: str | None = Query(
        None, description="Cursor (last product ID from previous page)"
    ),
    controller: ProductController = Inject(ProductController),
) -> dict[str, Any]:
    """
    List products with cursor pagination.

    Uses O(1) cursor-based pagination instead of offset-based.
    Pass ``next_cursor`` from the previous response to advance to the next page.

    Example:
        First page:  GET /api/products?per_page=15
        Next page:   GET /api/products?per_page=15&cursor=<next_cursor>
    """
    return await controller.index(per_page, cursor)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("600/minute")
async def store(
    request: Request,
    payload: StoreProductRequest = Validate(StoreProductRequest),
    controller: ProductController = Inject(ProductController),
) -> ProductResponse:
    """
    Create a new product.

    Rate limited to 600 requests/minute per client IP.

    Raises:
        422: Validation error (duplicate slug, invalid price, etc.)
        429: Rate limit exceeded
    """
    return await controller.store(payload)


@router.get("/search/query", response_model=list[ProductResponse])
async def search(
    query: str = Query(..., min_length=1, description="Search query"),
    controller: ProductController = Inject(ProductController),
) -> list[ProductResponse]:
    """
    Search products by name or description.

    Example:
        GET /api/products/search/query?query=widget
    """
    return await controller.search(query)


@router.get("/inventory/low-stock", response_model=list[ProductResponse])
async def low_stock(
    threshold: int = Query(10, ge=0, description="Stock threshold"),
    controller: ProductController = Inject(ProductController),
) -> list[ProductResponse]:
    """
    Return products with stock below ``threshold``.

    Example:
        GET /api/products/inventory/low-stock?threshold=5
    """
    return await controller.low_stock(threshold)


@router.get("/slug/{slug}", response_model=ProductResponse)
async def show_by_slug(
    slug: str,
    controller: ProductController = Inject(ProductController),
) -> ProductResponse:
    """
    Get product by slug.

    Example:
        GET /api/products/slug/widget-pro
    """
    return await controller.show_by_slug(slug)


@router.get("/{id}", response_model=ProductResponse)
async def show(
    id: str,
    controller: ProductController = Inject(ProductController),
) -> ProductResponse:
    """Get product by UUID."""
    return await controller.show(id)


@router.put("/{id}", response_model=ProductResponse)
async def update(
    id: str,
    payload: UpdateProductRequest = Validate(UpdateProductRequest),
    controller: ProductController = Inject(ProductController),
) -> ProductResponse:
    """
    Full replacement update (PUT).

    Replaces all product fields with the provided data.

    Raises:
        404: Product not found
        422: Validation error (duplicate slug, invalid price, etc.)
    """
    return await controller.update(id, payload)


@router.patch("/{id}", response_model=ProductResponse)
async def partial_update(
    id: str,
    payload: UpdateProductRequest = Validate(UpdateProductRequest),
    controller: ProductController = Inject(ProductController),
) -> ProductResponse:
    """
    Partial update (PATCH).

    Only the fields present in the request body are updated.

    Example:
        PATCH /api/products/550e8400-...
        Body: {"price": 89.99}
    """
    return await controller.partial_update(id, payload)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    id: str,
    controller: ProductController = Inject(ProductController),
) -> Response:
    """
    Delete product.

    Permanently removes the product. Returns 204 No Content on success.
    """
    return await controller.destroy(id)
