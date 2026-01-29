"""
Fast Track Framework - Models Module

Database models using SQLAlchemy 2.0 with Repository Pattern.

All models inherit from Base and use Mapped[] type hints for
type safety and IDE support.

Models:
    User: User model with posts, comments, and roles relationships
    Post: Blog post model with author and comments relationships
    Comment: Comment model with post and author relationships
    Role: Role model for authorization (many-to-many with User)

Example:
    from ftf.models import User, Post, Comment, Role
    from ftf.database import BaseRepository

    class UserRepository(BaseRepository[User]):
        async def get_with_posts(self, user_id: int) -> User:
            return await (
                self.query()
                .where(User.id == user_id)
                .with_(User.posts)  # Eager load posts
                .first_or_fail()
            )

    # In route:
    @app.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        repo: UserRepository = Inject(UserRepository)
    ):
        return await repo.get_with_posts(user_id)

See: docs/relationships.md for relationship usage guide
"""

from .comment import Comment
from .post import Post
from .role import Role
from .user import User

__all__ = ["Comment", "Post", "Role", "User"]
