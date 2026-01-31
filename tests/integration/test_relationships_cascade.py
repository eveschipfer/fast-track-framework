"""
Cascade Delete Tests

CRITICAL TESTS: Prove that deleting a parent deletes children automatically.

These tests answer:
- Does deleting a User ACTUALLY delete their Posts?
- Does deleting a Post ACTUALLY delete its Comments?
- Does cascade="all, delete-orphan" work for orphans?
- Do we get foreign key constraint violations?

Educational Note:
    In production, a failed cascade delete can leave orphaned
    records that pollute the database. These tests ensure
    cascades are configured correctly in SQLAlchemy.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fast_query import Base, BaseRepository, create_engine
from ftf.models import Comment, Post, User


# ===========================
# FIXTURES
# ===========================


@pytest.fixture
async def engine() -> AsyncEngine:
    """In-memory SQLite engine."""
    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncSession:
    """Database session."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        yield session


# ===========================
# CASCADE DELETE TESTS
# ===========================


@pytest.mark.asyncio
async def test_deleting_user_raises_integrity_error_for_posts(
    session: AsyncSession,
) -> None:
    """
    Test that deleting User with Posts raises IntegrityError.

    In our schema, User.posts does NOT have cascade delete.
    Since Post.user_id is NOT NULL, deleting a user with posts
    should FAIL with IntegrityError.

    This is CORRECT behavior! It prevents accidental data loss.

    To delete a user with posts, you must:
    1. Delete all their posts first, OR
    2. Add cascade delete to User.posts relationship, OR
    3. Allow NULL in Post.user_id column
    """
    from sqlalchemy.exc import IntegrityError

    # Create user with posts
    user = User(name="Author", email="author@test.com")
    session.add(user)
    await session.commit()

    post1 = Post(title="Post 1", content="Content 1", user_id=user.id)
    post2 = Post(title="Post 2", content="Content 2", user_id=user.id)
    session.add_all([post1, post2])
    await session.commit()

    # Delete user - should FAIL because posts still reference it
    await session.delete(user)

    # CRITICAL ASSERTION: Should raise IntegrityError!
    with pytest.raises(IntegrityError) as exc_info:
        await session.commit()

    # Error should mention the constraint violation
    assert "user_id" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_deleting_post_cascades_to_comments(
    session: AsyncSession,
) -> None:
    """
    Test that Post → Comments HAS cascade delete.

    cascade="all, delete-orphan" on Post.comments means:
    - Deleting Post should delete ALL its Comments
    - Removing Comment from post.comments should delete it

    This is CRITICAL for data integrity.
    """
    # Create user, post, and comments
    user = User(name="Author", email="author@test.com")
    session.add(user)
    await session.commit()

    post = Post(title="Post with Comments", content="Content", user_id=user.id)
    session.add(post)
    await session.commit()

    # Create 5 comments
    comment_ids = []
    for i in range(5):
        comment = Comment(
            content=f"Comment {i}",
            post_id=post.id,
            user_id=user.id,
        )
        session.add(comment)
        await session.commit()
        comment_ids.append(comment.id)

    # Verify comments exist
    result = await session.execute(select(Comment))
    comments = list(result.scalars().all())
    assert len(comments) == 5

    # Delete post
    await session.delete(post)
    await session.commit()

    # Comments should be DELETED (cascade)
    result = await session.execute(select(Comment))
    remaining_comments = list(result.scalars().all())

    # CRITICAL ASSERTION: All comments should be gone!
    assert len(remaining_comments) == 0, (
        f"Expected 0 comments after deleting post, "
        f"but found {len(remaining_comments)}. "
        "Cascade delete is NOT working!"
    )


@pytest.mark.asyncio
async def test_orphan_removal_with_cascade(
    session: AsyncSession,
) -> None:
    """
    Test cascade="all, delete-orphan" orphan removal.

    If we REMOVE a comment from post.comments list (without
    explicitly deleting it), the orphan should be auto-deleted.

    This is what "delete-orphan" does.
    """
    # Create user and post
    user = User(name="Author", email="author@test.com")
    session.add(user)
    await session.commit()

    post = Post(title="Post", content="Content", user_id=user.id)
    session.add(post)
    await session.commit()

    # Create comment
    comment = Comment(content="Comment", post_id=post.id, user_id=user.id)
    session.add(comment)
    await session.commit()

    comment_id = comment.id

    # Load post with comments
    result = await session.execute(
        select(Post)
        .where(Post.id == post.id)
    )
    loaded_post = result.scalar_one()

    # Refresh to load relationships
    await session.refresh(loaded_post, ["comments"])

    # Verify comment exists in relationship
    assert len(loaded_post.comments) == 1

    # Remove comment from relationship (create orphan)
    loaded_post.comments.remove(comment)

    # Commit - orphan should be deleted
    await session.commit()

    # Verify comment was deleted
    result = await session.execute(select(Comment).where(Comment.id == comment_id))
    orphaned_comment = result.scalar_one_or_none()

    # CRITICAL ASSERTION: Orphan should be deleted!
    assert orphaned_comment is None, (
        "Orphan comment was NOT deleted! "
        'cascade="all, delete-orphan" is not working.'
    )


@pytest.mark.asyncio
async def test_three_level_cascade_user_post_comment(
    session: AsyncSession,
) -> None:
    """
    Test 3-level cascade: User → Post → Comment.

    If we delete a User:
    - Posts are NOT deleted (no cascade on User.posts)
    - But if we delete a Post, Comments ARE deleted

    This tests the cascade chain.
    """
    # Create user
    user = User(name="Author", email="author@test.com")
    session.add(user)
    await session.commit()

    # Create post
    post = Post(title="Post", content="Content", user_id=user.id)
    session.add(post)
    await session.commit()

    # Create comments
    for i in range(3):
        comment = Comment(
            content=f"Comment {i}",
            post_id=post.id,
            user_id=user.id,
        )
        session.add(comment)

    await session.commit()

    # Verify comments exist
    result = await session.execute(select(Comment))
    assert len(list(result.scalars().all())) == 3

    # Delete POST (not user)
    await session.delete(post)
    await session.commit()

    # Comments should be DELETED (because Post → Comment has cascade)
    result = await session.execute(select(Comment))
    remaining_comments = list(result.scalars().all())

    assert len(remaining_comments) == 0, (
        "Comments were not deleted when Post was deleted! "
        "3-level cascade is broken."
    )


@pytest.mark.asyncio
async def test_bulk_cascade_delete(
    session: AsyncSession,
) -> None:
    """
    Test deleting a post with MANY comments.

    This ensures cascade works at scale.
    """
    # Create user and post
    user = User(name="Author", email="author@test.com")
    session.add(user)
    await session.commit()

    post = Post(title="Popular Post", content="Content", user_id=user.id)
    session.add(post)
    await session.commit()

    # Create 100 comments
    for i in range(100):
        comment = Comment(
            content=f"Comment {i}",
            post_id=post.id,
            user_id=user.id,
        )
        session.add(comment)

    await session.commit()

    # Verify 100 comments exist
    result = await session.execute(select(Comment))
    assert len(list(result.scalars().all())) == 100

    # Delete post
    await session.delete(post)
    await session.commit()

    # ALL 100 comments should be deleted
    result = await session.execute(select(Comment))
    remaining = list(result.scalars().all())

    assert len(remaining) == 0, (
        f"Expected 0 comments, found {len(remaining)}. "
        "Bulk cascade delete failed!"
    )


@pytest.mark.asyncio
async def test_repository_delete_cascades_correctly(
    session: AsyncSession,
) -> None:
    """
    Test that BaseRepository.delete() triggers cascades.

    This ensures our repository abstraction doesn't break
    SQLAlchemy's cascade behavior.
    """
    # Create user and post with repository
    class UserRepository(BaseRepository[User]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, User)

    class PostRepository(BaseRepository[Post]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, Post)

    class CommentRepository(BaseRepository[Comment]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, Comment)

    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Create user
    user = User(name="Author", email="author@test.com")
    await user_repo.create(user)

    # Create post
    post = Post(title="Post", content="Content", user_id=user.id)
    await post_repo.create(post)

    # Create comments
    for i in range(3):
        comment = Comment(
            content=f"Comment {i}",
            post_id=post.id,
            user_id=user.id,
        )
        await comment_repo.create(comment)

    # Verify comments exist
    assert await comment_repo.count() == 3

    # Delete post via repository
    await post_repo.delete(post)

    # Comments should be cascade deleted
    assert await comment_repo.count() == 0, (
        "Repository.delete() did not trigger cascade!"
    )
