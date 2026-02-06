"""
Application Configuration (Sprint 5.3 + 5.7)

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

    Sprint 5.7: DatabaseServiceProvider added for auto-configuration!
"""

import os

# Application Configuration
# Sprint 5.3: ConfigRepository expects a 'config' variable
# Sprint 5.7: DatabaseServiceProvider added for database auto-configuration
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
    "version": "1.0.0a1",

    # Application URL
    # Used for generating absolute URLs in emails, redirects, etc.
    "url": os.getenv("APP_URL", "http://localhost:8000"),

    # Timezone
    # Default timezone for timestamps (created_at, updated_at, etc.)
    "timezone": os.getenv("APP_TIMEZONE", "UTC"),

    # Service Providers
    # Providers are registered and booted in the order listed
    # Use string paths for dynamic loading
    "providers": [
        # Database auto-configuration (Sprint 5.7 + Sprint 15.0)
        # Reads config/database.py and sets up AsyncEngine + AsyncSession
        # Sprint 15.0: Serverless connection handling (NullPool in AWS Lambda)
        "ftf.providers.database_service_provider.DatabaseServiceProvider",

        # Application-level service registration
        "app.providers.app_service_provider.AppServiceProvider",

        # Route registration and configuration
        "app.providers.route_service_provider.RouteServiceProvider",

        # Authentication guards (Sprint 10)
        "workbench.app.providers.auth_service_provider.AuthServiceProvider",

        # Future providers:
        # "ftf.providers.cache.CacheServiceProvider",      # Cache driver configuration
        # "ftf.providers.mail.MailServiceProvider",        # Email service setup
        # "ftf.providers.queue.QueueServiceProvider",      # Job queue workers
    ],

    # Locale Configuration
    # Default language for the application
    "locale": os.getenv("APP_LOCALE", "en"),

    # Fallback locale when translation is missing
    "fallback_locale": "en",
}
