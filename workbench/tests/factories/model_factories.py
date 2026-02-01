"""
Concrete Factory Implementations (Sprint 2.8)

This module contains concrete factory implementations for our test models.
These factories demonstrate how to use the Factory system and provide
reusable test data generation.

Educational Note:
    These factories show real-world usage of the Factory system:
    - Using Faker for realistic data
    - Defining relationship hooks
    - Creating complex object graphs
"""

from typing import Any

from fast_query import Base
from fast_query.factories import Factory, has_relationship
from app.models import Comment, Post, User


class UserFactory(Factory[User]):
    """
    Factory for creating User instances.

    This factory generates users with realistic fake data using Faker.
    It demonstrates basic factory usage and relationship hooks.

    Example:
        >>> async with get_session() as session:
        ...     factory = UserFactory(session)
        ...
        ...     # Create a user
        ...     user = await factory.create()
        ...
        ...     # Create a user with posts
        ...     user = await factory.has_posts(5).create()
        ...
        ...     # Create a user with specific attributes
        ...     admin = await factory.create(name="Admin", email="admin@test.com")
    """

    _model_class = User

    def definition(self) -> dict[str, Any]:
        """
        Define default user attributes.

        Returns:
            dict[str, Any]: Default attributes with fake data
        """
        return {
            "name": self.faker.name(),
            "email": self.faker.email(),
        }

    def has_posts(self, count: int = 1) -> "UserFactory":
        """
        Create posts for this user after creation.

        This is a "magic method" that uses the after_create hook to
        automatically create related posts.

        Args:
            count: Number of posts to create (default: 1)

        Returns:
            UserFactory: Self for method chaining

        Example:
            >>> user = await factory.has_posts(5).create()
            >>> # User now has 5 posts
        """
        return self.after_create(
            has_relationship(PostFactory, count, "user_id", self._session)
        )

    def has_comments(self, count: int = 1) -> "UserFactory":
        """
        Create comments for this user after creation.

        Args:
            count: Number of comments to create (default: 1)

        Returns:
            UserFactory: Self for method chaining

        Educational Note:
            Comments need both a user_id and post_id. This creates orphan
            comments (comments without posts). In a real scenario, you might
            want to create posts first, then comments on those posts.
        """
        return self.after_create(
            has_relationship(CommentFactory, count, "user_id", self._session)
        )


class PostFactory(Factory[Post]):
    """
    Factory for creating Post instances.

    This factory generates posts with fake titles and content.
    It requires a user_id to be provided (posts belong to users).

    Example:
        >>> async with get_session() as session:
        ...     # Create a user first
        ...     user = await UserFactory(session).create()
        ...
        ...     # Create posts for that user
        ...     factory = PostFactory(session)
        ...     post = await factory.create(user_id=user.id)
        ...
        ...     # Create post with comments
        ...     post = await factory.has_comments(10).create(user_id=user.id)
    """

    _model_class = Post

    def definition(self) -> dict[str, Any]:
        """
        Define default post attributes.

        Returns:
            dict[str, Any]: Default attributes with fake data

        Educational Note:
            We don't set user_id here because it's required and should be
            provided explicitly. This forces the caller to think about the
            relationship, making tests more explicit.
        """
        return {
            "title": self.faker.sentence(),
            "content": self.faker.paragraph(nb_sentences=5),
        }

    def has_comments(self, count: int = 1, user_id: int | None = None) -> "PostFactory":
        """
        Create comments for this post after creation.

        Args:
            count: Number of comments to create (default: 1)
            user_id: User ID for the comments. If not provided, creates a new user.

        Returns:
            PostFactory: Self for method chaining

        Example:
            >>> # Create post with comments (creates user automatically)
            >>> post = await factory.has_comments(10).create(user_id=user.id)
            >>>
            >>> # Create post with comments from specific user
            >>> post = await factory.has_comments(10, user_id=user.id).create(...)

        Educational Note:
            Comments need both post_id and user_id. If user_id is not provided,
            we create a user automatically. This demonstrates that relationship
            hooks can create their own dependencies!
        """
        if user_id is not None:
            # Use provided user_id
            return self.after_create(
                has_relationship(
                    CommentFactory, count, "post_id", self._session, user_id=user_id
                )
            )
        else:
            # Create a user on the fly for comments
            async def hook(parent: Base) -> None:
                # Create a user for the comments
                user_factory = UserFactory(self._session)
                comment_user = await user_factory.create()

                # Create comments
                comment_factory = CommentFactory(self._session)
                await comment_factory.create_batch(
                    count, post_id=parent.id, user_id=comment_user.id
                )

            return self.after_create(hook)


class CommentFactory(Factory[Comment]):
    """
    Factory for creating Comment instances.

    This factory generates comments with fake content.
    It requires both user_id and post_id to be provided.

    Example:
        >>> async with get_session() as session:
        ...     user = await UserFactory(session).create()
        ...     post = await PostFactory(session).create(user_id=user.id)
        ...
        ...     # Create comment
        ...     factory = CommentFactory(session)
        ...     comment = await factory.create(
        ...         user_id=user.id,
        ...         post_id=post.id
        ...     )
    """

    _model_class = Comment

    def definition(self) -> dict[str, Any]:
        """
        Define default comment attributes.

        Returns:
            dict[str, Any]: Default attributes with fake data

        Educational Note:
            Like PostFactory, we don't set user_id or post_id in the
            definition. These are required foreign keys and should be
            provided explicitly to avoid creating orphan records.
        """
        return {
            "content": self.faker.text(max_nb_chars=200),
        }
