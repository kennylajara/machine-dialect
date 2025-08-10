"""Built-in native functions for the VM.

This module provides standard library functions that can be called
from Machine Dialect code.
"""

from typing import Any

from machine_dialect.vm.objects import NativeFunction


def native_print(*args: Any) -> None:
    """Print function for output.

    Args:
        *args: Values to print.
    """
    print(*args)


def native_say(*args: Any) -> None:
    """Say function (alias for print).

    Args:
        *args: Values to output.
    """
    print(*args)


def native_type(value: Any) -> str:
    """Get the type of a value.

    Args:
        value: The value to get the type of.

    Returns:
        String name of the type.
    """
    from machine_dialect.vm.objects import type_name

    return type_name(value)


def native_len(value: Any) -> int:
    """Get the length of a value.

    Args:
        value: A string or collection.

    Returns:
        The length of the value.

    Raises:
        RuntimeError: If value doesn't support len.
    """
    if isinstance(value, str):
        return len(value)
    if hasattr(value, "__len__"):
        return len(value)
    raise RuntimeError(f"Cannot get length of {type(value).__name__}")


def native_str(value: Any) -> str:
    """Convert a value to string.

    Args:
        value: The value to convert.

    Returns:
        String representation of the value.
    """
    if value is None:
        return "empty"
    return str(value)


def native_int(value: Any) -> int:
    """Convert a value to integer.

    Args:
        value: The value to convert.

    Returns:
        Integer representation of the value.

    Raises:
        RuntimeError: If conversion fails.
    """
    try:
        if isinstance(value, str):
            return int(value)
        if isinstance(value, int | float | bool):
            return int(value)
        raise RuntimeError(f"Cannot convert {type(value).__name__} to integer")
    except ValueError as e:
        raise RuntimeError(f"Invalid integer conversion: {e}") from e


def native_float(value: Any) -> float:
    """Convert a value to float.

    Args:
        value: The value to convert.

    Returns:
        Float representation of the value.

    Raises:
        RuntimeError: If conversion fails.
    """
    try:
        if isinstance(value, str):
            return float(value)
        if isinstance(value, int | float | bool):
            return float(value)
        raise RuntimeError(f"Cannot convert {type(value).__name__} to float")
    except ValueError as e:
        raise RuntimeError(f"Invalid float conversion: {e}") from e


def native_abs(value: Any) -> Any:
    """Get the absolute value.

    Args:
        value: A numeric value.

    Returns:
        The absolute value.

    Raises:
        RuntimeError: If value is not numeric.
    """
    if not isinstance(value, int | float):
        raise RuntimeError(f"Cannot get absolute value of {type(value).__name__}")
    return abs(value)


def native_min(*args: Any) -> Any:
    """Get the minimum value.

    Args:
        *args: Values to compare.

    Returns:
        The minimum value.

    Raises:
        RuntimeError: If no arguments provided.
    """
    if not args:
        raise RuntimeError("min() requires at least one argument")
    return min(args)


def native_max(*args: Any) -> Any:
    """Get the maximum value.

    Args:
        *args: Values to compare.

    Returns:
        The maximum value.

    Raises:
        RuntimeError: If no arguments provided.
    """
    if not args:
        raise RuntimeError("max() requires at least one argument")
    return max(args)


# Registry of native functions
NATIVE_FUNCTIONS: dict[str, NativeFunction] = {
    "print": NativeFunction("print", native_print, -1),
    "say": NativeFunction("say", native_say, -1),
    "type": NativeFunction("type", native_type, 1),
    "len": NativeFunction("len", native_len, 1),
    "str": NativeFunction("str", native_str, 1),
    "int": NativeFunction("int", native_int, 1),
    "float": NativeFunction("float", native_float, 1),
    "abs": NativeFunction("abs", native_abs, 1),
    "min": NativeFunction("min", native_min, -1),
    "max": NativeFunction("max", native_max, -1),
}


def get_native_function(name: str) -> NativeFunction | None:
    """Get a native function by name.

    Args:
        name: Function name.

    Returns:
        The native function or None if not found.
    """
    return NATIVE_FUNCTIONS.get(name)


def register_native_function(name: str, func: NativeFunction) -> None:
    """Register a new native function.

    Args:
        name: Function name.
        func: The native function to register.
    """
    NATIVE_FUNCTIONS[name] = func
