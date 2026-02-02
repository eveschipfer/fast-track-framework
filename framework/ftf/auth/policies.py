"""
Authorization Policies (Sprint 5.5)

This module provides the Policy base class for organizing model-specific
authorization logic. Policies group related authorization rules for a single
model type (e.g., PostPolicy, UserPolicy).

Key Features:
    - Standard CRUD methods (view, viewAny, create, update, delete)
    - Custom methods for domain-specific authorization
    - Clean separation of concerns
    - Automatic integration with Gate system

Public API:
    Policy: Abstract base class for authorization policies

Example:
    >>> from ftf.auth import Policy, Gate
    >>> from app.models import Post, User
    >>>
    >>> class PostPolicy(Policy):
    ...     def view(self, user: User, post: Post) -> bool:
    ...         # Anyone can view published posts
    ...         if post.published:
    ...             return True
    ...         # Authors can view their own drafts
    ...         return user.id == post.author_id
    ...
    ...     def update(self, user: User, post: Post) -> bool:
    ...         # Only authors can update
    ...         return user.id == post.author_id
    ...
    ...     def delete(self, user: User, post: Post) -> bool:
    ...         # Admins or authors can delete
    ...         return user.is_admin or user.id == post.author_id
    ...
    ...     # Custom method
    ...     def publish(self, user: User, post: Post) -> bool:
    ...         # Only admins can publish
    ...         return user.is_admin
    >>>
    >>> # Register policy
    >>> Gate.register_policy(Post, PostPolicy())
    >>>
    >>> # Use in routes
    >>> @app.put("/posts/{post_id}")
    >>> async def update_post(
    ...     post_id: int,
    ...     user: CurrentUser,
    ...     repo: PostRepository = Inject(PostRepository)
    ... ):
    ...     post = await repo.find_or_fail(post_id)
    ...     Gate.authorize(user, "update", post)  # Calls PostPolicy().update(user, post)
    ...     # ... update logic
"""

from typing import Any


class Policy:
    """
    Abstract base class for authorization policies.

    Policies group authorization logic for a specific model type.
    Each policy method receives the user and resource as parameters
    and returns a boolean indicating whether the action is allowed.

    Standard Methods:
        view(user, resource): Can view single resource?
        viewAny(user): Can view list/index?
        create(user): Can create new resource?
        update(user, resource): Can update resource?
        delete(user, resource): Can delete resource?

    Custom Methods:
        Add your own methods for domain-specific authorization.
        Example: publish(user, post), approve(user, comment), etc.

    Example:
        >>> class PostPolicy(Policy):
        ...     def view(self, user: User, post: Post) -> bool:
        ...         # Public posts = anyone
        ...         if post.published:
        ...             return True
        ...         # Private posts = author only
        ...         return user.id == post.author_id
        ...
        ...     def viewAny(self, user: User) -> bool:
        ...         # Anyone can see the post list
        ...         return True
        ...
        ...     def create(self, user: User) -> bool:
        ...         # Only verified users can create posts
        ...         return user.email_verified
        ...
        ...     def update(self, user: User, post: Post) -> bool:
        ...         # Only author can update
        ...         return user.id == post.author_id
        ...
        ...     def delete(self, user: User, post: Post) -> bool:
        ...         # Admin or author can delete
        ...         return user.is_admin or user.id == post.author_id

    Educational Note:
        Policies follow the Strategy Pattern - each policy is a different
        strategy for authorizing actions on a specific model type.

        This keeps authorization logic organized and testable:
        - PostPolicy handles all Post authorization
        - UserPolicy handles all User authorization
        - CommentPolicy handles all Comment authorization

        Compare to scattering authorization checks throughout your codebase!
    """

    def view(self, user: Any, resource: Any) -> bool:
        """
        Determine if the user can view the resource.

        Args:
            user: User instance
            resource: Resource instance to view

        Returns:
            bool: True if allowed, False if denied

        Example:
            >>> def view(self, user: User, post: Post) -> bool:
            ...     # Anyone can view published
            ...     if post.published:
            ...         return True
            ...     # Authors can view drafts
            ...     return user.id == post.author_id
        """
        return False  # Deny by default

    def viewAny(self, user: Any) -> bool:
        """
        Determine if the user can view any resources (list/index).

        Args:
            user: User instance

        Returns:
            bool: True if allowed, False if denied

        Example:
            >>> def viewAny(self, user: User) -> bool:
            ...     # Anyone can see the post list
            ...     return True
            ...
            >>> # Or restrict to authenticated users
            >>> def viewAny(self, user: User) -> bool:
            ...     return user is not None
        """
        return False  # Deny by default

    def create(self, user: Any) -> bool:
        """
        Determine if the user can create a new resource.

        Args:
            user: User instance

        Returns:
            bool: True if allowed, False if denied

        Example:
            >>> def create(self, user: User) -> bool:
            ...     # Only verified users can create
            ...     return user.email_verified
            ...
            >>> # Or restrict to specific roles
            >>> def create(self, user: User) -> bool:
            ...     return user.role in ["admin", "editor"]
        """
        return False  # Deny by default

    def update(self, user: Any, resource: Any) -> bool:
        """
        Determine if the user can update the resource.

        Args:
            user: User instance
            resource: Resource instance to update

        Returns:
            bool: True if allowed, False if denied

        Example:
            >>> def update(self, user: User, post: Post) -> bool:
            ...     # Only author can update
            ...     return user.id == post.author_id
            ...
            >>> # Or allow admins
            >>> def update(self, user: User, post: Post) -> bool:
            ...     if user.is_admin:
            ...         return True
            ...     return user.id == post.author_id
        """
        return False  # Deny by default

    def delete(self, user: Any, resource: Any) -> bool:
        """
        Determine if the user can delete the resource.

        Args:
            user: User instance
            resource: Resource instance to delete

        Returns:
            bool: True if allowed, False if denied

        Example:
            >>> def delete(self, user: User, post: Post) -> bool:
            ...     # Admin or author can delete
            ...     return user.is_admin or user.id == post.author_id
            ...
            >>> # Or restrict to admins only
            >>> def delete(self, user: User, post: Post) -> bool:
            ...     return user.is_admin
        """
        return False  # Deny by default


__all__ = [
    "Policy",
]
