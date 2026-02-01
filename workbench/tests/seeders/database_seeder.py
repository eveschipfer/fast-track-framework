"""
Example Database Seeders (Sprint 2.8)

This module contains example seeders that demonstrate how to populate
the database with realistic development data using the Factory system.

Educational Note:
    These seeders show real-world patterns for database seeding:
    - Creating users with related data
    - Orchestrating multiple seeders
    - Building complex object graphs
    - Using factories with relationship hooks

Usage:
    # Run the main database seeder
    async with get_session() as session:
        seeder = DatabaseSeeder(session)
        await seeder.run()

    # This will populate your database with:
    # - 10 users
    # - 5 posts per user (50 total)
    # - 3 comments per post (150 total)
"""

from fast_query.seeding import Seeder
from tests.factories import UserFactory


class UserSeeder(Seeder):
    """
    Seeder for creating users with posts and comments.

    This seeder creates a realistic set of users, each with multiple posts
    and comments. It demonstrates using factories with relationship hooks
    to build complex object graphs.

    Example:
        >>> async with get_session() as session:
        ...     seeder = UserSeeder(session)
        ...     await seeder.run()
        ...     print("Created 10 users with posts and comments")
    """

    async def run(self) -> None:
        """
        Run the user seeder.

        Creates 10 users, each with 5 posts, and each post with 3 comments.
        This results in:
        - 10 users
        - 50 posts (5 per user)
        - 150 comments (3 per post)
        """
        factory = UserFactory(self.session)

        # Create 10 users, each with 5 posts
        # Each post will have 3 comments (created via PostFactory's hook)
        users = await factory.has_posts(5).create_batch(10)

        print(f"✅ Created {len(users)} users with posts")


class DatabaseSeeder(Seeder):
    """
    Main database seeder that orchestrates all other seeders.

    This is the "master" seeder that you run to populate the entire
    database. It calls other specialized seeders in the correct order.

    Example:
        >>> async with get_session() as session:
        ...     seeder = DatabaseSeeder(session)
        ...     await seeder.run()
        ...     print("Database fully seeded!")

    Educational Note:
        This is inspired by Laravel's DatabaseSeeder class. It provides a
        single entry point for seeding, making it easy to reset your
        development database to a known state.
    """

    async def run(self) -> None:
        """
        Run all seeders in the correct order.

        This orchestrates the seeding process by calling specialized seeders.
        You can add more seeders here as your application grows.
        """
        print("🌱 Seeding database...")

        # Call specialized seeders
        await self.call(UserSeeder)

        # You can add more seeders here:
        # await self.call(RoleSeeder)
        # await self.call(PermissionSeeder)
        # await self.call(CategorySeeder)

        print("✅ Database seeding complete!")


# ============================================================================
# EXAMPLE: Specialized Seeders for Different Scenarios
# ============================================================================


class AdminSeeder(Seeder):
    """
    Seeder for creating admin users.

    This demonstrates creating specific types of users using state modifiers.

    Example:
        >>> async with get_session() as session:
        ...     seeder = AdminSeeder(session)
        ...     await seeder.run()
    """

    async def run(self) -> None:
        """Create admin users."""
        factory = UserFactory(self.session)

        # Create an admin user with specific email
        admin = await factory.create(
            name="Admin User",
            email="admin@example.com",
        )

        print(f"✅ Created admin: {admin.email}")


class DevelopmentDataSeeder(Seeder):
    """
    Seeder for creating a rich development dataset.

    This creates a more realistic dataset with varied data, perfect for
    frontend development and manual testing.

    Example:
        >>> async with get_session() as session:
        ...     seeder = DevelopmentDataSeeder(session)
        ...     await seeder.run()
    """

    async def run(self) -> None:
        """Create a rich development dataset."""
        factory = UserFactory(self.session)

        # Create users with varying amounts of content
        # Some users with lots of posts, some with few
        await factory.has_posts(10).create_batch(3)  # 3 active users
        await factory.has_posts(2).create_batch(5)   # 5 casual users
        await factory.create_batch(2)                # 2 users with no posts

        print("✅ Created varied development dataset")
