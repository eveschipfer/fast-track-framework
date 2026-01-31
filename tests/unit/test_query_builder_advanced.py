"""
Advanced Query Builder Tests (Sprint 2.6)

Tests for advanced ORM features:
    - Nested eager loading with dot notation
    - Global scopes (soft delete filtering)
    - Local scopes (reusable query logic)
    - Relationship filters (where_has)

These tests validate the "musculatura" enhancements that transform the
QueryBuilder from a simple wrapper into an advanced ORM tool.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fast_query import Base, BaseRepository, create_engine
from ftf.models import Comment, Post, User


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
async def engine() -> AsyncEngine:
    """In-memory SQLite engine for fast tests."""
    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables for all models
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


# ============================================================================
# REPOSITORY CLASSES
# ============================================================================


class UserRepository(BaseRepository[User]):
    """Repository for User model with advanced query capabilities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)


class PostRepository(BaseRepository[Post]):
    """Repository for Post model with advanced query capabilities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Post)


class CommentRepository(BaseRepository[Comment]):
    """Repository for Comment model with advanced query capabilities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Comment)


# ===========================
# FEATURE 1: Nested Eager Loading (Dot Notation)
# ===========================


@pytest.mark.asyncio
async def test_nested_eager_loading_single_level(session: AsyncSession) -> None:
    """Test dot notation with single-level relationship (same as object)."""
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    # Create test data
    user = User(name="Alice", email="alice@test.com")
    await user_repo.create(user)

    post = Post(title="My Post", content="Content", user_id=user.id)
    await post_repo.create(post)

    # Query with string notation
    posts = await post_repo.query().with_("author").get()

    assert len(posts) == 1
    assert posts[0].author.name == "Alice"  # Relationship loaded!


@pytest.mark.asyncio
async def test_nested_eager_loading_two_levels(session: AsyncSession) -> None:
    """Test dot notation with two-level nested relationship."""
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Create test data: User -> Post -> Comment
    user = User(name="Bob", email="bob@test.com")
    await user_repo.create(user)

    post = Post(title="Post 1", content="Content", user_id=user.id)
    await post_repo.create(post)

    comment = Comment(content="Great post!", post_id=post.id, user_id=user.id)
    await comment_repo.create(comment)

    # Query user with nested relationships using dot notation
    users = await user_repo.query().with_("posts.comments").get()

    assert len(users) == 1
    assert len(users[0].posts) == 1
    assert len(users[0].posts[0].comments) == 1
    assert users[0].posts[0].comments[0].content == "Great post!"


@pytest.mark.asyncio
async def test_nested_eager_loading_multiple_paths(session: AsyncSession) -> None:
    """Test dot notation with multiple relationship paths."""
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Create test data
    author = User(name="Author", email="author@test.com")
    commenter = User(name="Commenter", email="commenter@test.com")
    await user_repo.create(author)
    await user_repo.create(commenter)

    post = Post(title="Post", content="Content", user_id=author.id)
    await post_repo.create(post)

    comment = Comment(content="Comment", post_id=post.id, user_id=commenter.id)
    await comment_repo.create(comment)

    # Load post with both author AND comments.author
    posts = await post_repo.query().with_("author", "comments.author").get()

    assert len(posts) == 1
    assert posts[0].author.name == "Author"  # Post's author loaded
    assert len(posts[0].comments) == 1
    assert posts[0].comments[0].author.name == "Commenter"  # Comment's author loaded


@pytest.mark.asyncio
async def test_nested_eager_loading_invalid_relationship(session: AsyncSession) -> None:
    """Test that invalid relationship names raise clear errors."""
    user_repo = UserRepository(session)

    with pytest.raises(AttributeError) as exc_info:
        await user_repo.query().with_("invalid_relationship").get()

    assert "User" in str(exc_info.value)
    assert "invalid_relationship" in str(exc_info.value)


@pytest.mark.asyncio
async def test_nested_eager_loading_mixed_notation(session: AsyncSession) -> None:
    """Test mixing object-based and string-based eager loading."""
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    user = User(name="Alice", email="alice@test.com")
    await user_repo.create(user)

    post = Post(title="Post", content="Content", user_id=user.id)
    await post_repo.create(post)

    # Mix object notation and string notation (should work!)
    users = await user_repo.query().with_(User.posts, "posts.author").get()

    assert len(users) == 1
    assert len(users[0].posts) == 1


# ===========================
# FEATURE 2: Global Scopes (Soft Deletes)
# ===========================


@pytest.mark.asyncio
async def test_global_scope_excludes_soft_deleted_by_default(session: AsyncSession) -> None:
    """Test that soft-deleted records are excluded by default."""
    from datetime import datetime, timezone

    user_repo = UserRepository(session)

    # Create active and soft-deleted users
    active = User(name="Active", email="active@test.com")
    deleted = User(name="Deleted", email="deleted@test.com")
    deleted.deleted_at = datetime.now(timezone.utc)

    await user_repo.create(active)
    await user_repo.create(deleted)

    # Query without any flags - should exclude soft-deleted
    users = await user_repo.query().get()

    assert len(users) == 1
    assert users[0].name == "Active"


@pytest.mark.asyncio
async def test_global_scope_with_trashed_includes_deleted(session: AsyncSession) -> None:
    """Test with_trashed() includes soft-deleted records."""
    from datetime import datetime, timezone

    user_repo = UserRepository(session)

    active = User(name="Active", email="active@test.com")
    deleted = User(name="Deleted", email="deleted@test.com")
    deleted.deleted_at = datetime.now(timezone.utc)

    await user_repo.create(active)
    await user_repo.create(deleted)

    # Query with with_trashed() - should include both
    users = await user_repo.query().with_trashed().get()

    assert len(users) == 2
    names = {u.name for u in users}
    assert names == {"Active", "Deleted"}


@pytest.mark.asyncio
async def test_global_scope_only_trashed_shows_deleted_only(session: AsyncSession) -> None:
    """Test only_trashed() shows only soft-deleted records."""
    from datetime import datetime, timezone

    user_repo = UserRepository(session)

    active = User(name="Active", email="active@test.com")
    deleted = User(name="Deleted", email="deleted@test.com")
    deleted.deleted_at = datetime.now(timezone.utc)

    await user_repo.create(active)
    await user_repo.create(deleted)

    # Query with only_trashed() - should show only deleted
    users = await user_repo.query().only_trashed().get()

    assert len(users) == 1
    assert users[0].name == "Deleted"


@pytest.mark.asyncio
async def test_global_scope_applies_to_count(session: AsyncSession) -> None:
    """Test global scope applies to count() method."""
    from datetime import datetime, timezone

    user_repo = UserRepository(session)

    active = User(name="Active", email="active@test.com")
    deleted = User(name="Deleted", email="deleted@test.com")
    deleted.deleted_at = datetime.now(timezone.utc)

    await user_repo.create(active)
    await user_repo.create(deleted)

    # Default count - excludes deleted
    count_active = await user_repo.query().count()
    assert count_active == 1

    # With trashed - includes all
    count_all = await user_repo.query().with_trashed().count()
    assert count_all == 2

    # Only trashed - deleted only
    count_deleted = await user_repo.query().only_trashed().count()
    assert count_deleted == 1


@pytest.mark.asyncio
async def test_global_scope_applies_to_first(session: AsyncSession) -> None:
    """Test global scope applies to first() method."""
    from datetime import datetime, timezone

    user_repo = UserRepository(session)

    deleted = User(name="Deleted", email="deleted@test.com")
    deleted.deleted_at = datetime.now(timezone.utc)
    await user_repo.create(deleted)

    # first() without trashed - should return None
    user = await user_repo.query().first()
    assert user is None

    # first() with trashed - should find deleted user
    user = await user_repo.query().with_trashed().first()
    assert user is not None
    assert user.name == "Deleted"


@pytest.mark.asyncio
async def test_global_scope_applies_to_pluck(session: AsyncSession) -> None:
    """Test global scope applies to pluck() method."""
    from datetime import datetime, timezone

    user_repo = UserRepository(session)

    active = User(name="Active", email="active@test.com")
    deleted = User(name="Deleted", email="deleted@test.com")
    deleted.deleted_at = datetime.now(timezone.utc)

    await user_repo.create(active)
    await user_repo.create(deleted)

    # pluck() without trashed - only active
    names = await user_repo.query().pluck(User.name)
    assert names == ["Active"]

    # pluck() with trashed - all names
    all_names = await user_repo.query().with_trashed().pluck(User.name)
    assert set(all_names) == {"Active", "Deleted"}


@pytest.mark.asyncio
async def test_global_scope_does_not_apply_to_models_without_mixin(session: AsyncSession) -> None:
    """Test global scope doesn't affect models without SoftDeletesMixin."""
    post_repo = PostRepository(session)
    user_repo = UserRepository(session)

    # Post doesn't have SoftDeletesMixin
    user = User(name="User", email="user@test.com")
    await user_repo.create(user)

    post = Post(title="Post", content="Content", user_id=user.id)
    await post_repo.create(post)

    # Should work normally (no soft delete filtering)
    posts = await post_repo.query().get()
    assert len(posts) == 1

    # with_trashed() and only_trashed() don't cause errors, just do nothing
    posts_trashed = await post_repo.query().with_trashed().get()
    assert len(posts_trashed) == 1


# ===========================
# FEATURE 3: Local Scopes
# ===========================


@pytest.mark.asyncio
async def test_local_scope_with_static_method(session: AsyncSession) -> None:
    """Test local scope using static method on model."""
    user_repo = UserRepository(session)

    # Create test data
    active = User(name="Active", email="active@test.com")
    inactive = User(name="Inactive", email="inactive@test.com")
    await user_repo.create(active)
    await user_repo.create(inactive)

    # Define a scope (normally this would be on the User model)
    @staticmethod
    def active_scope(query):
        return query.where(User.name == "Active")

    # Apply scope
    users = await user_repo.query().scope(active_scope).get()

    assert len(users) == 1
    assert users[0].name == "Active"


@pytest.mark.asyncio
async def test_local_scope_with_lambda(session: AsyncSession) -> None:
    """Test local scope using lambda function."""
    user_repo = UserRepository(session)

    user1 = User(name="Alice", email="alice@test.com")
    user2 = User(name="Bob", email="bob@test.com")
    await user_repo.create(user1)
    await user_repo.create(user2)

    # Use lambda as scope
    users = await (
        user_repo.query()
        .scope(lambda q: q.where(User.name == "Alice"))
        .get()
    )

    assert len(users) == 1
    assert users[0].name == "Alice"


@pytest.mark.asyncio
async def test_local_scope_chaining_multiple(session: AsyncSession) -> None:
    """Test chaining multiple local scopes."""
    user_repo = UserRepository(session)

    user = User(name="Active", email="active@test.com")
    await user_repo.create(user)

    # Chain multiple scopes
    def scope1(q):
        return q.where(User.name == "Active")

    def scope2(q):
        return q.where(User.email.like("%test.com"))

    users = await user_repo.query().scope(scope1).scope(scope2).get()

    assert len(users) == 1
    assert users[0].name == "Active"


# ===========================
# FEATURE 4: Relationship Filters (where_has)
# ===========================


@pytest.mark.asyncio
async def test_where_has_one_to_many(session: AsyncSession) -> None:
    """Test where_has() with one-to-many relationship."""
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    # Create users with and without posts
    user_with_posts = User(name="Author", email="author@test.com")
    user_without_posts = User(name="Reader", email="reader@test.com")
    await user_repo.create(user_with_posts)
    await user_repo.create(user_without_posts)

    post = Post(title="Post", content="Content", user_id=user_with_posts.id)
    await post_repo.create(post)

    # Get only users who have posts
    users = await user_repo.query().where_has("posts").get()

    assert len(users) == 1
    assert users[0].name == "Author"


@pytest.mark.asyncio
async def test_where_has_many_to_one(session: AsyncSession) -> None:
    """Test where_has() with many-to-one relationship."""
    post_repo = PostRepository(session)
    user_repo = UserRepository(session)

    # All posts have an author (foreign key constraint)
    user = User(name="Author", email="author@test.com")
    await user_repo.create(user)

    post = Post(title="Post", content="Content", user_id=user.id)
    await post_repo.create(post)

    # Get posts that have an author
    posts = await post_repo.query().where_has("author").get()

    assert len(posts) == 1
    assert posts[0].title == "Post"


@pytest.mark.asyncio
async def test_where_has_combined_with_where(session: AsyncSession) -> None:
    """Test where_has() combined with other where conditions."""
    user_repo = UserRepository(session)
    post_repo = PostRepository(session)

    # Create multiple users
    alice = User(name="Alice", email="alice@test.com")
    bob = User(name="Bob", email="bob@test.com")
    charlie = User(name="Charlie", email="charlie@test.com")
    await user_repo.create(alice)
    await user_repo.create(bob)
    await user_repo.create(charlie)

    # Only Alice and Bob have posts
    post1 = Post(title="Alice Post", content="Content", user_id=alice.id)
    post2 = Post(title="Bob Post", content="Content", user_id=bob.id)
    await post_repo.create(post1)
    await post_repo.create(post2)

    # Get users with posts AND name starting with 'A'
    users = await (
        user_repo.query()
        .where(User.name.like("A%"))
        .where_has("posts")
        .get()
    )

    assert len(users) == 1
    assert users[0].name == "Alice"


@pytest.mark.asyncio
async def test_where_has_invalid_relationship(session: AsyncSession) -> None:
    """Test where_has() with non-existent relationship raises error."""
    user_repo = UserRepository(session)

    with pytest.raises(AttributeError) as exc_info:
        await user_repo.query().where_has("invalid_relationship").get()

    assert "User" in str(exc_info.value)
    assert "invalid_relationship" in str(exc_info.value)


@pytest.mark.asyncio
async def test_where_has_with_non_relationship_attribute(session: AsyncSession) -> None:
    """Test where_has() with non-relationship attribute raises error."""
    user_repo = UserRepository(session)

    with pytest.raises(AttributeError) as exc_info:
        await user_repo.query().where_has("name").get()  # 'name' is a column, not relationship

    assert "not a relationship" in str(exc_info.value)


# ===========================
# INTEGRATION TESTS (Multiple Features)
# ===========================


@pytest.mark.asyncio
async def test_integration_nested_loading_with_global_scope(session: AsyncSession) -> None:
    """Test nested loading works correctly with global soft delete scope."""
    from datetime import datetime, timezone

    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Create user with soft-deleted status
    active_user = User(name="Active", email="active@test.com")
    deleted_user = User(name="Deleted", email="deleted@test.com")
    deleted_user.deleted_at = datetime.now(timezone.utc)
    await user_repo.create(active_user)
    await user_repo.create(deleted_user)

    # Create posts for both users
    post1 = Post(title="Active Post", content="Content", user_id=active_user.id)
    post2 = Post(title="Deleted Post", content="Content", user_id=deleted_user.id)
    await post_repo.create(post1)
    await post_repo.create(post2)

    # Create comments
    comment1 = Comment(content="Comment 1", post_id=post1.id, user_id=active_user.id)
    comment2 = Comment(content="Comment 2", post_id=post2.id, user_id=deleted_user.id)
    await comment_repo.create(comment1)
    await comment_repo.create(comment2)

    # Query users with nested relationships - should exclude deleted user
    users = await user_repo.query().with_("posts.comments").get()

    assert len(users) == 1
    assert users[0].name == "Active"


@pytest.mark.asyncio
async def test_integration_all_features_combined(session: AsyncSession) -> None:
    """Test combining nested loading, global scope, local scope, and where_has."""
    from datetime import datetime, timezone

    user_repo = UserRepository(session)
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Create active user with posts
    active_user = User(name="Alice", email="alice@test.com")
    await user_repo.create(active_user)

    # Create deleted user with posts
    deleted_user = User(name="Bob", email="bob@test.com")
    deleted_user.deleted_at = datetime.now(timezone.utc)
    await user_repo.create(deleted_user)

    # Create user without posts
    no_posts_user = User(name="Charlie", email="charlie@test.com")
    await user_repo.create(no_posts_user)

    # Posts
    post1 = Post(title="Post 1", content="Content", user_id=active_user.id)
    post2 = Post(title="Post 2", content="Content", user_id=deleted_user.id)
    await post_repo.create(post1)
    await post_repo.create(post2)

    comment = Comment(content="Comment", post_id=post1.id, user_id=active_user.id)
    await comment_repo.create(comment)

    # Complex query: active users with posts, eager load nested relationships
    users = await (
        user_repo.query()
        .where_has("posts")  # Only users with posts
        .scope(lambda q: q.where(User.name.like("A%")))  # Name starts with A
        .with_("posts.comments")  # Eager load nested
        .get()
    )

    # Should only return Alice (not deleted, has posts, name starts with A)
    assert len(users) == 1
    assert users[0].name == "Alice"
    assert len(users[0].posts) == 1
    assert len(users[0].posts[0].comments) == 1
