"""
Factory System for Test Data Generation (Sprint 2.8)

This module provides a Laravel-inspired factory system for generating test data.
Factories allow you to define blueprints for creating model instances with fake
data, making it easy to populate your database for testing and development.

Key Features:
    - Generic Factory[T] class for type-safe factory definitions
    - Faker integration for realistic fake data
    - Async support for database persistence
    - State management for modifying attributes
    - Relationship hooks for creating related models
    - Batch creation for generating multiple records

Educational Note:
    This is inspired by Laravel's Model Factories but adapted for async Python.
    Instead of Laravel's static factory() method, we use explicit dependency
    injection to pass the session, maintaining our framework's philosophy.

Usage:
    # Define a factory
    class UserFactory(Factory[User]):
        _model_class = User

        def definition(self) -> dict[str, Any]:
            return {
                "name": self.faker.name(),
                "email": self.faker.email(),
            }

    # Use the factory
    async with get_session() as session:
        factory = UserFactory(session)

        # Create unpersisted instance
        user = factory.make()

        # Create and persist
        user = await factory.create()

        # Create batch
        users = await factory.create_batch(10)

        # Modify with state
        admin = await factory.state(lambda attrs: {"is_admin": True}).create()

        # Create with relationships
        user_with_posts = await factory.has_posts(5).create()
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, TypeVar, cast

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from fast_query.base import Base
from fast_query.repository import BaseRepository

# Type variable for the model class
T = TypeVar("T", bound=Base)


class Factory(ABC, Generic[T]):
    """
    Abstract base class for model factories.

    Factories provide a convenient way to generate test data with realistic
    fake values. Each factory defines a blueprint (definition) for creating
    model instances, and provides methods to create unpersisted or persisted
    instances.

    Type Parameters:
        T: The model class this factory creates (must extend Base)

    Attributes:
        _model_class: The SQLAlchemy model class (must be set in subclass)
        _session: AsyncSession for database operations
        faker: Faker instance for generating fake data
        _states: List of state modifier functions
        _after_create_hooks: List of async hooks to run after creation

    Example:
        >>> class UserFactory(Factory[User]):
        ...     _model_class = User
        ...
        ...     def definition(self) -> dict[str, Any]:
        ...         return {
        ...             "name": self.faker.name(),
        ...             "email": self.faker.email(),
        ...         }
        ...
        >>> async with get_session() as session:
        ...     factory = UserFactory(session)
        ...     user = await factory.create()
        ...     print(user.name)  # "John Doe"

    Educational Note:
        Unlike Laravel's static factories, we use dependency injection to pass
        the session. This keeps our factories testable and explicit about their
        database dependencies.
    """

    # Must be set by subclass (the model class this factory creates)
    _model_class: type[T]

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the factory.

        Args:
            session: AsyncSession for database operations (required for create())

        Raises:
            AttributeError: If _model_class is not set in the subclass
        """
        if not hasattr(self, "_model_class"):
            raise AttributeError(
                f"{self.__class__.__name__} must define _model_class attribute"
            )

        self._session = session
        self.faker = Faker()

        # State management
        self._states: list[Callable[[dict[str, Any]], dict[str, Any]]] = []

        # After create hooks (for relationships)
        self._after_create_hooks: list[Callable[[T], Any]] = []

    @abstractmethod
    def definition(self) -> dict[str, Any]:
        """
        Define the default attributes for the model.

        This method must be implemented by subclasses to return a dictionary
        of default attribute values. Use self.faker to generate fake data.

        Returns:
            dict[str, Any]: Default attribute values for the model

        Example:
            >>> def definition(self) -> dict[str, Any]:
            ...     return {
            ...         "name": self.faker.name(),
            ...         "email": self.faker.email(),
            ...         "age": self.faker.random_int(18, 80),
            ...     }
        """
        pass

    def _build_attributes(self, **kwargs: Any) -> dict[str, Any]:
        """
        Build final attributes by merging definition, states, and overrides.

        This internal method applies the following transformations:
        1. Start with definition() defaults
        2. Apply each state modifier in order
        3. Override with explicit kwargs

        Args:
            **kwargs: Explicit attribute overrides

        Returns:
            dict[str, Any]: Final merged attributes
        """
        # Start with definition defaults
        attributes = self.definition()

        # Apply state modifiers
        for state_fn in self._states:
            attributes = state_fn(attributes)

        # Override with explicit kwargs
        attributes.update(kwargs)

        return attributes

    def make(self, **kwargs: Any) -> T:
        """
        Create an unpersisted model instance.

        Builds the model with attributes from definition(), states, and kwargs,
        but does NOT save it to the database.

        Args:
            **kwargs: Attribute overrides to apply to the model

        Returns:
            T: Unpersisted model instance

        Example:
            >>> user = factory.make(name="Alice")
            >>> print(user.id)  # None (not persisted)
            >>> print(user.name)  # "Alice"
        """
        attributes = self._build_attributes(**kwargs)
        return self._model_class(**attributes)

    async def create(self, **kwargs: Any) -> T:
        """
        Create and persist a model instance to the database.

        Builds the model with attributes from definition(), states, and kwargs,
        then saves it to the database using a repository.

        Args:
            **kwargs: Attribute overrides to apply to the model

        Returns:
            T: Persisted model instance (with ID assigned)

        Example:
            >>> user = await factory.create(name="Bob")
            >>> print(user.id)  # 1 (persisted)
            >>> print(user.name)  # "Bob"

        Educational Note:
            This uses BaseRepository for persistence, ensuring we follow the
            Repository Pattern. We don't call model.save() like Active Record.
        """
        # Create the model instance
        instance = self.make(**kwargs)

        # Persist using repository
        repo = BaseRepository(self._session, self._model_class)
        persisted = await repo.create(instance)

        # Run after-create hooks (for relationships)
        for hook in self._after_create_hooks:
            await hook(persisted)

        return persisted

    async def create_batch(self, count: int, **kwargs: Any) -> list[T]:
        """
        Create and persist multiple model instances.

        Creates N instances with the same base attributes but regenerated
        fake data for each instance (definition() is called N times).

        Args:
            count: Number of instances to create
            **kwargs: Base attribute overrides (applied to all instances)

        Returns:
            list[T]: List of persisted model instances

        Example:
            >>> users = await factory.create_batch(10, is_active=True)
            >>> print(len(users))  # 10
            >>> print(all(u.is_active for u in users))  # True

        Educational Note:
            Each instance gets fresh fake data. If you do:
                users = await factory.create_batch(3)
            You'll get 3 users with different names/emails, not duplicates.
        """
        instances: list[T] = []

        for _ in range(count):
            # Call create() which regenerates definition() each time
            instance = await self.create(**kwargs)
            instances.append(instance)

        return instances

    def state(
        self, modifier: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> "Factory[T]":
        """
        Apply a state modifier to the factory.

        State modifiers allow you to customize attributes for specific scenarios.
        They receive the current attributes and return modified attributes.

        Args:
            modifier: Function that takes attributes dict and returns modified dict

        Returns:
            Factory[T]: Self for method chaining

        Example:
            >>> # Create an admin user
            >>> admin = await factory.state(
            ...     lambda attrs: {**attrs, "is_admin": True}
            ... ).create()
            >>>
            >>> # Create a suspended user
            >>> suspended = await factory.state(
            ...     lambda attrs: {**attrs, "status": "suspended"}
            ... ).create()

        Educational Note:
            This is inspired by Laravel's ->state() method. It allows you to
            define reusable modifications without subclassing the factory.
        """
        # Clone the factory to avoid mutating the original
        new_factory = self._clone()
        new_factory._states.append(modifier)
        return new_factory

    def after_create(self, hook: Callable[[T], Any]) -> "Factory[T]":
        """
        Register a hook to run after model creation.

        After-create hooks are async functions that run after the model is
        persisted. They receive the created model instance and can perform
        additional operations (like creating related models).

        Args:
            hook: Async function that takes the created model

        Returns:
            Factory[T]: Self for method chaining

        Example:
            >>> async def create_posts(user: User):
            ...     factory = PostFactory(session)
            ...     await factory.create_batch(5, user_id=user.id)
            >>>
            >>> user = await factory.after_create(create_posts).create()
            >>> # User now has 5 posts

        Educational Note:
            This is the foundation for "magic methods" like has_posts().
            Those methods are just convenient wrappers around after_create().
        """
        new_factory = self._clone()
        new_factory._after_create_hooks.append(hook)
        return new_factory

    def _clone(self) -> "Factory[T]":
        """
        Create a shallow clone of the factory.

        This is used internally to ensure method chaining doesn't mutate
        the original factory instance.

        Returns:
            Factory[T]: Cloned factory instance
        """
        new_factory = self.__class__(self._session)
        new_factory._states = self._states.copy()
        new_factory._after_create_hooks = self._after_create_hooks.copy()
        return new_factory

    def reset(self) -> "Factory[T]":
        """
        Reset all states and hooks.

        Returns the factory to its initial state, clearing all state modifiers
        and after-create hooks.

        Returns:
            Factory[T]: Self for method chaining

        Example:
            >>> factory = UserFactory(session)
            >>> factory = factory.state(lambda a: {**a, "admin": True})
            >>> factory = factory.reset()  # Back to defaults
        """
        self._states = []
        self._after_create_hooks = []
        return self


# ============================================================================
# RELATIONSHIP HELPERS
# ============================================================================


def has_relationship(
    factory_class: type[Factory[Any]],
    count: int,
    relationship_key: str,
    session: AsyncSession,
    **extra_attrs: Any,
) -> Callable[[Base], Any]:
    """
    Helper to create a relationship hook.

    This is used internally by magic methods like has_posts() to create
    related models after the parent model is created.

    Args:
        factory_class: Factory class for the related model
        count: Number of related models to create
        relationship_key: Foreign key attribute name (e.g., "user_id")
        session: AsyncSession for creating related models
        **extra_attrs: Additional attributes to set on related models

    Returns:
        Callable: Async hook function

    Example:
        >>> # Internally, has_posts(5) becomes:
        >>> hook = has_relationship(PostFactory, 5, "user_id", session)
        >>> factory.after_create(hook)
        >>>
        >>> # With extra attributes:
        >>> hook = has_relationship(
        ...     CommentFactory, 3, "post_id", session, user_id=user.id
        ... )

    Educational Note:
        This is a helper function, not meant to be called directly.
        Use the magic methods like has_posts() instead.
    """

    async def hook(parent: Base) -> None:
        # Create related models using the session from closure
        factory = factory_class(session)
        attrs = {relationship_key: parent.id, **extra_attrs}
        await factory.create_batch(count, **attrs)

    return hook
