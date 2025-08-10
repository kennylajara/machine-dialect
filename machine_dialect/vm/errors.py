"""VM-specific error types.

This module defines exceptions that can occur during bytecode execution.
"""


class VMError(Exception):
    """Base class for all VM errors."""

    pass


class StackUnderflowError(VMError):
    """Raised when trying to pop from an empty stack."""

    pass


class InvalidOpcodeError(VMError):
    """Raised when encountering an unknown or invalid opcode."""

    pass


class IndexOutOfRangeError(VMError):
    """Raised when accessing an invalid constant or variable index."""

    pass


class TypeError(VMError):
    """Raised when performing an unsupported operation on given types."""

    pass


class DivisionByZeroError(VMError):
    """Raised when attempting to divide by zero."""

    pass


class RuntimeError(VMError):
    """General runtime error."""

    pass
