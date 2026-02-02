"""
RBAC Gates System (Sprint 5.5)

This module provides Laravel-inspired authorization via Gates and Policies.
Gates define application-wide abilities, while Policies group model-specific
authorization logic.

Key Features:
    - Gate singleton facade for global authorization
    - Ability registry for custom authorization logic
    - Policy registry for model-specific authorization
    - FastAPI integration via dependencies
    - Clean DX for route protection

Public API:
    Gate: Singleton authorization facade
    GateManager: Internal implementation (users don't interact directly)

Example:
    >>> from ftf.auth import Gate, CurrentUser
    >>> from ftf.http import FastTrackFramework, Inject
    >>>
    >>> # Define global ability
    >>> Gate.define("view-dashboard", lambda user: user.is_admin)
    >>>
    >>> # Check permission
    >>> if Gate.allows(user, "view-dashboard"):
    ...     print("Access granted")
    >>>
    >>> # Authorize or raise 403
    >>> Gate.authorize(user, "view-dashboard")  # Raises AuthorizationError if denied
    >>>
    >>> # Use in route protection
    >>> @app.get("/dashboard")
    >>> async def dashboard(user: CurrentUser):
    ...     Gate.authorize(user, "view-dashboard")
    ...     return {"message": "Admin dashboard"}
"""

from typing import Any, Callable, Optional, Type

from ftf.http.exceptions import AuthorizationError


class GateManager:
    """
    Internal Gate implementation (Singleton pattern).

    This class manages the ability and policy registries and provides
    authorization logic. Users interact via the Gate facade (singleton instance).

    Attributes:
        _abilities: Dict mapping ability names to callback functions
        _policies: Dict mapping model classes to policy instances

    Educational Note:
        This uses the Singleton pattern to ensure only one Gate instance
        exists across the application. The Gate module-level instance
        (defined below) is the single point of access.
    """

    _instance: Optional["GateManager"] = None

    def __new__(cls) -> "GateManager":
        """
        Singleton pattern implementation.

        Ensures only one GateManager instance exists.

        Returns:
            GateManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._abilities = {}
            cls._instance._policies = {}
        return cls._instance

    def define(
        self, ability: str, callback: Callable[..., bool]
    ) -> "GateManager":
        """
        Define a new ability with authorization logic.

        Abilities are named permissions that can be checked globally.
        The callback receives the user and optional resource parameters.

        Args:
            ability: Ability name (e.g., "view-dashboard", "edit-post")
            callback: Function returning bool (True = allowed, False = denied)

        Returns:
            GateManager: Self for method chaining

        Example:
            >>> # Simple ability (no resource)
            >>> Gate.define("view-dashboard", lambda user: user.is_admin)
            >>>
            >>> # Resource-based ability
            >>> Gate.define(
            ...     "edit-post",
            ...     lambda user, post: user.id == post.author_id
            ... )
            >>>
            >>> # Complex logic
            >>> def can_publish(user, post):
            ...     if user.is_admin:
            ...         return True
            ...     if post.author_id != user.id:
            ...         return False
            ...     return post.draft_count >= 5
            >>> Gate.define("publish-post", can_publish)
        """
        self._abilities[ability] = callback
        return self

    def register_policy(
        self, model_class: Type[Any], policy_instance: Any
    ) -> "GateManager":
        """
        Register a policy for a model.

        Policies group authorization logic for a specific model type.
        When checking abilities on a model, the Gate automatically
        calls the corresponding policy method.

        Args:
            model_class: Model class (e.g., Post, User, Comment)
            policy_instance: Policy instance (e.g., PostPolicy())

        Returns:
            GateManager: Self for method chaining

        Example:
            >>> from app.models import Post
            >>> from app.policies import PostPolicy
            >>>
            >>> # Register policy
            >>> Gate.register_policy(Post, PostPolicy())
            >>>
            >>> # Now Gate.allows() will auto-route to policy
            >>> post = await repo.find(1)
            >>> Gate.allows(user, "update", post)  # Calls PostPolicy().update(user, post)
        """
        self._policies[model_class] = policy_instance
        return self

    def allows(
        self, user: Any, ability: str, resource: Any = None
    ) -> bool:
        """
        Check if user has permission for an ability.

        This method checks:
        1. If resource is provided and has a registered policy, call policy method
        2. Otherwise, call the registered ability callback
        3. If no ability registered, return False

        Args:
            user: User instance (usually CurrentUser from auth system)
            ability: Ability name (e.g., "view-dashboard", "update")
            resource: Optional resource to check (e.g., Post instance)

        Returns:
            bool: True if allowed, False if denied

        Example:
            >>> # Check global ability
            >>> if Gate.allows(user, "view-dashboard"):
            ...     print("Access granted")
            >>>
            >>> # Check with resource (auto-routed to policy)
            >>> post = await repo.find(1)
            >>> if Gate.allows(user, "update", post):
            ...     await repo.update(post)
            >>>
            >>> # Check with custom resource ability
            >>> comment = await repo.find_comment(1)
            >>> if Gate.allows(user, "delete-comment", comment):
            ...     await repo.delete(comment)
        """
        # If resource provided, try policy-based authorization first
        if resource is not None:
            resource_class = type(resource)

            # Check if policy registered for this resource type
            if resource_class in self._policies:
                policy = self._policies[resource_class]

                # Check if policy has method for this ability
                if hasattr(policy, ability):
                    method = getattr(policy, ability)
                    return method(user, resource)

        # Fall back to ability callback (resource can be None or passed through)
        if ability in self._abilities:
            callback = self._abilities[ability]

            # Call callback with user and resource (if provided)
            if resource is not None:
                return callback(user, resource)
            else:
                return callback(user)

        # No ability or policy found - deny by default
        return False

    def denies(
        self, user: Any, ability: str, resource: Any = None
    ) -> bool:
        """
        Check if user does NOT have permission for an ability.

        This is the inverse of allows() - convenience method for negative checks.

        Args:
            user: User instance
            ability: Ability name
            resource: Optional resource to check

        Returns:
            bool: True if denied, False if allowed

        Example:
            >>> if Gate.denies(user, "delete-post", post):
            ...     return {"error": "You cannot delete this post"}
        """
        return not self.allows(user, ability, resource)

    def authorize(
        self, user: Any, ability: str, resource: Any = None
    ) -> None:
        """
        Authorize user for ability or raise AuthorizationError (403).

        This is a convenience method for route protection. If authorization
        fails, it raises an AuthorizationError which is automatically
        converted to a 403 HTTP response by the ExceptionHandler.

        Args:
            user: User instance
            ability: Ability name
            resource: Optional resource to check

        Raises:
            AuthorizationError: If user does not have permission (403 response)

        Example:
            >>> @app.put("/posts/{post_id}")
            >>> async def update_post(
            ...     post_id: int,
            ...     user: CurrentUser,
            ...     repo: PostRepository = Inject(PostRepository)
            ... ):
            ...     post = await repo.find_or_fail(post_id)
            ...     Gate.authorize(user, "update", post)  # Raises 403 if denied
            ...     # ... update logic
            >>>
            >>> @app.get("/dashboard")
            >>> async def dashboard(user: CurrentUser):
            ...     Gate.authorize(user, "view-dashboard")  # Raises 403 if not admin
            ...     return {"message": "Admin dashboard"}
        """
        if not self.allows(user, ability, resource):
            # Raise AuthorizationError (automatically converted to 403 by ExceptionHandler)
            raise AuthorizationError(
                f"User is not authorized to perform action: {ability}"
            )


# Singleton instance (Facade pattern)
# Users interact with this instance, not the class
Gate = GateManager()

__all__ = [
    "Gate",
    "GateManager",
]
