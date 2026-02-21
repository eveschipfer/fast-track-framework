"""
UserController — HTTP Handler Layer for /users resource

Architecture:
    Request → Route function → UserController method
                → UserService method (pure domain logic)
                → UserRepository → Database

Exception mapping (domain → HTTP):
    UserNotFound      → 404 Not Found
    EmailAlreadyTaken → 422 Unprocessable Entity

All routes under /api/users require authentication (JWT token via
JwtMiddleware + explicit guard in each route function).
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status

from jtc.http import Inject

from app.exceptions.auth_exceptions import EmailAlreadyTaken, UserNotFound
from jtc.http import BaseController
from app.schemas import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService
from jtc.validation import Validate


# ============================================================================
# CONTROLLER
# ============================================================================


class UserController(BaseController):
    """
    Handles HTTP concerns for the /users resource.

    Receives ``UserService`` from the IoC container (scoped lifetime).
    Never contains domain logic — delegates everything to the service layer.
    """

    def __init__(self, service: UserService) -> None:
        self.service = service

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_auth(request: Request) -> dict[str, Any]:
        """
        Assert that JwtMiddleware has populated request.state.user.

        Returns the JWT payload dict if authenticated.

        Raises:
            HTTPException 401: If the request carries no valid token.
        """
        user_payload = getattr(request.state, "user", None)
        if not user_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_payload

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def index(self, request: Request) -> list[UserResponse]:
        """Return all users (requires auth)."""
        self._require_auth(request)
        return self.ok(await self.service.get_all_users())

    async def show(self, user_id: int, request: Request) -> UserResponse:
        """Return a single user by ID (requires auth)."""
        self._require_auth(request)
        try:
            return self.ok(await self.service.get_user_by_id(user_id))
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found.",
            )

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def store(self, payload: UserCreate) -> UserResponse:
        """
        Register a new user (public endpoint — no auth required).

        Returns 201 Created on success.
        Returns 422 if the email is already taken.
        """
        try:
            return self.created(await self.service.create_user(payload))
        except EmailAlreadyTaken as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

    async def update(
        self, user_id: int, payload: UserUpdate, request: Request
    ) -> UserResponse:
        """Update a user's profile (requires auth)."""
        self._require_auth(request)
        try:
            return self.ok(await self.service.update_user(user_id, payload))
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found.",
            )
        except EmailAlreadyTaken as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            )

    async def destroy(self, user_id: int, request: Request) -> Response:
        """Delete a user (requires auth). Returns 204 No Content."""
        self._require_auth(request)
        try:
            await self.service.delete_user(user_id)
            return self.no_content()
        except UserNotFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found.",
            )


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        401: {"description": "Authentication required"},
        404: {"description": "User not found"},
        422: {"description": "Validation error or email already taken"},
    },
)


@router.get("", response_model=list[UserResponse])
async def index(
    request: Request,
    controller: UserController = Inject(UserController),
) -> list[UserResponse]:
    """
    List all users.

    Requires: Authorization: Bearer <access_token>
    """
    return await controller.index(request)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def store(
    payload: UserCreate = Validate(UserCreate),
    controller: UserController = Inject(UserController),
) -> UserResponse:
    """
    Register a new user.

    Public endpoint — no authentication required.
    Returns 422 if the email is already registered.
    """
    return await controller.store(payload)


@router.get("/{user_id}", response_model=UserResponse)
async def show(
    user_id: int,
    request: Request,
    controller: UserController = Inject(UserController),
) -> UserResponse:
    """
    Get user by ID.

    Requires: Authorization: Bearer <access_token>
    """
    return await controller.show(user_id, request)


@router.put("/{user_id}", response_model=UserResponse)
async def update(
    user_id: int,
    request: Request,
    payload: UserUpdate = Validate(UserUpdate),
    controller: UserController = Inject(UserController),
) -> UserResponse:
    """
    Update a user's profile (partial — only supplied fields overwritten).

    Requires: Authorization: Bearer <access_token>
    """
    return await controller.update(user_id, payload, request)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    user_id: int,
    request: Request,
    controller: UserController = Inject(UserController),
) -> Response:
    """
    Delete a user (soft-delete via SoftDeletesMixin).

    Requires: Authorization: Bearer <access_token>
    Returns 204 No Content on success.
    """
    return await controller.destroy(user_id, request)
