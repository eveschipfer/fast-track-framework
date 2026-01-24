"""
Core exceptions for the Fast Track Framework.

Custom exceptions for dependency injection and container operations.
"""


class DependencyResolutionError(Exception):
    """
    Raised when dependency cannot be resolved.

    This is the base exception for all dependency injection errors.
    """



class CircularDependencyError(DependencyResolutionError):
    """
    Raised when circular dependency is detected.

    Example:
        ServiceA depends on ServiceB, which depends on ServiceA.
        This creates an infinite loop that must be prevented.
    """



class UnregisteredDependencyError(DependencyResolutionError):
    """
    Raised when trying to resolve unregistered dependency.

    This indicates that a type was requested but not registered
    in the container.
    """

