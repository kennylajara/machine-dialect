"""Runtime error definitions for Machine Dialect.

This module defines common runtime exceptions used across all execution modes.
"""


class RuntimeError(Exception):
    """Base class for all Machine Dialect runtime errors."""

    pass


class TypeError(RuntimeError):
    """Raised when an operation is performed on incompatible types."""

    pass


class DivisionByZeroError(RuntimeError):
    """Raised when division or modulo by zero is attempted."""

    pass


class NameError(RuntimeError):
    """Raised when a name/identifier is not found."""

    pass


class ArgumentError(RuntimeError):
    """Raised when function arguments are invalid."""

    pass


class ValueError(RuntimeError):
    """Raised when a value is invalid for an operation."""

    pass


# Error message templates
ERROR_MESSAGES = {
    "UNSUPPORTED_OPERAND_TYPE": "Unsupported operand type(s) for {operator}: '{left_type}' and '{right_type}'",
    "UNSUPPORTED_UNARY_OPERAND": "Unsupported operand type for unary {operator}: '{type}'",
    "DIVISION_BY_ZERO": "Division by zero",
    "MODULO_BY_ZERO": "Modulo by zero",
    "NAME_UNDEFINED": "Name '{name}' is not defined",
    "WRONG_ARGUMENT_COUNT": "Function '{name}' expects {expected} arguments, got {actual}",
    "INVALID_CONVERSION": "Cannot convert {from_type} to {to_type}",
    "UNKNOWN_OPERATOR": "Unknown operator: '{operator}'",
    "UNKNOWN_PREFIX_OPERATOR": "Unknown prefix operator: '{operator}'",
    "UNKNOWN_INFIX_OPERATOR": "Unknown infix operator: '{operator}'",
}
