"""
API Routes

This module contains main API routes for the workbench application.
Similar to Laravel's routes/api.php, all routes defined here will be
prefixed with /api.

Note:
    As of Sprint 18.2, product routes are registered via
    RouteServiceProvider (app/providers/route_service_provider.py) for proper
    dependency injection and organization.

The RouteServiceProvider automatically registers routes with
    FastTrackFramework application instance during the boot phase.

Available Routes:
    /api/products/*              - Product CRUD (registered by RouteServiceProvider)
    /api/                          - API health check and documentation

Example:
    GET /api/ping -> {"message": "pong"}
    GET /api/products -> [{"id": "...", "name": "Product 1"}, ...]
    POST /api/products -> Created product
    GET /api/products/{id} -> Single product
    PUT /api/products/{id} -> Updated product
    DELETE /api/products/{id} -> 204 No Content
"""

from fastapi import APIRouter

# Create main API router
api_router = APIRouter(tags=["API"])


@api_router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns API status and version information.
    Useful for load balancers and monitoring systems.

    Returns:
        dict: Health status information

    Example:
        GET /api/health
        Response: {
            "status": "healthy",
            "version": "1.0.0a1",
            "framework": "Fast Track Framework"
        }
    """
    return {
        "status": "healthy",
        "version": "1.0.0a1",
        "framework": "Fast Track Framework"
    }


@api_router.get("/")
async def api_index() -> dict[str, Any]:
    """
    API index endpoint.

    Returns available API endpoints and documentation links.

    Returns:
        dict: API information and available routes

    Example:
        GET /api/
        Response: {
            "name": "Fast Track Framework API",
            "version": "1.0.0a1",
            "endpoints": {
                "products": "/api/products",
                "health": "/api/health"
            },
            "documentation": "/docs"
        }
    """
    return {
        "name": "Fast Track Framework API",
        "version": "1.0.0a1",
        "endpoints": {
            "products": "/api/products",
            "health": "/api/health",
        },
        "documentation": "/docs",
    }
