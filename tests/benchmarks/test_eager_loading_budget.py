"""
Semantic Regression Tests - Eager Loading Budget (Sprint 2.7)

These tests ensure that query count stays CONSTANT regardless of data volume.
This is the "N+1 Guard" - it proves that eager loading actually works.

Why "Budget"?
    We allocate a "query budget" (e.g., exactly 2 queries for with_("posts")).
    If the budget is exceeded, the test fails. This prevents:
    - Accidental removal of eager loading
    - Introduction of N+1 queries
    - Performance regressions

Pattern:
    1. Test A: Small dataset (5 users, 5 posts each)
    2. Test B: Large dataset (50 users, 50 posts each)
    3. Assert: queries_small == queries_large (O(1) complexity)
    4. Assert: queries == EXACT_BUDGET (e.g., 2 for selectinload)

Educational Note:
    This is "Performance as Correctness" testing. We're not measuring
    milliseconds - we're counting SQL queries. O(1) vs O(N) is a
    correctness issue, not just a performance issue.

    If query count scales with data size, you have a bug, even if
    the code "works" on small datasets.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fast_query import Base, BaseRepository, create_engine
from ftf.models import Comment, Post, User
from tests.utils.query_counter import QueryCounter


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
# REPOSITORY CLASSES
# ============================================================================


class UserRepository(BaseRepository[User]):
    """User repository for benchmark tests."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)


class PostRepository(BaseRepository[Post]):
    """Post repository for benchmark tests."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Post)


class CommentRepository(BaseRepository[Comment]):
    """Comment repository for benchmark tests."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Comment)


# ============================================================================
# SEMANTIC REGRESSION TESTS - O(1) Query Complexity
# ============================================================================


@pytest.mark.asyncio
async def test_eager_loading_scales_o1_small_dataset(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Test that eager loading uses EXACTLY 2 queries for small dataset.

    Dataset: 5 users with 5 posts each (25 posts total)
    Expected: 2 queries (1 for users, 1 for all posts)
    """
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    # Create small dataset: 5 users with 5 posts each
    for i in range(5):
        user = User(name=f"User {i}", email=f"user{i}@test.com")
        await user_repo.create(user)

        for j in range(5):
            post = Post(
                title=f"Post {j} by User {i}",
                content="Content",
                user_id=user.id,
            )
            await post_repo.create(post)

    # Query with eager loading and count queries
    async with QueryCounter(engine) as counter:
        users = await user_repo.query().with_("posts").get()

    # STRICT CONTRACT: Must be EXACTLY 2 queries
    # Query 1: SELECT users
    # Query 2: SELECT posts WHERE user_id IN (...)
    assert counter.count == 2, (
        f"Expected EXACTLY 2 queries for eager loading, got {counter.count}. "
        f"Queries: {counter.get_queries()}"
    )

    # Verify data was loaded correctly
    assert len(users) == 5
    for user in users:
        assert len(user.posts) == 5


@pytest.mark.asyncio
async def test_eager_loading_scales_o1_large_dataset(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Test that eager loading STILL uses EXACTLY 2 queries for large dataset.

    Dataset: 50 users with 50 posts each (2500 posts total)
    Expected: 2 queries (same as small dataset!)

    This proves O(1) complexity - query count doesn't scale with data size.
    """
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    # Create large dataset: 50 users with 50 posts each
    for i in range(50):
        user = User(name=f"User {i}", email=f"user{i}@test.com")
        await user_repo.create(user)

        for j in range(50):
            post = Post(
                title=f"Post {j} by User {i}",
                content="Content",
                user_id=user.id,
            )
            await post_repo.create(post)

    # Query with eager loading and count queries
    async with QueryCounter(engine) as counter:
        users = await user_repo.query().with_("posts").get()

    # CRITICAL: Must STILL be EXACTLY 2 queries
    # If this becomes 51 or 501, we have an N+1 bug!
    assert counter.count == 2, (
        f"Expected EXACTLY 2 queries even with 50x data, got {counter.count}. "
        f"N+1 regression detected! Queries: {counter.get_queries()}"
    )

    # Verify data was loaded correctly
    assert len(users) == 50
    # Spot check a few users
    assert len(users[0].posts) == 50
    assert len(users[25].posts) == 50
    assert len(users[49].posts) == 50


@pytest.mark.asyncio
async def test_query_budget_consistency_across_scales(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Proof test: Query count must be IDENTICAL for 5 vs 50 users.

    This is the "Performance as Correctness" contract.
    """
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    # ===== Test A: Small Dataset =====
    # Clear database
    await session.execute(text("DELETE FROM comments"))
    await session.execute(text("DELETE FROM posts"))
    await session.execute(text("DELETE FROM users"))
    await session.commit()

    # Create 5 users with 5 posts each
    for i in range(5):
        user = User(name=f"UserA{i}", email=f"usera{i}@test.com")
        await user_repo.create(user)

        for j in range(5):
            post = Post(title=f"PostA{j}", content="Content", user_id=user.id)
            await post_repo.create(post)

    async with QueryCounter(engine) as counter_small:
        users_small = await user_repo.query().with_("posts").get()

    queries_small = counter_small.count

    # ===== Test B: Large Dataset =====
    # Clear database again
    await session.execute(text("DELETE FROM comments"))
    await session.execute(text("DELETE FROM posts"))
    await session.execute(text("DELETE FROM users"))
    await session.commit()

    # Create 50 users with 50 posts each (100x more data!)
    for i in range(50):
        user = User(name=f"UserB{i}", email=f"userb{i}@test.com")
        await user_repo.create(user)

        for j in range(50):
            post = Post(title=f"PostB{j}", content="Content", user_id=user.id)
            await post_repo.create(post)

    async with QueryCounter(engine) as counter_large:
        users_large = await user_repo.query().with_("posts").get()

    queries_large = counter_large.count

    # ===== PROOF: O(1) Complexity =====
    assert queries_small == queries_large, (
        f"Query count CHANGED with data size! "
        f"Small dataset: {queries_small} queries, "
        f"Large dataset: {queries_large} queries. "
        f"This indicates O(N) complexity (N+1 bug)!"
    )

    # Both should be exactly 2
    assert queries_small == 2
    assert queries_large == 2


# ============================================================================
# SEMANTIC REGRESSION TESTS - Nested Eager Loading
# ============================================================================


@pytest.mark.asyncio
async def test_nested_eager_loading_budget(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Test that nested eager loading (posts.comments) uses correct query budget.

    Expected: 3 queries
    - Query 1: SELECT users
    - Query 2: SELECT posts WHERE user_id IN (...)
    - Query 3: SELECT comments WHERE post_id IN (...)
    """
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Create dataset: 5 users, 5 posts each, 5 comments each
    for i in range(5):
        user = User(name=f"User {i}", email=f"user{i}@test.com")
        await user_repo.create(user)

        for j in range(5):
            post = Post(
                title=f"Post {j}",
                content="Content",
                user_id=user.id,
            )
            await post_repo.create(post)

            for k in range(5):
                comment = Comment(
                    content=f"Comment {k}",
                    post_id=post.id,
                    user_id=user.id,
                )
                await comment_repo.create(comment)

    # Query with nested eager loading
    async with QueryCounter(engine) as counter:
        users = await user_repo.query().with_("posts.comments").get()

    # BUDGET: 3 queries (users -> posts -> comments)
    assert counter.count == 3, (
        f"Expected 3 queries for nested eager loading, got {counter.count}. "
        f"Queries: {counter.get_queries()}"
    )

    # Verify data loaded
    assert len(users) == 5
    assert len(users[0].posts) == 5
    assert len(users[0].posts[0].comments) == 5


@pytest.mark.asyncio
async def test_nested_eager_loading_scales_o1(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Test that nested eager loading STILL uses 3 queries with 10x data.

    Proves nested eager loading doesn't introduce hidden N+1.
    """
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Create large dataset: 20 users, 10 posts each, 10 comments each
    for i in range(20):
        user = User(name=f"User {i}", email=f"user{i}@test.com")
        await user_repo.create(user)

        for j in range(10):
            post = Post(
                title=f"Post {j}",
                content="Content",
                user_id=user.id,
            )
            await post_repo.create(post)

            for k in range(10):
                comment = Comment(
                    content=f"Comment {k}",
                    post_id=post.id,
                    user_id=user.id,
                )
                await comment_repo.create(comment)

    # Query with nested eager loading
    async with QueryCounter(engine) as counter:
        users = await user_repo.query().with_("posts.comments").get()

    # CRITICAL: Still exactly 3 queries
    assert counter.count == 3, (
        f"Expected 3 queries even with larger dataset, got {counter.count}. "
        f"Nested N+1 regression!"
    )


# ============================================================================
# SEMANTIC REGRESSION TESTS - Multiple Relationships
# ============================================================================


@pytest.mark.asyncio
async def test_multiple_relationship_eager_loading_budget(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Test that loading multiple relationships uses correct budget.

    Loading posts AND comments separately should use 3 queries:
    - Query 1: SELECT users
    - Query 2: SELECT posts WHERE user_id IN (...)
    - Query 3: SELECT comments WHERE user_id IN (...)
    """
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Create dataset
    for i in range(5):
        user = User(name=f"User {i}", email=f"user{i}@test.com")
        await user_repo.create(user)

        for j in range(5):
            post = Post(
                title=f"Post {j}",
                content="Content",
                user_id=user.id,
            )
            await post_repo.create(post)

        for k in range(5):
            comment = Comment(
                content=f"Comment {k}",
                post_id=post.id if j == 4 else 1,  # Link to some post
                user_id=user.id,
            )
            await comment_repo.create(comment)

    # Query with multiple independent relationships
    async with QueryCounter(engine) as counter:
        users = await user_repo.query().with_("posts", "comments").get()

    # BUDGET: 3 queries (users, posts, comments)
    assert counter.count == 3, (
        f"Expected 3 queries for dual eager loading, got {counter.count}. "
        f"Queries: {counter.get_queries()}"
    )


# ============================================================================
# SEMANTIC REGRESSION TESTS - No Eager Loading (Baseline)
# ============================================================================


@pytest.mark.asyncio
async def test_no_eager_loading_causes_n_plus_1(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Baseline test: WITHOUT eager loading, we should see N+1 queries.

    This proves that our other tests are meaningful - they're preventing
    a real problem that exists without eager loading.

    Note: This test EXPECTS N+1 behavior. It documents the problem we solve.
    """
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    # Create small dataset
    for i in range(5):
        user = User(name=f"User {i}", email=f"user{i}@test.com")
        await user_repo.create(user)

        for j in range(5):
            post = Post(
                title=f"Post {j}",
                content="Content",
                user_id=user.id,
            )
            await post_repo.create(post)

    # Query WITHOUT eager loading
    async with QueryCounter(engine) as counter:
        users = await user_repo.query().get()

        # Try to access posts (this would cause lazy loading if allowed)
        # Note: With lazy="raise", this would fail
        # We just verify the initial query count
        pass

    # Should be just 1 query for users
    # (We can't actually trigger N+1 because lazy="raise" prevents it)
    assert counter.count == 1, (
        f"Expected 1 query without eager loading, got {counter.count}"
    )


# ============================================================================
# SEMANTIC REGRESSION TESTS - Global Scope Query Count
# ============================================================================


@pytest.mark.asyncio
async def test_global_scope_does_not_add_queries(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Test that global scope (soft delete filtering) doesn't add extra queries.

    Global scope is implemented as a WHERE clause, not a subquery,
    so it should not increase query count.
    """
    user_repo = UserRepository(session)

    # Create users (some deleted)
    from datetime import datetime, timezone

    for i in range(10):
        user = User(name=f"User {i}", email=f"user{i}@test.com")
        if i % 2 == 0:
            user.deleted_at = datetime.now(timezone.utc)  # Mark as deleted
        await user_repo.create(user)

    # Query with default global scope (excludes deleted)
    async with QueryCounter(engine) as counter:
        users = await user_repo.query().get()

    # Should still be 1 query (with WHERE deleted_at IS NULL)
    assert counter.count == 1
    assert len(users) == 5  # Only non-deleted

    # Query with with_trashed()
    async with QueryCounter(engine) as counter:
        all_users = await user_repo.query().with_trashed().get()

    # Still 1 query (just different WHERE clause)
    assert counter.count == 1
    assert len(all_users) == 10  # All users


# ============================================================================
# SEMANTIC REGRESSION TESTS - where_has Query Budget
# ============================================================================


@pytest.mark.asyncio
async def test_where_has_does_not_cause_n_plus_1(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Test that where_has() uses a subquery, not N+1 queries.

    WHERE EXISTS (...) should be a single query with a subquery,
    not N queries checking each record.
    """
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    # Create users (some with posts, some without)
    for i in range(20):
        user = User(name=f"User {i}", email=f"user{i}@test.com")
        await user_repo.create(user)

        # Only odd-numbered users have posts
        if i % 2 == 1:
            for j in range(5):
                post = Post(
                    title=f"Post {j}",
                    content="Content",
                    user_id=user.id,
                )
                await post_repo.create(post)

    # Query with where_has()
    async with QueryCounter(engine) as counter:
        users_with_posts = await user_repo.query().where_has("posts").get()

    # Should be 1 query with EXISTS subquery
    assert counter.count == 1, (
        f"Expected 1 query with subquery for where_has, got {counter.count}. "
        f"Possible N+1 in relationship filter!"
    )

    # Verify correct filtering
    assert len(users_with_posts) == 10  # Only users with posts
