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


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
