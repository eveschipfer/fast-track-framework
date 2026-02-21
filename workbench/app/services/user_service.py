"""
UserService — User Management Business Logic

Pure domain layer for User CRUD operations.

Design rules (same as ProductService):
    ✅ Repositories, domain models, Pydantic schemas, domain exceptions
    ❌ HTTPException, fastapi.status, JSONResponse, Request, Response

Raises:
    UserNotFound    — when a user cannot be located by ID.
    EmailAlreadyTaken — when a create/update would produce a duplicate email.
"""

from jtc.auth.crypto import hash_password, verify_password
from app.exceptions.auth_exceptions import EmailAlreadyTaken, UserNotFound
from app.repositories.user_repository import UserRepository
from app.schemas import UserCreate, UserResponse, UserUpdate
from fast_query import RecordNotFound


class UserService:
    """
    Orchestrates User CRUD operations.

    Receives ``UserRepository`` via the IoC container (scoped lifetime — one
    instance per HTTP request). All public methods return typed Pydantic objects.

    Password policy:
        - Passwords are hashed with bcrypt (via jtc.auth.crypto) before persisting.
        - Plain-text passwords are NEVER stored.
        - The response schema (UserResponse) never exposes the hashed password.
    """

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_all_users(self) -> list[UserResponse]:
        """Return all users (unfiltered, unsorted)."""
        users = await self.repo.all()
        return [UserResponse.model_validate(u) for u in users]

    async def get_user_by_id(self, user_id: int) -> UserResponse:
        """
        Locate a single user by primary key.

        Raises:
            UserNotFound: If no user with that ID exists.
        """
        try:
            user = await self.repo.find_or_fail(user_id)
        except RecordNotFound:
            raise UserNotFound(user_id)
        return UserResponse.model_validate(user)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create_user(self, data: UserCreate) -> UserResponse:
        """
        Register a new user.

        Hashes the plaintext password with bcrypt before persisting.

        Raises:
            EmailAlreadyTaken: If the email is already registered.
        """
        from app.models import User

        existing = await self.repo.find_by_email(data.email)
        if existing is not None:
            raise EmailAlreadyTaken(data.email)

        user = User(
            name=data.name,
            email=data.email,
            password=hash_password(data.password),
        )
        user = await self.repo.create(user)
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: int, data: UserUpdate) -> UserResponse:
        """
        Partially update an existing user.

        Only fields explicitly set in the payload are overwritten.
        If a new password is supplied it is re-hashed.

        Raises:
            UserNotFound: If the user does not exist.
            EmailAlreadyTaken: If the new email is already taken by another user.
        """
        try:
            user = await self.repo.find_or_fail(user_id)
        except RecordNotFound:
            raise UserNotFound(user_id)

        update_data = data.model_dump(exclude_unset=True)

        # Check email uniqueness if changing email
        if "email" in update_data:
            existing = await self.repo.find_by_email(update_data["email"])
            if existing is not None and existing.id != user_id:
                raise EmailAlreadyTaken(update_data["email"])

        # Re-hash password if provided
        if "password" in update_data:
            update_data["password"] = hash_password(update_data["password"])

        for key, value in update_data.items():
            setattr(user, key, value)

        user = await self.repo.update(user)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: int) -> None:
        """
        Soft-delete a user (sets deleted_at, does not remove the row).

        Raises:
            UserNotFound: If the user does not exist.
        """
        try:
            user = await self.repo.find_or_fail(user_id)
        except RecordNotFound:
            raise UserNotFound(user_id)

        await self.repo.delete(user)
