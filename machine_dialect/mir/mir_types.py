"""MIR Type System.

This module defines the type system used in the MIR, including type
representations, inference, and checking utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class MIRTypeKind(Enum):
    """Kind of MIR type."""

    # Primitive types
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    EMPTY = auto()  # null/none type

    # Complex types
    FUNCTION = auto()
    URL = auto()
    ARRAY = auto()  # Arrays (unordered/ordered lists)
    DICT = auto()  # Dictionary (named lists)

    # Special types
    UNION = auto()  # For union types
    UNKNOWN = auto()  # Type to be inferred
    ERROR = auto()  # Error type
    ANY = auto()  # Unknown/dynamic type


class MIRType(Enum):
    """MIR type enumeration."""

    # Primitive types
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    BOOL = auto()
    EMPTY = auto()  # null/none type

    # Complex types
    FUNCTION = auto()
    URL = auto()
    ARRAY = auto()  # Arrays (unordered/ordered lists)
    DICT = auto()  # Dictionary (named lists)

    # Special types
    UNKNOWN = auto()  # Type to be inferred
    ERROR = auto()  # Error type

    def __str__(self) -> str:
        """Return string representation of type."""
        return self.name.lower()

    def is_union(self) -> bool:
        """Check if this is a union type.

        Returns:
            Always False for regular MIRType
        """
        return False


def infer_type(value: Any) -> MIRType:
    """Infer MIR type from a Python value.

    Args:
        value: The value to infer type from.

    Returns:
        The inferred MIRType.
    """
    if value is None:
        return MIRType.EMPTY
    elif isinstance(value, bool):
        return MIRType.BOOL
    elif isinstance(value, int):
        return MIRType.INT
    elif isinstance(value, float):
        return MIRType.FLOAT
    elif isinstance(value, str):
        # Simple heuristic for URL detection
        if any(value.startswith(prefix) for prefix in ["http://", "https://", "ftp://", "file://"]):
            return MIRType.URL
        return MIRType.STRING
    else:
        return MIRType.UNKNOWN


def is_numeric_type(mir_type: MIRType | MIRUnionType) -> bool:
    """Check if a type is numeric (int or float).

    Args:
        mir_type: The type to check.

    Returns:
        True if the type is numeric, False otherwise.
    """
    if isinstance(mir_type, MIRUnionType):
        # Union is numeric if all its types are numeric
        return all(is_numeric_type(t) for t in mir_type.types)
    return mir_type in (MIRType.INT, MIRType.FLOAT)


def is_comparable_type(mir_type: MIRType | MIRUnionType) -> bool:
    """Check if a type supports comparison operations.

    Args:
        mir_type: The type to check.

    Returns:
        True if the type is comparable, False otherwise.
    """
    if isinstance(mir_type, MIRUnionType):
        # Union is comparable if all its types are comparable
        return all(is_comparable_type(t) for t in mir_type.types)
    return mir_type in (MIRType.INT, MIRType.FLOAT, MIRType.STRING, MIRType.BOOL)


@dataclass
class MIRUnionType:
    """Union type that can be one of multiple types.

    Attributes:
        types: List of possible MIR types
        kind: Always MIRTypeKind.UNION
    """

    kind: MIRTypeKind
    types: list[MIRType]

    def __init__(self, types: list[MIRType]) -> None:
        """Initialize union type.

        Args:
            types: List of possible types
        """
        self.kind = MIRTypeKind.UNION
        self.types = types

    def contains(self, mir_type: MIRType) -> bool:
        """Check if union contains a specific type.

        Args:
            mir_type: Type to check for

        Returns:
            True if union contains the type
        """
        return mir_type in self.types

    def __str__(self) -> str:
        """Return string representation."""
        type_strs = [str(t) for t in self.types]
        return f"Union[{', '.join(type_strs)}]"

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, MIRUnionType):
            return False
        return set(self.types) == set(other.types)

    def is_union(self) -> bool:
        """Check if this is a union type.

        Returns:
            Always True for MIRUnionType
        """
        return True


def ast_type_to_mir_type(type_spec: list[str]) -> MIRType | MIRUnionType:
    """Convert AST type specification to MIR type.

    Note: Yes/No type from the frontend is converted to Boolean
    in the MIR representation for internal processing.

    Args:
        type_spec: List of type names from AST

    Returns:
        Corresponding MIR type or MIRUnionType
    """
    if len(type_spec) == 1:
        # Single type
        type_name = type_spec[0]
        mapping = {
            "Whole Number": MIRType.INT,
            "Float": MIRType.FLOAT,
            "Yes/No": MIRType.BOOL,  # Yes/No -> Boolean in MIR
            "Text": MIRType.STRING,
            "URL": MIRType.URL,
            "Empty": MIRType.EMPTY,
            "Number": None,  # Special handling below
        }

        if type_name == "Number":
            # Number is a union of INT and FLOAT
            return MIRUnionType([MIRType.INT, MIRType.FLOAT])

        mir_type = mapping.get(type_name)
        if mir_type:
            return mir_type
        return MIRType.UNKNOWN
    else:
        # Union type
        mir_types = []
        for type_name in type_spec:
            single_type = ast_type_to_mir_type([type_name])
            if isinstance(single_type, MIRUnionType):
                # Flatten nested unions
                mir_types.extend(single_type.types)
            else:
                mir_types.append(single_type)
        return MIRUnionType(mir_types)


def coerce_types(left: MIRType | MIRUnionType, right: MIRType | MIRUnionType) -> MIRType | MIRUnionType | None:
    """Determine the result type when coercing two types.

    Args:
        left: The left operand type.
        right: The right operand type.

    Returns:
        The coerced type, or None if types cannot be coerced.
    """
    # Handle union types
    if isinstance(left, MIRUnionType) or isinstance(right, MIRUnionType):
        # For now, return UNKNOWN for union type operations
        # This could be improved to compute the union of result types
        return MIRType.UNKNOWN

    # Same types - no coercion needed
    if left == right:
        return left

    # Numeric coercion: int + float -> float
    if is_numeric_type(left) and is_numeric_type(right):
        return MIRType.FLOAT

    # String concatenation with any type
    if left == MIRType.STRING or right == MIRType.STRING:
        return MIRType.STRING

    # No valid coercion
    return None


def get_binary_op_result_type(
    op: str, left: MIRType | MIRUnionType, right: MIRType | MIRUnionType
) -> MIRType | MIRUnionType:
    """Get the result type of a binary operation.

    Args:
        op: The operator string (+, -, *, /, >, <, ==, etc.).
        left: The left operand type.
        right: The right operand type.

    Returns:
        The result type of the operation.
    """
    # Comparison operators always return bool
    if op in ("==", "!=", "===", "!==", ">", "<", ">=", "<="):
        return MIRType.BOOL

    # Logical operators
    if op in ("and", "or"):
        return MIRType.BOOL

    # Arithmetic operators
    if op in ("+", "-", "*", "/", "%", "**"):
        coerced = coerce_types(left, right)
        return coerced if coerced else MIRType.ERROR

    return MIRType.UNKNOWN


def can_cast(from_type: MIRType, to_type: MIRType) -> bool:
    """Check if a type can be cast to another type.

    Args:
        from_type: Source type
        to_type: Target type

    Returns:
        True if the cast is valid, False otherwise
    """
    # Same type - no cast needed
    if from_type == to_type:
        return True

    # Numeric casts
    if is_numeric_type(from_type) and is_numeric_type(to_type):
        return True

    # Bool to numeric
    if from_type == MIRType.BOOL and is_numeric_type(to_type):
        return True

    # Numeric to bool
    if is_numeric_type(from_type) and to_type == MIRType.BOOL:
        return True

    # Everything can be cast to string
    if to_type == MIRType.STRING:
        return True

    # Empty can be cast to any type (null coercion)
    if from_type == MIRType.EMPTY:
        return True

    return False


def is_assignable(value_type: MIRType | MIRUnionType, target_type: MIRType | MIRUnionType) -> bool:
    """Check if a value type can be assigned to a target type.

    Args:
        value_type: The type of the value being assigned
        target_type: The target type

    Returns:
        True if assignment is valid, False otherwise
    """
    # Handle union types
    if isinstance(target_type, MIRUnionType):
        if isinstance(value_type, MIRUnionType):
            # All value types must be in target union
            return all(any(can_cast(vt, tt) for tt in target_type.types) for vt in value_type.types)
        else:
            # Single type must be in union
            return any(can_cast(value_type, tt) for tt in target_type.types)

    if isinstance(value_type, MIRUnionType):
        # Union to single type - all possibilities must be assignable
        return all(can_cast(vt, target_type) for vt in value_type.types)

    # Both are single types
    return can_cast(value_type, target_type)


def get_unary_op_result_type(op: str, operand: MIRType | MIRUnionType) -> MIRType | MIRUnionType:
    """Get the result type of a unary operation.

    Args:
        op: The operator string (-, not).
        operand: The operand type.

    Returns:
        The result type of the operation.
    """
    if op == "-":
        if is_numeric_type(operand):
            return operand
        return MIRType.ERROR

    if op == "not":
        return MIRType.BOOL

    return MIRType.UNKNOWN
