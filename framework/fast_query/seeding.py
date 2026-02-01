"""
Database Seeding System (Sprint 2.8)

This module provides a Laravel-inspired seeding system for populating the
database with test or development data. Seeders orchestrate the use of
factories to create realistic datasets.

Key Features:
    - Abstract Seeder base class with run() method
    - call() helper for running other seeders
    - Async support for database operations
    - Integration with Factory system

Educational Note:
    This is inspired by Laravel's Database Seeding but adapted for async Python.
    Seeders are classes that encapsulate the logic for populating the database,
    making it easy to reset and repopulate data during development.

Usage:
    # Define a seeder
    class UserSeeder(Seeder):
        async def run(self) -> None:
            factory = UserFactory(self.session)
            await factory.create_batch(10)

    # Define a database seeder (orchestrates other seeders)
    class DatabaseSeeder(Seeder):
        async def run(self) -> None:
            await self.call(UserSeeder)
            await self.call(PostSeeder)

    # Run the seeder
    async with get_session() as session:
        seeder = DatabaseSeeder(session)
        await seeder.run()
"""

from abc import ABC, abstractmethod
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession


class Seeder(ABC):
    """
    Abstract base class for database seeders.

    Seeders encapsulate the logic for populating the database with test data.
    They use factories to create model instances and can call other seeders
    to build complex datasets.

    Attributes:
        session: AsyncSession for database operations

    Example:
        >>> class UserSeeder(Seeder):
        ...     async def run(self) -> None:
        ...         factory = UserFactory(self.session)
        ...         users = await factory.create_batch(10)
        ...         print(f"Created {len(users)} users")
        ...
        >>> async with get_session() as session:
        ...     seeder = UserSeeder(session)
        ...     await seeder.run()
        Created 10 users

    Educational Note:
        Unlike Laravel's seeders which use static methods and facades, our
        seeders use dependency injection. The session is passed explicitly,
        making the seeder's dependencies clear and testable.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the seeder.

        Args:
            session: AsyncSession for database operations
        """
        self.session = session

    @abstractmethod
    async def run(self) -> None:
        """
        Run the seeder logic.

        This method must be implemented by subclasses to define what data
        to create. Use factories to create model instances.

        Example:
            >>> async def run(self) -> None:
            ...     # Create users
            ...     user_factory = UserFactory(self.session)
            ...     users = await user_factory.create_batch(10)
            ...
            ...     # Create posts for each user
            ...     post_factory = PostFactory(self.session)
            ...     for user in users:
            ...         await post_factory.create_batch(5, user_id=user.id)
        """
        pass

    async def call(self, seeder_class: Type["Seeder"]) -> None:
        """
        Run another seeder.

        This allows you to compose seeders, building complex datasets by
        orchestrating multiple specialized seeders.

        Args:
            seeder_class: The seeder class to instantiate and run

        Example:
            >>> class DatabaseSeeder(Seeder):
            ...     async def run(self) -> None:
            ...         await self.call(UserSeeder)
            ...         await self.call(PostSeeder)
            ...         await self.call(CommentSeeder)
            ...
            >>> # This will run all three seeders in sequence

        Educational Note:
            This is inspired by Laravel's $this->call(UserSeeder::class).
            It provides a clean way to organize your seeding logic into
            reusable, composable units.
        """
        seeder = seeder_class(self.session)
        await seeder.run()


# ============================================================================
# SEEDER UTILITIES
# ============================================================================


async def run_seeder(seeder_class: Type[Seeder], session: AsyncSession) -> None:
    """
    Convenience function to run a seeder.

    This is a helper function that instantiates and runs a seeder in one call.
    Useful for running seeders from scripts or tests.

    Args:
        seeder_class: The seeder class to run
        session: AsyncSession for database operations

    Example:
        >>> async with get_session() as session:
        ...     await run_seeder(DatabaseSeeder, session)
        ...     print("Database seeded!")

    Educational Note:
        This is equivalent to:
            seeder = DatabaseSeeder(session)
            await seeder.run()

        But more concise for one-off seeding operations.
    """
    seeder = seeder_class(session)
    await seeder.run()


async def run_seeders(
    seeder_classes: list[Type[Seeder]], session: AsyncSession
) -> None:
    """
    Run multiple seeders in sequence.

    This helper runs a list of seeders one after another, ensuring they
    execute in the specified order.

    Args:
        seeder_classes: List of seeder classes to run
        session: AsyncSession for database operations

    Example:
        >>> async with get_session() as session:
        ...     await run_seeders([
        ...         UserSeeder,
        ...         PostSeeder,
        ...         CommentSeeder,
        ...     ], session)

    Educational Note:
        This is useful for running seeders from management commands or
        test setup. It ensures proper sequencing when seeders depend on
        each other (e.g., posts need users to exist first).
    """
    for seeder_class in seeder_classes:
        await run_seeder(seeder_class, session)
