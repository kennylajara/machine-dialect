"""MIR Value Representations.

This module defines the various value types used in MIR instructions,
including temporaries, variables, constants, and function references.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from .mir_types import MIRType, MIRUnionType, infer_type


class VariableScope(Enum):
    """Scope of a variable in the program."""

    GLOBAL = "global"  # Module-level variables
    PARAMETER = "param"  # Function parameters
    LOCAL = "local"  # Function-local variables


class MIRValue(ABC):
    """Base class for all MIR values with rich metadata."""

    def __init__(self, mir_type: MIRType | MIRUnionType) -> None:
        """Initialize a MIR value with rich metadata.

        Args:
            mir_type: The type of the value (can be union type).
        """
        self.type = mir_type
        # Additional metadata for union types
        self.union_type: MIRUnionType | None = None
        if isinstance(mir_type, MIRUnionType):
            self.union_type = mir_type
            self.type = MIRType.UNKNOWN  # Base type is unknown for unions

        # Rich metadata fields
        from machine_dialect.mir.dataflow import Range

        self.known_range: Range | None = None  # Value range for numeric types
        self.is_non_null: bool = False  # Guaranteed non-null/non-empty
        self.is_non_zero: bool = False  # Guaranteed non-zero
        self.alignment: int | None = None  # Memory alignment in bytes
        self.provenance: str | None = None  # Source of this value (e.g., "user_input", "constant")
        self.is_loop_invariant: bool = False  # True if value doesn't change in loops
        self.is_pure: bool = True  # True if computing this value has no side effects

    @abstractmethod
    def __str__(self) -> str:
        """Return string representation of the value."""
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Check equality with another value."""
        pass

    @abstractmethod
    def __hash__(self) -> int:
        """Return hash of the value."""
        pass


class Temp(MIRValue):
    """Temporary value in SSA form.

    Temporaries are compiler-generated values used to hold intermediate
    results in three-address code.
    """

    _next_id = 0

    def __init__(self, mir_type: MIRType | MIRUnionType, temp_id: int | None = None) -> None:
        """Initialize a temporary.

        Args:
            mir_type: The type of the temporary (can be union type).
            temp_id: Optional explicit ID. If None, auto-generated.
        """
        super().__init__(mir_type)
        if temp_id is None:
            self.id = Temp._next_id
            Temp._next_id += 1
        else:
            self.id = temp_id

    def __str__(self) -> str:
        """Return string representation (e.g., 't1')."""
        return f"t{self.id}"

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        return isinstance(other, Temp) and self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(("temp", self.id))

    @classmethod
    def reset_counter(cls) -> None:
        """Reset the temporary ID counter (useful for tests)."""
        cls._next_id = 0


class Variable(MIRValue):
    """User-defined variable.

    Variables represent named values from the source program.
    In SSA form, these may be versioned (e.g., x_1, x_2).
    """

    def __init__(self, name: str, mir_type: MIRType | MIRUnionType, version: int = 0) -> None:
        """Initialize a variable.

        Args:
            name: The variable name.
            mir_type: The type of the variable (can be union type).
            version: SSA version number (0 for non-SSA).
        """
        super().__init__(mir_type)
        self.name = name
        self.version = version

    def __str__(self) -> str:
        """Return string representation."""
        if self.version > 0:
            return f"{self.name}.{self.version}"
        return self.name

    def __eq__(self, other: object) -> bool:
        """Check equality based on name and version."""
        return isinstance(other, Variable) and self.name == other.name and self.version == other.version

    def __hash__(self) -> int:
        """Hash based on name and version."""
        return hash(("var", self.name, self.version))

    def with_version(self, version: int) -> "Variable":
        """Create a new variable with a different version.

        Args:
            version: The new version number.

        Returns:
            A new Variable with the same name and type but different version.
        """
        return Variable(self.name, self.type, version)


class ScopedVariable(Variable):
    """Variable with explicit scope information.

    This extends Variable to track whether it's a global, parameter, or local variable.
    """

    def __init__(
        self,
        name: str,
        scope: VariableScope,
        mir_type: MIRType | MIRUnionType,
        version: int = 0,
    ) -> None:
        """Initialize a scoped variable.

        Args:
            name: The variable name.
            scope: The scope of the variable.
            mir_type: The type of the variable.
            version: SSA version number (0 for non-SSA).
        """
        super().__init__(name, mir_type, version)
        self.scope = scope

    def __str__(self) -> str:
        """Return string representation."""
        base = super().__str__()
        if self.scope == VariableScope.LOCAL:
            return f"{base}[local]"
        elif self.scope == VariableScope.PARAMETER:
            return f"{base}[param]"
        return base

    def __eq__(self, other: object) -> bool:
        """Check equality based on name, version, and scope."""
        if not isinstance(other, ScopedVariable):
            # Allow comparison with regular Variable for compatibility
            return super().__eq__(other)
        return self.name == other.name and self.version == other.version and self.scope == other.scope

    def __hash__(self) -> int:
        """Hash based on name, version, and scope."""
        return hash(("scoped_var", self.name, self.version, self.scope))

    def with_version(self, version: int) -> "ScopedVariable":
        """Create a new scoped variable with a different version.

        Args:
            version: The new version number.

        Returns:
            A new ScopedVariable with the same name, type, and scope but different version.
        """
        return ScopedVariable(self.name, self.scope, self.type, version)


class Constant(MIRValue):
    """Constant value.

    Constants represent literal values from the source program.
    """

    def __init__(self, value: Any, mir_type: MIRType | MIRUnionType | None = None) -> None:
        """Initialize a constant.

        Args:
            value: The constant value.
            mir_type: Optional explicit type. If None, inferred from value.
        """
        if mir_type is None:
            mir_type = infer_type(value)
        super().__init__(mir_type)
        self.value = value

    def __str__(self) -> str:
        """Return string representation."""
        if self.type == MIRType.STRING:
            return f'"{self.value}"'
        elif self.type == MIRType.EMPTY:
            return "null"
        else:
            return str(self.value)

    def __eq__(self, other: object) -> bool:
        """Check equality based on value and type."""
        return isinstance(other, Constant) and self.value == other.value and self.type == other.type

    def __hash__(self) -> int:
        """Hash based on value and type."""
        return hash(("const", self.value, self.type))


class FunctionRef(MIRValue):
    """Function reference.

    Represents a reference to a function that can be called.
    """

    def __init__(self, name: str) -> None:
        """Initialize a function reference.

        Args:
            name: The function name.
        """
        super().__init__(MIRType.FUNCTION)
        self.name = name

    def __str__(self) -> str:
        """Return string representation."""
        return f"@{self.name}"

    def __eq__(self, other: object) -> bool:
        """Check equality based on name."""
        return isinstance(other, FunctionRef) and self.name == other.name

    def __hash__(self) -> int:
        """Hash based on name."""
        return hash(("func", self.name))
