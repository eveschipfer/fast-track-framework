"""
Fast Track Framework - Models Module

Database models using SQLAlchemy 2.0 with Repository Pattern.

All models inherit from Base and use Mapped[] type hints for
type safety and IDE support.

Example:
    from ftf.models import User
    from ftf.database import BaseRepository

    class UserRepository(BaseRepository[User]):
        pass

    # In route:
    @app.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        repo: UserRepository = Inject(UserRepository)
    ):
        return await repo.find_or_fail(user_id)
"""

from .user import User

__all__ = ["User"]
