"""
Integration Tests - Welcome Controller

This module tests the actual welcome controller routes to ensure
the proof-of-concept implementation works correctly.

KNOWN ISSUE (Sprint 5.0):
    These tests cause SQLAlchemy metadata conflicts when run with other
    integration tests due to ftf.main importing and initializing the app.
    Using lazy imports to avoid collection-time conflicts.
"""

import pytest
from fastapi.testclient import TestClient

# Lazy import to avoid collection-time metadata conflicts
def get_app():
    from jtc.main import app
    return app

def test_root_endpoint() -> None:
    """
    Test root endpoint returns API documentation.

    Verifies:
    - / route is accessible
    - Returns comprehensive framework info
    - Includes name, version, and features
    """
    client = TestClient(get_app())
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "Fast Track Framework"
    assert "version" in data
    assert "features" in data
    assert "endpoints" in data


def test_info_endpoint() -> None:
    """
    Test /info endpoint no longer exists (moved to /).

    The framework has evolved - API documentation is now at /
    instead of a separate /info endpoint.

    This test is kept for historical reference but marked to expect 404.
    """
    client = TestClient(get_app())
    response = client.get("/info")

    # /info endpoint no longer exists in ftf.main
    # (Functionality moved to / endpoint)
    assert response.status_code == 404


def test_health_endpoint() -> None:
    """
    Test health check endpoint.

    Verifies:
    - /health route is accessible
    - No dependencies required
    - Health status is returned with version info
    """
    client = TestClient(get_app())
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "framework" in data


def test_all_endpoints_with_same_client() -> None:
    """
    Test all endpoints using the same TestClient instance.

    Verifies:
    - Multiple requests work correctly
    - Service scope behaves as expected
    """
    client = TestClient(get_app())

    # Test root (API documentation)
    response1 = client.get("/")
    assert response1.status_code == 200
    assert "name" in response1.json()

    # Test health check
    response2 = client.get("/health")
    assert response2.status_code == 200
    assert response2.json()["status"] == "healthy"

    # Test docs endpoint (Swagger UI)
    response3 = client.get("/docs")
    assert response3.status_code == 200
