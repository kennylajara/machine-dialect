"""Type system and semantics for Machine Dialect runtime.

This module defines the type system used across all execution modes,
including type checking, coercion rules, and truthiness semantics.
"""

from enum import Enum, auto
from typing import Any


class MachineDialectType(Enum):
    """Enumeration of Machine Dialect types."""

    EMPTY = auto()
    BOOLEAN = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    URL = auto()
    FUNCTION = auto()
    ERROR = auto()
    RETURN = auto()
    UNKNOWN = auto()


def get_type(value: Any) -> MachineDialectType:
    """Get the Machine Dialect type of a value.

    Args:
        value: The value to get the type of.

    Returns:
        The MachineDialectType of the value.
    """
    # Handle None/Empty
    if value is None:
        return MachineDialectType.EMPTY

    # Handle primitive types
    if isinstance(value, bool):
        return MachineDialectType.BOOLEAN
    if isinstance(value, int):
        return MachineDialectType.INTEGER
    if isinstance(value, float):
        return MachineDialectType.FLOAT
    if isinstance(value, str):
        # Check if it's a URL (basic heuristic)
        if value.startswith(("http://", "https://", "ftp://", "file://")):
            return MachineDialectType.URL
        return MachineDialectType.STRING

    # Handle objects from interpreter
    if hasattr(value, "type"):
        # Map interpreter object types
        type_name = value.type.name if hasattr(value.type, "name") else str(value.type)
        type_map = {
            "EMPTY": MachineDialectType.EMPTY,
            "BOOLEAN": MachineDialectType.BOOLEAN,
            "INTEGER": MachineDialectType.INTEGER,
            "FLOAT": MachineDialectType.FLOAT,
            "STRING": MachineDialectType.STRING,
            "URL": MachineDialectType.URL,
            "FUNCTION": MachineDialectType.FUNCTION,
            "ERROR": MachineDialectType.ERROR,
            "RETURN": MachineDialectType.RETURN,
        }
        return type_map.get(type_name, MachineDialectType.UNKNOWN)

    # Handle callable objects
    if callable(value):
        return MachineDialectType.FUNCTION

    return MachineDialectType.UNKNOWN


def get_type_name(value: Any) -> str:
    """Get the human-readable type name for a value.

    Args:
        value: The value to get the type name of.

    Returns:
        String name of the type.
    """
    type_names = {
        MachineDialectType.EMPTY: "empty",
        MachineDialectType.BOOLEAN: "boolean",
        MachineDialectType.INTEGER: "integer",
        MachineDialectType.FLOAT: "float",
        MachineDialectType.STRING: "text",
        MachineDialectType.URL: "url",
        MachineDialectType.FUNCTION: "function",
        MachineDialectType.ERROR: "error",
        MachineDialectType.RETURN: "return",
        MachineDialectType.UNKNOWN: "unknown",
    }
    return type_names[get_type(value)]


def is_truthy(value: Any) -> bool:
    """Determine if a value is truthy in Machine Dialect.

    Falsy values:
    - None/Empty
    - False (boolean)
    - 0 (integer or float)
    - "" (empty string)

    Everything else is truthy.

    Args:
        value: The value to test.

    Returns:
        True if the value is considered truthy, False otherwise.
    """
    # Handle None/Empty
    if value is None:
        return False

    # Handle interpreter Empty object
    if hasattr(value, "type") and hasattr(value.type, "name") and value.type.name == "EMPTY":
        return False

    # Handle booleans
    if isinstance(value, bool):
        return value

    # Handle interpreter Boolean object
    if hasattr(value, "value") and hasattr(value, "type"):
        if hasattr(value.type, "name") and value.type.name == "BOOLEAN":
            return bool(value.value)

    # Handle numbers
    if isinstance(value, int | float):
        return value != 0

    # Handle interpreter numeric objects
    if hasattr(value, "value") and hasattr(value, "type"):
        if hasattr(value.type, "name") and value.type.name in ("INTEGER", "FLOAT"):
            return bool(value.value != 0)

    # Handle strings
    if isinstance(value, str):
        return len(value) > 0

    # Handle interpreter String/URL objects
    if hasattr(value, "value") and hasattr(value, "type"):
        if hasattr(value.type, "name") and value.type.name in ("STRING", "URL"):
            return len(value.value) > 0

    # Everything else is truthy
    return True


def is_numeric(value: Any) -> bool:
    """Check if a value is numeric (integer or float).

    Args:
        value: The value to check.

    Returns:
        True if the value is numeric, False otherwise.
    """
    # Check primitive types
    if isinstance(value, int | float) and not isinstance(value, bool):
        return True

    # Check interpreter objects
    if hasattr(value, "type") and hasattr(value.type, "name"):
        return value.type.name in ("INTEGER", "FLOAT")

    return False


def coerce_to_number(value: Any) -> float | int | None:
    """Attempt to coerce a value to a number.

    Args:
        value: The value to coerce.

    Returns:
        The numeric value if coercion is possible, None otherwise.
    """
    # Already a number
    if isinstance(value, int | float) and not isinstance(value, bool):
        return value

    # Handle interpreter numeric objects
    if hasattr(value, "value") and hasattr(value, "type"):
        if hasattr(value.type, "name") and value.type.name in ("INTEGER", "FLOAT"):
            raw_val = value.value
            return int(raw_val) if value.type.name == "INTEGER" else float(raw_val)

    # Try string conversion
    if isinstance(value, str):
        try:
            # Try integer first
            if "." not in value and "e" not in value.lower():
                return int(value)
            return float(value)
        except ValueError:
            return None

    # Handle interpreter String object
    if hasattr(value, "value") and hasattr(value, "type"):
        if hasattr(value.type, "name") and value.type.name == "STRING":
            return coerce_to_number(value.value)

    # Boolean to number
    if isinstance(value, bool):
        return int(value)

    # Handle interpreter Boolean object
    if hasattr(value, "value") and hasattr(value, "type"):
        if hasattr(value.type, "name") and value.type.name == "BOOLEAN":
            return int(value.value)

    return None
