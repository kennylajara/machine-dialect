"""Type system for compile-time type checking in Machine Dialect™.

This module provides the type system used during compilation for:
- Type checking variable definitions
- Validating assignments
- Union type support
- Type compatibility checking

IMPORTANT: This is for compile-time checking. Runtime types are in runtime/types.py.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class MDType(Enum):
    """Machine Dialect™ type enumeration for compile-time type checking.

    Maps to the language's type keywords and provides type compatibility rules.
    """

    TEXT = auto()  # "Text" keyword
    WHOLE_NUMBER = auto()  # "Whole Number" keyword
    FLOAT = auto()  # "Float" keyword
    NUMBER = auto()  # "Number" keyword (integer or float)
    YES_NO = auto()  # "Yes/No" keyword (boolean)
    URL = auto()  # "URL" keyword
    DATE = auto()  # "Date" keyword
    DATETIME = auto()  # "DateTime" keyword
    TIME = auto()  # "Time" keyword
    LIST = auto()  # "List" keyword (generic list)
    UNORDERED_LIST = auto()  # Unordered list (dash markers)
    ORDERED_LIST = auto()  # Ordered list (numbered markers)
    NAMED_LIST = auto()  # Named list (dictionary with colon syntax)
    EMPTY = auto()  # "Empty" keyword (null/none)
    ANY = auto()  # "Any" keyword (future, dynamic type)


# Mapping from type names (as they appear in source) to MDType enum
TYPE_NAME_MAP = {
    "Text": MDType.TEXT,
    "Whole Number": MDType.WHOLE_NUMBER,
    "Float": MDType.FLOAT,
    "Number": MDType.NUMBER,
    "Yes/No": MDType.YES_NO,
    "URL": MDType.URL,
    "Date": MDType.DATE,
    "DateTime": MDType.DATETIME,
    "Time": MDType.TIME,
    "List": MDType.LIST,
    "Unordered List": MDType.UNORDERED_LIST,
    "Ordered List": MDType.ORDERED_LIST,
    "Named List": MDType.NAMED_LIST,
    "Empty": MDType.EMPTY,
    "Any": MDType.ANY,
}


# Reverse mapping for error messages
TYPE_DISPLAY_NAMES = {
    MDType.TEXT: "Text",
    MDType.WHOLE_NUMBER: "Whole Number",
    MDType.FLOAT: "Float",
    MDType.NUMBER: "Number",
    MDType.YES_NO: "Yes/No",
    MDType.URL: "URL",
    MDType.DATE: "Date",
    MDType.DATETIME: "DateTime",
    MDType.TIME: "Time",
    MDType.LIST: "List",
    MDType.UNORDERED_LIST: "Unordered List",
    MDType.ORDERED_LIST: "Ordered List",
    MDType.NAMED_LIST: "Named List",
    MDType.EMPTY: "Empty",
    MDType.ANY: "Any",
}


@dataclass
class TypeSpec:
    """Type specification for a variable, supporting union types.

    Attributes:
        types: List of allowed types (for union types)
    """

    types: list[MDType]

    def __init__(self, type_names: list[str]) -> None:
        """Initialize TypeSpec from type name strings.

        Args:
            type_names: List of type names as strings (e.g., ["Whole Number", "Text"])
        """
        self.types = []
        for name in type_names:
            md_type = get_type_from_name(name)
            if md_type:
                self.types.append(md_type)

    def allows_type(self, md_type: MDType) -> bool:
        """Check if this TypeSpec allows the given type.

        Args:
            md_type: The type to check

        Returns:
            True if type is allowed, False otherwise
        """
        # ANY type allows everything
        if MDType.ANY in self.types:
            return True

        # Check direct membership
        if md_type in self.types:
            return True

        # Special case: Number allows both Whole Number and Float
        if MDType.NUMBER in self.types:
            if md_type in (MDType.WHOLE_NUMBER, MDType.FLOAT):
                return True

        # Special case: Whole Number/Float are assignable to Number
        # (This is for when we have a Number variable and assign int/float)
        # But this is handled by is_assignable_to, not here

        return False

    def __str__(self) -> str:
        """Return human-readable type specification."""
        if len(self.types) == 1:
            return TYPE_DISPLAY_NAMES[self.types[0]]
        return " or ".join(TYPE_DISPLAY_NAMES[t] for t in self.types)


def get_type_from_name(name: str) -> MDType | None:
    """Convert type name string to MDType enum.

    Args:
        name: Type name as it appears in source code

    Returns:
        Corresponding MDType or None if not recognized
    """
    return TYPE_NAME_MAP.get(name)


def get_type_from_value(value: Any) -> MDType | None:
    """Determine the MDType of a literal value during compilation.

    Args:
        value: The value to determine the type of

    Returns:
        The MDType of the value or None if unknown
    """
    # This is for compile-time type checking of literals
    # The value here would typically be from AST literal nodes

    if value is None or (hasattr(value, "value") and value.value is None):
        return MDType.EMPTY

    # Check AST literal nodes
    if hasattr(value, "__class__"):
        class_name = value.__class__.__name__

        if class_name == "WholeNumberLiteral":
            return MDType.WHOLE_NUMBER
        elif class_name == "FloatLiteral":
            return MDType.FLOAT
        elif class_name == "StringLiteral":
            # Check if it's a URL
            if hasattr(value, "value") and isinstance(value.value, str):
                if value.value.startswith(("http://", "https://", "ftp://", "file://")):
                    return MDType.URL
            return MDType.TEXT
        elif class_name == "YesNoLiteral":
            return MDType.YES_NO
        elif class_name == "EmptyLiteral":
            return MDType.EMPTY
        elif class_name == "URLLiteral":
            return MDType.URL
        elif class_name == "UnorderedListLiteral":
            return MDType.UNORDERED_LIST
        elif class_name == "OrderedListLiteral":
            return MDType.ORDERED_LIST
        elif class_name == "NamedListLiteral":
            return MDType.NAMED_LIST

    # Fallback to Python types (for testing or when we have actual values)
    if isinstance(value, bool):
        return MDType.YES_NO
    elif isinstance(value, int):
        return MDType.WHOLE_NUMBER
    elif isinstance(value, float):
        return MDType.FLOAT
    elif isinstance(value, str):
        if value.startswith(("http://", "https://", "ftp://", "file://")):
            return MDType.URL
        return MDType.TEXT
    elif isinstance(value, list):
        return MDType.LIST  # Generic list for Python lists
    elif isinstance(value, dict):
        return MDType.NAMED_LIST  # Dictionary maps to named list
    elif value == "empty" or value is None:
        return MDType.EMPTY

    return None


def is_assignable_to(value_type: MDType, target_type: MDType) -> bool:
    """Check if a value of one type can be assigned to a variable of another type.

    This implements the Machine Dialect™ type compatibility rules.
    NO implicit conversions are allowed per the spec.

    Args:
        value_type: The type of the value being assigned
        target_type: The type of the variable being assigned to

    Returns:
        True if assignment is allowed, False otherwise
    """
    # Exact match is always allowed
    if value_type == target_type:
        return True

    # ANY type can accept anything
    if target_type == MDType.ANY:
        return True

    # Number type can accept Whole Number or Float
    if target_type == MDType.NUMBER:
        if value_type in (MDType.WHOLE_NUMBER, MDType.FLOAT):
            return True

    # Empty can be assigned to any type (null/none value)
    if value_type == MDType.EMPTY:
        return True

    # NO other implicit conversions per spec
    return False


def check_type_compatibility(
    value_type: MDType,
    type_spec: TypeSpec,
) -> tuple[bool, str | None]:
    """Check if a value type is compatible with a type specification.

    Args:
        value_type: The type of the value being checked
        type_spec: The type specification to check against

    Returns:
        Tuple of (is_compatible, error_message)
        error_message is None if compatible
    """
    # Check each type in the union
    for allowed_type in type_spec.types:
        if is_assignable_to(value_type, allowed_type):
            return (True, None)

    # Not compatible with any type in the union
    value_name = TYPE_DISPLAY_NAMES[value_type]
    spec_name = str(type_spec)
    error = f"Cannot assign {value_name} value to variable of type {spec_name}"

    return (False, error)
