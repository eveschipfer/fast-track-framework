"""
Integration Tests for Product CRUD Endpoints

Tests the complete product API including:
- Creating products (with validation)
- Unique slug validation
- Retrieving products
- Updating products
- Deleting products
- Search functionality
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from fast_query import Base
from app.models import Product


@pytest.fixture
async def test_db():
    """Create a clean test database for each test."""
    # Use in-memory SQLite for fast tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield session_factory

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def session(test_db):
    """Provide a database session for tests."""
    async with test_db() as session:
        yield session


@pytest.fixture
async def client(session):
    """
    Provide an async HTTP client with test database.

    Note: This is a simplified fixture. In a real application,
    you'd override the dependency injection to use the test session.
    """
    from workbench.main import app

    # TODO: Override the database session dependency
    # For now, we'll test the repository layer directly

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def sample_product(session):
    """Create a sample product for testing."""
    product = Product(
        id=str(uuid4()),
        name="Test Widget",
        slug="test-widget",
        description="A test product",
        price=Decimal("99.99"),
        stock=100,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


class TestProductCreate:
    """Test product creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_product_success(self, session):
        """Test creating a product with valid data."""
        from app.repositories.product_repository import ProductRepository
        from app.http.requests.store_product_request import StoreProductRequest

        repo = ProductRepository(session)

        # Create request data
        request_data = StoreProductRequest(
            name="New Widget",
            slug="new-widget",
            description="A brand new widget",
            price=Decimal("149.99"),
            stock=50,
        )

        # Validate (this would normally happen in the endpoint)
        await request_data.rules(session)

        # Create product
        product = Product(**request_data.model_dump())
        created = await repo.create(product)

        assert created.id is not None
        assert created.name == "New Widget"
        assert created.slug == "new-widget"
        assert created.price == Decimal("149.99")
        assert created.stock == 50

    @pytest.mark.asyncio
    async def test_create_product_duplicate_slug(self, session, sample_product):
        """Test creating a product with duplicate slug fails validation."""
        from app.http.requests.store_product_request import StoreProductRequest
        from jtc.validation import ValidationError

        # Try to create with same slug
        request_data = StoreProductRequest(
            name="Another Widget",
            slug="test-widget",  # Same as sample_product
            description="This should fail",
            price=Decimal("199.99"),
            stock=25,
        )

        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await request_data.rules(session)

        assert "slug" in str(exc_info.value).lower()
        assert "already been taken" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_product_invalid_price(self):
        """Test creating a product with invalid price fails Pydantic validation."""
        from app.http.requests.store_product_request import StoreProductRequest
        from pydantic import ValidationError

        # Should fail Pydantic validation (price must be > 0)
        with pytest.raises(ValidationError) as exc_info:
            StoreProductRequest(
                name="Invalid Widget",
                slug="invalid-widget",
                price=Decimal("-10.00"),  # Negative price
                stock=100,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("price",) for error in errors)

    @pytest.mark.asyncio
    async def test_create_product_negative_stock(self):
        """Test creating a product with negative stock fails validation."""
        from app.http.requests.store_product_request import StoreProductRequest
        from pydantic import ValidationError

        # Should fail Pydantic validation (stock must be >= 0)
        with pytest.raises(ValidationError) as exc_info:
            StoreProductRequest(
                name="Invalid Widget",
                slug="invalid-widget",
                price=Decimal("99.99"),
                stock=-10,  # Negative stock
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("stock",) for error in errors)


class TestProductRetrieve:
    """Test product retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_get_all_products(self, session, sample_product):
        """Test retrieving all products."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)
        products = await repo.all()

        assert len(products) >= 1
        assert any(p.slug == "test-widget" for p in products)

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, session, sample_product):
        """Test retrieving a product by ID."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)
        product = await repo.find(sample_product.id)

        assert product is not None
        assert product.id == sample_product.id
        assert product.name == sample_product.name

    @pytest.mark.asyncio
    async def test_get_product_by_slug(self, session, sample_product):
        """Test retrieving a product by slug."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)
        product = await repo.find_by_slug("test-widget")

        assert product is not None
        assert product.slug == "test-widget"
        assert product.name == sample_product.name

    @pytest.mark.asyncio
    async def test_get_nonexistent_product(self, session):
        """Test retrieving a non-existent product returns None."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)
        product = await repo.find(str(uuid4()))

        assert product is None

    @pytest.mark.asyncio
    async def test_find_or_fail_raises(self, session):
        """Test find_or_fail raises RecordNotFound."""
        from app.repositories.product_repository import ProductRepository
        from fast_query import RecordNotFound

        repo = ProductRepository(session)

        with pytest.raises(RecordNotFound):
            await repo.find_or_fail(str(uuid4()))


class TestProductUpdate:
    """Test product update endpoints."""

    @pytest.mark.asyncio
    async def test_update_product_success(self, session, sample_product):
        """Test updating a product successfully."""
        from app.repositories.product_repository import ProductRepository
        from app.http.requests.update_product_request import UpdateProductRequest

        repo = ProductRepository(session)

        # Create update request
        request_data = UpdateProductRequest(
            name="Updated Widget",
            price=Decimal("129.99"),
        )
        request_data.set_product_id(sample_product.id)

        # Validate
        await request_data.rules(session)

        # Update product
        product = await repo.find_or_fail(sample_product.id)
        for key, value in request_data.model_dump(exclude_unset=True).items():
            if not key.startswith("_"):
                setattr(product, key, value)

        updated = await repo.update(product)

        assert updated.name == "Updated Widget"
        assert updated.price == Decimal("129.99")
        assert updated.slug == "test-widget"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_product_same_slug(self, session, sample_product):
        """Test updating a product with its own slug is allowed."""
        from app.repositories.product_repository import ProductRepository
        from app.http.requests.update_product_request import UpdateProductRequest

        repo = ProductRepository(session)

        # Update with same slug (should be allowed)
        request_data = UpdateProductRequest(
            slug="test-widget",  # Same slug
            price=Decimal("109.99"),
        )
        request_data.set_product_id(sample_product.id)

        # Should NOT raise ValidationError
        await request_data.rules(session)

        # Update should succeed
        product = await repo.find_or_fail(sample_product.id)
        product.price = Decimal("109.99")
        updated = await repo.update(product)

        assert updated.slug == "test-widget"
        assert updated.price == Decimal("109.99")

    @pytest.mark.asyncio
    async def test_update_product_duplicate_slug(self, session, sample_product):
        """Test updating a product with another product's slug fails."""
        from app.repositories.product_repository import ProductRepository
        from app.http.requests.update_product_request import UpdateProductRequest
        from jtc.validation import ValidationError

        repo = ProductRepository(session)

        # Create another product
        other_product = Product(
            id=str(uuid4()),
            name="Other Widget",
            slug="other-widget",
            price=Decimal("79.99"),
            stock=50,
        )
        session.add(other_product)
        await session.commit()

        # Try to update sample_product with other_product's slug
        request_data = UpdateProductRequest(
            slug="other-widget",  # Another product's slug
        )
        request_data.set_product_id(sample_product.id)

        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await request_data.rules(session)

        assert "slug" in str(exc_info.value).lower()


class TestProductDelete:
    """Test product deletion endpoint."""

    @pytest.mark.asyncio
    async def test_delete_product_success(self, session, sample_product):
        """Test deleting a product successfully."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)

        # Delete product
        await repo.delete(sample_product.id)

        # Should not be found
        product = await repo.find(sample_product.id)
        assert product is None or product.deleted_at is not None


class TestProductSearch:
    """Test product search functionality."""

    @pytest.mark.asyncio
    async def test_search_by_name(self, session, sample_product):
        """Test searching products by name."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)

        # Search for "Widget"
        results = await repo.search("Widget")

        assert len(results) >= 1
        assert any(p.name == "Test Widget" for p in results)

    @pytest.mark.asyncio
    async def test_search_by_description(self, session, sample_product):
        """Test searching products by description."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)

        # Search for "test"
        results = await repo.search("test")

        assert len(results) >= 1
        assert any(p.description and "test" in p.description.lower() for p in results)

    @pytest.mark.asyncio
    async def test_search_no_results(self, session):
        """Test search with no results."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)

        # Search for something that doesn't exist
        results = await repo.search("NonexistentProduct12345")

        assert len(results) == 0


class TestProductStock:
    """Test product stock management."""

    @pytest.mark.asyncio
    async def test_get_low_stock_products(self, session):
        """Test getting products with low stock."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)

        # Create products with different stock levels
        low_stock = Product(
            id=str(uuid4()),
            name="Low Stock Widget",
            slug="low-stock-widget",
            price=Decimal("49.99"),
            stock=5,  # Low stock
        )
        high_stock = Product(
            id=str(uuid4()),
            name="High Stock Widget",
            slug="high-stock-widget",
            price=Decimal("59.99"),
            stock=100,  # High stock
        )

        session.add_all([low_stock, high_stock])
        await session.commit()

        # Get low stock products (threshold = 10)
        results = await repo.low_stock(threshold=10)

        assert len(results) >= 1
        assert any(p.slug == "low-stock-widget" for p in results)
        assert not any(p.slug == "high-stock-widget" for p in results)

    @pytest.mark.asyncio
    async def test_update_stock(self, session, sample_product):
        """Test updating product stock."""
        from app.repositories.product_repository import ProductRepository

        repo = ProductRepository(session)
        initial_stock = sample_product.stock

        # Increase stock
        await repo.update_stock(sample_product.id, 50)
        product = await repo.find(sample_product.id)
        assert product.stock == initial_stock + 50

        # Decrease stock
        await repo.decrease_stock(sample_product.id, 25)
        product = await repo.find(sample_product.id)
        assert product.stock == initial_stock + 50 - 25
