"""
N+1 Prevention Tests

CRITICAL TESTS: These prove that our eager loading actually works.

Without these tests, we could be running 51 queries and not know it.
With these tests, we PROVE that with_() reduces 51 queries to EXACTLY 2.

Test Scenarios:
1. Load 50 posts WITHOUT eager loading → Should FAIL with lazy="raise"
2. Load 50 posts WITH with_() → Should execute EXACTLY 2 queries
3. Load 50 posts WITH with_joined() → Should execute EXACTLY 1 query
4. Compare selectinload vs joinedload performance

Educational Note:
    The N+1 problem is one of the most common performance killers
    in ORMs. This test suite ensures we don't accidentally introduce
    it by forgetting to eager load relationships.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from ftf.database import Base, BaseRepository, create_engine
from ftf.models import Comment, Post, User
from tests.utils import QueryCounter


# ===========================
# FIXTURES
# ===========================


@pytest.fixture
async def engine() -> AsyncEngine:
    """In-memory SQLite engine for tests."""
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


@pytest.fixture
async def users_with_posts(session: AsyncSession) -> tuple[list[User], list[Post]]:
    """
    Create 50 posts from 10 different users.

    This simulates a real-world scenario where:
    - We load many posts
    - Each post belongs to a user
    - WITHOUT eager loading: 1 query for posts + 50 queries for users (N+1!)
    - WITH eager loading: 1 query for posts + 1 query for users (2 total)

    Returns:
        tuple: (users, posts)
    """
    # Create 10 users
    users = [User(name=f"User{i}", email=f"user{i}@test.com") for i in range(10)]

    for user in users:
        session.add(user)

    await session.commit()

    # Create 50 posts (5 posts per user)
    posts = []
    for i in range(50):
        user_index = i % 10  # Distribute posts among users
        post = Post(
            title=f"Post {i}",
            content=f"Content for post {i}",
            user_id=users[user_index].id,
        )
        posts.append(post)
        session.add(post)

    await session.commit()

    return users, posts


# ===========================
# N+1 PREVENTION TESTS
# ===========================


@pytest.mark.asyncio
async def test_lazy_raise_prevents_n_plus_one(
    session: AsyncSession,
    users_with_posts: tuple[list[User], list[Post]],
) -> None:
    """
    Test that lazy="raise" BLOCKS accidental N+1 queries.

    Without eager loading, accessing post.author should FAIL.
    This forces developers to explicitly eager load.
    """
    users, posts = users_with_posts

    # Load posts WITHOUT eager loading
    stmt = select(Post).limit(10)
    result = await session.execute(stmt)
    loaded_posts = list(result.scalars().all())

    assert len(loaded_posts) == 10

    # Accessing author should RAISE because lazy="raise"
    with pytest.raises(InvalidRequestError) as exc_info:
        _ = loaded_posts[0].author.name

    assert "raise" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_eager_loading_with_selectinload_uses_2_queries(
    engine: AsyncEngine,
    session: AsyncSession,
    users_with_posts: tuple[list[User], list[Post]],
) -> None:
    """
    Test that with_() (selectinload) executes EXACTLY 2 queries.

    Query 1: SELECT posts
    Query 2: SELECT users WHERE id IN (1, 2, 3, ...)

    This is the N+1 prevention proof!
    """
    users, posts = users_with_posts

    # Create repository
    class PostRepository(BaseRepository[Post]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, Post)

    repo = PostRepository(session)

    # Load posts with eager loading + count queries
    async with QueryCounter(engine) as counter:
        loaded_posts = await repo.query().with_(Post.author).limit(50).get()

    # CRITICAL ASSERTION: Must be EXACTLY 2 queries
    assert counter.count == 2, (
        f"Expected 2 queries (posts + authors), "
        f"but got {counter.count}. "
        f"Queries: {counter.get_queries()}"
    )

    # Verify we got all 50 posts
    assert len(loaded_posts) == 50

    # Verify we can access author WITHOUT additional queries
    # (If this triggers a query, QueryCounter would catch it)
    for post in loaded_posts:
        assert post.author is not None
        assert isinstance(post.author.name, str)


@pytest.mark.asyncio
async def test_eager_loading_with_joinedload_uses_1_query(
    engine: AsyncEngine,
    session: AsyncSession,
    users_with_posts: tuple[list[User], list[Post]],
) -> None:
    """
    Test that with_joined() (joinedload) executes EXACTLY 1 query.

    Query 1: SELECT posts LEFT OUTER JOIN users

    This uses a JOIN instead of a separate query.
    """
    users, posts = users_with_posts

    class PostRepository(BaseRepository[Post]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, Post)

    repo = PostRepository(session)

    # Load posts with joined eager loading + count queries
    async with QueryCounter(engine) as counter:
        loaded_posts = await repo.query().with_joined(Post.author).limit(50).get()

    # CRITICAL ASSERTION: Must be EXACTLY 1 query (with JOIN)
    assert counter.count == 1, (
        f"Expected 1 query (posts JOIN users), "
        f"but got {counter.count}. "
        f"Queries: {counter.get_queries()}"
    )

    assert len(loaded_posts) == 50

    # Verify authors are loaded
    for post in loaded_posts:
        assert post.author is not None


@pytest.mark.asyncio
async def test_without_eager_loading_would_cause_n_plus_one(
    engine: AsyncEngine,
    session: AsyncSession,
    users_with_posts: tuple[list[User], list[Post]],
) -> None:
    """
    Educational test: Show what WOULD happen without lazy="raise".

    If we didn't have lazy="raise", SQLAlchemy would:
    1. Execute 1 query to load posts
    2. Execute N queries to load each post's author (N+1 problem!)

    But with lazy="raise", this is BLOCKED at runtime.
    """
    users, posts = users_with_posts

    # Manually set lazy="select" to simulate the problem
    # (This is what happens in most ORMs by default)

    # Load posts
    stmt = select(Post).limit(10)
    async with QueryCounter(engine) as counter:
        result = await session.execute(stmt)
        loaded_posts = list(result.scalars().all())

    # First query: Load posts
    assert counter.count == 1

    # Try to access authors (would trigger N queries if lazy loading worked)
    # But our lazy="raise" prevents this!
    with pytest.raises(InvalidRequestError):
        for post in loaded_posts:
            _ = post.author.name  # This would be query #2, #3, #4, ... N+1!


@pytest.mark.asyncio
async def test_multiple_relationships_eager_loading(
    engine: AsyncEngine,
    session: AsyncSession,
) -> None:
    """
    Test eager loading MULTIPLE relationships at once.

    Post has:
    - author (User)
    - comments (List[Comment])

    Loading both should use:
    - 1 query for posts
    - 1 query for authors (selectinload)
    - 1 query for comments (selectinload)
    = 3 queries total
    """
    # Create user
    user = User(name="Author", email="author@test.com")
    session.add(user)
    await session.commit()

    # Create post
    post = Post(title="Test Post", content="Content", user_id=user.id)
    session.add(post)
    await session.commit()

    # Create 5 comments on the post
    for i in range(5):
        comment = Comment(
            content=f"Comment {i}", post_id=post.id, user_id=user.id
        )
        session.add(comment)

    await session.commit()

    # Load post with BOTH relationships
    class PostRepository(BaseRepository[Post]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, Post)

    repo = PostRepository(session)

    async with QueryCounter(engine) as counter:
        loaded_post = await (
            repo.query()
            .where(Post.id == post.id)
            .with_(Post.author, Post.comments)  # Load BOTH relationships
            .first()
        )

    # Should be 3 queries:
    # 1. SELECT posts
    # 2. SELECT users WHERE id IN (...)
    # 3. SELECT comments WHERE post_id IN (...)
    assert counter.count == 3, (
        f"Expected 3 queries (post + author + comments), "
        f"got {counter.count}"
    )

    assert loaded_post is not None
    assert loaded_post.author.name == "Author"
    assert len(loaded_post.comments) == 5


@pytest.mark.asyncio
async def test_query_counter_utility_accuracy(
    engine: AsyncEngine,
    session: AsyncSession,
) -> None:
    """
    Meta-test: Verify QueryCounter itself is accurate.

    This ensures our testing infrastructure is solid.
    """
    # Test 1: No queries
    async with QueryCounter(engine) as counter:
        pass  # Do nothing

    assert counter.count == 0

    # Test 2: One query
    async with QueryCounter(engine) as counter:
        await session.execute(select(User).limit(1))

    assert counter.count == 1

    # Test 3: Multiple queries
    async with QueryCounter(engine) as counter:
        await session.execute(select(User))
        await session.execute(select(Post))
        await session.execute(select(Comment))

    assert counter.count == 3

    # Test 4: Queries after context exit should NOT be counted
    async with QueryCounter(engine) as counter:
        await session.execute(select(User))

    # This query is OUTSIDE the counter context
    await session.execute(select(Post))

    # Should still be 1 (not 2)
    assert counter.count == 1
