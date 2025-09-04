# AST (Abstract Syntax Tree) Module

## Overview

The AST module defines the node structure for the Machine Dialect language's abstract syntax
tree. It provides a comprehensive hierarchy of node types that represent the parsed structure
of Machine Dialect programs, enabling semantic analysis, interpretation, and code generation.

## Architecture

### Core Design Principles

1. **Hierarchical Structure**: All nodes inherit from the abstract `ASTNode` base class
1. **Token Preservation**: Nodes retain their originating tokens for error reporting and source mapping
1. **Type Safety**: All node classes use strict typing with comprehensive type hints
1. **String Representation**: Every node implements `__str__()` for debugging and visualization

### Module Structure

```text
ast/
├── __init__.py       # Public API exports
├── ast_node.py       # Abstract base class
├── expressions.py    # Expression nodes
├── literals.py       # Literal value nodes
├── statements.py     # Statement nodes
└── program.py        # Root program node
```

## Node Hierarchy

### Base Node

#### `ASTNode` (ast_node.py)

Abstract base class for all AST nodes.

```python
class ASTNode(ABC):
    @abstractmethod
    def __str__(self) -> str:
        """Return string representation of the node."""
        ...
```

### Program Root

#### `Program` (program.py)

Root node containing all top-level statements.

**Properties:**

- `statements: list[Statement]` - List of program statements

**String Format:** Concatenates all statement strings

### Expression Nodes (expressions.py)

#### `Expression`

Base class for all expressions that evaluate to values.

**Properties:**

- `token: Token` - Originating token for error reporting

#### `Identifier`

Represents variable or function names wrapped in backticks.

**Properties:**

- `token: Token` - The IDENT token
- `value: str` - The identifier name

**Example:** `` `variable_name` `` → `Identifier(value="variable_name")`

#### `PrefixExpression`

Unary operators applied to expressions.

**Properties:**

- `token: Token` - The operator token
- `operator: str` - String representation (`-`, `not`)
- `right: Expression` - The operand expression

**Example:** `-5` → `PrefixExpression(operator="-", right=IntegerLiteral(5))`

#### `InfixExpression`

Binary operators between two expressions.

**Properties:**

- `token: Token` - The operator token
- `left: Expression` - Left operand
- `operator: str` - Operator string (`+`, `-`, `*`, `/`, `<`, `>`, etc.)
- `right: Expression` - Right operand

**Supported Operators:**

- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Comparison: `<`, `>`, `<=`, `>=`
- Equality: `==`, `!=`, `===`, `!==`
- Logical: `and`, `or`

**Example:** `x + 5` → `InfixExpression(left=Identifier("x"), operator="+", right=IntegerLiteral(5))`

#### `Arguments`

Function call arguments supporting both positional and named parameters.

**Properties:**

- `token: Token` - Starting token
- `positional: list[Expression]` - Positional arguments
- `named: list[tuple[Identifier, Expression]]` - Named arguments as (name, value) pairs

**Example:** `with 5, name: "John"` →
`Arguments(positional=[IntegerLiteral(5)], named=[(Identifier("name"), StringLiteral("John"))])`

#### `ConditionalExpression`

Ternary conditional expressions.

**Properties:**

- `token: Token` - The IF token
- `consequence: Expression` - Value if condition is true
- `condition: Expression` - The condition to evaluate
- `alternative: Expression` - Value if condition is false

**Example:** `a if x > 0 else b` → `ConditionalExpression(consequence=a, condition=x>0, alternative=b)`

#### `ErrorExpression`

Represents parsing errors while maintaining AST structure.

**Properties:**

- `token: Token` - Token where error occurred
- `message: str` - Error description

### Literal Nodes (literals.py)

All literals inherit from `Expression` and represent constant values.

#### `IntegerLiteral`

**Properties:**

- `token: Token` - The INT token
- `value: int` - The integer value

**Example:** `_42_` → `IntegerLiteral(value=42)`

#### `FloatLiteral`

**Properties:**

- `token: Token` - The FLOAT token
- `value: float` - The floating-point value

**Example:** `_3.14_` → `FloatLiteral(value=3.14)`

#### `StringLiteral`

**Properties:**

- `token: Token` - The TEXT token
- `value: str` - The string content (without quotes)

**Example:** `_"hello"_` → `StringLiteral(value="hello")`

#### `YesNoLiteral`

**Properties:**

- `token: Token` - The BOOL token
- `value: bool` - The boolean value

**Example:** `_Yes_` → `YesNoLiteral(value=True)`

#### `EmptyLiteral`

Represents null/nil values using the `empty` keyword.

**Properties:**

- `token: Token` - The EMPTY token

**Example:** `empty` → `EmptyLiteral()`

### Statement Nodes (statements.py)

#### `Statement`

Base class for all statements that perform actions.

**Properties:**

- `token: Token` - Starting token of the statement

#### `ExpressionStatement`

Wraps an expression as a statement.

**Properties:**

- `token: Token` - Starting token
- `expression: Expression` - The wrapped expression

#### `SetStatement`

Variable assignment statement.

**Properties:**

- `token: Token` - The SET token
- `identifier: Identifier` - Variable being assigned
- `value: Expression` - Value to assign

**Example:** `Set x to 5.` → `SetStatement(identifier=Identifier("x"), value=IntegerLiteral(5))`

#### `ReturnStatement`

Returns a value from a function.

**Properties:**

- `token: Token` - The GIVE or GIVES token
- `value: Expression | None` - Value to return (None for void)

**Example:** `Give back result.` → `ReturnStatement(value=Identifier("result"))`

#### `CallStatement`

Function call statement.

**Properties:**

- `token: Token` - The CALL token
- `identifier: Identifier` - Function to call
- `arguments: Arguments | None` - Function arguments

**Example:** `Call print with "Hello".` → `CallStatement(identifier=Identifier("print"), arguments=Arguments(...))`

#### `IfStatement`

Conditional branching with optional else clause.

**Properties:**

- `token: Token` - The IF token
- `condition: Expression` - Condition to evaluate
- `consequence: BlockStatement` - If-true block
- `alternative: BlockStatement | None` - Optional else block

**Example:**

```text
If x > 0:
> Set result to positive.
Otherwise:
> Set result to negative.
```

#### `BlockStatement`

Container for multiple statements with depth tracking.

**Properties:**

- `token: Token` - Starting token
- `statements: list[Statement]` - Contained statements
- `depth: int` - Nesting depth (number of `>` markers)

#### `ActionStatement`

Private method definition.

**Properties:**

- `token: Token` - The ACTION token
- `identifier: Identifier` - Method name
- `parameters: list[Parameter]` - Method parameters
- `body: BlockStatement | None` - Method body

#### `InteractionStatement`

Public method definition.

**Properties:**

- `token: Token` - The INTERACTION token
- `identifier: Identifier` - Method name
- `parameters: list[Parameter]` - Method parameters
- `body: BlockStatement | None` - Method body

#### `Parameter`

Method parameter with optional type and default value.

**Properties:**

- `token: Token` - Parameter token
- `identifier: Identifier` - Parameter name
- `type_annotation: Identifier | None` - Optional type
- `default_value: Expression | None` - Optional default

**Example:** `name (text) = "Anonymous"` →
`Parameter(identifier="name", type_annotation="text", default_value="Anonymous")`

#### `SayStatement`

Output/display statement.

**Properties:**

- `token: Token` - The SAY token
- `expression: Expression` - Value to output

**Example:** `Say message.` → `SayStatement(expression=Identifier("message"))`

#### `ErrorStatement`

Represents parsing errors as statements.

**Properties:**

- `token: Token` - Error location
- `message: str` - Error description
- `tokens: list[Token]` - Tokens involved in error

## Usage Examples

### Creating AST Nodes Programmatically

```python
from machine_dialect.ast import (
    Program, SetStatement, Identifier, IntegerLiteral,
    IfStatement, BlockStatement, InfixExpression
)
from machine_dialect.lexer import Token, TokenType

# Create a simple program: Set x to 5.
program = Program(
    statements=[
        SetStatement(
            token=Token(TokenType.KW_SET, "Set", 1, 0),
            identifier=Identifier(
                Token(TokenType.MISC_IDENT, "x", 1, 4),
                "x"
            ),
            value=IntegerLiteral(
                Token(TokenType.LIT_INT, "5", 1, 9),
                5
            )
        )
    ]
)

print(program)  # Output: Set x to 5
```

### Traversing the AST

```python
def count_nodes(node: ASTNode) -> int:
    """Count total nodes in AST subtree."""
    count = 1
    
    if isinstance(node, Program):
        for stmt in node.statements:
            count += count_nodes(stmt)
    elif isinstance(node, IfStatement):
        count += count_nodes(node.consequence)
        if node.alternative:
            count += count_nodes(node.alternative)
    elif isinstance(node, BlockStatement):
        for stmt in node.statements:
            count += count_nodes(stmt)
    elif isinstance(node, InfixExpression):
        count += count_nodes(node.left)
        count += count_nodes(node.right)
    # ... handle other node types
    
    return count
```

### Pattern Matching (Python 3.10+)

```python
def evaluate_literal(node: ASTNode) -> Any:
    """Extract value from literal nodes."""
    match node:
        case IntegerLiteral(value=v):
            return v
        case FloatLiteral(value=v):
            return v
        case StringLiteral(value=v):
            return v
        case YesNoLiteral(value=v):
            return v
        case EmptyLiteral():
            return None
        case _:
            raise ValueError(f"Not a literal: {type(node)}")
```

## Error Handling

The AST module provides error nodes (`ErrorExpression` and `ErrorStatement`) that allow the
parser to continue building a valid AST structure even when encountering syntax errors. This
enables:

1. **Multiple Error Reporting**: Parser can find multiple errors in one pass
1. **Partial Analysis**: Valid portions of code can still be analyzed
1. **Better IDE Support**: Enables features like partial auto-completion

## Best Practices

1. **Always Preserve Tokens**: When creating nodes, always include the originating token for debugging
1. **Use Type Hints**: Leverage Python's typing system for better IDE support
1. **Implement `__str__()`**: Ensure all custom nodes have meaningful string representations
1. **Handle None Values**: Many properties (like `alternative` in `IfStatement`) can be None
1. **Validate Node Construction**: Ensure required properties are provided

## Extension Points

The AST module is designed for extensibility:

1. **New Node Types**: Inherit from appropriate base class (`Expression` or `Statement`)
1. **Visitor Pattern**: Nodes are ready for visitor pattern implementation
1. **Custom Attributes**: Nodes can be extended with additional metadata
1. **Serialization**: String representation enables easy serialization

## Testing

Test files are located in `tests/` and cover:

- Node construction and properties
- String representation formatting
- Edge cases and error conditions
- Complex nested structures

Run tests with:

```bash
python -m pytest machine_dialect/ast/tests/ -v
```

## Related Modules

- **Lexer** (`machine_dialect/lexer/`): Generates tokens consumed by AST nodes
- **Parser** (`machine_dialect/parser/`): Builds AST from token stream
- **Errors** (`machine_dialect/errors/`): Error types used by error nodes
