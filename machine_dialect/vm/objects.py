"""Runtime object representations for the VM.

This module defines the runtime representations of values
during VM execution.
"""

from collections.abc import Callable
from typing import Any


class NativeFunction:
    """Wrapper for native (host) functions callable from Machine Dialect."""

    def __init__(self, name: str, func: Callable[..., Any], arity: int = -1) -> None:
        """Initialize a native function.

        Args:
            name: Function name.
            func: The Python callable to wrap.
            arity: Number of arguments (-1 for variadic).
        """
        self.name = name
        self.func = func
        self.arity = arity

    def call(self, args: list[Any]) -> Any:
        """Call the native function with arguments.

        Args:
            args: List of arguments.

        Returns:
            The result of the function call.

        Raises:
            RuntimeError: If arity doesn't match.
        """
        if self.arity >= 0 and len(args) != self.arity:
            raise RuntimeError(f"Native function '{self.name}' expects {self.arity} arguments, got {len(args)}")
        return self.func(*args)

    def __str__(self) -> str:
        """String representation.

        Returns:
            String showing the native function.
        """
        return f"<native function '{self.name}'>"

    def __repr__(self) -> str:
        """Developer representation.

        Returns:
            Detailed string for debugging.
        """
        return f"NativeFunction(name='{self.name}', arity={self.arity})"


def is_truthy(value: Any) -> bool:
    """Determine if a value is truthy in Machine Dialect.

    Args:
        value: The value to test.

    Returns:
        True if the value is considered truthy, False otherwise.
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    # Everything else is truthy
    return True


def type_name(value: Any) -> str:
    """Get the Machine Dialect type name for a value.

    Args:
        value: The value to get the type of.

    Returns:
        String name of the type.
    """
    if value is None:
        return "empty"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "text"
    if isinstance(value, NativeFunction):
        return "function"
    return "unknown"


def equals(a: Any, b: Any) -> bool:
    """Check value equality in Machine Dialect.

    Args:
        a: First value.
        b: Second value.

    Returns:
        True if values are equal, False otherwise.
    """
    # Handle None specially
    if a is None or b is None:
        return a is b
    # Standard Python equality
    return bool(a == b)


def strict_equals(a: Any, b: Any) -> bool:
    """Check strict equality (same type and value).

    Args:
        a: First value.
        b: Second value.

    Returns:
        True if values are strictly equal, False otherwise.
    """
    # Must be same type
    if type(a) is not type(b):
        return False
    return equals(a, b)
