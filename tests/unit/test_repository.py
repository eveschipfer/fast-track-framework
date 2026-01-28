"""
Unit Tests for BaseRepository

Tests CRUD operations with in-memory SQLite database.

These tests validate:
1. Repository create/read/update/delete operations
2. Pagination (all method)
3. Error handling (find_or_fail with 404)
4. Count aggregation
5. Custom repository methods (find_by_email)

Run:
    pytest tests/unit/test_repository.py -v
    pytest tests/unit/test_repository.py -v --tb=short
"""

import pytest
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from ftf.database import Base, BaseRepository, create_engine


# ============================================================================
# TEST FIXTURES - Model for Testing
# ============================================================================


class User(Base):
    """Test user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)


class UserRepository(BaseRepository[User]):
    """Test user repository with custom methods."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def find_by_email(self, email: str) -> User | None:
        """Custom query: find user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
async def engine() -> AsyncEngine:
    """In-memory SQLite engine for fast tests."""
    # Note: Using global create_engine for consistency with production usage
    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncSession:
    """Database session for each test."""
    factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with factory() as session:
        yield session


@pytest.fixture
def user_repo(session: AsyncSession) -> UserRepository:
    """User repository fixture."""
    return UserRepository(session)


# ============================================================================
# CREATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_create_user(user_repo: UserRepository) -> None:
    """Test creating a new user."""
    user = User(name="Alice", email="alice@example.com")
    created = await user_repo.create(user)

    assert created.id is not None
    assert created.name == "Alice"
    assert created.email == "alice@example.com"


@pytest.mark.asyncio
async def test_create_multiple_users(user_repo: UserRepository) -> None:
    """Test creating multiple users."""
    user1 = await user_repo.create(User(name="Alice", email="alice@example.com"))
    user2 = await user_repo.create(User(name="Bob", email="bob@example.com"))

    assert user1.id != user2.id
    assert user1.id is not None
    assert user2.id is not None


# ============================================================================
# READ TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_find_user_by_id(user_repo: UserRepository) -> None:
    """Test finding user by primary key."""
    user = await user_repo.create(User(name="Bob", email="bob@example.com"))
    found = await user_repo.find(user.id)

    assert found is not None
    assert found.id == user.id
    assert found.name == "Bob"
    assert found.email == "bob@example.com"


@pytest.mark.asyncio
async def test_find_nonexistent_user_returns_none(
    user_repo: UserRepository,
) -> None:
    """Test that finding nonexistent user returns None."""
    found = await user_repo.find(999)
    assert found is None


@pytest.mark.asyncio
async def test_find_or_fail_returns_user(user_repo: UserRepository) -> None:
    """Test find_or_fail returns user when found."""
    user = await user_repo.create(User(name="Charlie", email="charlie@example.com"))
    found = await user_repo.find_or_fail(user.id)

    assert found.id == user.id
    assert found.name == "Charlie"


@pytest.mark.asyncio
async def test_find_or_fail_raises_404(user_repo: UserRepository) -> None:
    """Test find_or_fail raises HTTPException(404) when not found."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await user_repo.find_or_fail(999)

    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_all_returns_all_users(user_repo: UserRepository) -> None:
    """Test fetching all users."""
    await user_repo.create(User(name="Alice", email="alice@example.com"))
    await user_repo.create(User(name="Bob", email="bob@example.com"))
    await user_repo.create(User(name="Charlie", email="charlie@example.com"))

    users = await user_repo.all()

    assert len(users) == 3
    names = {user.name for user in users}
    assert names == {"Alice", "Bob", "Charlie"}


@pytest.mark.asyncio
async def test_all_with_pagination(user_repo: UserRepository) -> None:
    """Test pagination in all() method."""
    # Create 5 users
    for i in range(5):
        await user_repo.create(User(name=f"User{i}", email=f"user{i}@example.com"))

    # Get first page (2 items)
    page1 = await user_repo.all(limit=2, offset=0)
    assert len(page1) == 2

    # Get second page (2 items)
    page2 = await user_repo.all(limit=2, offset=2)
    assert len(page2) == 2

    # Get third page (1 item)
    page3 = await user_repo.all(limit=2, offset=4)
    assert len(page3) == 1

    # Ensure no overlap
    page1_ids = {user.id for user in page1}
    page2_ids = {user.id for user in page2}
    page3_ids = {user.id for user in page3}

    assert len(page1_ids & page2_ids) == 0
    assert len(page2_ids & page3_ids) == 0


# ============================================================================
# UPDATE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_update_user(user_repo: UserRepository) -> None:
    """Test updating a user."""
    user = await user_repo.create(User(name="Alice", email="alice@example.com"))

    # Modify user
    user.name = "Alice Updated"
    updated = await user_repo.update(user)

    assert updated.id == user.id
    assert updated.name == "Alice Updated"

    # Verify persistence
    found = await user_repo.find(user.id)
    assert found is not None
    assert found.name == "Alice Updated"


@pytest.mark.asyncio
async def test_update_multiple_fields(user_repo: UserRepository) -> None:
    """Test updating multiple fields."""
    user = await user_repo.create(User(name="Bob", email="bob@example.com"))

    # Modify multiple fields
    user.name = "Bob Smith"
    user.email = "bob.smith@example.com"
    updated = await user_repo.update(user)

    assert updated.name == "Bob Smith"
    assert updated.email == "bob.smith@example.com"


# ============================================================================
# DELETE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_delete_user(user_repo: UserRepository) -> None:
    """Test deleting a user."""
    user = await user_repo.create(User(name="Charlie", email="charlie@example.com"))
    user_id = user.id

    # Delete user
    await user_repo.delete(user)

    # Verify deletion
    found = await user_repo.find(user_id)
    assert found is None


@pytest.mark.asyncio
async def test_delete_does_not_affect_other_users(
    user_repo: UserRepository,
) -> None:
    """Test that deleting one user doesn't affect others."""
    user1 = await user_repo.create(User(name="Alice", email="alice@example.com"))
    user2 = await user_repo.create(User(name="Bob", email="bob@example.com"))

    # Delete user1
    await user_repo.delete(user1)

    # user2 should still exist
    found = await user_repo.find(user2.id)
    assert found is not None
    assert found.name == "Bob"


# ============================================================================
# COUNT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_count_empty_table(user_repo: UserRepository) -> None:
    """Test counting records in empty table."""
    count = await user_repo.count()
    assert count == 0


@pytest.mark.asyncio
async def test_count_with_records(user_repo: UserRepository) -> None:
    """Test counting records."""
    await user_repo.create(User(name="Alice", email="alice@example.com"))
    await user_repo.create(User(name="Bob", email="bob@example.com"))
    await user_repo.create(User(name="Charlie", email="charlie@example.com"))

    count = await user_repo.count()
    assert count == 3


@pytest.mark.asyncio
async def test_count_after_delete(user_repo: UserRepository) -> None:
    """Test count decreases after deletion."""
    user1 = await user_repo.create(User(name="Alice", email="alice@example.com"))
    await user_repo.create(User(name="Bob", email="bob@example.com"))

    assert await user_repo.count() == 2

    await user_repo.delete(user1)

    assert await user_repo.count() == 1


# ============================================================================
# CUSTOM METHOD TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_find_by_email(user_repo: UserRepository) -> None:
    """Test custom repository method."""
    await user_repo.create(User(name="Alice", email="alice@example.com"))

    found = await user_repo.find_by_email("alice@example.com")

    assert found is not None
    assert found.name == "Alice"


@pytest.mark.asyncio
async def test_find_by_email_not_found(user_repo: UserRepository) -> None:
    """Test custom method returns None when not found."""
    found = await user_repo.find_by_email("nonexistent@example.com")
    assert found is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
