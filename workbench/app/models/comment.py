"""
Comment Model

Example model demonstrating nested relationships (Comment -> Post -> User).

This demonstrates:
    - Multiple BelongsTo relationships (Comment belongs to both Post and User)
    - lazy="raise" for async safety
    - TYPE_CHECKING imports for circular dependencies
    - Nested relationships (comment.post.author)

Relationships:
    post: Post (many-to-one) - Each comment belongs to one post
    author: User (many-to-one) - Each comment belongs to one user

Example Usage:
    # Eager load nested relationships
    from app.models import Comment

    class CommentRepository(BaseRepository[Comment]):
        async def get_with_author_and_post(self, comment_id: int) -> Comment:
            return await (
                self.query()
                .where(Comment.id == comment_id)
                .with_(Comment.author, Comment.post)  # Load both relationships
                .first_or_fail()
            )

    # Access nested relationships
    comment = await repo.get_with_author_and_post(1)
    print(comment.author.name)  # OK! Author loaded
    print(comment.post.title)   # OK! Post loaded

    # Nested eager loading (load post's author too)
    # Note: Use joinedload for nested relationships
    from sqlalchemy.orm import joinedload

    query = (
        repo.query()
        .options(
            joinedload(Comment.author),
            joinedload(Comment.post).joinedload(Post.author)
        )
    )
    comment = await query.first()
    print(comment.post.author.name)  # OK! Post's author loaded

See: docs/relationships.md for nested relationship loading
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fast_query import Base

if TYPE_CHECKING:
    from .post import Post
    from .user import User


class Comment(Base):
    """
    Comment model for blog posts.

    Attributes:
        id: Primary key (auto-generated)
        content: Comment content (text)
        post_id: Foreign key to posts table
        user_id: Foreign key to users table (comment author)
        created_at: Timestamp when comment was created
        post: Post this comment belongs to (many-to-one)
        author: User who created this comment (many-to-one)

    Table:
        comments

    Example:
        >>> comment = Comment(
        ...     content="Great post!",
        ...     post_id=1,
        ...     user_id=2
        ... )
        >>> print(comment)
        Comment(id=None, post_id=1, user_id=2)
    """

    __tablename__ = "comments"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # BelongsTo: Comment belongs to Post (many-to-one)
    post: Mapped["Post"] = relationship(
        "Post",
        back_populates="comments",
        lazy="raise",  # Prevent N+1 queries
    )

    # BelongsTo: Comment belongs to User (many-to-one)
    author: Mapped["User"] = relationship(
        "User",
        back_populates="comments",
        lazy="raise",  # Prevent N+1 queries
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"Comment(id={self.id}, post_id={self.post_id}, user_id={self.user_id})"
        )
