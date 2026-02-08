"""
Store Product Request - Form Request with Validation

This FormRequest validates product creation data including:
- Required fields (name, slug, price)
- Unique constraint on slug
- Business rules (price > 0, stock >= 0)
"""

from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from jtc.validation import FormRequest, Rule
from pydantic import Field

from app.models import Product


class StoreProductRequest(FormRequest):
    """
    Form Request for creating a new product.

    Validates incoming product data and checks uniqueness constraints.

    Attributes:
        name: Product name (1-100 characters)
        slug: URL-friendly identifier (must be unique)
        description: Product description (optional)
        price: Product price (must be > 0)
        stock: Initial stock quantity (default 0, must be >= 0)

    Validation:
        - slug must be unique in products table
        - price must be greater than 0
        - stock cannot be negative

    Example:
        @router.post("/products")
        async def create(request: StoreProductRequest = Validate(StoreProductRequest)):
            # request is already validated!
            product = Product(**request.model_dump())
            await repo.create(product)
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Product name"
    )

    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="URL-friendly identifier (must be unique)"
    )

    description: str | None = Field(
        None,
        description="Product description (optional)"
    )

    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Product price (must be greater than 0)"
    )

    stock: int = Field(
        default=0,
        ge=0,
        description="Initial stock quantity (default 0, cannot be negative)"
    )

    async def authorize(self, session: AsyncSession) -> bool:
        """
        Authorization check (always allow for now).

        Override this to add permission checks, e.g.:
        - Check if user has 'create_product' permission
        - Check if user is admin

        Args:
            session: Database session (injected automatically)

        Returns:
            bool: True if authorized, False otherwise
        """
        return True

    async def rules(self, session: AsyncSession) -> None:
        """
        Custom validation rules.

        This method is called after Pydantic validation.
        Use it for database-dependent validation like uniqueness checks.

        Args:
            session: Database session (injected automatically)

        Raises:
            ValidationError: If validation fails
        """
        # Check if slug is unique
        await Rule.unique(session, Product, "slug", self.slug)
