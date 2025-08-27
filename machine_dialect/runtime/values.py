"""Value representations and conversions for Machine Dialect runtime.

This module provides uniform value handling across all execution modes,
including conversion functions and value semantics.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RuntimeValue(Protocol):
    """Protocol for runtime values that can be used across backends.

    This protocol allows both primitive values and interpreter objects
    to be handled uniformly.
    """

    def __str__(self) -> str:
        """Get string representation of the value."""
        ...

    def __bool__(self) -> bool:
        """Get boolean representation of the value."""
        ...


def get_raw_value(value: Any) -> Any:
    """Extract the raw value from an interpreter object or return as-is.

    Args:
        value: The value to extract from.

    Returns:
        The raw primitive value.
    """
    # Handle interpreter objects with .value attribute
    if hasattr(value, "value") and not isinstance(value, type):
        return value.value

    # Return primitive values as-is
    return value


def to_bool(value: Any) -> bool:
    """Convert a value to boolean using Machine Dialect semantics.

    Args:
        value: The value to convert.

    Returns:
        Boolean representation of the value.
    """
    from machine_dialect.runtime.types import is_truthy

    return is_truthy(value)


def to_int(value: Any) -> int:
    """Convert a value to integer.

    Args:
        value: The value to convert.

    Returns:
        Integer representation of the value.

    Raises:
        ValueError: If conversion is not possible.
    """
    raw = get_raw_value(value)

    # None/Empty to 0
    if raw is None:
        return 0

    # Already an int
    if isinstance(raw, int) and not isinstance(raw, bool):
        return raw

    # Float to int
    if isinstance(raw, float):
        return int(raw)

    # Boolean to int
    if isinstance(raw, bool):
        return int(raw)

    # String to int
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            # Try float first then int (handles "3.0" -> 3)
            try:
                return int(float(raw))
            except ValueError:
                raise ValueError(f"Cannot convert '{raw}' to integer") from None

    raise ValueError(f"Cannot convert {type(raw).__name__} to integer")


def to_float(value: Any) -> float:
    """Convert a value to float.

    Args:
        value: The value to convert.

    Returns:
        Float representation of the value.

    Raises:
        ValueError: If conversion is not possible.
    """
    raw = get_raw_value(value)

    # None/Empty to 0.0
    if raw is None:
        return 0.0

    # Already a float
    if isinstance(raw, float):
        return raw

    # Int to float
    if isinstance(raw, int):
        return float(raw)

    # Boolean to float
    if isinstance(raw, bool):
        return float(raw)

    # String to float
    if isinstance(raw, str):
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"Cannot convert '{raw}' to float") from None

    raise ValueError(f"Cannot convert {type(raw).__name__} to float")


def to_string(value: Any) -> str:
    """Convert a value to string representation.

    Args:
        value: The value to convert.

    Returns:
        String representation of the value.
    """
    # Handle None/Empty specially
    if value is None:
        return "empty"

    # Handle interpreter Empty object
    if hasattr(value, "type") and hasattr(value.type, "name") and value.type.name == "EMPTY":
        return "empty"

    # Handle interpreter objects with inspect method
    if hasattr(value, "inspect") and callable(value.inspect):
        return str(value.inspect())

    # Extract raw value for interpreter objects
    raw = get_raw_value(value)

    # None/Empty
    if raw is None:
        return "empty"

    # Boolean (Yes/No format like interpreter)
    if isinstance(raw, bool):
        return "Yes" if raw else "No"

    # Direct string conversion for everything else
    return str(raw)


def is_empty(value: Any) -> bool:
    """Check if a value represents empty/null.

    Args:
        value: The value to check.

    Returns:
        True if the value is empty/null, False otherwise.
    """
    # Check for None
    if value is None:
        return True

    # Check for interpreter Empty object
    if hasattr(value, "type") and hasattr(value.type, "name") and value.type.name == "EMPTY":
        return True

    return False


def equals(a: Any, b: Any) -> bool:
    """Check value equality using Machine Dialect semantics.

    This implements value equality (==), where values of different
    types can be equal if they represent the same value.

    Args:
        a: First value.
        b: Second value.

    Returns:
        True if values are equal, False otherwise.
    """
    # Handle empty values
    if is_empty(a) or is_empty(b):
        return is_empty(a) and is_empty(b)

    # Extract raw values
    raw_a = get_raw_value(a)
    raw_b = get_raw_value(b)

    # Numeric comparison (int and float can be equal)
    from machine_dialect.runtime.types import is_numeric

    if is_numeric(a) and is_numeric(b):
        return bool(raw_a == raw_b)

    # String comparison
    if isinstance(raw_a, str) and isinstance(raw_b, str):
        return raw_a == raw_b

    # Boolean comparison
    if isinstance(raw_a, bool) and isinstance(raw_b, bool):
        return raw_a == raw_b

    # Default to Python equality
    return bool(raw_a == raw_b)


def strict_equals(a: Any, b: Any) -> bool:
    """Check strict equality (same type and value).

    This implements strict equality (===), where values must be
    of the same type to be equal.

    Args:
        a: First value.
        b: Second value.

    Returns:
        True if values are strictly equal, False otherwise.
    """
    from machine_dialect.runtime.types import get_type

    # Must be same type
    if get_type(a) != get_type(b):
        return False

    # Then check value equality
    return equals(a, b)
