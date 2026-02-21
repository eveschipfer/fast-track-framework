"""
Product Domain Exceptions

These exceptions represent domain-level failures and are deliberately free of
any HTTP or framework concerns. The service layer raises them; the controller
layer is responsible for translating them into the appropriate HTTP responses.

Why domain exceptions instead of HTTPException?
    - Services stay independently testable (no HTTP layer required).
    - The same service can power REST controllers, CLI commands, and async jobs
      without modification.
    - Exception semantics belong to the domain; status codes belong to HTTP.
"""


class ProductNotFound(Exception):
    """Raised when a product cannot be located by any identifier (ID or slug)."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Product '{identifier}' not found")


class DuplicateSlug(Exception):
    """Raised when a create/update would produce a slug that already exists."""

    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"A product with slug '{slug}' already exists")
