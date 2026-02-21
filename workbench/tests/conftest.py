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


@pytest.fixture(autouse=True)
def reset_db_engine():
    """
    Reset the fast_query engine singleton before each test.

    WHY THIS IS NEEDED:
    fast_query.create_engine() caches the first engine as a module-level singleton
    (if _engine is None: ...). This is correct for production — engines are expensive
    and should be shared across requests.

    In tests, however, importing the app (e.g. `from jtc.main import app`) triggers
    engine creation with the real file-based SQLite URL at collection time. Any
    subsequent test fixture that calls create_engine("sqlite+aiosqlite:///:memory:")
    gets the pre-cached file-based engine instead of a fresh in-memory one,
    causing test data to accumulate in the real database across runs.

    This autouse fixture resets the singleton to None before each test so that
    the per-test engine fixture always creates a fresh in-memory engine.
    """
    from fast_query import reset_engine
    reset_engine()
    yield


@pytest.fixture
async def db_session():
    """
    Provide an async database session for tests (Sprint 5.5).

    Creates an in-memory SQLite database for testing pagination
    and other database features.

    Yields:
        AsyncSession: Async database session for testing
    """
    from fast_query import create_engine
    from fast_query.session import AsyncSessionFactory

    # Create in-memory database for testing
    engine = create_engine("sqlite+aiosqlite:///:memory:")

    # Create session factory
    factory = AsyncSessionFactory()
    factory._engine = engine

    # Create session
    async with factory() as session:
        yield session

    # Cleanup
    await engine.dispose()


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
