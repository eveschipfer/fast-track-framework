"""
Model Mixins for Fast Query

Reusable mixins that add common functionality to SQLAlchemy models.

These mixins follow the DRY principle and provide Laravel-inspired features:
    - TimestampMixin: Auto-managed created_at and updated_at timestamps
    - SoftDeletesMixin: Soft delete functionality with deleted_at column

Usage:
    from fast_query import Base, TimestampMixin, SoftDeletesMixin
    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, mapped_column

    class User(Base, TimestampMixin, SoftDeletesMixin):
        __tablename__ = "users"

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))

    # Usage:
    user = User(name="Alice")
    # user.created_at automatically set on insert
    # user.updated_at automatically set on insert and update
    # user.deleted_at can be set for soft delete

WHY MIXINS:
    - DRY: Define common columns once, use everywhere
    - Consistent: All models use same timestamp format
    - Maintainable: Change timestamp logic in one place
    - Type-safe: Full MyPy support with Mapped types

See: docs/models.md for mixin usage guide
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, event
from sqlalchemy.orm import Mapped, Session, mapped_column


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.

    Automatically manages timestamps:
        - created_at: Set on insert (never changes)
        - updated_at: Set on insert and updated on every update

    All timestamps use UTC timezone for consistency across deployments.

    Attributes:
        created_at: When the record was created (UTC)
        updated_at: When the record was last updated (UTC)

    Example:
        >>> class Post(Base, TimestampMixin):
        ...     __tablename__ = "posts"
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     title: Mapped[str] = mapped_column(String(200))
        >>>
        >>> # On create
        >>> post = Post(title="My First Post")
        >>> session.add(post)
        >>> await session.commit()
        >>> # post.created_at and post.updated_at are now set
        >>>
        >>> # On update
        >>> post.title = "Updated Title"
        >>> await session.commit()
        >>> # post.updated_at is updated, created_at stays the same

    Implementation:
        Uses SQLAlchemy's @event.listens_for decorator to automatically
        update timestamps before insert and update operations.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# Event listener to ensure updated_at is always updated
@event.listens_for(Session, "before_flush")
def receive_before_flush(session: Session, flush_context: object, instances: object) -> None:  # noqa: ARG001
    """
    SQLAlchemy event handler that updates updated_at before flush.

    This ensures updated_at is always set to current UTC time when:
        - A new record is inserted (if not already set)
        - An existing record is updated

    Args:
        session: SQLAlchemy session
        flush_context: Flush context (unused)
        instances: Instances being flushed (unused)

    Note:
        This is a session-level event that fires before any flush operation.
        It checks all dirty (modified) objects and updates their updated_at.
    """
    for obj in session.dirty:
        if isinstance(obj, TimestampMixin):
            obj.updated_at = datetime.now(timezone.utc)


class SoftDeletesMixin:
    """
    Mixin that adds soft delete functionality via deleted_at column.

    Soft deletes mark records as deleted without actually removing them from
    the database. This allows for:
        - Data recovery (undo deletions)
        - Audit trails (who deleted what, when)
        - Maintaining referential integrity
        - Compliance requirements (data retention)

    Attributes:
        deleted_at: When the record was soft-deleted (None if not deleted)
        is_deleted: Property that returns True if record is soft-deleted

    Example:
        >>> class User(Base, SoftDeletesMixin):
        ...     __tablename__ = "users"
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     name: Mapped[str] = mapped_column(String(100))
        >>>
        >>> # Soft delete (repository does this automatically)
        >>> user.deleted_at = datetime.now(timezone.utc)
        >>> await session.commit()
        >>>
        >>> # Check if deleted
        >>> if user.is_deleted:
        ...     print("User is soft-deleted")
        >>>
        >>> # Restore (undelete)
        >>> user.deleted_at = None
        >>> await session.commit()

    Repository Integration:
        The BaseRepository automatically checks for this mixin:
        - If model has SoftDeletesMixin: sets deleted_at (soft delete)
        - If model doesn't have it: performs hard delete (removes row)

        >>> await repo.delete(user)
        >>> # If User has SoftDeletesMixin: sets deleted_at
        >>> # If User doesn't have it: DELETE FROM users WHERE id = ?

    Querying Soft-Deleted Records:
        >>> # Exclude soft-deleted (recommended default)
        >>> active_users = await (
        ...     repo.query()
        ...     .where(User.deleted_at.is_(None))
        ...     .get()
        ... )
        >>>
        >>> # Include soft-deleted
        >>> all_users = await repo.query().get()
        >>>
        >>> # Only soft-deleted
        >>> deleted_users = await (
        ...     repo.query()
        ...     .where(User.deleted_at.isnot(None))
        ...     .get()
        ... )

    See: docs/soft-deletes.md for complete guide
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """
        Check if the record has been soft-deleted.

        Returns:
            bool: True if deleted_at is set, False otherwise

        Example:
            >>> if user.is_deleted:
            ...     print("This user has been deleted")
            >>> else:
            ...     print("This user is active")
        """
        return self.deleted_at is not None
