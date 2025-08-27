"""Built-in functions for Machine Dialect runtime.

This module provides standard library functions that can be called
from Machine Dialect code across all execution modes.
"""

from collections.abc import Callable
from typing import Any, NamedTuple

from machine_dialect.runtime.errors import ArgumentError, ValueError
from machine_dialect.runtime.types import get_type_name
from machine_dialect.runtime.values import get_raw_value, is_empty, to_float, to_int, to_string


class BuiltinFunction(NamedTuple):
    """Descriptor for a built-in function."""

    name: str
    func: Callable[..., Any]
    arity: int  # -1 for variadic
    description: str


def builtin_print(*args: Any) -> None:
    """Print function for output.

    Args:
        *args: Values to print.
    """
    # Convert all arguments to string representation
    str_args = [to_string(arg) for arg in args]
    print(*str_args)


def builtin_say(*args: Any) -> None:
    """Say function (alias for print).

    Args:
        *args: Values to output.
    """
    builtin_print(*args)


def builtin_type(value: Any) -> str:
    """Get the type of a value.

    Args:
        value: The value to get the type of.

    Returns:
        String name of the type.
    """
    return get_type_name(value)


def builtin_len(value: Any) -> int:
    """Get the length of a value.

    Args:
        value: A string or collection.

    Returns:
        The length of the value.

    Raises:
        ValueError: If value doesn't support len.
    """
    raw = get_raw_value(value)

    if isinstance(raw, str):
        return len(raw)

    if hasattr(raw, "__len__"):
        return len(raw)

    raise ValueError(f"Cannot get length of {get_type_name(value)}")


def builtin_str(value: Any) -> str:
    """Convert a value to string.

    Args:
        value: The value to convert.

    Returns:
        String representation of the value.
    """
    return to_string(value)


def builtin_int(value: Any) -> int:
    """Convert a value to integer.

    Args:
        value: The value to convert.

    Returns:
        Integer representation of the value.

    Raises:
        ValueError: If conversion fails.
    """
    try:
        return to_int(value)
    except Exception as e:
        raise ValueError(str(e)) from None


def builtin_float(value: Any) -> float:
    """Convert a value to float.

    Args:
        value: The value to convert.

    Returns:
        Float representation of the value.

    Raises:
        ValueError: If conversion fails.
    """
    try:
        return to_float(value)
    except Exception as e:
        raise ValueError(str(e)) from None


def builtin_abs(value: Any) -> Any:
    """Get the absolute value.

    Args:
        value: A numeric value.

    Returns:
        The absolute value.

    Raises:
        ValueError: If value is not numeric.
    """
    from machine_dialect.runtime.types import is_numeric

    if not is_numeric(value):
        raise ValueError(f"Cannot get absolute value of {get_type_name(value)}")

    raw = get_raw_value(value)
    result = abs(raw)

    # Preserve type
    if isinstance(raw, int):
        return int(result)
    return result


def builtin_min(*args: Any) -> Any:
    """Get the minimum value.

    Args:
        *args: Values to compare.

    Returns:
        The minimum value.

    Raises:
        ArgumentError: If no arguments provided.
    """
    if not args:
        raise ArgumentError("min() requires at least one argument")

    # Extract raw values for comparison
    raw_values = [get_raw_value(arg) for arg in args]

    # Find the minimum
    min_val = raw_values[0]
    min_arg = args[0]

    for val, arg in zip(raw_values[1:], args[1:], strict=False):
        if val < min_val:
            min_val = val
            min_arg = arg

    return min_arg


def builtin_max(*args: Any) -> Any:
    """Get the maximum value.

    Args:
        *args: Values to compare.

    Returns:
        The maximum value.

    Raises:
        ArgumentError: If no arguments provided.
    """
    if not args:
        raise ArgumentError("max() requires at least one argument")

    # Extract raw values for comparison
    raw_values = [get_raw_value(arg) for arg in args]

    # Find the maximum
    max_val = raw_values[0]
    max_arg = args[0]

    for val, arg in zip(raw_values[1:], args[1:], strict=False):
        if val > max_val:
            max_val = val
            max_arg = arg

    return max_arg


def builtin_bool(value: Any) -> bool:
    """Convert a value to boolean.

    Args:
        value: The value to convert.

    Returns:
        Boolean representation of the value.
    """
    from machine_dialect.runtime.types import is_truthy

    return is_truthy(value)


def builtin_is_empty(value: Any) -> bool:
    """Check if a value is empty/null.

    Args:
        value: The value to check.

    Returns:
        True if the value is empty, False otherwise.
    """
    return is_empty(value)


def builtin_round(value: Any, precision: Any = 0) -> Any:
    """Round a number to given precision.

    Args:
        value: The number to round.
        precision: Number of decimal places (default 0).

    Returns:
        Rounded value.

    Raises:
        ValueError: If value is not numeric.
    """
    from machine_dialect.runtime.types import is_numeric

    if not is_numeric(value):
        raise ValueError(f"Cannot round {get_type_name(value)}")

    raw_value = get_raw_value(value)
    raw_precision = get_raw_value(precision)

    if not isinstance(raw_precision, int):
        raise ValueError("Precision must be an integer")

    result = round(raw_value, raw_precision)

    # If precision is 0 and value was int, return int
    if raw_precision == 0 and isinstance(raw_value, int):
        return int(result)
    return result


# Registry of built-in functions
BUILTIN_FUNCTIONS: dict[str, BuiltinFunction] = {
    "print": BuiltinFunction("print", builtin_print, -1, "Print values to output"),
    "say": BuiltinFunction("say", builtin_say, -1, "Output values (alias for print)"),
    "type": BuiltinFunction("type", builtin_type, 1, "Get the type of a value"),
    "len": BuiltinFunction("len", builtin_len, 1, "Get the length of a string or collection"),
    "str": BuiltinFunction("str", builtin_str, 1, "Convert value to string"),
    "int": BuiltinFunction("int", builtin_int, 1, "Convert value to integer"),
    "float": BuiltinFunction("float", builtin_float, 1, "Convert value to float"),
    "bool": BuiltinFunction("bool", builtin_bool, 1, "Convert value to boolean"),
    "abs": BuiltinFunction("abs", builtin_abs, 1, "Get absolute value"),
    "min": BuiltinFunction("min", builtin_min, -1, "Get minimum value"),
    "max": BuiltinFunction("max", builtin_max, -1, "Get maximum value"),
    "is_empty": BuiltinFunction("is_empty", builtin_is_empty, 1, "Check if value is empty"),
    "round": BuiltinFunction("round", builtin_round, -1, "Round a number to given precision"),
}


def get_builtin(name: str) -> BuiltinFunction | None:
    """Get a built-in function by name.

    Args:
        name: Function name.

    Returns:
        The built-in function or None if not found.
    """
    return BUILTIN_FUNCTIONS.get(name)


def register_builtin(name: str, func: Callable[..., Any], arity: int = -1, description: str = "") -> None:
    """Register a new built-in function.

    Args:
        name: Function name.
        func: The callable to register.
        arity: Number of arguments (-1 for variadic).
        description: Description of the function.
    """
    BUILTIN_FUNCTIONS[name] = BuiltinFunction(name, func, arity, description)


def call_builtin(name: str, *args: Any) -> Any:
    """Call a built-in function by name.

    Args:
        name: Function name.
        *args: Arguments to pass to the function.

    Returns:
        Result of the function call.

    Raises:
        NameError: If function not found.
        ArgumentError: If wrong number of arguments.
    """
    from machine_dialect.runtime.errors import NameError

    builtin = get_builtin(name)
    if builtin is None:
        raise NameError(f"Built-in function '{name}' is not defined")

    # Check arity if not variadic
    if builtin.arity >= 0 and len(args) != builtin.arity:
        raise ArgumentError(f"Function '{name}' expects {builtin.arity} arguments, got {len(args)}")

    return builtin.func(*args)
