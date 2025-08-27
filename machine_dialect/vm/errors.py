"""VM-specific error types.

This module defines exceptions that are specific to VM bytecode execution.
General runtime errors are imported from the runtime module.
"""

from machine_dialect.runtime import RuntimeError as BaseRuntimeError


class VMError(BaseRuntimeError):
    """Base class for VM-specific errors."""

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
