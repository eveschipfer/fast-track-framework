"""
Pytest configuration and shared fixtures.

This file provides shared fixtures and configuration for all tests.
"""

import pytest
import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_data_dir(tmp_path):
    """
    Provide temporary directory for test data.

    Args:
        tmp_path: pytest built-in fixture for temporary directory

    Returns:
        Path object to temporary directory
    """
    return tmp_path


@pytest.fixture(scope="session", autouse=True)
def configure_sqlalchemy_for_tests():
    """
    Configure SQLAlchemy to handle multiple model definitions gracefully.

    During test collection, pytest imports all test modules, which can cause
    "Multiple classes found for path" errors when both app models and test
    models use the same class names (e.g., User, Post).

    This fixture doesn't clear metadata (which would remove table definitions),
    but instead relies on test models using unique class names or unique table names.
    """
    # No action needed - just a marker for documentation
    yield


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
