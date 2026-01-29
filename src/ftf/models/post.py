"""
Post Model

Example model with relationships demonstrating one-to-many patterns.

This demonstrates:
    - BelongsTo relationship (Post belongs to User via author)
    - HasMany relationship (Post has many Comments)
    - lazy="raise" for async safety (forces explicit eager loading)
    - TYPE_CHECKING imports to avoid circular dependencies
    - created_at timestamp for ordering

Relationships:
    author: User (many-to-one) - Each post belongs to one user
    comments: List[Comment] (one-to-many) - Each post has many comments

Example Usage:
    # With eager loading (REQUIRED in async)
    from ftf.database import BaseRepository
    from ftf.models import Post

    class PostRepository(BaseRepository[Post]):
        async def get_with_author(self, post_id: int) -> Post:
            return await (
                self.query()
                .where(Post.id == post_id)
                .with_(Post.author)  # Eager load author
                .first_or_fail()
            )

    # Access relationship (works because of eager loading)
    post = await repo.get_with_author(1)
    print(post.author.name)  # OK! Author already loaded

    # Without eager loading (FAILS with lazy="raise")
    post = await repo.find(1)
    print(post.author.name)  # ERROR: lazy load not allowed in async

See: docs/relationships.md for complete relationship guide
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ftf.database import Base

if TYPE_CHECKING:
    from .comment import Comment
    from .user import User


class Post(Base):
    """
    Blog post model.

    Attributes:
        id: Primary key (auto-generated)
        title: Post title (max 200 characters)
        content: Post content (text)
        user_id: Foreign key to users table
        created_at: Timestamp when post was created
        author: User who created this post (many-to-one)
        comments: Comments on this post (one-to-many)

    Table:
        posts

    Example:
        >>> post = Post(
        ...     title="My First Post",
        ...     content="Hello, world!",
        ...     user_id=1
        ... )
        >>> print(post)
        Post(id=None, title='My First Post', user_id=1)
    """

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # BelongsTo: Post belongs to User (many-to-one)
    # lazy="raise" forces explicit eager loading in async code
    author: Mapped["User"] = relationship(
        "User",
        back_populates="posts",
        lazy="raise",  # Prevent N+1 queries, force explicit loading
    )

    # HasMany: Post has many Comments (one-to-many)
    # cascade="all, delete-orphan" deletes comments when post is deleted
    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="post",
        lazy="raise",  # Prevent N+1 queries
        cascade="all, delete-orphan",  # Delete comments when post deleted
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Post(id={self.id}, title='{self.title}', user_id={self.user_id})"
