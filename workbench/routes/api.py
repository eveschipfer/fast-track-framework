"""
API Routes

This module contains the main API routes for the workbench application.
Similar to Laravel's routes/api.php, all routes defined here will be
prefixed with /api.

The RouteServiceProvider automatically registers these routes with
the FastTrackFramework application instance.

Example:
    GET /api/ping -> {"message": "pong"}
    GET /api/users -> [{"id": 1, "name": "John Doe"}, ...]
"""

from fastapi import APIRouter

# Create API router (will be prefixed with /api by RouteServiceProvider)
api_router = APIRouter()


@api_router.get("/ping")
async def ping() -> dict[str, str]:
    """
    Simple ping endpoint to verify the API is responding.

    Returns:
        dict: A simple pong message

    Example:
        >>> GET /api/ping
        {"message": "pong"}
    """
    return {"message": "pong"}


@api_router.get("/users")
async def list_users() -> list[dict[str, str | int]]:
    """
    List all users (sample endpoint).

    This is a placeholder endpoint that returns mock data.
    In a real application, this would query the database via
    a repository and return actual user data.

    Returns:
        list: List of user dictionaries

    Example:
        >>> GET /api/users
        [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
        ]
    """
    # Mock data - in production, this would come from UserRepository
    return [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
    ]
