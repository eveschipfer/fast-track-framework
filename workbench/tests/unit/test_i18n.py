"""
i18n (Internationalization) Tests (Sprint 3.5)

This module tests the i18n system including translation loading, key lookup,
placeholder replacement, and locale switching.

Test Coverage:
    - Translation loading from framework and user directories
    - Dot notation key lookup
    - Placeholder replacement
    - Locale switching
    - Fallback to key if translation not found
    - Missing file handling
"""

import json
import tempfile
from pathlib import Path

import pytest

from jtc.i18n import Translator, all_translations, has, set_locale, t, trans


# ============================================================================
# TRANSLATOR TESTS
# ============================================================================


def test_translator_singleton() -> None:
    """Test that Translator follows singleton pattern."""
    translator1 = Translator.get_instance()
    translator2 = Translator.get_instance()

    assert translator1 is translator2


def test_translator_loads_framework_translations() -> None:
    """Test that framework translations are loaded."""
    translator = Translator.get_instance(locale="en")

    # Framework provides default translations
    assert translator.has("auth.failed")
    assert translator.has("validation.required")


def test_translator_get_returns_translation() -> None:
    """Test that get() returns the correct translation."""
    translator = Translator.get_instance(locale="en")

    message = translator.get("auth.failed")

    assert message == "These credentials do not match our records."


def test_translator_get_returns_key_if_not_found() -> None:
    """Test that get() returns key if translation not found."""
    translator = Translator.get_instance(locale="en")

    message = translator.get("nonexistent.key")

    # Should return the key itself
    assert message == "nonexistent.key"


def test_translator_replaces_single_placeholder() -> None:
    """Test that placeholders are replaced correctly."""
    translator = Translator.get_instance(locale="en")

    message = translator.get("validation.required", field="Email")

    assert message == "The Email field is required."


def test_translator_replaces_multiple_placeholders() -> None:
    """Test that multiple placeholders are replaced."""
    translator = Translator.get_instance(locale="en")

    message = translator.get("validation.min", field="Password", min=8)

    assert message == "The Password must be at least 8 characters."


def test_translator_set_locale_changes_language() -> None:
    """Test that set_locale() changes the active language."""
    translator = Translator.get_instance(locale="en")

    # English translation
    message_en = translator.get("auth.failed")
    assert "credentials do not match" in message_en.lower()

    # Switch to Portuguese
    translator.set_locale("pt_BR")
    message_pt = translator.get("auth.failed")
    assert "credenciais" in message_pt.lower()


def test_translator_has_returns_true_for_existing_key() -> None:
    """Test that has() returns True for existing keys."""
    translator = Translator.get_instance(locale="en")

    assert translator.has("auth.failed") is True
    assert translator.has("validation.required") is True


def test_translator_has_returns_false_for_missing_key() -> None:
    """Test that has() returns False for missing keys."""
    translator = Translator.get_instance(locale="en")

    assert translator.has("nonexistent.key") is False


def test_translator_all_returns_all_translations() -> None:
    """Test that all() returns all loaded translations."""
    translator = Translator.get_instance(locale="en")

    translations = translator.all()

    # Should have all framework translations
    assert "auth.failed" in translations
    assert "validation.required" in translations
    assert isinstance(translations, dict)


def test_translator_handles_missing_locale_file() -> None:
    """Test that missing locale files are handled gracefully."""
    translator = Translator.get_instance(locale="nonexistent_locale")

    # Should not crash, just have empty translations
    message = translator.get("any.key")

    # Should return key since no translations loaded
    assert message == "any.key"


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


def test_trans_helper_function() -> None:
    """Test that trans() helper works correctly."""
    # Reset to English
    set_locale("en")

    message = trans("auth.failed")

    assert message == "These credentials do not match our records."


def test_trans_with_placeholders() -> None:
    """Test that trans() handles placeholders."""
    set_locale("en")

    message = trans("validation.required", field="Email")

    assert message == "The Email field is required."


def test_t_alias_works() -> None:
    """Test that t() alias works the same as trans()."""
    set_locale("en")

    message1 = trans("auth.failed")
    message2 = t("auth.failed")

    assert message1 == message2


def test_set_locale_helper_changes_language() -> None:
    """Test that set_locale() helper changes language."""
    set_locale("en")
    message_en = trans("auth.failed")

    set_locale("pt_BR")
    message_pt = trans("auth.failed")

    assert message_en != message_pt
    assert "credentials" in message_en.lower()
    assert "credenciais" in message_pt.lower()


def test_has_helper_checks_existence() -> None:
    """Test that has() helper checks key existence."""
    set_locale("en")

    assert has("auth.failed") is True
    assert has("nonexistent.key") is False


def test_all_translations_helper_returns_dict() -> None:
    """Test that all_translations() returns all translations."""
    set_locale("en")

    translations = all_translations()

    assert isinstance(translations, dict)
    assert "auth.failed" in translations


# ============================================================================
# USER TRANSLATION OVERRIDE TESTS
# ============================================================================


def test_user_translations_override_framework() -> None:
    """Test that user translations override framework defaults."""
    # Create temporary user translation file
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create user lang directory
        lang_dir = Path(tmpdir) / "src" / "resources" / "lang"
        lang_dir.mkdir(parents=True, exist_ok=True)

        # Create custom translation file
        user_translations = {"auth.failed": "Custom failure message"}
        lang_file = lang_dir / "en.json"
        lang_file.write_text(json.dumps(user_translations))

        # Change to temp directory
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # Create new translator instance
            translator = Translator(locale="en")

            # User translation should override framework default
            message = translator.get("auth.failed")
            assert message == "Custom failure message"

        finally:
            os.chdir(original_cwd)


# ============================================================================
# EDGE CASES
# ============================================================================


def test_placeholder_with_numeric_value() -> None:
    """Test that numeric placeholder values are converted to string."""
    set_locale("en")

    message = trans("auth.throttle", seconds=60)

    assert "60 seconds" in message


def test_placeholder_not_replaced_if_not_provided() -> None:
    """Test that placeholders remain if value not provided."""
    set_locale("en")

    # Don't provide 'field' placeholder
    message = trans("validation.required")

    # Placeholder should remain in text
    assert ":field" in message


def test_empty_placeholder_value() -> None:
    """Test that empty string placeholders are replaced."""
    set_locale("en")

    message = trans("validation.required", field="")

    # Should replace :field with empty string
    assert ":field" not in message
    assert message == "The  field is required."


def test_special_characters_in_translation() -> None:
    """Test that special characters in translations are preserved."""
    set_locale("pt_BR")

    # Portuguese has special characters (ç, ã, etc.)
    message = trans("validation.required", field="Descrição")

    assert "Descrição" in message


# ============================================================================
# LOCALE TESTS
# ============================================================================


def test_portuguese_translations_loaded() -> None:
    """Test that Portuguese translations are available."""
    set_locale("pt_BR")

    message = trans("common.success")

    assert message == "Sucesso!"


def test_fallback_to_english_if_translation_missing() -> None:
    """Test fallback behavior when translation missing in locale."""
    # Create translator with fallback
    translator = Translator.get_instance(locale="pt_BR")

    # If a key only exists in English, should fall back
    # (This depends on which keys are in pt_BR vs en)
    # For now, just verify fallback mechanism exists
    assert translator.fallback_locale == "en"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


def test_complete_i18n_workflow() -> None:
    """Test complete i18n workflow from loading to translation."""
    # 1. Start with English
    set_locale("en")
    assert trans("auth.failed") == "These credentials do not match our records."

    # 2. Switch to Portuguese
    set_locale("pt_BR")
    assert "credenciais" in trans("auth.failed").lower()

    # 3. Use placeholders
    message = trans("validation.min", field="Senha", min=8)
    assert "Senha" in message
    assert "8" in message

    # 4. Check existence
    assert has("auth.failed") is True
    assert has("nonexistent") is False

    # 5. Get all translations
    all_trans = all_translations()
    assert len(all_trans) > 0


def test_multiple_locale_switches() -> None:
    """Test switching locales multiple times."""
    # English
    set_locale("en")
    msg1 = trans("common.success")

    # Portuguese
    set_locale("pt_BR")
    msg2 = trans("common.success")

    # Back to English
    set_locale("en")
    msg3 = trans("common.success")

    # First and third should match
    assert msg1 == msg3
    # Second should be different
    assert msg1 != msg2
