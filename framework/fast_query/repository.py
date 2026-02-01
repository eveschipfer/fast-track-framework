"""
Generic Repository Pattern

Provides CRUD operations without Active Record magic.

This implements the Repository Pattern with explicit dependency injection,
providing 80% of Laravel Eloquent's functionality without the pitfalls of
Active Record in async Python.

WHY REPOSITORY PATTERN:
    - Explicit Session Dependency: `repo = UserRepository(session)`
    - Testable: Easy to mock session in tests
    - Works Everywhere: HTTP, CLI, background jobs, tests
    - Transaction Control: Manual commit/rollback
    - Type Safe: Full MyPy support

Example:
    from fast_query import BaseRepository, Base
    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, mapped_column

    # Define model
    class User(Base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))

    # Create repository
    class UserRepository(BaseRepository[User]):
        def __init__(self, session: AsyncSession):
            super().__init__(session, User)

    # Register in container (if using FTF)
    app.register(UserRepository, scope="transient")

    # Use in route
    @app.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        repo: UserRepository = Inject(UserRepository)
    ):
        user = await repo.find_or_fail(user_id)
        return user

COMPARISON TO ELOQUENT:
    Laravel (Active Record):
        user = User.find(1)
        user.name = "Bob"
        user.save()

    FastQuery (Repository):
        repo = UserRepository(session)
        user = await repo.find(1)
        user.name = "Bob"
        await repo.update(user)

    Trade-off: More verbose, but explicit and testable.

See: Fast Track Framework documentation for anti-pattern details
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Generic, Optional, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base
from .exceptions import RecordNotFound

if TYPE_CHECKING:
    from .mixins import SoftDeletesMixin
    from .query_builder import QueryBuilder

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic repository with CRUD operations.

    Provides standard database operations for any model type without
    requiring Active Record pattern. Accepts AsyncSession via constructor
    for explicit dependency injection.

    Type Parameters:
        T: Model type (must inherit from Base)

    Usage:
        >>> class UserRepository(BaseRepository[User]):
        ...     def __init__(self, session: AsyncSession):
        ...         super().__init__(session, User)
        ...
        ...     # Add custom query methods here
        ...     async def find_by_email(self, email: str) -> Optional[User]:
        ...         stmt = select(self.model).where(self.model.email == email)
        ...         result = await self.session.execute(stmt)
        ...         return result.scalar_one_or_none()
    """

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        """
        Initialize repository with session and model type.

        Args:
            session: AsyncSession for database operations
            model: Model class (e.g., User, Product)

        Example:
            >>> session = container.resolve(AsyncSession)
            >>> user_repo = BaseRepository[User](session, User)
        """
        self.session = session
        self.model = model

    async def create(self, instance: T) -> T:
        """
        Create new record in database.

        Args:
            instance: Model instance to create (not yet persisted)

        Returns:
            T: The created instance with ID populated

        Example:
            >>> user = User(name="Alice", email="alice@example.com")
            >>> created_user = await repo.create(user)
            >>> assert created_user.id is not None
        """
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def find(self, id: int) -> Optional[T]:
        """
        Find record by primary key.

        Args:
            id: Primary key value

        Returns:
            Optional[T]: Model instance or None if not found

        Example:
            >>> user = await repo.find(123)
            >>> if user:
            ...     print(user.name)
            ... else:
            ...     print("User not found")
        """
        return await self.session.get(self.model, id)

    async def find_or_fail(self, id: int) -> T:
        """
        Find record by primary key or raise RecordNotFound.

        Args:
            id: Primary key value

        Returns:
            T: Model instance (guaranteed to exist)

        Raises:
            RecordNotFound: If record not found

        Example:
            >>> user = await repo.find_or_fail(123)
            >>> # No None check needed - either returns user or raises
            >>> print(user.name)
        """
        result = await self.find(id)

        if result is None:
            raise RecordNotFound(self.model.__name__, id)

        return result

    async def all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """
        Get all records with pagination.

        Args:
            limit: Maximum records to return (default: 100)
            offset: Number of records to skip (default: 0)

        Returns:
            list[T]: List of model instances

        Example:
            >>> # Get first page
            >>> users = await repo.all(limit=10, offset=0)
            >>>
            >>> # Get second page
            >>> users = await repo.all(limit=10, offset=10)
        """
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, instance: T) -> T:
        """
        Update existing record.

        Note: The instance must already be tracked by the session.
        This commits changes made to the instance.

        Args:
            instance: Model instance with modified attributes

        Returns:
            T: The updated instance

        Example:
            >>> user = await repo.find(123)
            >>> user.name = "Bob Updated"
            >>> updated_user = await repo.update(user)
            >>> assert updated_user.name == "Bob Updated"
        """
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: T) -> None:
        """
        Delete record from database.

        Smart Delete Logic:
            - If model has SoftDeletesMixin: Performs soft delete (sets deleted_at)
            - If model doesn't have mixin: Performs hard delete (removes row)

        Args:
            instance: Model instance to delete

        Example:
            >>> # Model with SoftDeletesMixin
            >>> user = await repo.find(123)
            >>> await repo.delete(user)
            >>> # user.deleted_at is set, record still in DB
            >>>
            >>> # Model without SoftDeletesMixin
            >>> tag = await repo.find(456)
            >>> await repo.delete(tag)
            >>> # Row is permanently removed from database
        """
        # Import here to avoid circular import
        from .mixins import SoftDeletesMixin

        # Check if model has SoftDeletesMixin
        if isinstance(instance, SoftDeletesMixin):
            # Soft delete: Set deleted_at timestamp
            instance.deleted_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(instance)
        else:
            # Hard delete: Remove from database
            await self.session.delete(instance)
            await self.session.commit()

    async def count(self) -> int:
        """
        Count total records in table.

        Returns:
            int: Total number of records

        Example:
            >>> total_users = await repo.count()
            >>> print(f"Database has {total_users} users")
        """
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def query(self) -> "QueryBuilder[T]":
        """
        Create fluent query builder for this model.

        Returns a QueryBuilder instance that provides a Laravel Eloquent-inspired
        fluent interface for building complex queries with method chaining.

        Returns:
            QueryBuilder[T]: Fluent query builder for this model type

        Example:
            >>> # Simple query
            >>> users = await repo.query().where(User.age >= 18).get()
            >>>
            >>> # Complex query with chaining
            >>> async def find_active_adults(self) -> list[User]:
            ...     return await (
            ...         self.query()
            ...         .where(User.age >= 18)
            ...         .where(User.status == "active")
            ...         .order_by(User.created_at, "desc")
            ...         .limit(50)
            ...         .get()
            ...     )
            >>>
            >>> # With eager loading (prevent N+1)
            >>> posts = await (
            ...     repo.query()
            ...     .with_(Post.author)
            ...     .latest()
            ...     .get()
            ... )

        See: docs/query-builder.md for complete API reference
        """
        # Import here to avoid circular dependency
        from .query_builder import QueryBuilder

        return QueryBuilder(self.session, self.model)
