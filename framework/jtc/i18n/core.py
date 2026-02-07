"""
Internationalization (i18n) System (Sprint 3.5)

This module provides a lightweight i18n system inspired by Laravel's translation
service. It supports JSON-based translations, dot notation keys, and placeholder
replacement.

Key Features:
    - JSON translation files (resources/lang/{locale}.json)
    - Dot notation keys (e.g., "auth.failed", "validation.required")
    - Placeholder replacement (e.g., ":name", ":field")
    - Hot-swappable locale (set_locale())
    - Fallback to key if translation not found
    - Graceful handling of missing files

Educational Note:
    This is inspired by Laravel's __() and trans() helpers. Laravel uses PHP
    arrays for translations, but we use JSON for simplicity and portability.

    Laravel example:
        __('auth.failed')  // Returns "These credentials do not match our records."

    Fast Track example:
        trans('auth.failed')  // Same functionality, different syntax

Architecture Decision:
    - Singleton pattern for global access
    - JSON files for easy editing and version control
    - No complex pluralization (future sprint)
    - Dot notation for hierarchical organization

Comparison with Laravel:
    Laravel (resources/lang/en/auth.php):
        <?php
        return [
            'failed' => 'These credentials do not match our records.',
            'throttle' => 'Too many login attempts. Please try again in :seconds seconds.',
        ];

    Fast Track (resources/lang/en.json):
        {
            "auth.failed": "These credentials do not match our records.",
            "auth.throttle": "Too many login attempts. Please try again in :seconds seconds."
        }

Usage:
    from jtc.i18n import trans, set_locale

    # Get translation
    message = trans('auth.failed')

    # With placeholders
    message = trans('validation.required', field='Email')
    # Returns: "The Email field is required."

    # Change locale
    set_locale('pt_BR')
    message = trans('auth.failed')
    # Returns: "Essas credenciais não correspondem aos nossos registros."
"""

import json
import os
from pathlib import Path
from typing import Any


class Translator:
    """
    Singleton translator for i18n (internationalization).

    This class manages translation loading, key lookup, and placeholder
    replacement. It follows the singleton pattern to ensure a single global
    instance across the application.

    Attributes:
        locale: Current locale (e.g., "en", "pt_BR", "es")
        translations: Dictionary of loaded translations
        fallback_locale: Fallback locale if translation not found

    Example:
        >>> translator = Translator.get_instance()
        >>> translator.set_locale('en')
        >>> translator.get('auth.failed')
        'These credentials do not match our records.'
        >>>
        >>> translator.set_locale('pt_BR')
        >>> translator.get('auth.failed')
        'Essas credenciais não correspondem aos nossos registros.'

    Educational Note:
        Singleton pattern ensures:
        - Only one translator instance exists
        - Translations are loaded once per locale change
        - Global state is consistent across the app

        Alternative: Dependency injection (but singleton is simpler for i18n)
    """

    _instance: "Translator | None" = None

    def __init__(self, locale: str = "en", fallback_locale: str = "en") -> None:
        """
        Initialize the Translator.

        Args:
            locale: The locale to use (default: "en")
            fallback_locale: Fallback locale if translation not found

        Note:
            This should not be called directly. Use get_instance() instead.

        Example:
            >>> # Don't do this
            >>> translator = Translator()  # Creates new instance
            >>>
            >>> # Do this instead
            >>> translator = Translator.get_instance()  # Uses singleton
        """
        self.locale = locale
        self.fallback_locale = fallback_locale
        self.translations: dict[str, str] = {}
        self.fallback_translations: dict[str, str] = {}
        self._load_translations()

    @classmethod
    def get_instance(cls, locale: str | None = None) -> "Translator":
        """
        Get the singleton Translator instance.

        This method ensures only one Translator instance exists. If an instance
        doesn't exist, it creates one. If locale is provided and different from
        current locale, it changes the locale.

        Args:
            locale: Optional locale to set (if different from current)

        Returns:
            Translator: The singleton instance

        Example:
            >>> translator = Translator.get_instance()
            >>> translator.get('auth.failed')
            'These credentials do not match our records.'
            >>>
            >>> # Change locale
            >>> translator = Translator.get_instance(locale='pt_BR')
            >>> translator.get('auth.failed')
            'Essas credenciais não correspondem aos nossos registros.'

        Educational Note:
            Singleton pattern implemented with class variable _instance.
            This is thread-safe in Python due to GIL (Global Interpreter Lock).
        """
        if cls._instance is None:
            # Read default locale from environment
            default_locale = os.getenv("DEFAULT_LOCALE", "en")
            cls._instance = cls(locale=locale or default_locale)
        elif locale is not None and locale != cls._instance.locale:
            # Locale changed, reload translations
            cls._instance.set_locale(locale)

        return cls._instance

    def _load_translations(self) -> None:
        """
        Load translation files from framework and user directories.

        This method loads translations from two locations:
        1. Framework translations: src/jtc/resources/lang/{locale}.json
        2. User translations: src/resources/lang/{locale}.json

        User translations override framework translations (merge strategy).

        Example file structure:
            src/jtc/resources/lang/en.json       (framework defaults)
            src/resources/lang/en.json           (user overrides)
            src/resources/lang/pt_BR.json        (user Portuguese)

        Educational Note:
            This "cascade" pattern allows framework to provide defaults
            while users can override or extend with their own translations.

            Laravel does the same with vendor translations vs app translations.

        Merge Strategy:
            Framework: {"auth.failed": "Invalid credentials"}
            User:      {"auth.failed": "Wrong password", "auth.success": "Welcome"}
            Result:    {"auth.failed": "Wrong password", "auth.success": "Welcome"}
        """
        self.translations = {}

        # 1. Load framework translations (built-in defaults)
        framework_path = self._get_framework_translation_path(self.locale)
        if framework_path.exists():
            with open(framework_path, "r", encoding="utf-8") as f:
                self.translations.update(json.load(f))

        # 2. Load user translations (project-specific overrides)
        user_path = self._get_user_translation_path(self.locale)
        if user_path.exists():
            with open(user_path, "r", encoding="utf-8") as f:
                # User translations override framework translations
                self.translations.update(json.load(f))

        # 3. Load fallback translations (if locale is different from fallback)
        if self.locale != self.fallback_locale:
            self.fallback_translations = {}

            # Load framework fallback
            fallback_framework_path = self._get_framework_translation_path(
                self.fallback_locale
            )
            if fallback_framework_path.exists():
                with open(fallback_framework_path, "r", encoding="utf-8") as f:
                    self.fallback_translations.update(json.load(f))

            # Load user fallback
            fallback_user_path = self._get_user_translation_path(self.fallback_locale)
            if fallback_user_path.exists():
                with open(fallback_user_path, "r", encoding="utf-8") as f:
                    self.fallback_translations.update(json.load(f))

    def _get_framework_translation_path(self, locale: str) -> Path:
        """
        Get path to framework translation file.

        Args:
            locale: The locale code (e.g., "en", "pt_BR")

        Returns:
            Path: Path to framework translation file

        Example:
            >>> translator._get_framework_translation_path('en')
            PosixPath('src/jtc/resources/lang/en.json')
        """
        # Framework translations are in src/jtc/resources/lang/
        return Path(__file__).parent.parent / "resources" / "lang" / f"{locale}.json"

    def _get_user_translation_path(self, locale: str) -> Path:
        """
        Get path to user translation file.

        Args:
            locale: The locale code (e.g., "en", "pt_BR")

        Returns:
            Path: Path to user translation file

        Example:
            >>> translator._get_user_translation_path('pt_BR')
            PosixPath('src/resources/lang/pt_BR.json')
        """
        # User translations are in src/resources/lang/
        # Assuming we're running from project root
        return Path.cwd() / "src" / "resources" / "lang" / f"{locale}.json"

    def set_locale(self, locale: str) -> None:
        """
        Change the current locale and reload translations.

        This allows hot-swapping the language at runtime, which is useful
        for middleware that detects user language from Accept-Language header.

        Args:
            locale: The new locale code (e.g., "pt_BR", "es", "fr")

        Example:
            >>> translator = Translator.get_instance()
            >>> translator.get('auth.failed')
            'These credentials do not match our records.'
            >>>
            >>> translator.set_locale('pt_BR')
            >>> translator.get('auth.failed')
            'Essas credenciais não correspondem aos nossos registros.'

        Educational Note:
            This is useful for:
            - Multi-tenant applications (different users, different languages)
            - API responses based on Accept-Language header
            - Admin panel language switcher

            Laravel equivalent:
                App::setLocale('pt_BR');
        """
        if locale != self.locale:
            self.locale = locale
            self._load_translations()

    def get(self, key: str, **kwargs: Any) -> str:
        """
        Get a translation by key with optional placeholder replacement.

        This method:
        1. Looks up the key in loaded translations
        2. If found, replaces placeholders with provided values
        3. If not found, tries fallback locale
        4. If still not found, returns the key itself

        Args:
            key: Translation key in dot notation (e.g., "auth.failed")
            **kwargs: Placeholder values to replace (e.g., field="Email")

        Returns:
            str: Translated string with placeholders replaced, or key if not found

        Example:
            >>> translator.get('auth.failed')
            'These credentials do not match our records.'
            >>>
            >>> translator.get('validation.required', field='Email')
            'The Email field is required.'
            >>>
            >>> translator.get('nonexistent.key')
            'nonexistent.key'  # Returns key if translation not found

        Placeholder Syntax:
            Translation: "The :field field is required."
            Call: get('validation.required', field='Email')
            Result: "The Email field is required."

        Educational Note:
            This is similar to Laravel's __() and trans() functions:

            Laravel:
                __('validation.required', ['field' => 'Email'])

            Fast Track:
                trans('validation.required', field='Email')

            We use **kwargs instead of a dict for cleaner Python syntax.
        """
        # Look up translation in current locale
        translation = self.translations.get(key)

        # If not found, try fallback locale
        if translation is None and self.fallback_translations:
            translation = self.fallback_translations.get(key)

        # If still not found, return the key itself
        if translation is None:
            return key

        # Replace placeholders (e.g., :field -> Email)
        return self._replace_placeholders(translation, **kwargs)

    def _replace_placeholders(self, text: str, **kwargs: Any) -> str:
        """
        Replace placeholders in translation text.

        Placeholders use the format :name and are replaced with provided values.

        Args:
            text: Translation text with placeholders (e.g., "Hello :name")
            **kwargs: Placeholder values (e.g., name="John")

        Returns:
            str: Text with placeholders replaced

        Example:
            >>> translator._replace_placeholders("Hello :name", name="John")
            'Hello John'
            >>>
            >>> translator._replace_placeholders(
            ...     "The :field field must be at least :min characters.",
            ...     field="Password",
            ...     min=8
            ... )
            'The Password field must be at least 8 characters.'

        Educational Note:
            Laravel uses :name syntax for placeholders.
            We do the same for consistency.

            Alternative syntaxes considered but rejected:
            - {name} (conflicts with Python f-strings)
            - {{name}} (too verbose)
            - %s (not descriptive)

            The :name syntax is:
            - Clear and readable
            - Easy to type
            - Doesn't conflict with Python syntax
        """
        for key, value in kwargs.items():
            # Replace :key with value
            text = text.replace(f":{key}", str(value))

        return text

    def has(self, key: str) -> bool:
        """
        Check if a translation key exists.

        Args:
            key: Translation key to check

        Returns:
            bool: True if key exists in translations, False otherwise

        Example:
            >>> translator.has('auth.failed')
            True
            >>> translator.has('nonexistent.key')
            False

        Educational Note:
            Useful for conditional logic based on translation availability.
        """
        return key in self.translations or key in self.fallback_translations

    def all(self) -> dict[str, str]:
        """
        Get all loaded translations.

        Returns:
            dict: All translations for current locale

        Example:
            >>> translations = translator.all()
            >>> print(translations)
            {'auth.failed': 'Invalid credentials', ...}

        Educational Note:
            Useful for debugging or exporting translations.
        """
        return self.translations.copy()
