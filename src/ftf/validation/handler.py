"""
Form Request Dependency Handler (Sprint 2.9)

This module provides the Validate() dependency resolver that integrates
FormRequests with FastAPI's dependency injection system.

Key Responsibilities:
    1. Parse request body into Pydantic model (structural validation)
    2. Inject AsyncSession from IoC container
    3. Run async authorize() check
    4. Run async rules() validation
    5. Return validated model instance

Educational Note:
    This is the "glue" between Pydantic and async validation. It leverages
    FastAPI's Depends() mechanism to:
    - Parse the request body (Pydantic handles this)
    - Inject dependencies (AsyncSession from container)
    - Run async validation (our custom logic)
    - Fail with proper HTTP status codes (403 for auth, 422 for validation)

Usage:
    @app.post("/users")
    async def create(request: StoreUserRequest = Validate(StoreUserRequest)):
        # request is fully validated and authorized
        return {"message": "User created", "email": request.email}
"""

from typing import Any, Callable, Type, TypeVar

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ftf.http.params import Inject
from ftf.validation.request import FormRequest, ValidationError

# Type variable for FormRequest subclasses
T = TypeVar("T", bound=FormRequest)


def Validate(model_class: Type[T]) -> Callable[..., T]:
    """
    Create a FastAPI dependency that validates a FormRequest.

    This function returns a dependency callable that:
    1. Parses the request body into the Pydantic model
    2. Injects AsyncSession from the container
    3. Runs authorize() and raises 403 if False
    4. Runs rules() and raises 422 if validation fails
    5. Returns the validated model instance

    Args:
        model_class: FormRequest subclass to validate

    Returns:
        Callable: FastAPI dependency that returns validated model

    Example:
        >>> class StoreUserRequest(FormRequest):
        ...     name: str
        ...     email: EmailStr
        ...
        ...     async def rules(self, session: AsyncSession) -> None:
        ...         await Rule.unique(session, User, "email", self.email)
        ...
        >>> @app.post("/users")
        ... async def create(request: StoreUserRequest = Validate(StoreUserRequest)):
        ...     # request is fully validated
        ...     user = User(**request.dict())
        ...     await session.add(user)
        ...     return user

    Educational Note:
        This uses FastAPI's Depends() mechanism under the hood. The flow is:
        1. FastAPI parses request body into model_class (Pydantic validation)
        2. Our dependency injects AsyncSession
        3. We run authorize() - fail fast with 403 if not authorized
        4. We run rules() - fail with 422 if validation fails
        5. Return validated model to route handler

        This is inspired by Laravel's FormRequest but adapted for FastAPI's
        async-first architecture and dependency injection system.
    """

    async def dependency(
        request_body: model_class,  # type: ignore
        session: AsyncSession = Inject(AsyncSession),
    ) -> T:
        """
        Dependency callable that validates the FormRequest.

        Args:
            request_body: Parsed Pydantic model (from request body)
            session: AsyncSession injected from container

        Returns:
            T: Validated FormRequest instance

        Raises:
            HTTPException: 403 if not authorized, 422 if validation fails
        """
        # At this point, Pydantic has already validated the structure
        # (types, required fields, regex patterns, etc.)

        # Step 1: Run authorization check
        try:
            is_authorized = await request_body.authorize(session)
            if not is_authorized:
                raise HTTPException(
                    status_code=403,
                    detail="You are not authorized to perform this action.",
                )
        except HTTPException:
            # Re-raise HTTPExceptions (including from stop())
            raise
        except Exception as e:
            # Catch any unexpected errors in authorize()
            raise HTTPException(
                status_code=500,
                detail=f"Authorization check failed: {str(e)}",
            )

        # Step 2: Run business logic validation
        try:
            await request_body.rules(session)
        except HTTPException:
            # Re-raise HTTPExceptions (from stop() or Rule helpers)
            raise
        except ValidationError as e:
            # Convert ValidationError to HTTPException
            detail: list[dict[str, Any]] = [
                {
                    "msg": e.message,
                    "type": "value_error",
                    "loc": ["body", e.field] if e.field else ["body"],
                }
            ]
            raise HTTPException(status_code=422, detail=detail)
        except Exception as e:
            # Catch any unexpected errors in rules()
            raise HTTPException(
                status_code=500,
                detail=f"Validation failed: {str(e)}",
            )

        # Step 3: Return validated model
        return request_body

    return Depends(dependency)


# ============================================================================
# ALTERNATIVE API: Validate as a class (for explicit session injection)
# ============================================================================


class ValidateWith:
    """
    Alternative API for Validate that allows explicit session injection.

    This is useful when you want more control over the validation process
    or need to pass additional dependencies.

    Example:
        >>> @app.post("/users")
        ... async def create(
        ...     request: StoreUserRequest,
        ...     session: AsyncSession = Inject(AsyncSession)
        ... ):
        ...     # Manually validate
        ...     await ValidateWith.validate(request, session)
        ...     # Now request is validated
        ...     return request
    """

    @staticmethod
    async def validate(request: FormRequest, session: AsyncSession) -> None:
        """
        Manually validate a FormRequest.

        Args:
            request: FormRequest instance (already parsed by Pydantic)
            session: AsyncSession for database queries

        Raises:
            HTTPException: 403 if not authorized, 422 if validation fails

        Example:
            >>> request = StoreUserRequest(name="Alice", email="alice@test.com")
            >>> await ValidateWith.validate(request, session)
            >>> # request is now validated
        """
        # Run authorization
        is_authorized = await request.authorize(session)
        if not is_authorized:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to perform this action.",
            )

        # Run validation rules
        try:
            await request.rules(session)
        except HTTPException:
            raise
        except ValidationError as e:
            detail: list[dict[str, Any]] = [
                {
                    "msg": e.message,
                    "type": "value_error",
                    "loc": ["body", e.field] if e.field else ["body"],
                }
            ]
            raise HTTPException(status_code=422, detail=detail)
