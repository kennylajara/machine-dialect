"""Operator implementations for Machine Dialect runtime.

This module provides uniform operator semantics across all execution modes.
"""

from typing import Any

from machine_dialect.runtime.errors import DivisionByZeroError, TypeError
from machine_dialect.runtime.types import get_type_name, is_numeric, is_truthy
from machine_dialect.runtime.values import equals as value_equals
from machine_dialect.runtime.values import get_raw_value
from machine_dialect.runtime.values import strict_equals as value_strict_equals


def add(a: Any, b: Any) -> Any:
    """Addition operator (+).

    Supports:
    - Numeric addition (int + int, float + float, mixed)
    - String concatenation

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        Result of addition.

    Raises:
        TypeError: If operands are incompatible.
    """
    raw_a = get_raw_value(a)
    raw_b = get_raw_value(b)

    # String concatenation
    if isinstance(raw_a, str) or isinstance(raw_b, str):
        return str(raw_a) + str(raw_b)

    # Numeric addition
    if is_numeric(a) and is_numeric(b):
        result = raw_a + raw_b
        # Preserve int type if both operands are ints
        if isinstance(raw_a, int) and isinstance(raw_b, int):
            return int(result)
        return result

    raise TypeError(f"Unsupported operand type(s) for +: '{get_type_name(a)}' and '{get_type_name(b)}'")


def subtract(a: Any, b: Any) -> Any:
    """Subtraction operator (-).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        Result of subtraction.

    Raises:
        TypeError: If operands are not numeric.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for -: '{get_type_name(a)}' and '{get_type_name(b)}'")

    raw_a = get_raw_value(a)
    raw_b = get_raw_value(b)
    result = raw_a - raw_b

    # Preserve int type if both operands are ints
    if isinstance(raw_a, int) and isinstance(raw_b, int):
        return int(result)
    return result


def multiply(a: Any, b: Any) -> Any:
    """Multiplication operator (*).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        Result of multiplication.

    Raises:
        TypeError: If operands are not numeric.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for *: '{get_type_name(a)}' and '{get_type_name(b)}'")

    raw_a = get_raw_value(a)
    raw_b = get_raw_value(b)
    result = raw_a * raw_b

    # Preserve int type if both operands are ints
    if isinstance(raw_a, int) and isinstance(raw_b, int):
        return int(result)
    return result


def divide(a: Any, b: Any) -> Any:
    """Division operator (/).

    Always returns a float (true division).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        Result of division.

    Raises:
        TypeError: If operands are not numeric.
        DivisionByZeroError: If divisor is zero.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for /: '{get_type_name(a)}' and '{get_type_name(b)}'")

    raw_a = get_raw_value(a)
    raw_b = get_raw_value(b)

    if raw_b == 0:
        raise DivisionByZeroError("Division by zero")

    # Always use true division
    return raw_a / raw_b


def modulo(a: Any, b: Any) -> Any:
    """Modulo operator (%).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        Result of modulo.

    Raises:
        TypeError: If operands are not numeric.
        DivisionByZeroError: If divisor is zero.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for %: '{get_type_name(a)}' and '{get_type_name(b)}'")

    raw_a = get_raw_value(a)
    raw_b = get_raw_value(b)

    if raw_b == 0:
        raise DivisionByZeroError("Modulo by zero")

    result = raw_a % raw_b

    # Preserve int type if both operands are ints
    if isinstance(raw_a, int) and isinstance(raw_b, int):
        return int(result)
    return result


def power(a: Any, b: Any) -> Any:
    """Exponentiation operator (** or ^).

    Args:
        a: Base.
        b: Exponent.

    Returns:
        Result of exponentiation.

    Raises:
        TypeError: If operands are not numeric.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for ^: '{get_type_name(a)}' and '{get_type_name(b)}'")

    raw_a = get_raw_value(a)
    raw_b = get_raw_value(b)
    result = raw_a**raw_b

    # Preserve int type if both operands are ints and exponent is non-negative
    if isinstance(raw_a, int) and isinstance(raw_b, int) and raw_b >= 0:
        return int(result)
    return result


def negate(value: Any) -> Any:
    """Negation operator (unary -).

    Args:
        value: The value to negate.

    Returns:
        Negated value.

    Raises:
        TypeError: If value is not numeric.
    """
    if not is_numeric(value):
        raise TypeError(f"Unsupported operand type for unary -: '{get_type_name(value)}'")

    raw = get_raw_value(value)

    # Handle -0 case
    if raw == 0:
        return type(raw)(0)  # Preserve int/float type

    return -raw


def logical_not(value: Any) -> bool:
    """Logical NOT operator (not).

    Args:
        value: The value to negate.

    Returns:
        Boolean negation of the value.
    """
    return not is_truthy(value)


def logical_and(a: Any, b: Any) -> bool:
    """Logical AND operator.

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if both values are truthy, False otherwise.
    """
    return is_truthy(a) and is_truthy(b)


def logical_or(a: Any, b: Any) -> bool:
    """Logical OR operator.

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if either value is truthy, False otherwise.
    """
    return is_truthy(a) or is_truthy(b)


def equals(a: Any, b: Any) -> bool:
    """Value equality operator (==).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if values are equal, False otherwise.
    """
    return value_equals(a, b)


def not_equals(a: Any, b: Any) -> bool:
    """Value inequality operator (!=).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if values are not equal, False otherwise.
    """
    return not value_equals(a, b)


def strict_equals(a: Any, b: Any) -> bool:
    """Strict equality operator (===).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if values are strictly equal (same type and value), False otherwise.
    """
    return value_strict_equals(a, b)


def strict_not_equals(a: Any, b: Any) -> bool:
    """Strict inequality operator (!==).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if values are not strictly equal, False otherwise.
    """
    return not value_strict_equals(a, b)


def less_than(a: Any, b: Any) -> bool:
    """Less than operator (<).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if a < b, False otherwise.

    Raises:
        TypeError: If operands are not comparable.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for <: '{get_type_name(a)}' and '{get_type_name(b)}'")

    return bool(get_raw_value(a) < get_raw_value(b))


def greater_than(a: Any, b: Any) -> bool:
    """Greater than operator (>).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if a > b, False otherwise.

    Raises:
        TypeError: If operands are not comparable.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for >: '{get_type_name(a)}' and '{get_type_name(b)}'")

    return bool(get_raw_value(a) > get_raw_value(b))


def less_than_or_equal(a: Any, b: Any) -> bool:
    """Less than or equal operator (<=).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if a <= b, False otherwise.

    Raises:
        TypeError: If operands are not comparable.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for <=: '{get_type_name(a)}' and '{get_type_name(b)}'")

    return bool(get_raw_value(a) <= get_raw_value(b))


def greater_than_or_equal(a: Any, b: Any) -> bool:
    """Greater than or equal operator (>=).

    Args:
        a: Left operand.
        b: Right operand.

    Returns:
        True if a >= b, False otherwise.

    Raises:
        TypeError: If operands are not comparable.
    """
    if not is_numeric(a) or not is_numeric(b):
        raise TypeError(f"Unsupported operand type(s) for >=: '{get_type_name(a)}' and '{get_type_name(b)}'")

    return bool(get_raw_value(a) >= get_raw_value(b))
