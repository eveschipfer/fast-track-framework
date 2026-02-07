"""
Fast Track Framework - i18n Module (Sprint 3.5)

This module provides internationalization (i18n) support with JSON-based
translations, dot notation keys, and placeholder replacement.

Public API:
    trans(key, **kwargs): Get translation with placeholder replacement
    t(key, **kwargs): Alias for trans() (shorter syntax)
    set_locale(locale): Change the current locale
    has(key): Check if translation key exists
    all(): Get all loaded translations

Usage:
    from jtc.i18n import trans, set_locale

    # Basic usage
    message = trans('auth.failed')

    # With placeholders
    message = trans('validation.required', field='Email')

    # Change locale
    set_locale('pt_BR')

    # Check if key exists
    if has('custom.message'):
        message = trans('custom.message')

Educational Note:
    This module exposes a global API for translations, similar to Laravel's
    __() and trans() functions. The underlying Translator is a singleton
    to ensure consistent state across the application.

Comparison with Laravel:
    Laravel:
        __('auth.failed')
        trans('validation.required', ['field' => 'Email'])
        App::setLocale('pt_BR')

    Fast Track:
        trans('auth.failed')
        trans('validation.required', field='Email')
        set_locale('pt_BR')
"""

from typing import Any

from .core import Translator

__all__ = [
    "trans",
    "t",
    "set_locale",
    "has",
    "all_translations",
    "Translator",
]


def trans(key: str, **kwargs: Any) -> str:
    """
    Get a translation by key with optional placeholder replacement.

    This is the main function for retrieving translations. It uses the
    global Translator singleton to look up keys and replace placeholders.

    Args:
        key: Translation key in dot notation (e.g., "auth.failed")
        **kwargs: Placeholder values (e.g., field="Email", min=8)

    Returns:
        str: Translated string with placeholders replaced, or key if not found

    Example:
        >>> trans('auth.failed')
        'These credentials do not match our records.'
        >>>
        >>> trans('validation.required', field='Email')
        'The Email field is required.'
        >>>
        >>> trans('validation.min', field='Password', min=8)
        'The Password must be at least 8 characters.'

    Educational Note:
        This function is inspired by Laravel's trans() and __() helpers.
        It provides a clean, Pythonic API for translations.

        Laravel:
            trans('auth.failed')

        Fast Track:
            trans('auth.failed')

        The advantage of a global function:
        - No need to pass translator around
        - Clean, simple syntax
        - Easy to use in any part of the code

    Why not a class method?
        We could do Translator.get_instance().get('auth.failed'),
        but trans('auth.failed') is much cleaner and more Pythonic.
    """
    translator = Translator.get_instance()
    return translator.get(key, **kwargs)


def t(key: str, **kwargs: Any) -> str:
    """
    Alias for trans() - shorter syntax.

    Some developers prefer a shorter function name for frequently used
    functions. This is especially common in templates.

    Args:
        key: Translation key
        **kwargs: Placeholder values

    Returns:
        str: Translated string

    Example:
        >>> t('auth.failed')
        'These credentials do not match our records.'
        >>>
        >>> t('validation.required', field='Email')
        'The Email field is required.'

    Educational Note:
        Many frameworks provide short aliases:
        - Laravel: __() (even shorter!)
        - Django: _() (gettext-style)
        - Rails: t()

        We provide t() as an alias for developers who prefer brevity.
        Use whichever you prefer:
        - trans() is more explicit
        - t() is more concise
    """
    return trans(key, **kwargs)


def set_locale(locale: str) -> None:
    """
    Change the current locale.

    This updates the global Translator instance to use a different locale
    and reloads all translations.

    Args:
        locale: Locale code (e.g., "pt_BR", "es", "fr")

    Example:
        >>> set_locale('en')
        >>> trans('auth.failed')
        'These credentials do not match our records.'
        >>>
        >>> set_locale('pt_BR')
        >>> trans('auth.failed')
        'Essas credenciais não correspondem aos nossos registros.'

    Use Cases:
        1. Middleware that detects user language from Accept-Language header
        2. User preferences (save locale in database)
        3. Admin panel language switcher
        4. Multi-tenant applications (different locales per tenant)

    Example Middleware:
        >>> from jtc.i18n import set_locale
        >>>
        >>> async def locale_middleware(request, call_next):
        ...     # Detect locale from header
        ...     locale = request.headers.get('Accept-Language', 'en')
        ...     set_locale(locale)
        ...
        ...     response = await call_next(request)
        ...     return response

    Educational Note:
        Laravel equivalent:
            App::setLocale('pt_BR');

        Fast Track:
            set_locale('pt_BR')

        This function modifies global state (the Translator singleton).
        In a request-scoped context (like middleware), this is safe because
        each request runs in its own async context.
    """
    translator = Translator.get_instance()
    translator.set_locale(locale)


def has(key: str) -> bool:
    """
    Check if a translation key exists.

    Args:
        key: Translation key to check

    Returns:
        bool: True if key exists, False otherwise

    Example:
        >>> has('auth.failed')
        True
        >>> has('nonexistent.key')
        False
        >>>
        >>> # Conditional translation
        >>> if has('custom.welcome'):
        ...     message = trans('custom.welcome')
        ... else:
        ...     message = "Welcome!"

    Educational Note:
        Useful for:
        - Checking if user has customized a translation
        - Conditional rendering based on translation availability
        - Debugging missing translations
    """
    translator = Translator.get_instance()
    return translator.has(key)


def all_translations() -> dict[str, str]:
    """
    Get all loaded translations for the current locale.

    Returns:
        dict: All translations

    Example:
        >>> translations = all_translations()
        >>> print(translations)
        {'auth.failed': 'Invalid credentials', 'validation.required': '...'}

    Educational Note:
        Useful for:
        - Debugging (see what translations are loaded)
        - Exporting translations (for external tools)
        - Generating translation coverage reports

        Be careful using this in production - it returns ALL translations
        which could be a lot of data.
    """
    translator = Translator.get_instance()
    return translator.all()
