"""
Form Request System (Sprint 2.9 + Sprint 11)

This module provides a Laravel-inspired Form Request system that combines
Pydantic's structural validation with async authorization and business logic
validation.

Key Features:
    - Inherits from Pydantic BaseModel (preserves Swagger/OpenAPI docs)
    - Async authorization via authorize() method
    - Async database validation via rules() method with METHOD INJECTION (Sprint 11)
    - Integration with FastAPI dependency injection
    - Type-safe with MyPy support

Educational Note:
    Sprint 11 Upgrade: Method Injection for rules()
    ============================================
    The rules() method now supports type-hinted dependencies that are
    automatically resolved from the Container. This enables:
    
    - Injecting UserRepository instead of AsyncSession:
        async def rules(self, user_repo: UserRepository) -> None:
            await Rule.unique(user_repo, "email", self.email)
    
    - Injecting AuthManager for authorization:
        async def rules(self, auth: AuthManager) -> None:
            if not await auth.check(self.credentials):
                self.stop("Invalid credentials")
    
    - Injecting any Service:
        async def rules(self, my_service: MyService) -> None:
            await my_service.validate(self)

    The framework automatically inspects the rules() signature and resolves
    dependencies using Container.resolve() before calling the method.

Usage:
    class StoreUserRequest(FormRequest):
        name: str
        email: EmailStr

        async def authorize(self, session: AsyncSession) -> bool:
            # Check if user has permission to create users
            return True

        async def rules(self, user_repo: UserRepository) -> None:  # Method Injection!
            # Check if email is unique in database
            await Rule.unique(
                user_repo,  # Injected Repository, not Session!
                "email",
                self.email
            )

    @app.post("/users")
    async def create(request: StoreUserRequest = Validate(StoreUserRequest)):
        return {"message": "User created", "data": request}
"""

import inspect
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
        - rules(): Async business logic validation with METHOD INJECTION (default: pass)
        - stop(): Raise validation error with custom message

    Example (Sprint 11 - Method Injection):
        >>> class StoreUserRequest(FormRequest):
        ...     name: str
        ...     email: EmailStr
        ...     # Repository injected automatically!
        ...     async def rules(self, user_repo: UserRepository) -> None:
        ...         # Injected dependency, not session!
        ...         await Rule.unique(user_repo, "email", self.email)
        ...
        ...     async def authorize(self, auth: AuthManager) -> bool:
        ...         # AuthManager injected automatically!
        ...         return await auth.check(self.credentials)

    Example (Old - Session Injection):
        >>> class OldStoreUserRequest(FormRequest):
        ...     async def rules(self, session: AsyncSession) -> None:
        ...         await Rule.unique(session, User, "email", self.email)

    Educational Note:
        Unlike Laravel's FormRequest which uses PHP's Validator class,
        we use Pydantic for structural validation and async methods for
        business logic. This is a "best of both worlds" approach:
        - Pydantic: Fast, type-safe, generates OpenAPI docs
        - Async methods: Can perform database queries during validation
        - Sprint 11: Method Injection for type-safe dependency injection
    """

    async def authorize(self, session: AsyncSession) -> bool:
        """
        Determine if user is authorized to make this request.

        Override this method to implement authorization logic. By default,
        all requests are authorized.

        Args:
            session: AsyncSession for database queries
            NOTE: In Sprint 11, you can also type-hint AuthManager here:
            async def authorize(self, auth: AuthManager) -> bool

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
            validation, so you can fail Fast if user isn't authorized.
            This prevents unnecessary database queries for validation if user
            doesn't have permission anyway.
        """
        return True

    async def rules(self, **dependencies: Any) -> None:
        """
        Define custom validation rules with METHOD INJECTION.

        Override this method to implement business logic validation that
        requires database access. Use to Rule helpers for common patterns
        like unique checks and foreign key validation.

        Sprint 11: Method Injection
        =========================
        You can now type-hint ANY dependency and the framework will
        automatically resolve it from the Container before calling this method.

        Supported Dependencies:
            - AsyncSession (legacy, for backward compatibility)
            - BaseRepository (e.g., UserRepository)
            - Any registered service (e.g., AuthManager)
            - Any class registered in Container

        Args:
            **dependencies: Any type-hinted dependencies to inject

        Raises:
            ValidationError: If validation fails (via stop() or Rule helpers)

        Example (Sprint 11 - Repository Injection):
            >>> class StoreUserRequest(FormRequest):
            ...     async def rules(self, user_repo: UserRepository) -> None:
            ...         # Injected Repository, not Session!
            ...         await Rule.unique(
            ...             user_repo,  # Injected dependency
            ...             User.model.__tablename__,
            ...             "email",
            ...             self.email
            ...         )

        Example (Sprint 11 - AuthManager Injection):
            >>> class LoginRequest(FormRequest):
            ...     email: str
            ...     password: str
            ...
            ...     async def rules(self, auth: AuthManager) -> None:
            ...         # Check credentials using AuthManager
            ...         if not await auth.check(self.credentials):
            ...             self.stop("Invalid credentials")

        Example (Sprint 11 - Custom Service Injection):
            >>> class CreatePostRequest(FormRequest):
            ...     async def rules(self, post_service: PostService) -> None:
            ...         # Use custom service
            ...         await post_service.validate_title(self.title)

        Educational Note:
            This is where async validation shines. In Pydantic, you can't
            do async database queries in validators. With FormRequest, you
            can! This method runs AFTER Pydantic validation but BEFORE the
            route handler executes.

            Sprint 11 Enhancement: Method Injection allows type-safe dependencies
            instead of hardcoded session parameter.
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
    by Validate() dependency resolver and converted to HTTPException(422).

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
