"""
Update Product Request - Form Request with Validation

This FormRequest validates product update data including:
- Optional fields (all fields can be updated)
- Unique constraint on slug (excluding current product)
- Business rules (price > 0, stock >= 0)
"""

from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from jtc.validation import FormRequest, Rule
from pydantic import Field

from app.models import Product


class UpdateProductRequest(FormRequest):
    """
    Form Request for updating an existing product.

    All fields are optional to support partial updates (PATCH).

    Attributes:
        name: Product name (optional)
        slug: URL-friendly identifier (optional, must be unique)
        description: Product description (optional)
        price: Product price (optional, must be > 0)
        stock: Stock quantity (optional, must be >= 0)

    Validation:
        - If slug is provided, it must be unique (excluding current product)
        - If price is provided, it must be greater than 0
        - If stock is provided, it cannot be negative

    Example:
        @router.patch("/products/{id}")
        async def update(
            id: str,
            request: UpdateProductRequest = Validate(UpdateProductRequest)
        ):
            # request is already validated!
            product = await repo.find_or_fail(id)
            for key, value in request.model_dump(exclude_unset=True).items():
                setattr(product, key, value)
            await repo.update(product)
    """

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Product name"
    )

    slug: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="URL-friendly identifier (must be unique)"
    )

    description: str | None = Field(
        None,
        description="Product description"
    )

    price: Decimal | None = Field(
        None,
        gt=0,
        decimal_places=2,
        description="Product price (must be greater than 0)"
    )

    stock: int | None = Field(
        None,
        ge=0,
        description="Stock quantity (cannot be negative)"
    )

    # Store product ID for unique validation (set by controller)
    _product_id: str | None = None

    def set_product_id(self, product_id: str) -> None:
        """
        Set the current product ID for unique validation.

        This allows the unique check to exclude the current product.

        Args:
            product_id: UUID of the product being updated
        """
        self._product_id = product_id

    async def authorize(self, session: AsyncSession) -> bool:
        """
        Authorization check (always allow for now).

        Override this to add permission checks, e.g.:
        - Check if user has 'update_product' permission
        - Check if user owns the product

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
        # Check if slug is unique (only if slug is being updated)
        if self.slug is not None:
            await Rule.unique(
                session,
                Product,
                "slug",
                self.slug,
                ignore_id=self._product_id  # Exclude current product
            )
