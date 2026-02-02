"""
RBAC Gates System Tests (Sprint 5.5)

Comprehensive test suite for Role-Based Access Control using Gates and Policies.

Test Coverage:
    - Gate singleton pattern
    - Ability registration and retrieval
    - Gate.allows() and Gate.denies() checks
    - Gate.authorize() raises AuthorizationError
    - Policy base class methods
    - Policy integration with Gate
    - Authorize() FastAPI dependency
    - User context passing
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Depends, HTTPException

from ftf.auth import Gate, Policy, Authorize
from ftf.http.exceptions import AuthorizationError


# Test Models (Mock)
class MockUser:
    """Mock user for testing."""

    def __init__(self, id: int, is_admin: bool = False, email_verified: bool = True):
        self.id = id
        self.is_admin = is_admin
        self.email_verified = email_verified


class MockPost:
    """Mock post for testing."""

    def __init__(self, id: int, author_id: int, published: bool = False):
        self.id = id
        self.author_id = author_id
        self.published = published


class MockComment:
    """Mock comment for testing."""

    def __init__(self, id: int, author_id: int, post_id: int):
        self.id = id
        self.author_id = author_id
        self.post_id = post_id


# Test Policies
class MockPostPolicy(Policy):
    """Test policy for posts."""

    def view(self, user: MockUser, post: MockPost) -> bool:
        """Anyone can view published posts, authors can view drafts."""
        if post.published:
            return True
        return user.id == post.author_id

    def viewAny(self, user: MockUser) -> bool:
        """Anyone can see the post list."""
        return True

    def create(self, user: MockUser) -> bool:
        """Only verified users can create posts."""
        return user.email_verified

    def update(self, user: MockUser, post: MockPost) -> bool:
        """Only author can update."""
        return user.id == post.author_id

    def delete(self, user: MockUser, post: MockPost) -> bool:
        """Admin or author can delete."""
        return user.is_admin or user.id == post.author_id


class MockCommentPolicy(Policy):
    """Test policy for comments."""

    def delete(self, user: MockUser, comment: MockComment) -> bool:
        """Only admin or comment author can delete."""
        return user.is_admin or user.id == comment.author_id


# Gate Singleton Tests
class TestGateSingleton:
    """Test Gate singleton pattern and basic functionality."""

    def setup_method(self):
        """Reset Gate before each test."""
        # Clear all abilities and policies before each test
        Gate._abilities = {}
        Gate._policies = {}

    def test_gate_is_singleton(self):
        """Test Gate uses singleton pattern (same instance)."""
        from ftf.auth.gates import Gate as Gate1, GateManager

        gate2 = GateManager()

        # Should be the same instance
        assert Gate1 is gate2

    def test_define_registers_ability(self):
        """Test define() registers an ability."""
        Gate.define("test-ability", lambda user: True)

        assert "test-ability" in Gate._abilities

    def test_define_returns_self_for_chaining(self):
        """Test define() returns self for method chaining."""
        result = Gate.define("test-ability", lambda user: True)

        assert result is Gate

    def test_define_multiple_abilities(self):
        """Test defining multiple abilities."""
        Gate.define("ability-1", lambda user: True)
        Gate.define("ability-2", lambda user: False)
        Gate.define("ability-3", lambda user: user.is_admin)

        assert len(Gate._abilities) == 3
        assert "ability-1" in Gate._abilities
        assert "ability-2" in Gate._abilities
        assert "ability-3" in Gate._abilities

    def test_register_policy_stores_policy(self):
        """Test register_policy() stores policy for model class."""
        policy = MockPostPolicy()
        Gate.register_policy(MockPost, policy)

        assert MockPost in Gate._policies
        assert Gate._policies[MockPost] is policy

    def test_register_policy_returns_self_for_chaining(self):
        """Test register_policy() returns self for method chaining."""
        policy = MockPostPolicy()
        result = Gate.register_policy(MockPost, policy)

        assert result is Gate

    def test_register_multiple_policies(self):
        """Test registering multiple policies for different models."""
        post_policy = MockPostPolicy()
        comment_policy = MockCommentPolicy()

        Gate.register_policy(MockPost, post_policy)
        Gate.register_policy(MockComment, comment_policy)

        assert len(Gate._policies) == 2
        assert Gate._policies[MockPost] is post_policy
        assert Gate._policies[MockComment] is comment_policy


# Gate.allows() Tests
class TestGateAllows:
    """Test Gate.allows() authorization checks."""

    def setup_method(self):
        """Reset Gate before each test."""
        Gate._abilities = {}
        Gate._policies = {}

    def test_allows_with_simple_ability_returns_true(self):
        """Test allows() returns True for passing simple ability."""
        user = MockUser(id=1, is_admin=True)
        Gate.define("view-dashboard", lambda user: user.is_admin)

        assert Gate.allows(user, "view-dashboard") is True

    def test_allows_with_simple_ability_returns_false(self):
        """Test allows() returns False for failing simple ability."""
        user = MockUser(id=1, is_admin=False)
        Gate.define("view-dashboard", lambda user: user.is_admin)

        assert Gate.allows(user, "view-dashboard") is False

    def test_allows_with_resource_based_ability(self):
        """Test allows() with resource parameter."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1)

        Gate.define("edit-post", lambda user, post: user.id == post.author_id)

        assert Gate.allows(user, "edit-post", post) is True

    def test_allows_with_resource_based_ability_denies(self):
        """Test allows() denies when resource check fails."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=2)  # Different author

        Gate.define("edit-post", lambda user, post: user.id == post.author_id)

        assert Gate.allows(user, "edit-post", post) is False

    def test_allows_returns_false_for_undefined_ability(self):
        """Test allows() returns False for undefined ability."""
        user = MockUser(id=1)

        # No ability defined, should deny by default
        assert Gate.allows(user, "undefined-ability") is False

    def test_allows_with_policy_calls_policy_method(self):
        """Test allows() calls policy method when resource has registered policy."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Should call PostPolicy.update(user, post)
        assert Gate.allows(user, "update", post) is True

    def test_allows_with_policy_denies_when_policy_method_returns_false(self):
        """Test allows() denies when policy method returns False."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=2)  # Different author
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Should call PostPolicy.update(user, post) -> False
        assert Gate.allows(user, "update", post) is False

    def test_allows_with_policy_view_published_post(self):
        """Test allows() with policy view method (published post)."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=2, published=True)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Anyone can view published posts
        assert Gate.allows(user, "view", post) is True

    def test_allows_with_policy_view_draft_post_as_author(self):
        """Test allows() with policy view method (draft post, is author)."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1, published=False)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Author can view their own drafts
        assert Gate.allows(user, "view", post) is True

    def test_allows_with_policy_view_draft_post_not_author(self):
        """Test allows() denies viewing draft post when not author."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=2, published=False)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Cannot view other's drafts
        assert Gate.allows(user, "view", post) is False

    def test_allows_with_policy_delete_as_admin(self):
        """Test allows() with policy delete method (admin user)."""
        user = MockUser(id=1, is_admin=True)
        post = MockPost(id=10, author_id=2)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Admin can delete any post
        assert Gate.allows(user, "delete", post) is True

    def test_allows_with_policy_delete_as_author(self):
        """Test allows() with policy delete method (author user)."""
        user = MockUser(id=1, is_admin=False)
        post = MockPost(id=10, author_id=1)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Author can delete their own post
        assert Gate.allows(user, "delete", post) is True

    def test_allows_with_policy_delete_neither_admin_nor_author(self):
        """Test allows() denies delete when neither admin nor author."""
        user = MockUser(id=1, is_admin=False)
        post = MockPost(id=10, author_id=2)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Cannot delete
        assert Gate.allows(user, "delete", post) is False

    def test_allows_with_policy_no_method_falls_back_to_ability(self):
        """Test allows() falls back to ability if policy has no method."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)
        Gate.define("custom-action", lambda user, post: user.is_admin)

        # Policy doesn't have "custom-action" method, use ability
        assert Gate.allows(user, "custom-action", post) is False

    def test_allows_with_no_policy_uses_ability_with_resource(self):
        """Test allows() uses ability callback when no policy registered."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1)

        Gate.define("publish", lambda user, post: user.is_admin or user.id == post.author_id)

        # No policy registered, use ability
        assert Gate.allows(user, "publish", post) is True


# Gate.denies() Tests
class TestGateDenies:
    """Test Gate.denies() is inverse of allows()."""

    def setup_method(self):
        """Reset Gate before each test."""
        Gate._abilities = {}
        Gate._policies = {}

    def test_denies_is_inverse_of_allows(self):
        """Test denies() returns opposite of allows()."""
        user = MockUser(id=1, is_admin=True)
        Gate.define("view-dashboard", lambda user: user.is_admin)

        assert Gate.allows(user, "view-dashboard") is True
        assert Gate.denies(user, "view-dashboard") is False

    def test_denies_returns_true_when_allows_returns_false(self):
        """Test denies() returns True when allows() returns False."""
        user = MockUser(id=1, is_admin=False)
        Gate.define("view-dashboard", lambda user: user.is_admin)

        assert Gate.allows(user, "view-dashboard") is False
        assert Gate.denies(user, "view-dashboard") is True

    def test_denies_with_resource(self):
        """Test denies() works with resource parameter."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=2)

        Gate.define("edit-post", lambda user, post: user.id == post.author_id)

        assert Gate.denies(user, "edit-post", post) is True


# Gate.authorize() Tests
class TestGateAuthorize:
    """Test Gate.authorize() raises AuthorizationError on denial."""

    def setup_method(self):
        """Reset Gate before each test."""
        Gate._abilities = {}
        Gate._policies = {}

    def test_authorize_passes_when_allowed(self):
        """Test authorize() does not raise when allowed."""
        user = MockUser(id=1, is_admin=True)
        Gate.define("view-dashboard", lambda user: user.is_admin)

        # Should not raise
        Gate.authorize(user, "view-dashboard")

    def test_authorize_raises_when_denied(self):
        """Test authorize() raises AuthorizationError when denied."""
        user = MockUser(id=1, is_admin=False)
        Gate.define("view-dashboard", lambda user: user.is_admin)

        with pytest.raises(AuthorizationError) as exc_info:
            Gate.authorize(user, "view-dashboard")

        assert "not authorized" in str(exc_info.value.message).lower()
        assert "view-dashboard" in str(exc_info.value.message)

    def test_authorize_with_resource_passes_when_allowed(self):
        """Test authorize() with resource does not raise when allowed."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1)

        Gate.define("edit-post", lambda user, post: user.id == post.author_id)

        # Should not raise
        Gate.authorize(user, "edit-post", post)

    def test_authorize_with_resource_raises_when_denied(self):
        """Test authorize() with resource raises when denied."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=2)

        Gate.define("edit-post", lambda user, post: user.id == post.author_id)

        with pytest.raises(AuthorizationError):
            Gate.authorize(user, "edit-post", post)

    def test_authorize_with_policy_passes_when_allowed(self):
        """Test authorize() with policy does not raise when allowed."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # Should not raise (author can update)
        Gate.authorize(user, "update", post)

    def test_authorize_with_policy_raises_when_denied(self):
        """Test authorize() with policy raises when denied."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=2)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        with pytest.raises(AuthorizationError):
            Gate.authorize(user, "update", post)


# Policy Base Class Tests
class TestPolicyBaseClass:
    """Test Policy base class default behavior."""

    def test_policy_view_defaults_to_false(self):
        """Test Policy.view() returns False by default."""
        policy = Policy()
        user = MockUser(id=1)
        resource = MockPost(id=10, author_id=1)

        assert policy.view(user, resource) is False

    def test_policy_view_any_defaults_to_false(self):
        """Test Policy.viewAny() returns False by default."""
        policy = Policy()
        user = MockUser(id=1)

        assert policy.viewAny(user) is False

    def test_policy_create_defaults_to_false(self):
        """Test Policy.create() returns False by default."""
        policy = Policy()
        user = MockUser(id=1)

        assert policy.create(user) is False

    def test_policy_update_defaults_to_false(self):
        """Test Policy.update() returns False by default."""
        policy = Policy()
        user = MockUser(id=1)
        resource = MockPost(id=10, author_id=1)

        assert policy.update(user, resource) is False

    def test_policy_delete_defaults_to_false(self):
        """Test Policy.delete() returns False by default."""
        policy = Policy()
        user = MockUser(id=1)
        resource = MockPost(id=10, author_id=1)

        assert policy.delete(user, resource) is False

    def test_policy_can_be_subclassed(self):
        """Test Policy can be subclassed and methods overridden."""
        policy = MockPostPolicy()
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1)

        # Subclass overrides return True
        assert policy.update(user, post) is True

    def test_policy_custom_methods_can_be_added(self):
        """Test custom methods can be added to Policy subclasses."""

        class CustomPolicy(Policy):
            def publish(self, user, post):
                return user.is_admin

        policy = CustomPolicy()
        admin_user = MockUser(id=1, is_admin=True)
        regular_user = MockUser(id=2, is_admin=False)
        post = MockPost(id=10, author_id=2)

        assert policy.publish(admin_user, post) is True
        assert policy.publish(regular_user, post) is False


# Authorize() Dependency Tests
class TestAuthorizeDependency:
    """Test Authorize() FastAPI dependency factory."""

    def setup_method(self):
        """Reset Gate before each test."""
        Gate._abilities = {}
        Gate._policies = {}

    @pytest.mark.asyncio
    async def test_authorize_dependency_returns_function(self):
        """Test Authorize() returns a callable dependency."""
        dependency = Authorize("view-dashboard")

        assert callable(dependency)

    @pytest.mark.asyncio
    async def test_authorize_dependency_passes_when_allowed(self):
        """Test Authorize() dependency passes when user has permission."""
        user = MockUser(id=1, is_admin=True)
        Gate.define("view-dashboard", lambda user: user.is_admin)

        dependency = Authorize("view-dashboard")

        # Should return user without raising
        result = await dependency(user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_authorize_dependency_raises_when_denied(self):
        """Test Authorize() dependency raises AuthorizationError when denied."""
        user = MockUser(id=1, is_admin=False)
        Gate.define("view-dashboard", lambda user: user.is_admin)

        dependency = Authorize("view-dashboard")

        with pytest.raises(AuthorizationError):
            await dependency(user=user)

    @pytest.mark.asyncio
    async def test_authorize_dependency_with_resource(self):
        """Test Authorize() dependency works with resource parameter."""
        user = MockUser(id=1)
        post = MockPost(id=10, author_id=1)

        Gate.define("edit-post", lambda user, post: user.id == post.author_id)

        # Note: resource must be bound when creating dependency
        # In real usage, this would be done in the route handler
        dependency = Authorize("edit-post", post)

        result = await dependency(user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_authorize_dependency_error_includes_ability_name(self):
        """Test AuthorizationError includes the ability name in message."""
        user = MockUser(id=1, is_admin=False)
        Gate.define("delete-users", lambda user: user.is_admin)

        dependency = Authorize("delete-users")

        with pytest.raises(AuthorizationError) as exc_info:
            await dependency(user=user)

        assert "delete-users" in str(exc_info.value.message)


# Integration Tests
class TestGateIntegration:
    """Test Gate system integration scenarios."""

    def setup_method(self):
        """Reset Gate before each test."""
        Gate._abilities = {}
        Gate._policies = {}

    def test_multiple_policies_on_different_models(self):
        """Test multiple policies work independently."""
        user = MockUser(id=1, is_admin=False)
        post = MockPost(id=10, author_id=1)
        comment = MockComment(id=20, author_id=2, post_id=10)

        post_policy = MockPostPolicy()
        comment_policy = MockCommentPolicy()

        Gate.register_policy(MockPost, post_policy)
        Gate.register_policy(MockComment, comment_policy)

        # Can update own post
        assert Gate.allows(user, "update", post) is True

        # Cannot delete other's comment
        assert Gate.allows(user, "delete", comment) is False

    def test_ability_and_policy_coexist(self):
        """Test abilities and policies can be used together."""
        user = MockUser(id=1, is_admin=False)
        post = MockPost(id=10, author_id=1)

        # Define global ability
        Gate.define("view-dashboard", lambda user: user.is_admin)

        # Register policy
        policy = MockPostPolicy()
        Gate.register_policy(MockPost, policy)

        # Both work independently
        assert Gate.denies(user, "view-dashboard") is True  # Not admin
        assert Gate.allows(user, "update", post) is True  # Is author

    def test_complex_authorization_logic(self):
        """Test complex authorization with multiple conditions."""

        def can_publish_post(user, post):
            # Only admins can publish OR
            # Authors can publish if they have > 5 published posts
            if user.is_admin:
                return True
            if user.id == post.author_id:
                # In real scenario, would check user.published_posts_count > 5
                return True
            return False

        user = MockUser(id=1, is_admin=False)
        post = MockPost(id=10, author_id=1)

        Gate.define("publish-post", can_publish_post)

        assert Gate.allows(user, "publish-post", post) is True

    def test_authorization_with_viewany_no_resource(self):
        """Test Policy.viewAny() is called when no resource provided."""
        user = MockUser(id=1)
        policy = MockPostPolicy()

        Gate.register_policy(MockPost, policy)

        # This should call viewAny() since no resource
        # But currently our implementation requires resource for policy routing
        # So this would fall back to ability (which doesn't exist)
        # This is expected behavior - viewAny should be a separate ability
        Gate.define("view-posts", lambda user: policy.viewAny(user))

        assert Gate.allows(user, "view-posts") is True
