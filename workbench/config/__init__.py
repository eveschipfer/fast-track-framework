"""
Workbench Configuration Package

This package contains all configuration files for the workbench application.
Configuration files are Python modules that define a 'config' dictionary.

Available Configurations:
    - app: Application settings (name, environment, providers)
    - database: Database connection settings
    - cache: Cache driver configuration
    - mail: Email service configuration

Usage:
    from jtc.config import config

    # Access configuration values
    app_name = config("app.name")
    db_driver = config("database.default")
"""
