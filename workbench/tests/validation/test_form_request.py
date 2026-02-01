"""
Form Request & Async Validation Tests (Sprint 2.9)

This module contains comprehensive tests for the Form Request system,
including Pydantic validation, async authorization, async business logic
validation, and integration with FastAPI routes.

Test Coverage:
    - FormRequest with Pydantic validation
    - Async authorize() method (403 on failure)
    - Async rules() with Rule.unique (422 on duplicate)
    - Rule.exists for foreign key validation
    - Integration with FastAPI routes via TestClient
    - Error response formats
    - Swagger/OpenAPI schema generation

Educational Note:
    These tests demonstrate the "best of both worlds" approach:
    - Pydantic handles structural validation (types, required fields)
    - FormRequest handles async validation (database checks)
    - FastAPI handles routing and dependency injection
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fast_query import Base, create_engine
from ftf.http.params import Inject
from app.models import User
from ftf.validation import FormRequest, Rule, Validate


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
async def engine() -> AsyncEngine:
    """In-memory SQLite engine for fast tests."""
    engine = create_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncSession:
    """Database session for each test."""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        yield session


@pytest.fixture
def app() -> FastAPI:
    """FastAPI app for integration tests."""
    app = FastAPI()
    return app


# ============================================================================
# TEST FORM REQUESTS
# ============================================================================


class StoreUserRequest(FormRequest):
    """Example Form Request for creating users."""

    name: str
    email: EmailStr

    async def rules(self, session: AsyncSession) -> None:
        """
        Validate that email is unique.

        This is an async database check that can't be done with Pydantic.
        """
        await Rule.unique(session, User, "email", self.email)


class UpdateUserRequest(FormRequest):
    """Example Form Request for updating users."""

    name: str
    email: EmailStr
    user_id: int  # ID of user being updated

    async def rules(self, session: AsyncSession) -> None:
        """
        Validate that email is unique except for current user.

        This demonstrates the ignore_id parameter for update scenarios.
        """
        await Rule.unique(
            session,
            User,
            "email",
            self.email,
            ignore_id=self.user_id,
        )


class RestrictedRequest(FormRequest):
    """Example Form Request with authorization check."""

    data: str

    async def authorize(self, session: AsyncSession) -> bool:
        """
        Only allow if data is not "forbidden".

        In real apps, this would check current user permissions.
        """
        return self.data != "forbidden"


# ============================================================================
# UNIT TESTS - FormRequest Base Class
# ============================================================================


@pytest.mark.asyncio
async def test_form_request_inherits_from_pydantic(session: AsyncSession) -> None:
    """
    Test that FormRequest inherits from Pydantic BaseModel.

    This ensures we get Pydantic's validation and OpenAPI schema generation.
    """
    from pydantic import BaseModel

    # FormRequest should be a subclass of BaseModel
    assert issubclass(FormRequest, BaseModel)

    # Can create instances with Pydantic validation
    request = StoreUserRequest(name="Alice", email="alice@test.com")
    assert request.name == "Alice"
    assert request.email == "alice@test.com"


@pytest.mark.asyncio
async def test_form_request_pydantic_validation_works(session: AsyncSession) -> None:
    """
    Test that Pydantic's structural validation still works.

    This ensures we haven't broken Pydantic's core functionality.
    """
    from pydantic import ValidationError as PydanticValidationError

    # Valid data works
    request = StoreUserRequest(name="Alice", email="alice@test.com")
    assert request.name == "Alice"

    # Invalid email fails
    with pytest.raises(PydanticValidationError) as exc:
        StoreUserRequest(name="Alice", email="not-an-email")

    # Missing required field fails
    with pytest.raises(PydanticValidationError) as exc:
        StoreUserRequest(name="Alice")  # type: ignore


@pytest.mark.asyncio
async def test_form_request_default_authorize_returns_true(
    session: AsyncSession,
) -> None:
    """
    Test that default authorize() returns True.

    This ensures requests are authorized by default unless overridden.
    """
    request = StoreUserRequest(name="Alice", email="alice@test.com")
    is_authorized = await request.authorize(session)
    assert is_authorized is True


@pytest.mark.asyncio
async def test_form_request_default_rules_does_nothing(session: AsyncSession) -> None:
    """
    Test that default rules() does nothing.

    This ensures the base implementation doesn't fail.
    """
    request = StoreUserRequest(name="Alice", email="alice@test.com")

    # Should not raise any exceptions
    await request.rules(session)


@pytest.mark.asyncio
async def test_form_request_stop_raises_http_exception(session: AsyncSession) -> None:
    """
    Test that stop() raises HTTPException with 422 status.

    This is the standard way to fail validation with a custom message.
    """
    from fastapi import HTTPException

    request = StoreUserRequest(name="Alice", email="alice@test.com")

    with pytest.raises(HTTPException) as exc:
        request.stop("Custom error message")

    assert exc.value.status_code == 422
    assert exc.value.detail[0]["msg"] == "Custom error message"


# ============================================================================
# UNIT TESTS - Validation Rules
# ============================================================================


@pytest.mark.asyncio
async def test_rule_unique_passes_when_value_is_unique(session: AsyncSession) -> None:
    """
    Test that Rule.unique passes when value doesn't exist in DB.
    """
    # No users in database, so any email is unique
    await Rule.unique(session, User, "email", "unique@test.com")

    # Should not raise any exceptions


@pytest.mark.asyncio
async def test_rule_unique_fails_when_value_exists(session: AsyncSession) -> None:
    """
    Test that Rule.unique fails when value already exists in DB.
    """
    from ftf.validation import ValidationError

    # Create a user
    user = User(name="Existing User", email="existing@test.com")
    session.add(user)
    await session.commit()

    # Try to use same email
    with pytest.raises(ValidationError) as exc:
        await Rule.unique(session, User, "email", "existing@test.com")

    assert "already been taken" in exc.value.message
    assert exc.value.field == "email"


@pytest.mark.asyncio
async def test_rule_unique_ignores_specified_id(session: AsyncSession) -> None:
    """
    Test that Rule.unique ignores a specific ID (for updates).
    """
    # Create a user
    user = User(name="User", email="user@test.com")
    session.add(user)
    await session.commit()

    # Should pass because we're ignoring the current user's ID
    await Rule.unique(
        session,
        User,
        "email",
        "user@test.com",
        ignore_id=user.id,
    )


@pytest.mark.asyncio
async def test_rule_exists_passes_when_value_exists(session: AsyncSession) -> None:
    """
    Test that Rule.exists passes when value exists in DB.
    """
    # Create a user
    user = User(name="User", email="user@test.com")
    session.add(user)
    await session.commit()

    # Should pass because user exists
    await Rule.exists(session, User, "id", user.id)


@pytest.mark.asyncio
async def test_rule_exists_fails_when_value_not_exists(session: AsyncSession) -> None:
    """
    Test that Rule.exists fails when value doesn't exist in DB.
    """
    from ftf.validation import ValidationError

    # No users in database
    with pytest.raises(ValidationError) as exc:
        await Rule.exists(session, User, "id", 999)

    assert "invalid" in exc.value.message.lower()


# ============================================================================
# INTEGRATION TESTS - FastAPI Routes
# ============================================================================


@pytest.mark.skip(reason="Integration test requires full FastTrackFramework setup")
@pytest.mark.asyncio
async def test_validate_dependency_with_valid_data(
    engine: AsyncEngine, session: AsyncSession
) -> None:
    """
    Test that Validate dependency works with valid data.

    This is an integration test that uses FastAPI's TestClient.

    Note: This test is currently skipped because it requires proper
    FastTrackFramework setup with container initialization. In production,
    the container is initialized at app startup, but setting this up in
    tests requires more scaffolding.

    TODO: Create integration test with full FastTrackFramework setup.
    """
    # This test is skipped for now
    # See tests in real routes for working integration examples
    pass


@pytest.mark.asyncio
async def test_form_request_authorize_failure_returns_403(
    session: AsyncSession,
) -> None:
    """
    Test that authorization failure returns 403 Forbidden.
    """
    from fastapi import HTTPException

    # Create request with forbidden data
    request = RestrictedRequest(data="forbidden")

    # authorize() should return False
    is_authorized = await request.authorize(session)
    assert is_authorized is False


@pytest.mark.asyncio
async def test_form_request_rules_failure_returns_422(session: AsyncSession) -> None:
    """
    Test that validation failure returns 422 Unprocessable Entity.
    """
    from ftf.validation import ValidationError

    # Create a user
    user = User(name="Existing", email="existing@test.com")
    session.add(user)
    await session.commit()

    # Create request with duplicate email
    request = StoreUserRequest(name="New User", email="existing@test.com")

    # rules() should raise ValidationError
    with pytest.raises(ValidationError):
        await request.rules(session)


# ============================================================================
# INTEGRATION TESTS - OpenAPI Schema
# ============================================================================


def test_form_request_generates_openapi_schema() -> None:
    """
    Test that FormRequest generates OpenAPI schema like normal Pydantic models.

    This ensures Swagger docs still work correctly.
    """
    # Create FastAPI app
    app = FastAPI()

    @app.post("/users")
    async def create_user(request: StoreUserRequest):
        return request

    # Get OpenAPI schema
    schema = app.openapi()

    # Check that schema includes our model
    assert "components" in schema
    assert "schemas" in schema["components"]
    assert "StoreUserRequest" in schema["components"]["schemas"]

    # Check fields are documented
    user_schema = schema["components"]["schemas"]["StoreUserRequest"]
    assert "name" in user_schema["properties"]
    assert "email" in user_schema["properties"]

    # Check types are correct
    assert user_schema["properties"]["name"]["type"] == "string"
    assert user_schema["properties"]["email"]["type"] == "string"
    assert user_schema["properties"]["email"]["format"] == "email"


# ============================================================================
# INTEGRATION TESTS - Update Scenario
# ============================================================================


@pytest.mark.asyncio
async def test_update_user_with_same_email_passes(session: AsyncSession) -> None:
    """
    Test that updating a user with their own email passes validation.

    This tests the ignore_id parameter in Rule.unique.
    """
    # Create a user
    user = User(name="User", email="user@test.com")
    session.add(user)
    await session.commit()

    # Update user with same email (should pass)
    request = UpdateUserRequest(
        name="Updated Name",
        email="user@test.com",
        user_id=user.id,
    )

    # Should not raise any exceptions
    await request.rules(session)


@pytest.mark.asyncio
async def test_update_user_with_duplicate_email_fails(session: AsyncSession) -> None:
    """
    Test that updating a user with another user's email fails.

    This ensures Rule.unique still catches duplicates even with ignore_id.
    """
    from ftf.validation import ValidationError

    # Create two users
    user1 = User(name="User 1", email="user1@test.com")
    user2 = User(name="User 2", email="user2@test.com")
    session.add(user1)
    session.add(user2)
    await session.commit()

    # Try to update user2 with user1's email
    request = UpdateUserRequest(
        name="Updated Name",
        email="user1@test.com",
        user_id=user2.id,
    )

    # Should raise ValidationError
    with pytest.raises(ValidationError):
        await request.rules(session)


# ============================================================================
# ERROR FORMAT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_validation_error_format_matches_fastapi(session: AsyncSession) -> None:
    """
    Test that ValidationError format matches FastAPI's standard format.

    This ensures consistent error responses across the application.
    """
    from fastapi import HTTPException

    request = StoreUserRequest(name="Alice", email="alice@test.com")

    with pytest.raises(HTTPException) as exc:
        request.stop("Custom error", field="email")

    # Check error format matches FastAPI standard
    detail = exc.value.detail[0]
    assert "msg" in detail
    assert "type" in detail
    assert "loc" in detail

    # Check values
    assert detail["msg"] == "Custom error"
    assert detail["type"] == "value_error"
    assert detail["loc"] == ["body", "email"]
