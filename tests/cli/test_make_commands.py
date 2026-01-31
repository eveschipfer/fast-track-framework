"""
Tests for CLI Make Commands (Sprint 3.0)

This module tests all make:* scaffolding commands to ensure they generate
files with correct structure, imports, and content.

Test Coverage:
    - make model: Generate models with mixins
    - make repository: Generate repositories
    - make request: Generate requests with governance warning
    - make factory: Generate factories
    - make seeder: Generate seeders
    - Helper functions: to_snake_case, pluralize
    - File conflict handling (--force flag)
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from ftf.cli.commands.make import pluralize, to_snake_case
from ftf.cli.main import app

# Create CLI test runner
runner = CliRunner()


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


def test_to_snake_case_converts_pascal_case() -> None:
    """Test that to_snake_case converts PascalCase to snake_case."""
    assert to_snake_case("User") == "user"
    assert to_snake_case("UserRepository") == "user_repository"
    assert to_snake_case("StoreUserRequest") == "store_user_request"
    assert to_snake_case("HTTPResponse") == "http_response"


def test_pluralize_simple_words() -> None:
    """Test that pluralize handles simple English pluralization."""
    assert pluralize("user") == "users"
    assert pluralize("post") == "posts"
    assert pluralize("comment") == "comments"


def test_pluralize_words_ending_in_y() -> None:
    """Test that pluralize handles words ending in 'y'."""
    assert pluralize("category") == "categories"
    assert pluralize("story") == "stories"


def test_pluralize_words_ending_in_s() -> None:
    """Test that pluralize handles words ending in 's'."""
    assert pluralize("class") == "classes"
    assert pluralize("address") == "addresses"


# ============================================================================
# MAKE MODEL TESTS
# ============================================================================


def test_make_model_creates_file(tmp_path: Path) -> None:
    """Test that make model creates a file with correct name."""
    # Change to temp directory
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Run command
        result = runner.invoke(app, ["make", "model", "Product"])

        # Check success
        assert result.exit_code == 0
        assert "✓ Model created:" in result.stdout

        # Check file exists
        model_file = tmp_path / "src/ftf/models/product.py"
        assert model_file.exists()

        # Check content
        content = model_file.read_text()
        assert "class Product(Base, TimestampMixin, SoftDeletesMixin):" in content
        assert '__tablename__ = "products"' in content
        assert "from fast_query import Base, SoftDeletesMixin, TimestampMixin" in content
    finally:
        os.chdir(original_dir)


def test_make_model_fails_if_file_exists(tmp_path: Path) -> None:
    """Test that make model fails if file already exists without --force."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Create file first time
        runner.invoke(app, ["make", "model", "Product"])

        # Try to create again
        result = runner.invoke(app, ["make", "model", "Product"])

        # Should fail
        assert result.exit_code == 1
        assert "✗ File already exists:" in result.stdout
        assert "--force" in result.stdout
    finally:
        os.chdir(original_dir)


def test_make_model_overwrites_with_force_flag(tmp_path: Path) -> None:
    """Test that make model overwrites file with --force flag."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Create file first time
        runner.invoke(app, ["make", "model", "Product"])

        # Overwrite with --force
        result = runner.invoke(app, ["make", "model", "Product", "--force"])

        # Should succeed
        assert result.exit_code == 0
        assert "✓ Model created:" in result.stdout
    finally:
        os.chdir(original_dir)


# ============================================================================
# MAKE REPOSITORY TESTS
# ============================================================================


def test_make_repository_creates_file(tmp_path: Path) -> None:
    """Test that make repository creates a file with correct name."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = runner.invoke(app, ["make", "repository", "ProductRepository"])

        assert result.exit_code == 0
        assert "✓ Repository created:" in result.stdout

        repo_file = tmp_path / "src/ftf/repositories/product_repository.py"
        assert repo_file.exists()

        content = repo_file.read_text()
        assert "class ProductRepository(BaseRepository[Product]):" in content
        assert "from fast_query import BaseRepository" in content
        assert "from ftf.models import Product" in content
    finally:
        os.chdir(original_dir)


def test_make_repository_auto_detects_model_name(tmp_path: Path) -> None:
    """Test that make repository auto-detects model name from repository name."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = runner.invoke(app, ["make", "repository", "UserRepository"])

        assert result.exit_code == 0

        repo_file = tmp_path / "src/ftf/repositories/user_repository.py"
        content = repo_file.read_text()

        # Should detect "User" model from "UserRepository"
        assert "from ftf.models import User" in content
        assert "BaseRepository[User]" in content
    finally:
        os.chdir(original_dir)


def test_make_repository_accepts_custom_model_name(tmp_path: Path) -> None:
    """Test that make repository accepts custom model name via --model flag."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = runner.invoke(
            app, ["make", "repository", "CustomRepo", "--model", "Product"]
        )

        assert result.exit_code == 0

        repo_file = tmp_path / "src/ftf/repositories/custom_repo.py"
        content = repo_file.read_text()

        # Should use specified model
        assert "from ftf.models import Product" in content
        assert "BaseRepository[Product]" in content
    finally:
        os.chdir(original_dir)


# ============================================================================
# MAKE REQUEST TESTS
# ============================================================================


def test_make_request_creates_file_with_governance_warning(tmp_path: Path) -> None:
    """Test that make request creates file with governance warning."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = runner.invoke(app, ["make", "request", "StoreProductRequest"])

        assert result.exit_code == 0
        assert "✓ Request created:" in result.stdout
        assert "⚠️  Remember: rules() is for validation only!" in result.stdout

        request_file = tmp_path / "src/ftf/requests/store_product_request.py"
        assert request_file.exists()

        content = request_file.read_text()

        # Check class definition
        assert "class StoreProductRequest(FormRequest):" in content

        # Check governance warnings (both in module docstring and rules() docstring)
        assert "⚠️ WARNING: rules() is for data validation only." in content
        assert "DO NOT mutate data or perform side effects here." in content
        assert "DO NOT:" in content
        assert "Mutate data (self.field = new_value)" in content

        # Check imports
        assert "from ftf.validation import FormRequest, Rule" in content
    finally:
        os.chdir(original_dir)


# ============================================================================
# MAKE FACTORY TESTS
# ============================================================================


def test_make_factory_creates_file(tmp_path: Path) -> None:
    """Test that make factory creates a file with correct name."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = runner.invoke(app, ["make", "factory", "ProductFactory"])

        assert result.exit_code == 0
        assert "✓ Factory created:" in result.stdout

        factory_file = tmp_path / "tests/factories/product_factory.py"
        assert factory_file.exists()

        content = factory_file.read_text()
        assert "class ProductFactory(Factory[Product]):" in content
        assert "_model_class = Product" in content
        assert "def definition(self) -> dict[str, Any]:" in content
        assert "from fast_query import Factory" in content
        assert "from ftf.models import Product" in content
    finally:
        os.chdir(original_dir)


def test_make_factory_auto_detects_model_name(tmp_path: Path) -> None:
    """Test that make factory auto-detects model name from factory name."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = runner.invoke(app, ["make", "factory", "UserFactory"])

        assert result.exit_code == 0

        factory_file = tmp_path / "tests/factories/user_factory.py"
        content = factory_file.read_text()

        # Should detect "User" model from "UserFactory"
        assert "from ftf.models import User" in content
        assert "Factory[User]" in content
        assert "_model_class = User" in content
    finally:
        os.chdir(original_dir)


# ============================================================================
# MAKE SEEDER TESTS
# ============================================================================


def test_make_seeder_creates_file(tmp_path: Path) -> None:
    """Test that make seeder creates a file with correct name."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        result = runner.invoke(app, ["make", "seeder", "ProductSeeder"])

        assert result.exit_code == 0
        assert "✓ Seeder created:" in result.stdout

        seeder_file = tmp_path / "tests/seeders/product_seeder.py"
        assert seeder_file.exists()

        content = seeder_file.read_text()
        assert "class ProductSeeder(Seeder):" in content
        assert "async def run(self) -> None:" in content
        assert "from fast_query import Seeder" in content
    finally:
        os.chdir(original_dir)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_make_commands_create_directory_structure(tmp_path: Path) -> None:
    """Test that make commands create necessary directory structure."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Run multiple commands
        runner.invoke(app, ["make", "model", "User"])
        runner.invoke(app, ["make", "repository", "UserRepository"])
        runner.invoke(app, ["make", "factory", "UserFactory"])

        # Check directories were created
        assert (tmp_path / "src/ftf/models").exists()
        assert (tmp_path / "src/ftf/repositories").exists()
        assert (tmp_path / "tests/factories").exists()
    finally:
        os.chdir(original_dir)
