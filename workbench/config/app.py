"""
Application Configuration

This file contains the core application settings including:
- Application metadata (name, environment, version)
- Service providers to be registered
- Debug mode and timezone settings

All settings can use environment variables via os.getenv() for
environment-specific configuration.

Service Providers:
    Providers are registered in the order they appear in the list.
    The framework will call register() on all providers first, then
    call boot() on all providers during application startup.
"""

import os

from app.providers import AppServiceProvider, RouteServiceProvider

# Application Configuration Dictionary
config = {
    # Application Name
    # Used in API responses, logs, and email templates
    "name": os.getenv("APP_NAME", "Fast Track Framework"),
    # Application Environment
    # Options: "local", "development", "staging", "production"
    # Affects logging, error reporting, and debug mode
    "env": os.getenv("APP_ENV", "production"),
    # Debug Mode
    # When True, shows detailed error messages and stack traces
    # NEVER enable in production!
    "debug": os.getenv("APP_DEBUG", "false").lower() == "true",
    # Application Version
    # Semantic versioning for API version tracking
    "version": "5.3.0",
    # Application URL
    # Used for generating absolute URLs in emails, redirects, etc.
    "url": os.getenv("APP_URL", "http://localhost:8000"),
    # Timezone
    # Default timezone for timestamps (created_at, updated_at, etc.)
    "timezone": os.getenv("APP_TIMEZONE", "UTC"),
    # Service Providers
    # Providers are registered and booted in the order listed
    # Add new providers here as features are added
    "providers": [
        # Application-level service registration
        AppServiceProvider,
        # Route registration and configuration
        RouteServiceProvider,
        # Future providers:
        # DatabaseServiceProvider,  # Database connection pooling
        # CacheServiceProvider,      # Cache driver configuration
        # MailServiceProvider,       # Email service setup
        # QueueServiceProvider,      # Job queue workers
        # AuthServiceProvider,       # Authentication guards
    ],
    # Locale Configuration
    # Default language for the application
    "locale": os.getenv("APP_LOCALE", "en"),
    # Fallback locale when translation is missing
    "fallback_locale": "en",
}
