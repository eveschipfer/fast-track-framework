"""
Factory System Tests (Sprint 2.8)

This module contains comprehensive tests for the Factory and Seeder system.
Tests verify that factories correctly generate test data with Faker integration,
async database persistence, state management, and relationship hooks.

Test Coverage:
    - Factory.make() creates unpersisted instances
    - Factory.create() persists to database
    - Factory.create_batch() creates multiple records
    - Factory.state() modifies attributes
    - Relationship hooks create related models
    - Seeder.run() executes seeding logic
    - Seeder.call() orchestrates other seeders

Educational Note:
    These tests demonstrate "async first" testing patterns. Every database
    operation is async, and we use pytest-asyncio to handle async test functions.
"""

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fast_query import Base, BaseRepository, create_engine
from fast_query.seeding import Seeder, run_seeder, run_seeders
from app.models import Comment, Post, User
from tests.factories import CommentFactory, PostFactory, UserFactory


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
async def engine() -> AsyncEngine:
    """In-memory SQLite engine for fast tests."""
    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncSession:
    """Database session for each test."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        yield session


# ============================================================================
# FACTORY TESTS - Basic Operations
# ============================================================================


@pytest.mark.asyncio
async def test_factory_make_creates_unpersisted_instance(session: AsyncSession) -> None:
    """
    Test that make() creates an unpersisted model instance.

    This verifies that make() builds the model but doesn't save it to the
    database. The instance should have all attributes but no ID.
    """
    factory = UserFactory(session)

    # Create unpersisted user
    user = factory.make()

    # Should have attributes from definition()
    assert user.name is not None
    assert user.email is not None

    # Should NOT have an ID (not persisted)
    assert user.id is None

    # Verify it's not in the database
    repo = BaseRepository(session, User)
    users = await repo.all()
    assert len(users) == 0


@pytest.mark.asyncio
async def test_factory_make_accepts_attribute_overrides(session: AsyncSession) -> None:
    """
    Test that make() accepts explicit attribute overrides.

    Explicit kwargs should override the values from definition().
    """
    factory = UserFactory(session)

    # Override name and email
    user = factory.make(name="Alice", email="alice@test.com")

    assert user.name == "Alice"
    assert user.email == "alice@test.com"
    assert user.id is None  # Still unpersisted


@pytest.mark.asyncio
async def test_factory_create_persists_to_database(session: AsyncSession) -> None:
    """
    Test that create() persists the model to the database.

    This verifies that create() both builds and saves the model,
    resulting in an instance with an assigned ID.
    """
    factory = UserFactory(session)

    # Create and persist user
    user = await factory.create()

    # Should have an ID (persisted)
    assert user.id is not None
    assert user.name is not None
    assert user.email is not None

    # Verify it's in the database
    repo = BaseRepository(session, User)
    users = await repo.all()
    assert len(users) == 1
    assert users[0].id == user.id


@pytest.mark.asyncio
async def test_factory_create_accepts_attribute_overrides(session: AsyncSession) -> None:
    """
    Test that create() accepts explicit attribute overrides.
    """
    factory = UserFactory(session)

    # Override attributes
    user = await factory.create(name="Bob", email="bob@test.com")

    assert user.id is not None  # Persisted
    assert user.name == "Bob"
    assert user.email == "bob@test.com"

    # Verify in database
    repo = BaseRepository(session, User)
    found = await repo.find(user.id)
    assert found is not None
    assert found.name == "Bob"


@pytest.mark.asyncio
async def test_factory_create_batch_creates_multiple_records(
    session: AsyncSession,
) -> None:
    """
    Test that create_batch() creates multiple persisted records.

    Each record should have unique fake data (definition() called N times).
    """
    factory = UserFactory(session)

    # Create 10 users
    users = await factory.create_batch(10)

    # Should have 10 users
    assert len(users) == 10

    # All should be persisted with IDs
    assert all(user.id is not None for user in users)

    # All should have unique emails (faker generates unique values)
    emails = [user.email for user in users]
    assert len(set(emails)) == 10  # All unique

    # Verify in database
    repo = BaseRepository(session, User)
    db_users = await repo.all()
    assert len(db_users) == 10


@pytest.mark.asyncio
async def test_factory_create_batch_accepts_shared_attributes(
    session: AsyncSession,
) -> None:
    """
    Test that create_batch() can apply shared attributes to all instances.

    The shared kwargs should be applied to all instances, but faker-generated
    values should still be unique per instance.
    """
    factory = UserFactory(session)

    # Create batch with shared attribute
    users = await factory.create_batch(5, name="Test User")

    # All should have the same name
    assert all(user.name == "Test User" for user in users)

    # But all should have unique emails (from faker)
    emails = [user.email for user in users]
    assert len(set(emails)) == 5


# ============================================================================
# FACTORY TESTS - State Management
# ============================================================================


@pytest.mark.asyncio
async def test_factory_state_modifies_attributes(session: AsyncSession) -> None:
    """
    Test that state() allows modifying attributes via a callback.

    State modifiers should receive the current attributes and return
    modified attributes.
    """
    factory = UserFactory(session)

    # Create user with state modifier
    user = await factory.state(lambda attrs: {**attrs, "name": "Admin"}).create()

    assert user.name == "Admin"
    assert user.email is not None  # Still has email from definition()


@pytest.mark.asyncio
async def test_factory_state_can_chain_multiple_modifiers(
    session: AsyncSession,
) -> None:
    """
    Test that multiple state() calls can be chained.

    Each modifier should be applied in order.
    """
    factory = UserFactory(session)

    # Chain multiple state modifiers
    user = await (
        factory.state(lambda attrs: {**attrs, "name": "Admin"})
        .state(lambda attrs: {**attrs, "email": "admin@test.com"})
        .create()
    )

    assert user.name == "Admin"
    assert user.email == "admin@test.com"


@pytest.mark.asyncio
async def test_factory_state_does_not_mutate_original_factory(
    session: AsyncSession,
) -> None:
    """
    Test that state() returns a new factory instance.

    The original factory should remain unchanged (immutable pattern).
    """
    factory = UserFactory(session)

    # Create modified factory
    admin_factory = factory.state(lambda attrs: {**attrs, "name": "Admin"})

    # Original factory should be unchanged
    user1 = await factory.create()
    user2 = await admin_factory.create()

    assert user1.name != "Admin"  # Original factory
    assert user2.name == "Admin"  # Modified factory


@pytest.mark.asyncio
async def test_factory_reset_clears_states(session: AsyncSession) -> None:
    """
    Test that reset() clears all state modifiers.
    """
    factory = UserFactory(session)

    # Add state modifier
    factory = factory.state(lambda attrs: {**attrs, "name": "Admin"})

    # Reset
    factory = factory.reset()

    # Should use original definition() now
    user = await factory.create()
    assert user.name != "Admin"


# ============================================================================
# FACTORY TESTS - Relationship Hooks
# ============================================================================


@pytest.mark.asyncio
async def test_factory_has_posts_creates_related_posts(session: AsyncSession) -> None:
    """
    Test that has_posts() creates related posts after user creation.

    This tests the "magic method" pattern where relationship hooks
    automatically create related models.
    """
    factory = UserFactory(session)

    # Create user with posts
    user = await factory.has_posts(5).create()

    # Verify user was created
    assert user.id is not None

    # Verify posts were created
    post_repo = BaseRepository(session, Post)
    posts = await post_repo.query().where(Post.user_id == user.id).get()

    assert len(posts) == 5
    assert all(post.user_id == user.id for post in posts)


@pytest.mark.asyncio
async def test_factory_relationship_hooks_work_with_batch(
    session: AsyncSession,
) -> None:
    """
    Test that relationship hooks work with create_batch().

    Each user in the batch should get their own related posts.
    """
    factory = UserFactory(session)

    # Create 3 users, each with 2 posts
    users = await factory.has_posts(2).create_batch(3)

    assert len(users) == 3

    # Verify each user has 2 posts
    post_repo = BaseRepository(session, Post)
    for user in users:
        posts = await post_repo.query().where(Post.user_id == user.id).get()
        assert len(posts) == 2


# ============================================================================
# FACTORY TESTS - Complex Scenarios
# ============================================================================


@pytest.mark.asyncio
async def test_factory_with_required_foreign_keys(session: AsyncSession) -> None:
    """
    Test creating models with required foreign keys.

    PostFactory requires a user_id, so we must provide it explicitly.
    """
    # Create a user first
    user_factory = UserFactory(session)
    user = await user_factory.create()

    # Create post with user_id
    post_factory = PostFactory(session)
    post = await post_factory.create(user_id=user.id)

    assert post.id is not None
    assert post.user_id == user.id
    assert post.title is not None
    assert post.content is not None


@pytest.mark.asyncio
async def test_factory_nested_relationships(session: AsyncSession) -> None:
    """
    Test creating nested relationships (user -> posts -> comments).

    This tests a complex scenario where we create a full object graph.
    """
    # First, we need to create a post with comments capability
    user_factory = UserFactory(session)
    user = await user_factory.create()

    # Create post with comments
    post_factory = PostFactory(session)
    post = await post_factory.has_comments(3).create(user_id=user.id)

    # Verify post was created
    assert post.id is not None

    # Verify comments were created
    comment_repo = BaseRepository(session, Comment)
    comments = await comment_repo.query().where(Comment.post_id == post.id).get()

    assert len(comments) == 3
    assert all(comment.post_id == post.id for comment in comments)


@pytest.mark.asyncio
async def test_factory_faker_generates_unique_data(session: AsyncSession) -> None:
    """
    Test that Faker generates unique data for each instance.

    This verifies that each call to make() or create() regenerates
    the fake data, rather than reusing cached values.
    """
    factory = UserFactory(session)

    # Create multiple users
    users = await factory.create_batch(5)

    # All names should be different (very unlikely to get duplicates)
    names = [user.name for user in users]
    assert len(set(names)) == 5

    # All emails should be unique
    emails = [user.email for user in users]
    assert len(set(emails)) == 5


# ============================================================================
# SEEDER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_seeder_run_method_executes(session: AsyncSession) -> None:
    """
    Test that Seeder.run() executes the seeding logic.
    """

    class TestSeeder(Seeder):
        async def run(self) -> None:
            factory = UserFactory(self.session)
            await factory.create_batch(5)

    # Run seeder
    seeder = TestSeeder(session)
    await seeder.run()

    # Verify users were created
    repo = BaseRepository(session, User)
    users = await repo.all()
    assert len(users) == 5


@pytest.mark.asyncio
async def test_seeder_call_runs_other_seeders(session: AsyncSession) -> None:
    """
    Test that Seeder.call() can orchestrate other seeders.
    """

    class UserTestSeeder(Seeder):
        async def run(self) -> None:
            factory = UserFactory(self.session)
            await factory.create_batch(3)

    class PostTestSeeder(Seeder):
        async def run(self) -> None:
            # Get first user
            repo = BaseRepository(self.session, User)
            users = await repo.all()
            if users:
                factory = PostFactory(self.session)
                await factory.create_batch(2, user_id=users[0].id)

    class MasterSeeder(Seeder):
        async def run(self) -> None:
            await self.call(UserTestSeeder)
            await self.call(PostTestSeeder)

    # Run master seeder
    seeder = MasterSeeder(session)
    await seeder.run()

    # Verify both seeders ran
    user_repo = BaseRepository(session, User)
    users = await user_repo.all()
    assert len(users) == 3

    post_repo = BaseRepository(session, Post)
    posts = await post_repo.all()
    assert len(posts) == 2


@pytest.mark.asyncio
async def test_run_seeder_helper_function(session: AsyncSession) -> None:
    """
    Test the run_seeder() helper function.
    """

    class HelperTestSeeder(Seeder):
        async def run(self) -> None:
            factory = UserFactory(self.session)
            await factory.create()

    # Use helper function
    await run_seeder(HelperTestSeeder, session)

    # Verify seeder ran
    repo = BaseRepository(session, User)
    users = await repo.all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_run_seeders_helper_runs_multiple_seeders(
    session: AsyncSession,
) -> None:
    """
    Test the run_seeders() helper that runs multiple seeders in sequence.
    """

    class Seeder1(Seeder):
        async def run(self) -> None:
            factory = UserFactory(self.session)
            await factory.create_batch(2)

    class Seeder2(Seeder):
        async def run(self) -> None:
            factory = UserFactory(self.session)
            await factory.create_batch(3)

    # Run multiple seeders
    await run_seeders([Seeder1, Seeder2], session)

    # Verify both ran
    repo = BaseRepository(session, User)
    users = await repo.all()
    assert len(users) == 5  # 2 + 3


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_factory_raises_error_without_model_class() -> None:
    """
    Test that Factory raises AttributeError if _model_class is not set.
    """
    from fast_query.factories import Factory
    from typing import Any

    # Create invalid factory (no _model_class)
    class InvalidFactory(Factory[User]):
        def definition(self) -> dict[str, Any]:
            return {}

    # Should raise on instantiation
    with pytest.raises(AttributeError, match="_model_class"):
        factory = InvalidFactory(None)  # type: ignore


# ============================================================================
# INTEGRATION TESTS - Real-World Scenarios
# ============================================================================


@pytest.mark.asyncio
async def test_realistic_blog_dataset_creation(session: AsyncSession) -> None:
    """
    Integration test: Create a realistic blog dataset.

    This demonstrates a real-world scenario where we create:
    - 10 users
    - 5 posts per user (50 total)
    - Each post with varied comments
    """
    user_factory = UserFactory(session)

    # Create 10 users, each with 5 posts
    users = await user_factory.has_posts(5).create_batch(10)

    # Verify users
    assert len(users) == 10

    # Verify posts
    post_repo = BaseRepository(session, Post)
    all_posts = await post_repo.all()
    assert len(all_posts) == 50

    # Verify each user has 5 posts
    for user in users:
        user_posts = await post_repo.query().where(Post.user_id == user.id).get()
        assert len(user_posts) == 5
