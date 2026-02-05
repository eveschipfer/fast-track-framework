"""
Example StoreUserRequest with Method Injection (Sprint 11)

This example demonstrates the new METHOD INJECTION capability
for FormRequest.rules() method.

Created for testing and documentation purposes.
"""

from ftf.validation import FormRequest, Validate, Rule
from ftf.auth.contracts import Credentials
from app.models import User


class StoreUserRequest(FormRequest):
    """
    Example Form Request with METHOD INJECTION.

    This demonstrates how to inject UserRepository instead of
    hardcoded AsyncSession, leveraging the Container DI system.
    """

    name: str
    email: str

    async def authorize(self, session) -> bool:
        """
        Check if user is authorized.

        Sprint 11: Can also inject AuthManager here:
            async def authorize(self, auth) -> bool
        """
        return True

    async def rules(self, user_repo) -> None:
        """
        Validate email uniqueness using injected UserRepository.

        Args:
            user_repo: UserRepository (injected automatically!)
        """
        await Rule.unique(user_repo, User, "email", self.email)


class LoginRequest(FormRequest):
    """
    Example LoginRequest demonstrating AuthManager injection.

    Sprint 11: Shows how AuthManager can be injected for
    credential validation.
    """

    email: str
    password: str

    async def authorize(self, auth) -> bool:
        """
        Check if credentials are valid using AuthManager.

        Args:
            auth: AuthManager (injected automatically!)
        """
        from ftf.auth import AuthManager
        from ftf.auth.contracts import Credentials

        credentials = Credentials(email=self.email, password=self.password)
        return await auth.check(credentials)

    async def rules(self, auth) -> None:
        """
        Validate credentials using AuthManager.

        Args:
            auth: AuthManager (injected automatically!)
        """
        pass
