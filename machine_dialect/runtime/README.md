# Runtime Module

## Overview

The **Runtime** module provides shared runtime functionality used across all Machine Dialect
execution modes: the interpreter, VM, and future LLVM backend. It ensures consistent language
semantics regardless of how the code is executed.

This module serves as the single source of truth for:

- Type system and coercion rules
- Operator implementations
- Built-in functions
- Value representations
- Error definitions

## Architecture

### Components

```text
runtime/
├── __init__.py      # Public API exports
├── types.py         # Type system and semantics
├── values.py        # Value representations and conversions
├── operators.py     # Operator implementations
├── builtins.py      # Built-in functions registry
└── errors.py        # Runtime error definitions
```

### Design Principles

1. **Backend Agnostic**: Works with both interpreter objects and primitive values
1. **Type Safety**: Full MyPy strict compliance
1. **Consistent Semantics**: Same behavior across all execution modes
1. **Extensible**: Easy to add new functions and operators
1. **Performance Aware**: Minimal overhead for each backend

## Type System

### Machine Dialect Types

```python
from machine_dialect.runtime import MachineDialectType

# Available types
MachineDialectType.EMPTY      # None/null value
MachineDialectType.BOOLEAN    # Yes/No
MachineDialectType.INTEGER    # Whole numbers
MachineDialectType.FLOAT      # Decimal numbers
MachineDialectType.STRING     # Text values
MachineDialectType.URL        # URL strings
MachineDialectType.FUNCTION   # Callable objects
MachineDialectType.ERROR      # Error objects
MachineDialectType.RETURN     # Return values
```

### Type Operations

```python
from machine_dialect.runtime import get_type, get_type_name, is_truthy, is_numeric

value = 42
get_type(value)         # MachineDialectType.INTEGER
get_type_name(value)    # "integer"
is_numeric(value)       # True
is_truthy(0)           # False
is_truthy("hello")     # True
```

### Truthiness Rules

Falsy values:

- `None` / Empty
- `False` (boolean)
- `0` (integer or float)
- `""` (empty string)

Everything else is truthy.

## Value System

### Value Conversions

```python
from machine_dialect.runtime import to_int, to_float, to_string, to_bool

to_int("42")           # 42
to_float("3.14")       # 3.14
to_string(True)        # "Yes"
to_bool("")            # False
```

### Value Comparison

```python
from machine_dialect.runtime import equals, strict_equals

# Value equality (==) - type coercion allowed
equals(42, 42.0)       # True - numeric values are equal

# Strict equality (===) - same type required
strict_equals(42, 42.0)  # False - different types
```

### Raw Value Extraction

```python
from machine_dialect.runtime import get_raw_value

# Works with both primitives and interpreter objects
raw = get_raw_value(interpreter_object)  # Extracts .value attribute
raw = get_raw_value(42)                  # Returns 42 as-is
```

## Operators

### Arithmetic Operators

```python
from machine_dialect.runtime import add, subtract, multiply, divide, modulo, power

add(2, 3)              # 5
add("hello", "world")  # "helloworld" (string concatenation)
subtract(5, 3)         # 2
multiply(4, 5)         # 20
divide(10, 3)          # 3.333... (always float division)
modulo(10, 3)          # 1
power(2, 8)            # 256
```

### Comparison Operators

```python
from machine_dialect.runtime import (
    less_than, greater_than, 
    less_than_or_equal, greater_than_or_equal
)

less_than(3, 5)                # True
greater_than(10, 5)            # True
less_than_or_equal(5, 5)       # True
greater_than_or_equal(3, 5)    # False
```

### Logical Operators

```python
from machine_dialect.runtime import logical_not, logical_and, logical_or

logical_not(False)             # True
logical_and(True, False)       # False
logical_or(False, True)        # True
```

### Unary Operators

```python
from machine_dialect.runtime import negate

negate(5)                      # -5
negate(-3)                     # 3
```

## Built-in Functions

### Function Registry

```python
from machine_dialect.runtime import BUILTIN_FUNCTIONS, get_builtin, call_builtin

# Get function metadata
func = get_builtin("print")
func.name          # "print"
func.arity         # -1 (variadic)
func.description   # "Print values to output"

# Call built-in function
call_builtin("type", 42)       # "integer"
call_builtin("len", "hello")   # 5
```

### Available Built-ins

| Function   | Arity    | Description                              |
| ---------- | -------- | ---------------------------------------- |
| `print`    | variadic | Print values to output                   |
| `say`      | variadic | Output values (alias for print)          |
| `type`     | 1        | Get the type of a value                  |
| `len`      | 1        | Get the length of a string or collection |
| `str`      | 1        | Convert value to string                  |
| `int`      | 1        | Convert value to integer                 |
| `float`    | 1        | Convert value to float                   |
| `bool`     | 1        | Convert value to boolean                 |
| `abs`      | 1        | Get absolute value                       |
| `min`      | variadic | Get minimum value                        |
| `max`      | variadic | Get maximum value                        |
| `is_empty` | 1        | Check if value is empty                  |
| `round`    | variadic | Round a number to given precision        |

### Extending Built-ins

```python
from machine_dialect.runtime import register_builtin

def custom_function(x, y):
    return x * y

register_builtin(
    "multiply",
    custom_function,
    arity=2,
    description="Multiply two values"
)
```

## Error Handling

### Error Types

```python
from machine_dialect.runtime import (
    RuntimeError,      # Base error class
    TypeError,         # Type mismatch errors  
    ValueError,        # Invalid value errors
    DivisionByZeroError,  # Division/modulo by zero
    NameError,         # Undefined names
    ArgumentError      # Function argument errors
)
```

### Error Messages

```python
from machine_dialect.runtime import ERROR_MESSAGES

# Predefined error message templates
ERROR_MESSAGES["DIVISION_BY_ZERO"]  # "Division by zero"
ERROR_MESSAGES["NAME_UNDEFINED"]    # "Name '{name}' is not defined"
```

## Integration Guide

### For Interpreter

```python
# In interpreter/evaluator.py
from machine_dialect.runtime import add, get_type

def evaluate_addition(left, right):
    # Use runtime operator instead of custom logic
    return add(left, right)
```

### For VM

```python
# In vm/vm.py
from machine_dialect.runtime import BUILTIN_FUNCTIONS

# Replace native functions with runtime builtins
for name, func in BUILTIN_FUNCTIONS.items():
    register_vm_function(name, func.func)
```

### For LLVM (Future)

```c
// Runtime library in C/Rust
extern "C" {
    Value* runtime_add(Value* a, Value* b);
    bool runtime_is_truthy(Value* v);
}
```

## Testing

```python
# Test type semantics
from machine_dialect.runtime import is_truthy

assert is_truthy(1) == True
assert is_truthy(0) == False
assert is_truthy("") == False
assert is_truthy("hello") == True

# Test operators
from machine_dialect.runtime import add, multiply

assert add(2, 3) == 5
assert add("hello", " world") == "hello world"
assert multiply(4, 5) == 20

# Test built-ins
from machine_dialect.runtime import call_builtin

assert call_builtin("type", 42) == "integer"
assert call_builtin("len", "hello") == 5
```

## Performance Considerations

1. **Interpreter**: Uses rich object system, runtime provides compatibility layer
1. **VM**: Uses primitives directly, runtime adds minimal overhead
1. **LLVM**: Will link to optimized C/Rust runtime library

The runtime is designed to have minimal performance impact while ensuring consistency.

## Future Extensions

Planned additions:

- Collection types (lists, dictionaries)
- More built-in functions (math, string manipulation)
- Async/await support
- Module system integration
- Foreign Function Interface (FFI)

## API Stability

The runtime module API is designed to be stable across Machine Dialect versions. Breaking changes
will be clearly documented and migration guides provided.

## Contributing

When adding new features to the runtime:

1. Ensure type safety with MyPy strict mode
1. Add comprehensive docstrings
1. Update this README
1. Add tests for new functionality
1. Consider impact on all three backends
