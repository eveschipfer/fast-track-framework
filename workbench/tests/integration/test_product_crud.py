"""
Product CRUD Integration Tests

Tests for Product CRUD operations using FastAPI Test Client.
Sprint 18.2: Complete CRUD testing with UUID support.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient

from jtc.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test API health check endpoint."""
    async with AsyncClient(base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "framework" in data


@pytest.mark.asyncio
async def test_api_index():
    """Test API index endpoint."""
    async with AsyncClient(base_url="http://test") as client:
        response = await client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "endpoints" in data


@pytest.mark.asyncio
async def test_create_product():
    """Test creating a new product."""
    async with AsyncClient(base_url="http://test") as client:
        payload = {
            "name": "Widget Pro",
            "slug": "widget-pro",
            "description": "Premium widget for professionals",
            "price": 99.99,
            "stock": 100
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


@pytest.mark.asyncio
async def test_create_product_validation_error_empty_name():
    """Test creating product with empty name (should fail validation)."""
    async with AsyncClient(base_url="http://test") as client:
        payload = {
            "name": "",  # Invalid: empty
            "slug": "widget-pro",
            "price": 99.99,
            "stock": 100
        }

        response = await client.post("/api/products", json=payload)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_validation_error_invalid_slug():
    """Test creating product with invalid slug (should fail validation)."""
    async with AsyncClient(base_url="http://test") as client:
        payload = {
            "name": "Widget Pro",
            "slug": "Invalid Slug!",  # Invalid: uppercase and special chars
            "price": 99.99,
            "stock": 100
        }

        response = await client.post("/api/products", json=payload)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_validation_error_negative_price():
    """Test creating product with negative price (should fail validation)."""
    async with AsyncClient(base_url="http://test") as client:
        payload = {
            "name": "Widget Pro",
            "slug": "widget-pro",
            "price": -10.99,  # Invalid: negative
            "stock": 100
        }

        response = await client.post("/api/products", json=payload)

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_products():
    """Test listing all products with cursor pagination."""
    async with AsyncClient(base_url="http://test") as client:
        # Create a product first
        await client.post(
            "/api/products",
            json={
                "name": "Widget Pro",
                "slug": "widget-pro",
                "price": 99.99,
                "stock": 100
            }
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


@pytest.mark.asyncio
async def test_get_product_by_id():
    """Test getting a product by UUID."""
    async with AsyncClient(base_url="http://test") as client:
        # Create a product
        create_response = await client.post(
            "/api/products",
            json={
                "name": "Widget Pro",
                "slug": "widget-pro",
                "price": 99.99,
                "stock": 100
            }
        )
        product_id = create_response.json()["id"]

        # Get the product
        response = await client.get(f"/api/products/{product_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == product_id
        assert data["name"] == "Widget Pro"


@pytest.mark.asyncio
async def test_get_product_by_slug():
    """Test getting a product by slug."""
    async with AsyncClient(base_url="http://test") as client:
        # Create a product
        create_response = await client.post(
            "/api/products",
            json={
                "name": "Widget Pro",
                "slug": "widget-pro",
                "price": 99.99,
                "stock": 100
            }
        )

        # Get product by slug
        response = await client.get("/api/products/slug/widget-pro")

        assert response.status_code == 200
        data = response.json()

        assert data["slug"] == "widget-pro"
        assert data["name"] == "Widget Pro"


@pytest.mark.asyncio
async def test_get_product_not_found():
    """Test getting a non-existent product."""
    async with AsyncClient(base_url="http://test") as client:
        response = await client.get("/api/products/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data


@pytest.mark.asyncio
async def test_update_product():
    """Test updating a product."""
    async with AsyncClient(base_url="http://test") as client:
        # Create a product
        create_response = await client.post(
            "/api/products",
            json={
                "name": "Widget Pro",
                "slug": "widget-pro",
                "description": "Premium widget",
                "price": 99.99,
                "stock": 100
            }
        )
        product_id = create_response.json()["id"]

        # Update the product
        update_payload = {
            "name": "Widget Pro 2",
            "price": 89.99,
            "stock": 150
        }

        response = await client.put(f"/api/products/{product_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == product_id
        assert data["name"] == "Widget Pro 2"
        assert float(data["price"]) == 89.99
        assert data["stock"] == 150


@pytest.mark.asyncio
async def test_partial_update_product():
    """Test partially updating a product."""
    async with AsyncClient(base_url="http://test") as client:
        # Create a product
        create_response = await client.post(
            "/api/products",
            json={
                "name": "Widget Pro",
                "slug": "widget-pro",
                "description": "Premium widget",
                "price": 99.99,
                "stock": 100
            }
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


@pytest.mark.asyncio
async def test_delete_product():
    """Test deleting a product."""
    async with AsyncClient(base_url="http://test") as client:
        # Create a product
        create_response = await client.post(
            "/api/products",
            json={
                "name": "Widget Pro",
                "slug": "widget-pro",
                "description": "Premium widget",
                "price": 99.99,
                "stock": 100
            }
        )
        product_id = create_response.json()["id"]

        # Delete the product
        response = await client.delete(f"/api/products/{product_id}")

        assert response.status_code == 204
        assert response.content == b""


@pytest.mark.asyncio
async def test_search_products():
    """Test searching products by query."""
    async with AsyncClient(base_url="http://test") as client:
        # Create products
        await client.post(
            "/api/products",
            json={
                "name": "Widget Pro",
                "slug": "widget-pro",
                "description": "Premium widget for professionals",
                "price": 99.99,
                "stock": 100
            }
        )

        # Search products
        response = await client.get("/api/products/search?query=widget")

        assert response.status_code == 200
        products = response.json()

        assert isinstance(products, list)
        assert len(products) >= 1


@pytest.mark.asyncio
async def test_low_stock_products():
    """Test getting products with low stock."""
    async with AsyncClient(base_url="http://test") as client:
        # Create a product with low stock
        await client.post(
            "/api/products",
            json={
                "name": "Low Stock Widget",
                "slug": "low-stock-widget",
                "description": "Widget with low inventory",
                "price": 49.99,
                "stock": 3
            }
        )

        # Get low stock products (threshold = 5)
        response = await client.get("/api/products/low-stock?threshold=5")

        assert response.status_code == 200
        products = response.json()

        assert isinstance(products, list)
        assert len(products) >= 1
        assert any(p["stock"] < 5 for p in products)
