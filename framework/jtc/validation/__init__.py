"""
Form Request & Async Validation System (Sprint 2.9)

This package provides a Laravel-inspired Form Request system that combines
Pydantic's structural validation with async authorization and business logic
validation.

Public API:
    - FormRequest: Base class for form requests
    - Validate: Dependency resolver for FastAPI routes
    - Rule: Validation rule helpers (unique, exists)
    - ValidationError: Custom validation error exception

Example Usage:
    from jtc.validation import FormRequest, Validate, Rule
    from pydantic import EmailStr

    class StoreUserRequest(FormRequest):
        name: str
        email: EmailStr

        async def authorize(self, session: AsyncSession) -> bool:
            # Check if user has permission
            return True

        async def rules(self, session: AsyncSession) -> None:
            # Check if email is unique
            await Rule.unique(session, User, "email", self.email)

    @app.post("/users")
    async def create(request: StoreUserRequest = Validate(StoreUserRequest)):
        # request is fully validated and authorized
        return {"message": "User created", "data": request}

Educational Note:
    This solves a key limitation of Pydantic: it's synchronous and can't
    perform async database checks during validation. Our solution:
    1. Use Pydantic for structural validation (preserves Swagger docs)
    2. Use async methods for business logic validation (DB checks)
    3. Integrate with FastAPI's dependency injection system
"""

from jtc.validation.handler import Validate, ValidateWith
from jtc.validation.request import FormRequest, ValidationError
from jtc.validation.rules import Rule

__all__ = [
    # Core classes
    "FormRequest",
    "ValidationError",
    # Dependency resolver
    "Validate",
    "ValidateWith",
    # Validation rules
    "Rule",
]
