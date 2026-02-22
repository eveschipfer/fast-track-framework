"""
Product CRUD Integration Tests

Tests for Product CRUD operations via HTTP using an isolated test app
with in-memory SQLite. This avoids the asyncpg event-loop incompatibility
that arises when the production app's connection pool is shared across
pytest-asyncio function-scoped event loops.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from fast_query import Base
from jtc.http import FastTrackFramework
from jtc.http.middleware import DatabaseSessionMiddleware
from app.models import Product  # registers Product in Base.metadata  # noqa: F401
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService
from app.http.controllers.product_controller import ProductController
from app.http.controllers.product_controller import router as product_router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def app():
    """
    Isolated FastTrackFramework with product routes and in-memory SQLite.

    Creates a clean database and app for each test so tests are independent.
    """
    test_app = FastTrackFramework()

    # In-memory SQLite (StaticPool keeps the same connection so tables persist)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables (Product, User, etc. — whatever is in Base.metadata)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Build a session factory for this engine
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Register AsyncEngine singleton
    test_app.container.register(AsyncEngine, scope="singleton")
    test_app.container._singletons[AsyncEngine] = engine

    # Register AsyncSession as scoped (one per request)
    def make_session() -> AsyncSession:
        return session_factory()

    test_app.register(AsyncSession, implementation=make_session, scope="scoped")

    # Register product domain services
    test_app.register(ProductRepository, scope="scoped")
    test_app.register(ProductService, scope="scoped")
    test_app.register(ProductController, scope="scoped")

    # Session lifecycle middleware (commit on 2xx, rollback on error)
    test_app.add_middleware(DatabaseSessionMiddleware)

    # Rate limiter (required by @limiter.limit decorator on store endpoint)
    _limiter = Limiter(key_func=get_remote_address)
    test_app.state.limiter = _limiter

    @test_app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})

    # Mount product routes
    test_app.include_router(product_router, prefix="/api", tags=["Products"])

    # Simple health and index endpoints
    @test_app.get("/health")
    async def health() -> dict:
        return {"status": "healthy"}

    @test_app.get("/")
    async def index() -> dict:
        return {"message": "Test API"}

    yield test_app

    await engine.dispose()


@pytest.fixture
async def client(app):
    """Async HTTP client bound to the isolated test app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# Override the global reset_db_engine fixture (from conftest.py) so it does
# NOT clear the engine singleton that our isolated fixture manages.
@pytest.fixture(autouse=True)
def reset_db_engine():
    """No-op override: the isolated `app` fixture manages its own engine."""
    yield


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_health_check(client):
    """Test API health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


async def test_api_index(client):
    """Test API index endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


async def test_create_product(client):
    """Test creating a new product."""
    payload = {
        "name": "Widget Pro",
        "slug": "widget-pro",
        "description": "Premium widget for professionals",
        "price": 99.99,
        "stock": 100,
    }

    response = await client.post("/api/products", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["name"] == "Widget Pro"
    assert data["slug"] == "widget-pro"
    assert data["description"] == "Premium widget for professionals"
    assert float(data["price"]) == 99.99
    assert data["stock"] == 100
    assert "created_at" in data


async def test_create_product_validation_error_empty_name(client):
    """Test creating product with empty name (should fail Pydantic validation)."""
    payload = {
        "name": "",  # Invalid: empty
        "slug": "widget-pro",
        "price": 99.99,
        "stock": 100,
    }

    response = await client.post("/api/products", json=payload)

    assert response.status_code == 422


async def test_create_product_validation_error_invalid_slug(client):
    """Test creating product with invalid slug (should fail Pydantic validation)."""
    payload = {
        "name": "Widget Pro",
        "slug": "Invalid Slug!",  # Invalid: uppercase and special chars
        "price": 99.99,
        "stock": 100,
    }

    response = await client.post("/api/products", json=payload)

    assert response.status_code == 422


async def test_create_product_validation_error_negative_price(client):
    """Test creating product with negative price (should fail Pydantic validation)."""
    payload = {
        "name": "Widget Pro",
        "slug": "widget-pro",
        "price": -10.99,  # Invalid: negative
        "stock": 100,
    }

    response = await client.post("/api/products", json=payload)

    assert response.status_code == 422


async def test_list_products(client):
    """Test listing all products with cursor pagination."""
    # Create a product first
    await client.post(
        "/api/products",
        json={
            "name": "Widget Pro",
            "slug": "widget-pro",
            "price": 99.99,
            "stock": 100,
        },
    )

    # List products (cursor paginated)
    response = await client.get("/api/products")

    assert response.status_code == 200
    body = response.json()

    # Verify cursor-paginated response structure
    assert "data" in body
    assert "meta" in body
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1

    # Verify meta fields
    meta = body["meta"]
    assert meta["per_page"] == 15
    assert "next_cursor" in meta
    assert "has_more_pages" in meta
    assert meta["count"] >= 1


async def test_get_product_by_id(client):
    """Test getting a product by UUID."""
    # Create a product
    create_response = await client.post(
        "/api/products",
        json={
            "name": "Widget Pro",
            "slug": "widget-pro",
            "price": 99.99,
            "stock": 100,
        },
    )
    product_id = create_response.json()["id"]

    # Get the product
    response = await client.get(f"/api/products/{product_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Widget Pro"


async def test_get_product_by_slug(client):
    """Test getting a product by slug."""
    # Create a product
    await client.post(
        "/api/products",
        json={
            "name": "Widget Pro",
            "slug": "widget-pro",
            "price": 99.99,
            "stock": 100,
        },
    )

    # Get product by slug
    response = await client.get("/api/products/slug/widget-pro")

    assert response.status_code == 200
    data = response.json()

    assert data["slug"] == "widget-pro"
    assert data["name"] == "Widget Pro"


async def test_get_product_not_found(client):
    """Test getting a non-existent product."""
    response = await client.get("/api/products/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    data = response.json()

    assert "detail" in data


async def test_update_product(client):
    """Test updating a product."""
    # Create a product
    create_response = await client.post(
        "/api/products",
        json={
            "name": "Widget Pro",
            "slug": "widget-pro",
            "description": "Premium widget",
            "price": 99.99,
            "stock": 100,
        },
    )
    product_id = create_response.json()["id"]

    # Update the product
    update_payload = {
        "name": "Widget Pro 2",
        "price": 89.99,
        "stock": 150,
    }

    response = await client.put(f"/api/products/{product_id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == product_id
    assert data["name"] == "Widget Pro 2"
    assert float(data["price"]) == 89.99
    assert data["stock"] == 150


async def test_partial_update_product(client):
    """Test partially updating a product."""
    # Create a product
    create_response = await client.post(
        "/api/products",
        json={
            "name": "Widget Pro",
            "slug": "widget-pro",
            "description": "Premium widget",
            "price": 99.99,
            "stock": 100,
        },
    )
    product_id = create_response.json()["id"]

    # Partial update (only price)
    update_payload = {"price": 79.99}

    response = await client.patch(f"/api/products/{product_id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == product_id
    assert float(data["price"]) == 79.99
    assert data["name"] == "Widget Pro"  # Unchanged
    assert data["description"] == "Premium widget"  # Unchanged


async def test_delete_product(client):
    """Test deleting a product."""
    # Create a product
    create_response = await client.post(
        "/api/products",
        json={
            "name": "Widget Pro",
            "slug": "widget-pro",
            "description": "Premium widget",
            "price": 99.99,
            "stock": 100,
        },
    )
    product_id = create_response.json()["id"]

    # Delete the product
    response = await client.delete(f"/api/products/{product_id}")

    assert response.status_code == 204
    assert response.content == b""


async def test_search_products(client):
    """Test searching products by query."""
    # Create a product
    await client.post(
        "/api/products",
        json={
            "name": "Widget Pro",
            "slug": "widget-pro",
            "description": "Premium widget for professionals",
            "price": 99.99,
            "stock": 100,
        },
    )

    # Search products
    response = await client.get("/api/products/search/query?query=widget")

    assert response.status_code == 200
    products = response.json()

    assert isinstance(products, list)
    assert len(products) >= 1


async def test_low_stock_products(client):
    """Test getting products with low stock."""
    # Create a product with low stock
    await client.post(
        "/api/products",
        json={
            "name": "Low Stock Widget",
            "slug": "low-stock-widget",
            "description": "Widget with low inventory",
            "price": 49.99,
            "stock": 3,
        },
    )

    # Get low stock products (threshold = 5)
    response = await client.get("/api/products/inventory/low-stock?threshold=5")

    assert response.status_code == 200
    products = response.json()

    assert isinstance(products, list)
    assert len(products) >= 1
    assert any(p["stock"] < 5 for p in products)
