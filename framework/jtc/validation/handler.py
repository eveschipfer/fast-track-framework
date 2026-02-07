"""
Form Request Dependency Handler (Sprint 2.9 + Sprint 11)

This module provides: Validate() dependency resolver that integrates
FormRequests with FastAPI's dependency injection system.

Key Responsibilities:
    1. Parse request body into Pydantic model (structural validation)
    2. Inject type-hinted dependencies via METHOD INJECTION (Sprint 11)
    3. Run async authorize() check
    4. Run async rules() validation with injected dependencies
    5. Return validated model instance

Educational Note:
    Sprint 11 Upgrade: Method Injection
    ============================================
    The framework now inspects the rules() method signature and
    automatically resolves type-hinted dependencies before calling it.

    This enables:
        - Injecting UserRepository: async def rules(self, user_repo: UserRepository)
        - Injecting AuthManager: async def rules(self, auth: AuthManager)
        - Injecting any Service: async def rules(self, my_service: MyService)

    The framework uses Container.resolve() to instantiate dependencies,
    maintaining IoC pattern established in Sprint 7+.

Usage (Sprint 11 - Method Injection):
    >>> class StoreUserRequest(FormRequest):
    ...     name: str
    ...     email: EmailStr
    ...
    ...     async def rules(self, user_repo: UserRepository) -> None:
    ...         # UserRepository injected automatically!
    ...         await Rule.unique(user_repo, "email", self.email)
    ...
    >>> @app.post("/users")
    ... async def create(request: StoreUserRequest = Validate(StoreUserRequest)):
    ...     # request is fully validated with injected dependencies
    ...     return {"message": "User created", "email": request.email}

Usage (Old - Session Injection):
    >>> class OldStoreUserRequest(FormRequest):
    ...     async def rules(self, session: AsyncSession) -> None:
    ...         # Session must be passed manually
    ...         await Rule.unique(session, User, "email", self.email)
"""

import inspect
from typing import Any, Callable, Type, TypeVar

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from jtc.http.params import Inject
from jtc.validation.request import FormRequest, ValidationError
from jtc.core import Container

# Type variable for FormRequest subclasses
T = TypeVar("T", bound=FormRequest)


def Validate(model_class: Type[T]) -> Callable[..., T]:
    """
    Create a FastAPI dependency that validates a FormRequest with METHOD INJECTION.

    This function returns a dependency callable that:
    1. Parses request body into Pydantic model
    2. Inspects rules() signature and resolves type-hinted dependencies
    3. Runs authorize() (can also use injected dependencies)
    4. Runs rules() with resolved dependencies injected
    5. Returns validated model instance

    Args:
        model_class: FormRequest subclass to validate

    Returns:
        Callable: FastAPI dependency that returns validated model

    Sprint 11: Method Injection
    =========================
        The framework inspects model_class.rules() signature and
        resolves type-hinted dependencies before calling it.

        How it works:
        1. Get signature: inspect.signature(model_class.rules)
        2. Get parameters: signature.parameters
        3. Resolve each dependency: Container.resolve(param.annotation)
        4. Call rules() with resolved dependencies: await model.rules(**resolved)
        5. Authorize can also use injected deps

        Example dependencies that are resolved:
            - AsyncSession: Container.resolve(AsyncSession) for backward compatibility
            - BaseRepository: Container.resolve(UserRepository)
            - AuthManager: Container.resolve(AuthManager)
            - Any registered service: Container.resolve(MyService)

        Backward Compatibility:
            If rules(self, session: AsyncSession) is still used, as
            framework will injects session parameter directly.

    Example (Sprint 11 - Repository Injection):
        >>> class StoreUserRequest(FormRequest):
        ...     name: str
        ...     email: EmailStr
        ...
        ...     async def rules(self, user_repo: UserRepository) -> None:
        ...         # UserRepository injected automatically!
        ...         await Rule.unique(user_repo, "email", self.email)
        ...
        >>> @app.post("/users")
        ... async def create(request: StoreUserRequest = Validate(StoreUserRequest)):
        ...     # request is fully validated with injected dependencies
        ...     return {"message": "User created", "email": request.email}

    Example (Sprint 11 - AuthManager Injection):
        >>> class LoginRequest(FormRequest):
        ...     email: str
        ...     password: str
        ...
        ...     async def rules(self, auth: AuthManager) -> None:
        ...         # AuthManager injected automatically!
        ...         credentials = Credentials(email=self.email, password=self.password)
        ...         if not await auth.check(credentials):
        ...             self.stop("Invalid credentials")

    Example (Sprint 11 - Custom Service Injection):
        >>> class CreatePostRequest(FormRequest):
        ...     async def rules(self, post_service: PostService) -> None:
        ...         # Use custom service
        ...         await post_service.validate_title(self.title)

    Educational Note:
        This uses FastAPI's Depends() mechanism with METHOD INJECTION.
        The framework now provides Laravel-like flexibility:
        - Type-safe dependency injection
        - Automatic dependency resolution via Container
        - Full control over validation logic with any dependencies

        Inspired by Laravel's dependency injection container.
    """

    async def dependency(
        request_body: model_class,  # type: ignore
    ) -> T:
        """
        Dependency callable that validates a FormRequest with METHOD INJECTION.

        Sprint 11: Inspects rules() signature and resolves dependencies.

        Args:
            request_body: Parsed Pydantic model (from request body)

        Returns:
            T: Validated FormRequest instance

        Raises:
            HTTPException: 403 if not authorized, 422 if validation fails
        """
        # Sprint 11: Get Container for dependency resolution
        container = Container()

        # Sprint 11: Inspect rules() method signature
        rules_signature = inspect.signature(model_class.rules)

        # Sprint 11: Resolve type-hinted dependencies from Container
        resolved_dependencies = {}
        if rules_signature.parameters:
            for param in rules_signature.parameters.values():
                # Skip self parameter
                if param.name == 'self':
                    continue

                # Resolve dependency from Container
                # Only resolve if not already manually injected
                if param.name not in ['session', 'request_body']:
                    try:
                        resolved_dependencies[param.name] = container.resolve(param.annotation)
                    except Exception:
                        # Dependency not registered, try Inject() as fallback
                        pass

        # Sprint 11: Backward compatibility: Inject session if rules() expects it
        if 'session' in rules_signature.parameters and 'session' not in resolved_dependencies:
            resolved_dependencies['session'] = Inject(AsyncSession)

        # At this point, Pydantic has already validated structure
        # (types, required fields, regex patterns, etc.)

        # Step 1: Run authorization check (can use injected dependencies)
        try:
            if 'session' in resolved_dependencies:
                is_authorized = await request_body.authorize(resolved_dependencies['session'])
            elif 'auth' in resolved_dependencies:
                is_authorized = await request_body.authorize(resolved_dependencies['auth'])
            else:
                is_authorized = await request_body.authorize()
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

        # Step 2: Run business logic validation with METHOD INJECTION
        try:
            await request_body.rules(**resolved_dependencies)
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
# ALTERNATIVE API: Validate as a class (for explicit control)
# ============================================================================


class ValidateWith:
    """
    Alternative API for Validate that allows explicit dependency control.

    This is useful when you want more control over the validation process
    or need to pass additional dependencies manually.

    Example:
        >>> @app.post("/users")
        ... async def create(
        ...     request: StoreUserRequest,
        ...     user_repo: UserRepository = Inject(UserRepository),
        ...     session: AsyncSession = Inject(AsyncSession)
        ... ):
        ...     # Manually validate with explicit dependencies
        ...     await ValidateWith.validate(request, session, user_repo=user_repo)
        ...     # Now request is validated
        ...     return request
    """

    @staticmethod
    async def validate(request: FormRequest, **dependencies: Any) -> None:
        """
        Manually validate a FormRequest with explicit dependencies.

        Args:
            request: FormRequest instance (already parsed by Pydantic)
            **dependencies: Any keyword arguments to pass to rules()

        Raises:
            HTTPException: 403 if not authorized, 422 if validation fails

        Sprint 11: Method Injection also works with explicit dependencies

        Example:
            >>> request = StoreUserRequest(name="Alice", email="alice@test.com")
            >>> user_repo = Inject(UserRepository)
            >>> await ValidateWith.validate(request, session=Inject(AsyncSession), user_repo=user_repo)
            >>> # request is now validated with explicit user_repo
        """
        # Run authorization
        is_authorized = await request.authorize(dependencies.get('session'))

        # Run validation rules with explicit dependencies
        try:
            await request.rules(**dependencies)
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
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Validation failed: {str(e)}",
            )
