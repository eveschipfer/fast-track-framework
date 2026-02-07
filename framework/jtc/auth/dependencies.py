"""
Authorization Dependencies for FastAPI (Sprint 5.5)

This module provides clean FastAPI dependencies for route protection using
the Gate authorization system. It integrates seamlessly with the existing
JWT authentication system (Sprint 3.3).

Key Features:
    - Authorize() dependency factory for route protection
    - Integration with CurrentUser (JWT auth)
    - Automatic 403 responses on authorization failure
    - Clean, declarative syntax

Public API:
    Authorize: Dependency factory for authorization checks

Example:
    >>> from jtc.http import FastTrackFramework, Inject
    >>> from jtc.auth import CurrentUser, Gate, Authorize
    >>> from fastapi import Depends
    >>>
    >>> app = FastTrackFramework()
    >>>
    >>> # Define abilities
    >>> Gate.define("view-dashboard", lambda user: user.is_admin)
    >>>
    >>> # Protect route with Authorize dependency
    >>> @app.get("/dashboard", dependencies=[Depends(Authorize("view-dashboard"))])
    >>> async def dashboard(user: CurrentUser):
    ...     return {"message": "Admin dashboard"}
    >>>
    >>> # With resource check (manual)
    >>> @app.put("/posts/{post_id}")
    >>> async def update_post(
    ...     post_id: int,
    ...     user: CurrentUser,
    ...     repo: PostRepository = Inject(PostRepository)
    ... ):
    ...     post = await repo.find_or_fail(post_id)
    ...     Gate.authorize(user, "update", post)  # Manual check
    ...     # ... update logic
"""

from typing import Any

from fastapi import Depends

from jtc.auth.gates import Gate
from jtc.auth.guard import get_current_user
from jtc.http.exceptions import AuthorizationError


def Authorize(ability: str, resource: Any = None):
    """
    Create a FastAPI dependency that authorizes the current user for an ability.

    This factory function creates a dependency that:
    1. Gets the current user from JWT authentication (get_current_user)
    2. Checks authorization using Gate.allows()
    3. Raises AuthorizationError (403) if denied
    4. Returns the user if authorized

    Args:
        ability: Ability name to check (e.g., "view-dashboard", "update")
        resource: Optional resource to check (usually None for route-level checks)

    Returns:
        Callable: FastAPI dependency function

    Example:
        >>> from fastapi import Depends
        >>> from jtc.auth import Authorize, CurrentUser, Gate
        >>>
        >>> # Define ability
        >>> Gate.define("view-admin", lambda user: user.is_admin)
        >>>
        >>> # Protect route
        >>> @app.get("/admin", dependencies=[Depends(Authorize("view-admin"))])
        >>> async def admin_panel(user: CurrentUser):
        ...     return {"message": "Admin panel"}
        >>>
        >>> # Route protection with multiple abilities
        >>> @app.post(
        ...     "/publish",
        ...     dependencies=[
        ...         Depends(Authorize("create-post")),
        ...         Depends(Authorize("publish-content"))
        ...     ]
        ... )
        >>> async def publish_post(...):
        ...     # Only if user has BOTH abilities
        ...     pass

    Educational Note:
        This uses FastAPI's dependency system to create reusable authorization
        checks. The dependencies are evaluated BEFORE the route handler runs,
        providing clean separation between authorization and business logic.

        Compare to:
        - Django: @permission_required('app.delete_post')
        - Flask: @login_required + manual checks
        - Laravel: Route::middleware('can:delete-post')

        FastAPI's dependency system provides:
        - Composition (multiple dependencies)
        - Type safety (full IDE support)
        - Testability (easy to mock)
    """

    async def authorize_dependency(
        user: Any = Depends(get_current_user),
    ) -> Any:
        """
        FastAPI dependency that checks authorization.

        Args:
            user: Current user from JWT auth (injected by FastAPI)

        Returns:
            Any: The authorized user

        Raises:
            AuthorizationError: If user does not have permission (403 response)
        """
        # Check authorization using Gate
        if not Gate.allows(user, ability, resource):
            raise AuthorizationError(
                f"User is not authorized to perform action: {ability}"
            )

        # Return user if authorized (allows chaining with other dependencies)
        return user

    return authorize_dependency


# Alias for common pattern: protect route without additional logic
# Example: @app.get("/admin", dependencies=[Requires("view-admin")])
Requires = Authorize

__all__ = [
    "Authorize",
    "Requires",
]
