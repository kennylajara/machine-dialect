"""Type system for Machine Dialect™ compile-time type checking."""

from .type_system import (
    TYPE_DISPLAY_NAMES,
    MDType,
    TypeSpec,
    check_type_compatibility,
    get_type_from_name,
    get_type_from_value,
    is_assignable_to,
)

__all__ = [
    "TYPE_DISPLAY_NAMES",
    "MDType",
    "TypeSpec",
    "check_type_compatibility",
    "get_type_from_name",
    "get_type_from_value",
    "is_assignable_to",
]
