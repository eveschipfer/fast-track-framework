"""
Validation Rules for Form Requests (Sprint 2.9)

This module provides async validation rule helpers for common database
validation patterns like unique checks and foreign key validation.

Key Rules:
    - Rule.unique(): Check if a value is unique in the database
    - Rule.exists(): Check if a foreign key exists

Educational Note:
    These rules solve a key limitation of Pydantic: it can't perform async
    database queries during validation. With FormRequest.rules(), we can!

    This is inspired by Laravel's validation rules, but adapted for async Python:
    - Laravel: 'email' => 'unique:users,email'
    - Fast Track: await Rule.unique(session, User, "email", self.email)

Usage:
    class StoreUserRequest(FormRequest):
        name: str
        email: EmailStr
        role_id: int

        async def rules(self, session: AsyncSession) -> None:
            # Check email is unique
            await Rule.unique(session, User, "email", self.email)

            # Check role exists (foreign key validation)
            await Rule.exists(session, Role, "id", self.role_id)
"""

from typing import Any, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fast_query import Base
from ftf.validation.request import ValidationError


class Rule:
    """
    Collection of validation rule helpers.

    These are static methods that perform common validation patterns
    against the database. They raise ValidationError if validation fails.

    Example:
        >>> async def rules(self, session: AsyncSession) -> None:
        ...     # Unique email
        ...     await Rule.unique(session, User, "email", self.email)
        ...
        ...     # Email unique except for current user (update scenario)
        ...     await Rule.unique(
        ...         session, User, "email", self.email, ignore_id=self.user_id
        ...     )
        ...
        ...     # Category must exist
        ...     await Rule.exists(session, Category, "id", self.category_id)

    Educational Note:
        These helpers use fast_query to query the database. They're async
        because database queries are async in SQLAlchemy 2.0+.

        The pattern is similar to Laravel's validation rules, but more explicit:
        - Laravel: 'email' => 'unique:users,email,id,' . $userId
        - Fast Track: await Rule.unique(session, User, "email", value, ignore_id)
    """

    @staticmethod
    async def unique(
        session: AsyncSession,
        model: Type[Base],
        column: str,
        value: Any,
        ignore_id: int | None = None,
        field_name: str | None = None,
    ) -> None:
        """
        Check if a value is unique in the database.

        Queries the database to ensure the value doesn't already exist in
        the specified column. Optionally ignores a specific record (useful
        for update operations).

        Args:
            session: AsyncSession for database queries
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
            >>>
            >>> # Update: Check if email is unique except for current user
            >>> await Rule.unique(
            ...     session,
            ...     User,
            ...     "email",
            ...     "alice@test.com",
            ...     ignore_id=1
            ... )

        Educational Note:
            This is the async equivalent of Laravel's 'unique' rule.
            We query the database directly instead of using a string-based
            rule syntax, which gives us:
            - Type safety (MyPy knows what columns exist)
            - IDE autocomplete
            - No magic string parsing
        """
        # Build query to check if value exists
        query = select(model).where(getattr(model, column) == value)

        # If updating, ignore the current record
        if ignore_id is not None:
            query = query.where(model.id != ignore_id)

        # Execute query
        result = await session.execute(query)
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
        session: AsyncSession,
        model: Type[Base],
        column: str,
        value: Any,
        field_name: str | None = None,
    ) -> None:
        """
        Check if a value exists in the database (foreign key validation).

        Queries the database to ensure the value exists in the specified
        column. This is commonly used to validate foreign keys.

        Args:
            session: AsyncSession for database queries
            model: SQLAlchemy model class to query
            column: Column name to check
            value: Value to check for existence
            field_name: Optional field name for error message (defaults to column)

        Raises:
            ValidationError: If value does not exist

        Example:
            >>> # Check if category exists before creating post
            >>> await Rule.exists(session, Category, "id", self.category_id)
            >>>
            >>> # Check if user exists before assigning post
            >>> await Rule.exists(session, User, "id", self.user_id)

        Educational Note:
            This is the async equivalent of Laravel's 'exists' rule.
            It's commonly used for foreign key validation to ensure the
            related record exists before creating/updating.

            Why not use database foreign keys?
            - Database FK constraints give cryptic error messages
            - This gives user-friendly validation errors
            - We can validate before hitting the database
        """
        # Build query to check if value exists
        query = select(model).where(getattr(model, column) == value)

        # Execute query
        result = await session.execute(query)
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


# ============================================================================
# ADDITIONAL VALIDATION RULES (Future Enhancement)
# ============================================================================


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

        Example use case: Ensure a tag is used at least 3 times before
        making it a "featured" tag.

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
