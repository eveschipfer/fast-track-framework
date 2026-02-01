"""
Integration Tests for Database with FastAPI

Tests full request lifecycle with scoped sessions and middleware.

These tests validate:
1. Database engine registration (singleton)
2. Session registration (scoped)
3. Middleware manages session lifecycle
4. Repository pattern works in HTTP routes
5. Sessions are isolated between requests
6. Proper cleanup on request end

Run:
    pytest tests/integration/test_database_integration.py -v
    pytest tests/integration/test_database_integration.py -v --tb=short
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from fast_query import AsyncSessionFactory, Base, BaseRepository, create_engine
from ftf.http import FastTrackFramework, Inject
from ftf.http.app import ScopedMiddleware


# ============================================================================
# TEST FIXTURES - Model and Repository
# ============================================================================


class IntegrationTestUser(Base):
    """Test user model for integration tests.

    Note: Renamed from 'User' to avoid conflicts with app.models.User
    when running full test suite.
    """

    __tablename__ = "integration_test_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)


class IntegrationTestUserRepository(BaseRepository[IntegrationTestUser]):
    """Test user repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, IntegrationTestUser)


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
async def app() -> FastTrackFramework:
    """
    FastAPI app with database integration.

    This fixture sets up the complete stack:
    1. In-memory SQLite database
    2. AsyncEngine registered as singleton
    3. AsyncSession registered as scoped
    4. Middleware for session lifecycle
    5. UserRepository registered as transient
    """
    app = FastTrackFramework()

    # Setup in-memory database
    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Register engine as singleton
    app.container.register(AsyncEngine, scope="singleton")
    app.container._singletons[AsyncEngine] = engine

    # Register session factory (scoped)
    def session_factory() -> AsyncSession:
        factory = AsyncSessionFactory()
        return factory()

    app.register(AsyncSession, implementation=session_factory, scope="scoped")

    # Register repository (transient)
    app.register(IntegrationTestUserRepository, scope="transient")

    # Add middleware for scoped session lifecycle
    app.add_middleware(ScopedMiddleware)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield app

    # Cleanup
    await engine.dispose()


# ============================================================================
# BASIC INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_database_session_injection(app: FastTrackFramework) -> None:
    """Test that AsyncSession can be injected into routes."""

    @app.get("/test-session")
    async def test_route(session: AsyncSession = Inject(AsyncSession)) -> dict:
        # Verify session is valid
        assert session is not None
        assert isinstance(session, AsyncSession)
        return {"status": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test-session")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_repository_injection(app: FastTrackFramework) -> None:
    """Test that repositories can be injected into routes."""

    @app.get("/test-repo")
    async def test_route(repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)) -> dict:
        assert repo is not None
        assert isinstance(repo, IntegrationTestUserRepository)
        count = await repo.count()
        return {"count": count}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/test-repo")
        assert response.status_code == 200
        assert response.json() == {"count": 0}


# ============================================================================
# CRUD OPERATION TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_user_via_http(app: FastTrackFramework) -> None:
    """Test creating a user through HTTP endpoint."""

    @app.post("/users")
    async def create_user(repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)) -> dict:
        user = IntegrationTestUser(name="Alice", email="alice@example.com")
        created = await repo.create(user)
        return {"id": created.id, "name": created.name, "email": created.email}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/users")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice"
        assert data["email"] == "alice@example.com"
        assert "id" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_user_via_http(app: FastTrackFramework) -> None:
    """Test reading a user through HTTP endpoint."""

    @app.post("/users")
    async def create_user(repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)) -> dict:
        user = IntegrationTestUser(name="Bob", email="bob@example.com")
        created = await repo.create(user)
        return {"id": created.id}

    @app.get("/users/{user_id}")
    async def get_user(
        user_id: int, repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)
    ) -> dict:
        user = await repo.find_or_fail(user_id)
        return {"id": user.id, "name": user.name, "email": user.email}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create user
        create_response = await client.post("/users")
        user_id = create_response.json()["id"]

        # Read user
        get_response = await client.get(f"/users/{user_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "Bob"
        assert data["email"] == "bob@example.com"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_user_via_http(app: FastTrackFramework) -> None:
    """Test updating a user through HTTP endpoint."""

    @app.post("/users")
    async def create_user(repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)) -> dict:
        user = IntegrationTestUser(name="Charlie", email="charlie@example.com")
        created = await repo.create(user)
        return {"id": created.id}

    @app.put("/users/{user_id}")
    async def update_user(
        user_id: int, repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)
    ) -> dict:
        user = await repo.find_or_fail(user_id)
        user.name = "Charlie Updated"
        updated = await repo.update(user)
        return {"id": updated.id, "name": updated.name}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create user
        create_response = await client.post("/users")
        user_id = create_response.json()["id"]

        # Update user
        update_response = await client.put(f"/users/{user_id}")
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Charlie Updated"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_user_via_http(app: FastTrackFramework) -> None:
    """Test deleting a user through HTTP endpoint."""

    @app.post("/users")
    async def create_user(repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)) -> dict:
        user = IntegrationTestUser(name="Dave", email="dave@example.com")
        created = await repo.create(user)
        return {"id": created.id}

    @app.delete("/users/{user_id}")
    async def delete_user(
        user_id: int, repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)
    ) -> dict:
        user = await repo.find_or_fail(user_id)
        await repo.delete(user)
        return {"deleted": True}

    @app.get("/users/{user_id}")
    async def get_user(
        user_id: int, repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)
    ) -> dict:
        user = await repo.find_or_fail(user_id)
        return {"id": user.id}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Create user
        create_response = await client.post("/users")
        user_id = create_response.json()["id"]

        # Delete user
        delete_response = await client.delete(f"/users/{user_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] is True

        # Verify deletion (should 404)
        get_response = await client.get(f"/users/{user_id}")
        assert get_response.status_code == 404


# ============================================================================
# SESSION LIFECYCLE TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scoped_session_same_within_request(app: FastTrackFramework) -> None:
    """Test that same session is used within a single request."""

    session_ids: list[int] = []

    @app.get("/test")
    async def test_route(session: AsyncSession = Inject(AsyncSession)) -> dict:
        # Record session ID
        session_ids.append(id(session))

        # Resolve session again in same request
        session2 = app.container.resolve(AsyncSession)
        session_ids.append(id(session2))

        return {"status": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.get("/test")

    # Both should be same session
    assert len(session_ids) == 2
    assert session_ids[0] == session_ids[1]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_scoped_session_different_between_requests(
    app: FastTrackFramework,
) -> None:
    """Test that different sessions are used between requests."""

    session_ids: list[int] = []

    @app.get("/test")
    async def test_route(session: AsyncSession = Inject(AsyncSession)) -> dict:
        session_ids.append(id(session))
        return {"status": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.get("/test")
        await client.get("/test")

    # Should be different sessions
    assert len(session_ids) == 2
    assert session_ids[0] != session_ids[1]


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_find_or_fail_returns_404(app: FastTrackFramework) -> None:
    """Test that find_or_fail properly raises 404."""

    @app.get("/users/{user_id}")
    async def get_user(
        user_id: int, repo: IntegrationTestUserRepository = Inject(IntegrationTestUserRepository)
    ) -> dict:
        user = await repo.find_or_fail(user_id)
        return {"id": user.id, "name": user.name}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/users/999")
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
