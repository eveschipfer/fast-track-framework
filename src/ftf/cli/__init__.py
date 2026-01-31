"""
Fast Track Framework CLI Package (Sprint 3.0)

This package provides command-line interface tools for scaffolding and
operational tasks. It uses Typer for command parsing and Rich for output.

Public API:
    - app: Main Typer application (entry point)
    - console: Rich Console for formatted output

Example:
    >>> from ftf.cli import console
    >>> console.print("[green]Success![/green]")
"""

from ftf.cli.main import app, console

__all__ = ["app", "console"]
