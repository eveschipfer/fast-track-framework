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
    from ftf.main import app
    return app

def test_root_endpoint() -> None:
    """
    Test root endpoint returns welcome message.

    Verifies:
    - / route is accessible
    - MessageService is injected correctly
    - Welcome message is returned
    """
    client = TestClient(get_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()
    assert "Welcome to Fast Track Framework" in response.json()["message"]


def test_info_endpoint() -> None:
    """
    Test info endpoint returns framework information.

    Verifies:
    - /info route is accessible
    - MessageService is injected correctly
    - Framework info is returned
    """
    client = TestClient(get_app())
    response = client.get("/info")

    assert response.status_code == 200
    data = response.json()

    # Verify expected fields
    assert "framework" in data
    assert "version" in data
    assert "description" in data
    assert "status" in data

    # Verify values
    assert data["framework"] == "Fast Track Framework"
    assert data["version"] == "0.1.0"


def test_health_endpoint() -> None:
    """
    Test health check endpoint.

    Verifies:
    - /health route is accessible
    - No dependencies required
    - Health status is returned
    """
    client = TestClient(get_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_all_endpoints_with_same_client() -> None:
    """
    Test all endpoints using the same TestClient instance.

    Verifies:
    - Multiple requests work correctly
    - Service scope behaves as expected
    """
    client = TestClient(get_app())

    # Test root
    response1 = client.get("/")
    assert response1.status_code == 200

    # Test info
    response2 = client.get("/info")
    assert response2.status_code == 200

    # Test health
    response3 = client.get("/health")
    assert response3.status_code == 200
