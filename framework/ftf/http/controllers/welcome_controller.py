"""
Welcome Controller - Proof of Concept for FastAPI Integration

This controller demonstrates:
1. Service class definition (dependency)
2. FastAPI router setup
3. Dependency injection using Inject()
4. JSON response handling

This is an educational example showing how Fast Track Framework
integrates the IoC Container with FastAPI routes.
"""

from fastapi import APIRouter

from ftf.http.params import Inject

# ============================================================================
# SERVICE LAYER
# ============================================================================


class MessageService:
    """
    Simple service for generating welcome messages.

    This acts as a dependency that will be injected into the controller.
    In a real application, this might interact with databases, external APIs,
    or perform complex business logic.

    Design Decision:
        No __init__ parameters means Container can instantiate it directly
        without resolving dependencies. This makes it a good starting point
        for demonstrating DI basics.
    """

    def get_welcome_message(self) -> str:
        """
        Generate a welcome message.

        Returns:
            Welcome message string
        """
        return "Welcome to Fast Track Framework! 🚀"

    def get_info(self) -> dict[str, str]:
        """
        Get framework information.

        Returns:
            Dictionary with framework details
        """
        return {
            "framework": "Fast Track Framework",
            "version": "0.1.0",
            "description": "A Laravel-inspired micro-framework built on FastAPI",
            "status": "Sprint 2.1 - FastAPI Integration Complete",
        }


# ============================================================================
# ROUTER SETUP
# ============================================================================

# Create router (will be included in main app)
router = APIRouter(
    tags=["welcome"],
    responses={
        404: {"description": "Not found"},
    },
)


# ============================================================================
# ROUTE HANDLERS
# ============================================================================


@router.get("/")
def index(service: MessageService = Inject(MessageService)) -> dict[str, str]:
    """
    Root endpoint - returns welcome message.

    This demonstrates basic dependency injection:
    - MessageService is injected via Inject()
    - Container resolves and instantiates MessageService
    - Route handler receives the instance and uses it

    Args:
        service: MessageService injected by the Container

    Returns:
        JSON response with welcome message

    Example Response:
        {
            "message": "Welcome to Fast Track Framework! 🚀"
        }
    """
    return {"message": service.get_welcome_message()}


@router.get("/info")
def info(service: MessageService = Inject(MessageService)) -> dict[str, str]:
    """
    Info endpoint - returns framework information.

    This demonstrates that the same service can be injected
    into multiple routes. Depending on the registration scope:
    - transient: New instance for each request
    - scoped: Same instance within a request
    - singleton: Same instance across all requests

    Args:
        service: MessageService injected by the Container

    Returns:
        JSON response with framework information

    Example Response:
        {
            "framework": "Fast Track Framework",
            "version": "0.1.0",
            "description": "A Laravel-inspired micro-framework built on FastAPI",
            "status": "Sprint 2.1 - FastAPI Integration Complete"
        }
    """
    return service.get_info()


@router.get("/health")
def health() -> dict[str, str]:
    """
    Health check endpoint - no dependencies required.

    This demonstrates that routes can exist without DI if needed.

    Returns:
        JSON response with health status

    Example Response:
        {
            "status": "healthy"
        }
    """
    return {"status": "healthy"}
