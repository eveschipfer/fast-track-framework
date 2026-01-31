"""
Form Request System (Sprint 2.9)

This module provides a Laravel-inspired Form Request system that combines
Pydantic's structural validation with async authorization and business logic
validation.

Key Features:
    - Inherits from Pydantic BaseModel (preserves Swagger/OpenAPI docs)
    - Async authorization via authorize() method
    - Async database validation via rules() method
    - Integration with FastAPI dependency injection
    - Type-safe with MyPy support

Educational Note:
    This solves a key limitation of Pydantic: it's synchronous and can't
    perform async database checks during validation. We solve this by:
    1. Using Pydantic for structural validation (types, regex, etc.)
    2. Using async methods for business logic validation (DB checks)
    3. Integrating with FastAPI's dependency injection system

Usage:
    class StoreUserRequest(FormRequest):
        name: str
        email: EmailStr

        async def authorize(self, session: AsyncSession) -> bool:
            # Check if user has permission to create users
            return True

        async def rules(self, session: AsyncSession) -> None:
            # Check if email is unique in database
            await Rule.unique(
                session,
                User,
                "email",
                self.email
            )

    @app.post("/users")
    async def create(request: StoreUserRequest = Validate(StoreUserRequest)):
        return {"message": "User created", "data": request}
"""

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession


class FormRequest(BaseModel):
    """
    Base class for Form Requests.

    Form Requests combine Pydantic's structural validation with async
    authorization and business logic validation. They inherit from BaseModel
    to preserve Swagger/OpenAPI documentation.

    Key Methods:
        - authorize(): Async authorization check (default: True)
        - rules(): Async business logic validation (default: pass)
        - stop(): Raise validation error with custom message

    Example:
        >>> class CreatePostRequest(FormRequest):
        ...     title: str
        ...     content: str
        ...     user_id: int
        ...
        ...     async def authorize(self, session: AsyncSession) -> bool:
        ...         # Check if user exists and has permission
        ...         user = await session.get(User, self.user_id)
        ...         return user is not None and user.can_create_posts
        ...
        ...     async def rules(self, session: AsyncSession) -> None:
        ...         # Check if user exists (foreign key validation)
        ...         await Rule.exists(session, User, "id", self.user_id)
        ...
        >>> @app.post("/posts")
        ... async def create(request: CreatePostRequest = Validate(CreatePostRequest)):
        ...     return {"message": "Post created"}

    Educational Note:
        Unlike Laravel's FormRequest which uses PHP's Validator class,
        we use Pydantic for structural validation and async methods for
        business logic. This is the "best of both worlds" approach:
        - Pydantic: Fast, type-safe, generates OpenAPI docs
        - Async methods: Can perform database queries during validation
    """

    async def authorize(self, session: AsyncSession) -> bool:
        """
        Determine if the user is authorized to make this request.

        Override this method to implement authorization logic. By default,
        all requests are authorized.

        Args:
            session: AsyncSession for database queries

        Returns:
            bool: True if authorized, False otherwise

        Raises:
            HTTPException: 403 Forbidden if authorization fails

        Example:
            >>> async def authorize(self, session: AsyncSession) -> bool:
            ...     # Check if user is admin
            ...     user = await get_current_user()
            ...     return user.is_admin
            >>>
            >>> # Or check ownership
            >>> async def authorize(self, session: AsyncSession) -> bool:
            ...     post = await session.get(Post, self.post_id)
            ...     current_user = await get_current_user()
            ...     return post.user_id == current_user.id

        Educational Note:
            This is inspired by Laravel's authorize() method. It runs BEFORE
            validation, so you can fail fast if the user isn't authorized.
            This prevents unnecessary database queries for validation if the
            user doesn't have permission anyway.
        """
        return True

    async def rules(self, session: AsyncSession) -> None:
        """
        Define custom validation rules.

        Override this method to implement business logic validation that
        requires database access. Use the Rule helpers for common patterns
        like unique checks and foreign key validation.

        Args:
            session: AsyncSession for database queries

        Raises:
            ValidationError: If validation fails (via stop() or Rule helpers)

        Example:
            >>> async def rules(self, session: AsyncSession) -> None:
            ...     # Check email is unique
            ...     await Rule.unique(session, User, "email", self.email)
            ...
            ...     # Check category exists (foreign key)
            ...     await Rule.exists(session, Category, "id", self.category_id)
            ...
            ...     # Custom validation
            ...     if self.age < 18:
            ...         self.stop("You must be 18 or older")

        Educational Note:
            This is where async validation shines. In Pydantic, you can't
            do async database queries in validators. With FormRequest, you
            can! This method runs AFTER Pydantic validation but BEFORE the
            route handler executes.
        """
        pass

    def stop(self, message: str, field: str | None = None) -> None:
        """
        Stop validation with a custom error message.

        This is a convenience method that raises HTTPException with a 422
        status code (Unprocessable Entity) and a structured error response.

        Args:
            message: Error message to display
            field: Optional field name to associate the error with

        Raises:
            HTTPException: 422 with validation error details

        Example:
            >>> async def rules(self, session: AsyncSession) -> None:
            ...     if self.password != self.password_confirmation:
            ...         self.stop("Passwords do not match", field="password")
            ...
            ...     if len(self.password) < 8:
            ...         self.stop("Password must be at least 8 characters")

        Educational Note:
            This is similar to Laravel's Validator::fails() but more explicit.
            We use HTTPException(422) because that's the standard HTTP status
            for validation errors (Unprocessable Entity).

            The response format matches FastAPI's validation error format:
            {
                "detail": [
                    {"msg": "...", "type": "value_error", "loc": ["body", "field"]}
                ]
            }
        """
        detail: list[dict[str, Any]] = [
            {
                "msg": message,
                "type": "value_error",
                "loc": ["body", field] if field else ["body"],
            }
        ]
        raise HTTPException(status_code=422, detail=detail)

    # Pydantic v2 configuration
    model_config = ConfigDict(
        # Allow arbitrary types (like AsyncSession in methods)
        arbitrary_types_allowed=True
    )


class ValidationError(Exception):
    """
    Custom validation error for Form Requests.

    This is raised by Rule helpers when validation fails. It's caught
    by the Validate() dependency resolver and converted to HTTPException(422).

    Attributes:
        message: Error message
        field: Optional field name

    Example:
        >>> raise ValidationError("Email already exists", field="email")
    """

    def __init__(self, message: str, field: str | None = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Optional field name to associate error with
        """
        self.message = message
        self.field = field
        super().__init__(message)
