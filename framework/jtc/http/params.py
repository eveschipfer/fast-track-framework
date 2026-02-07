"""
Fast Track Framework - Dependency Injection Bridge

This module provides the bridge between FastAPI's Depends() system
and our custom IoC Container.

Key Concept:
    FastAPI uses Depends() for dependency injection, but it doesn't
    know about our Container. This module bridges that gap.

Design Decision:
    Using Depends() (not custom parameter inspection) because:
    - Works with FastAPI's existing DI system
    - Compatible with OpenAPI/Swagger docs
    - No monkey-patching or magic required
    - Users get IDE autocomplete and type checking

Architecture:
    User Code:           service: UserService = Inject(UserService)
                                    ↓
    FastAPI:             Depends(lambda: app.container.resolve(UserService))
                                    ↓
    Our Container:       Resolves UserService with all dependencies
                                    ↓
    Route Handler:       Receives fully resolved UserService instance
"""

from typing import TypeVar, cast

from fastapi import Depends, Request

# Type variable for generic dependency type
T = TypeVar("T")


def Inject(dependency_type: type[T]) -> T:  # noqa: N802
    """
    Inject a dependency from the IoC Container into a FastAPI route.

    This is the main API for dependency injection in Fast Track Framework.
    It bridges FastAPI's Depends() with our Container.

    Args:
        dependency_type: The type to resolve from the container

    Returns:
        A FastAPI Depends() instance that resolves the dependency

    Example:
        >>> @app.get("/users/{user_id}")
        >>> def get_user(
        ...     user_id: int,
        ...     service: UserService = Inject(UserService),
        ...     repo: UserRepository = Inject(UserRepository)
        ... ):
        ...     return service.get_user(user_id)

    How it works:
        1. User calls Inject(UserService)
        2. We create a resolver function for UserService
        3. FastAPI calls the resolver during request handling
        4. Resolver extracts container from request.app
        5. Container resolves UserService with all dependencies
        6. Fully resolved instance is passed to route handler

    Design Trade-offs:
        + Type-safe: MyPy validates dependency_type
        + IDE-friendly: Autocomplete works correctly
        + No magic: Standard FastAPI Depends() pattern
        - Slightly verbose: Must specify type twice (annotation + Inject)
          (This is unavoidable in Python due to type system limitations)
    """

    def resolver(request: Request) -> T:
        """
        Resolve dependency from the application's container.

        This function is called by FastAPI during request handling.
        It extracts the container from the request and resolves the dependency.

        Args:
            request: FastAPI request object (contains app.container)

        Returns:
            Resolved dependency instance

        Raises:
            AttributeError: If app doesn't have a container
            DependencyResolutionError: If resolution fails
        """
        # Extract container from application
        # request.app is the FastTrackFramework instance
        container = request.app.container

        # Resolve dependency using container
        # This may recursively resolve nested dependencies
        # Cast needed because resolve() returns Any at runtime
        return cast(T, container.resolve(dependency_type))

    # Return a FastAPI Depends() that uses our resolver
    # FastAPI will call resolver() when this route is executed
    # Type ignore needed because Depends returns a callable, not T
    return Depends(resolver)  # type: ignore
