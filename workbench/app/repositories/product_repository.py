"""
ProductRepository

This module defines a repository for Product database operations.
Sprint 18.2: PostgreSQL Product CRUD Implementation with UUID support.

Repository Pattern:
    - Inherits from BaseRepository (Hybrid Pattern - Sprint 8.0)
    - Provides convenience methods: find(), create(), update(), delete(), all()
    - Supports native AsyncSession access for advanced queries
    - Custom methods for business logic (slug lookup, stock management)

Available Methods:
    - find(id): Find by UUID primary key
    - find_or_fail(id): Find or raise RecordNotFound
    - find_by_slug(slug): Find product by slug
    - all(): Get all records
    - create(data): Create new record
    - update(id, data): Update existing record
    - delete(id): Delete record (soft delete if mixin enabled)
    - update_stock(id, quantity): Adjust stock quantity
    - query(): Get QueryBuilder for fluent queries
    - session: Native AsyncSession access for advanced queries

Usage:
    >>> repo = ProductRepository(session)
    >>>
    >>> # Find by slug
    >>> product = await repo.find_by_slug("widget-pro")
    >>>
    >>> # Update stock
    >>> await repo.update_stock(product_id, quantity=10)
    >>>
    >>> # Native session for complex queries
    >>> from sqlalchemy import select
    >>> stmt = select(Product).where(Product.price > 100)
    >>> result = await repo.session.execute(stmt)
    >>> products = result.scalars().all()
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fast_query import BaseRepository, RecordNotFound
from app.models import Product


class ProductRepository(BaseRepository[Product]):
    """
    Repository for Product database operations.

    Inherits from BaseRepository (Hybrid Pattern - Sprint 8.0):
    - Convenience methods: find(id), create(), update(), delete(), all(), etc.
    - Native session access: self.session.execute(select(...)) for advanced queries
    - Supports CTEs, Window Functions, Bulk Operations

    Sprint 18.2:
        - UUID primary key support
        - Slug-based lookups
        - Stock management methods

    Available methods:
        - find(id): Find by UUID
        - find_or_fail(id): Find or raise RecordNotFound
        - find_by_slug(slug): Find product by slug
        - all(): Get all records
        - create(data): Create new record
        - update(id, data): Update existing record
        - delete(id): Delete record (soft delete if mixin enabled)
        - update_stock(id, quantity): Adjust stock quantity
        - query(): Get QueryBuilder for fluent queries
        - session: Native AsyncSession access for advanced queries

    Example:
        >>> # Use convenience methods (recommended for simple operations)
        >>> product = await repo.find(uuid4())
        >>>
        >>> # Use custom methods
        >>> product = await repo.find_by_slug("widget-pro")
        >>> await repo.update_stock(product.id, 10)  # Add 10 to stock
        >>>
        >>> # Use native session for advanced queries
        >>> stmt = select(Product).where(Product.price > 100)
        >>> result = await repo.session.execute(stmt)
        >>> products = result.scalars().all()
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with Container-injected AsyncSession.

        Args:
            session: AsyncSession for database operations (injected via Container)
        """
        super().__init__(session, Product)

    async def find_by_slug(self, slug: str) -> Product | None:
        """
        Find product by slug.

        This is useful for URL routing where products are accessed
        via their slug instead of UUID.

        Args:
            slug: The product slug to search for

        Returns:
            Product if found, None otherwise

        Example:
            >>> product = await repo.find_by_slug("widget-pro")
            >>> if product:
            ...     print(f"Found: {product.name}")
        """
        stmt = select(Product).where(Product.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_slug_or_fail(self, slug: str) -> Product:
        """
        Find product by slug or raise RecordNotFound.

        This is useful for URL routing where you want to return 404
        if a product doesn't exist.

        Args:
            slug: The product slug to search for

        Returns:
            Product if found

        Raises:
            RecordNotFound: If product with slug doesn't exist

        Example:
            >>> try:
            ...     product = await repo.find_by_slug_or_fail("widget-pro")
            ...     print(f"Found: {product.name}")
            ... except RecordNotFound:
            ...     raise HTTPException(status_code=404, detail="Product not found")
        """
        product = await self.find_by_slug(slug)
        if not product:
            raise RecordNotFound(f"Product with slug '{slug}' not found")
        return product

    async def update_stock(self, product_id: str, quantity: int) -> Product | None:
        """
        Update product stock quantity.

        This method adjusts the stock by adding or subtracting the
        specified quantity. Useful for order processing.

        Args:
            product_id: UUID of the product
            quantity: Amount to add (positive) or subtract (negative)

        Returns:
            Updated product if found, None otherwise

        Example:
            >>> # Add 10 to stock
            >>> product = await repo.update_stock(uuid4(), 10)
            >>>
            >>> # Subtract 5 from stock
            >>> product = await repo.update_stock(uuid4(), -5)
        """
        product = await self.find(product_id)
        if product:
            product.stock += quantity
            await self.session.commit()
        return product

    async def decrease_stock(self, product_id: str, quantity: int) -> Product | None:
        """
        Decrease product stock.

        Helper method for reducing stock (e.g., when an order is placed).

        Args:
            product_id: UUID of the product
            quantity: Amount to decrease (must be positive)

        Returns:
            Updated product if found, None otherwise

        Example:
            >>> # Decrease stock when order placed
            >>> product = await repo.decrease_stock(uuid4(), 5)
            >>> if product.stock < 0:
            ...     # Handle out of stock
            ...     pass
        """
        product = await self.find(product_id)
        if product:
            product.stock -= quantity
            await self.session.commit()
        return product

    async def increase_stock(self, product_id: str, quantity: int) -> Product | None:
        """
        Increase product stock.

        Helper method for adding to stock (e.g., when order is cancelled).

        Args:
            product_id: UUID of the product
            quantity: Amount to increase (must be positive)

        Returns:
            Updated product if found, None otherwise

        Example:
            >>> # Increase stock when cancelled
            >>> product = await repo.increase_stock(uuid4(), 5)
            >>> print(f"New stock: {product.stock}")
        """
        product = await self.find(product_id)
        if product:
            product.stock += quantity
            await self.session.commit()
        return product

    async def get_low_stock_products(self, threshold: int = 10) -> list[Product]:
        """
        Get products with stock below threshold.

        Useful for inventory alerts and reorder notifications.

        Args:
            threshold: Stock threshold (default: 10)

        Returns:
            List of products with stock below threshold

        Example:
            >>> # Get products that need reordering
            >>> low_stock = await repo.get_low_stock_products(threshold=5)
            >>> for product in low_stock:
            ...     print(f"Reorder needed: {product.name} (stock: {product.stock})")
        """
        stmt = select(Product).where(Product.stock < threshold)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def low_stock(self, threshold: int = 10) -> list[Product]:
        """
        Alias for get_low_stock_products().

        Get products with stock below threshold.

        Args:
            threshold: Stock threshold (default: 10)

        Returns:
            List of products with stock below threshold
        """
        return await self.get_low_stock_products(threshold)

    async def search(self, query: str) -> list[Product]:
        """
        Search products by name or description.

        Performs case-insensitive search on product name and description.

        Args:
            query: Search query string

        Returns:
            List of matching products

        Example:
            >>> products = await repo.search("widget")
            >>> for product in products:
            ...     print(f"Found: {product.name}")
        """
        from sqlalchemy import or_

        search_term = f"%{query}%"
        stmt = select(Product).where(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
