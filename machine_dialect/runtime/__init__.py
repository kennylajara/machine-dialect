"""Common runtime module for Machine Dialect.

This module provides shared runtime functionality used by the interpreter,
VM, and future LLVM backend. It ensures consistent behavior across all
execution modes.

The runtime includes:
- Type system and semantics
- Value representations and conversions
- Operator implementations
- Built-in functions
- Error definitions
"""

from machine_dialect.runtime.builtins import (
    BUILTIN_FUNCTIONS,
    BuiltinFunction,
    call_builtin,
    get_builtin,
    register_builtin,
)
from machine_dialect.runtime.errors import (
    ERROR_MESSAGES,
    ArgumentError,
    DivisionByZeroError,
    NameError,
    RuntimeError,
    TypeError,
    ValueError,
)
from machine_dialect.runtime.operators import (
    add,
    divide,
    equals,
    greater_than,
    greater_than_or_equal,
    less_than,
    less_than_or_equal,
    logical_and,
    logical_not,
    logical_or,
    modulo,
    multiply,
    negate,
    not_equals,
    power,
    strict_equals,
    strict_not_equals,
    subtract,
)
from machine_dialect.runtime.types import (
    MachineDialectType,
    coerce_to_number,
    get_type,
    get_type_name,
    is_numeric,
    is_truthy,
)
from machine_dialect.runtime.values import (
    RuntimeValue,
    get_raw_value,
    is_empty,
    to_bool,
    to_float,
    to_int,
    to_string,
)
from machine_dialect.runtime.values import (
    equals as value_equals,
)
from machine_dialect.runtime.values import (
    strict_equals as value_strict_equals,
)

__all__ = [
    # Builtins
    "BUILTIN_FUNCTIONS",
    "BuiltinFunction",
    "call_builtin",
    "get_builtin",
    "register_builtin",
    # Errors
    "ArgumentError",
    "DivisionByZeroError",
    "ERROR_MESSAGES",
    "NameError",
    "RuntimeError",
    "TypeError",
    "ValueError",
    # Operators
    "add",
    "divide",
    "equals",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "logical_and",
    "logical_not",
    "logical_or",
    "modulo",
    "multiply",
    "negate",
    "not_equals",
    "power",
    "strict_equals",
    "strict_not_equals",
    "subtract",
    # Types
    "MachineDialectType",
    "coerce_to_number",
    "get_type",
    "get_type_name",
    "is_numeric",
    "is_truthy",
    # Values
    "RuntimeValue",
    "get_raw_value",
    "is_empty",
    "to_bool",
    "to_float",
    "to_int",
    "to_string",
    "value_equals",
    "value_strict_equals",
]
