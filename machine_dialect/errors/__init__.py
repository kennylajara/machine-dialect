"""Error handling for Machine Dialect™.

This package provides exception classes and error reporting utilities.
"""

from machine_dialect.errors.exceptions import (
    MDException,
    MDNameError,
    MDSyntaxError,
    MDTypeError,
    MDUninitializedError,
    MDValueError,
)
from machine_dialect.errors.messages import (
    EXPECTED_BLOCK_MARKER,
    EXPECTED_EXPRESSION,
    EXPECTED_PREFIX_OPERATOR,
    UNEXPECTED_TOKEN,
)

__all__ = [
    "EXPECTED_BLOCK_MARKER",
    "EXPECTED_EXPRESSION",
    "EXPECTED_PREFIX_OPERATOR",
    "UNEXPECTED_TOKEN",
    "MDException",
    "MDNameError",
    "MDSyntaxError",
    "MDTypeError",
    "MDUninitializedError",
    "MDValueError",
]
