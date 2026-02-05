"""
Validation Rules for Form Requests (Sprint 2.9 + Sprint 11)

This module provides async validation rule helpers for common database
validation patterns like unique checks and foreign key validation.

Sprint 11 Upgrade: Support for BaseRepository
========================================
    Rule helpers now support either AsyncSession or BaseRepository
    for backward compatibility and method injection.

    How it works:
        1. Accept session: AsyncSession OR repository: BaseRepository
        2. If AsyncSession: Use session.execute() directly (old style)
        3. If BaseRepository: Use repository.session.execute() (new style)

    Example (Sprint 11 - Method Injection):
        >>> class StoreUserRequest(FormRequest):
        ...     async def rules(self, user_repo: UserRepository) -> None:
        ...         await Rule.unique(user_repo, "email", self.email)
        ...
        >>> class OldStoreUserRequest(FormRequest):
        ...     async def rules(self, session: AsyncSession) -> None:
        ...         await Rule.unique(session, User, "email", self.email)

Key Rules:
    - Rule.unique(): Check if a value is unique in database
    - Rule.exists(): Check if a foreign key exists
    - Additional rules: min_count, max_count (future)

Educational Note:
    These rules solve a key limitation of Pydantic: it can't
    perform async database queries during validation. With FormRequest.rules(), we can!

    This is inspired by Laravel's validation rules, but adapted for async Python:
    - Laravel: 'email' => 'unique:users,email'
    - Fast Track: await Rule.unique(session, User, "email", value)
    - Fast Track: await Rule.unique(user_repo, "email", value)

Usage:
    >>> class StoreUserRequest(FormRequest):
    ...     name: str
    ...     email: EmailStr
    ...     role_id: int
    ...
    ...     async def rules(self, user_repo: UserRepository) -> None:
    ...         await Rule.unique(user_repo, "email", self.email)
    ...
    ...     async def rules(self, session: AsyncSession) -> None:
    ...         await Rule.unique(session, User, "email", self.email)
"""

from typing import Any, Type, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fast_query import Base, BaseRepository
from ftf.validation.request import ValidationError


class Rule:
    """
    Collection of validation rule helpers.

    These are static methods that perform common validation patterns
    againsts database. They raise ValidationError if validation fails.

    Sprint 11: Support for BaseRepository
    =========================================
        Rule helpers now accept either AsyncSession or BaseRepository.

        How it works:
        1. Accept session: AsyncSession | BaseRepository
        2. If AsyncSession: Use session.execute() directly
        3. If BaseRepository: Use repository.session.execute()

    Example:
        >>> # Method Injection (new)
        >>> await Rule.unique(user_repo, User, "email", value)
        >>>
        >>> # Session Injection (old, backward compatible)
        >>> await Rule.unique(session, User, "email", value)
    """

    @staticmethod
    async def unique(
        session: Union[AsyncSession, BaseRepository],
        model: Type[Base],
        column: str,
        value: Any,
        ignore_id: int | None = None,
        field_name: str | None = None,
    ) -> None:
        """
        Check if a value is unique in a database.

        Queries: database to ensure that value doesn't already exist in
        the specified column. Optionally ignores a specific record (useful
        for update operations).

        Sprint 11: Support for BaseRepository
        =====================================
            Accepts either AsyncSession OR BaseRepository.

            If AsyncSession: Uses session.execute() directly (old style)
            If BaseRepository: Uses repository.session.execute() (new style)

        Args:
            session: AsyncSession for database queries (old style)
                OR BaseRepository for database queries (new style with method injection)
            model: SQLAlchemy model class to query
            column: Column name to check
            value: Value to check for uniqueness
            ignore_id: Optional ID to ignore (for updates)
            field_name: Optional field name for error message (defaults to column)

        Raises:
            ValidationError: If value is not unique

        Example:
            >>> # Create: Check if email is unique
            >>> await Rule.unique(session, User, "email", "alice@test.com")

            >>> # Create: Check if email is unique (Method Injection)
            >>> user_repo = Inject(UserRepository)
            >>> await Rule.unique(user_repo, User, "email", "alice@test.com")

            >>> # Create: Check if email is unique except for current user (update)
            >>> await Rule.unique(session, User, "email", "alice@test.com", ignore_id=1)

            >>> # Update: Check if email is unique (Method Injection)
            >>> await Rule.unique(user_repo, User, "email", "alice@test.com", ignore_id=1)

            >>> # Update: Check if email is unique (Method Injection - Repository with ignore_id)
            >>> await Rule.unique(Inject(UserRepository, ignore_id=1), User, "email", "alice@test.com", ignore_id=1)
        """
        # Determine if we have AsyncSession or BaseRepository
        if isinstance(session, BaseRepository):
            repository: BaseRepository = session
            db_session = repository.session
        else:
            db_session: AsyncSession = session
            repository = None

        # Build query to check if value exists
        query = select(model).where(getattr(model, column) == value)

        # If updating, ignore the current record
        if ignore_id is not None:
            query = query.where(model.id != ignore_id)

        # Execute query using session
        result = await db_session.execute(query)
        existing = result.scalar_one_or_none()

        # If record exists, validation fails
        if existing is not None:
            field = field_name or column
            raise ValidationError(
                f"The {field} has already been taken.",
                field=field,
            )

    @staticmethod
    async def exists(
        session: Union[AsyncSession, BaseRepository],
        model: Type[Base],
        column: str,
        value: Any,
        field_name: str | None = None,
    ) -> None:
        """
        Check if a value exists in a database (foreign key validation).

        Queries the database to ensure that value exists in the specified
        column. This is commonly used to validate foreign keys.

        Sprint 11: Support for BaseRepository
        =====================================
            Accepts either AsyncSession OR BaseRepository.

        Args:
            session: AsyncSession for database queries
                OR BaseRepository for database queries (new style)

        Raises:
            ValidationError: If value does not exist

        Example:
            >>> # Check if category exists before creating post
            >>> await Rule.exists(session, Category, "id", self.category_id)
            >>>
            >>> # Check if category exists (Method Injection)
            >>> category_repo = Inject(CategoryRepository)
            >>> await Rule.exists(category_repo, Category, "id", self.category_id)

        Educational Note:
            This is an async equivalent of Laravel's 'exists' rule.
            It's commonly used for foreign key validation to ensure that
            related record exists before creating/updating.

            Why not use database foreign keys?
            - Database FK constraints give cryptic error messages
            - This gives user-friendly validation errors
            - We can validate before hitting the database
        """
        # Determine if we have AsyncSession or BaseRepository
        if isinstance(session, BaseRepository):
            repository: BaseRepository = session
            db_session = repository.session
        else:
            db_session: AsyncSession = session
            repository = None

        # Build query to check if value exists
        query = select(model).where(getattr(model, column) == value)

        # Execute query using session
        result = await db_session.execute(query)
        existing = result.scalar_one_or_none()

        # If record doesn't exist, validation fails
        if existing is None:
            field = field_name or column
            # Make field name more user-friendly
            friendly_field = field.replace("_id", "").replace("_", " ")
            raise ValidationError(
                f"The selected {friendly_field} is invalid.",
                field=field,
            )


class RuleExtensions:
    """
    Additional validation rules for future enhancements.

    These are examples of other validation patterns that could be implemented
    in future sprints. Commented out for now.
    """

    @staticmethod
    async def min_count(
        session: AsyncSession,
        model: Type[Base],
        column: str,
        value: Any,
        min_count: int,
        field_name: str | None = None,
    ) -> None:
        """
        Check if a value appears at least min_count times.

        Example use case: Ensure a tag is used at least 3 times
        before making it a "featured" tag.

        Example:
            >>> await Rule.min_count(
            ...     session, Post, "tag_id", self.tag_id, min_count=3
            ... )
        """
        query = select(model).where(getattr(model, column) == value)
        result = await session.execute(query)
        count = len(result.scalars().all())

        if count < min_count:
            field = field_name or column
            raise ValidationError(
                f"The {field} must be used at least {min_count} times.",
                field=field,
            )

    @staticmethod
    async def max_count(
        session: AsyncSession,
        model: Type[Base],
        column: str,
        value: Any,
        max_count: int,
        field_name: str | None = None,
    ) -> None:
        """
        Check if a value appears at most max_count times.

        Example use case: Ensure a user doesn't create more than 5 posts
        with the same category.

        Example:
            >>> await Rule.max_count(
            ...     session, Post, "category_id", self.category_id, max_count=5
            ... )
        """
        query = select(model).where(getattr(model, column) == value)
        result = await session.execute(query)
        count = len(result.scalars().all())

        if count >= max_count:
            field = field_name or column
            raise ValidationError(
                f"The {field} has reached the maximum limit of {max_count}.",
                field=field,
            )
