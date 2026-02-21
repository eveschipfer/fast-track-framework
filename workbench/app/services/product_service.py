"""
ProductService — Business Logic Layer

This module owns all product-related domain rules. It is deliberately free of
any HTTP / FastAPI concerns:

    ✅ Allowed:  repositories, domain models, Pydantic schemas, domain exceptions
    ❌ Forbidden: HTTPException, fastapi.status, JSONResponse, Request, Response

Why the strict boundary?
    - The same service can be called from REST controllers, CLI scripts, and
      background workers without modification.
    - Unit tests exercise business rules without spinning up an HTTP server.
    - Errors are expressed as domain facts (ProductNotFound) not HTTP accidents
      (404); callers decide how to translate them to the wire.

Raises:
    ProductNotFound  — when a product cannot be located by ID or slug.
    DuplicateSlug    — reserved for future use if slug uniqueness must be
                       enforced at the service layer rather than in FormRequest.
"""

from fast_query import CursorMeta, CursorPage
from app.exceptions.product_exceptions import ProductNotFound
from app.http.requests.store_product_request import StoreProductRequest
from app.http.requests.update_product_request import UpdateProductRequest
from app.repositories.product_repository import ProductRepository
from app.schemas import ProductResponse
from fast_query import RecordNotFound


class ProductService:
    """
    Orchestrates product CRUD and query operations.

    Receives ``ProductRepository`` via the framework IoC container (registered
    as *scoped*, meaning one instance per HTTP request).  All public methods
    return typed Pydantic objects — never raw ORM models or plain dicts.
    """

    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_all_products(self) -> list[ProductResponse]:
        """Return every product in the catalogue (unfiltered, unsorted)."""
        products = await self.repo.all()
        return [ProductResponse.model_validate(p) for p in products]

    async def get_paginated_products(
        self,
        per_page: int = 15,
        cursor: str | None = None,
    ) -> CursorPage[ProductResponse]:
        """
        Return a cursor-paginated slice of the product catalogue.

        Uses a single SQL query with no COUNT(*): O(1) regardless of table size.

        Args:
            per_page: Maximum items to return (default 15, max enforced by caller).
            cursor:   Last product ID from the previous page; ``None`` for the
                      first page.

        Returns:
            ``CursorPage[ProductResponse]`` containing items and navigation meta.
        """
        paginator = await self.repo.query().cursor_paginate(
            per_page=per_page,
            cursor=cursor,
            cursor_column="id",
        )
        return CursorPage[ProductResponse](
            data=[ProductResponse.model_validate(p) for p in paginator.items],
            meta=CursorMeta(
                per_page=paginator.per_page,
                next_cursor=paginator.next_cursor,
                has_more_pages=paginator.has_more_pages,
                count=paginator.count,
            ),
        )

    async def get_product_by_id(self, product_id: str) -> ProductResponse:
        """
        Locate a single product by its UUID primary key.

        Raises:
            ProductNotFound: if no product with that ID exists.
        """
        try:
            product = await self.repo.find_or_fail(product_id)
        except RecordNotFound:
            raise ProductNotFound(product_id)
        return ProductResponse.model_validate(product)

    async def get_product_by_slug(self, slug: str) -> ProductResponse:
        """
        Locate a single product by its URL-friendly slug.

        Raises:
            ProductNotFound: if no product with that slug exists.
        """
        product = await self.repo.find_by_slug(slug)
        if not product:
            raise ProductNotFound(slug)
        return ProductResponse.model_validate(product)

    async def search_products(self, query: str) -> list[ProductResponse]:
        """Full-text search across product names and descriptions."""
        products = await self.repo.search(query)
        return [ProductResponse.model_validate(p) for p in products]

    async def get_low_stock_products(self, threshold: int = 10) -> list[ProductResponse]:
        """Return products whose stock level is below ``threshold``."""
        products = await self.repo.low_stock(threshold)
        return [ProductResponse.model_validate(p) for p in products]

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create_product(self, data: StoreProductRequest) -> ProductResponse:
        """
        Persist a new product from a validated ``StoreProductRequest``.

        Slug uniqueness is enforced upstream by the FormRequest; the service
        does not duplicate that check.

        Returns:
            The newly created ``ProductResponse``.
        """
        from app.models import Product

        product = Product(**data.model_dump())
        product = await self.repo.create(product)
        return ProductResponse.model_validate(product)

    async def update_product(
        self, product_id: str, data: UpdateProductRequest
    ) -> ProductResponse:
        """
        Full replacement update (PUT semantics — all fields overwritten).

        Raises:
            ProductNotFound: if the product does not exist.
        """
        try:
            product = await self.repo.find_or_fail(product_id)
        except RecordNotFound:
            raise ProductNotFound(product_id)

        data.set_product_id(product_id)
        for key, value in data.model_dump(exclude_unset=False).items():
            if not key.startswith("_"):
                setattr(product, key, value)

        product = await self.repo.update(product)
        return ProductResponse.model_validate(product)

    async def partial_update_product(
        self, product_id: str, data: UpdateProductRequest
    ) -> ProductResponse:
        """
        Partial update (PATCH semantics — only supplied fields overwritten).

        Raises:
            ProductNotFound: if the product does not exist.
        """
        try:
            product = await self.repo.find_or_fail(product_id)
        except RecordNotFound:
            raise ProductNotFound(product_id)

        data.set_product_id(product_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            if not key.startswith("_"):
                setattr(product, key, value)

        product = await self.repo.update(product)
        return ProductResponse.model_validate(product)

    async def delete_product(self, product_id: str) -> None:
        """
        Permanently remove a product.

        Raises:
            ProductNotFound: if the product does not exist.
        """
        try:
            product = await self.repo.find_or_fail(product_id)
        except RecordNotFound:
            raise ProductNotFound(product_id)

        await self.repo.delete(product)
