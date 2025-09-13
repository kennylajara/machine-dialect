# Parser Module

## Overview

The Parser module implements a sophisticated hybrid parsing system for the Machine Dialect™
language, combining recursive descent parsing for statements with Pratt parsing (operator
precedence) for expressions. It transforms a stream of tokens from the lexer into a structured
Abstract Syntax Tree (AST), featuring robust error recovery and natural language syntax support.

## Architecture

### Core Components

```text
parser/
├── __init__.py         # Public API exports
├── parser.py           # Main parser implementation
├── token_buffer.py     # Token stream management
├── enums.py           # Precedence levels and parser types
└── tests/             # Comprehensive test suite
```

### Design Philosophy

1. **Hybrid Parsing Strategy**: Combines recursive descent (statements) with Pratt parsing (expressions)
1. **Streaming Architecture**: Memory-efficient token processing with minimal lookahead
1. **Error Recovery**: Panic mode recovery allows parsing to continue after errors
1. **Natural Language Support**: Handles multi-word operators and case-insensitive keywords
1. **Extensibility**: Function registration pattern for easy language extension

## Parser Implementation

### Main Parser Class (`parser.py`)

The `Parser` class orchestrates the entire parsing process:

```python
class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer
        self._token_buffer = TokenBuffer(lexer)
        self._current_token: Token | None = None
        self._peek_token: Token | None = None
        self._errors: list[str] = []
        
        # Function registration
        self._prefix_parse_fns: dict[TokenType, PrefixParseFn] = {}
        self._infix_parse_fns: dict[TokenType, InfixParseFn] = {}
        self._statement_parse_fns: dict[TokenType, Callable] = {}
```

### Token Buffer (`token_buffer.py`)

Efficient token stream management with configurable lookahead:

```python
class TokenBuffer:
    BUFFER_SIZE = 4  # Small buffer for memory efficiency
    
    def current(self) -> Token:
        """Get current token without consuming."""
        
    def peek(self, offset: int = 0) -> Token | None:
        """Look ahead in token stream."""
        
    def advance(self) -> None:
        """Consume current token and refill buffer."""
        
    def set_block_context(self, in_block: bool) -> None:
        """Inform lexer about block parsing context."""
```

## Parsing Strategies

### 1. Statement Parsing (Recursive Descent)

Statements are parsed using traditional recursive descent with dedicated parsing functions:

#### Statement Registration (lines 1449-1458)

```python
self._statement_parse_fns = {
    TokenType.KW_SET: self._parse_set_statement,
    TokenType.KW_GIVE: self._parse_return_statement,
    TokenType.KW_GIVES: self._parse_return_statement,
    TokenType.KW_IF: self._parse_if_statement,
    TokenType.KW_CALL: self._parse_call_statement,
    TokenType.KW_ACTION: self._parse_action_statement,
    TokenType.KW_INTERACTION: self._parse_interaction_statement,
    TokenType.KW_SAY: self._parse_say_statement,
}
```

#### Example: Set Statement Parsing (lines 646-708)

```python
def _parse_set_statement(self) -> SetStatement | ErrorStatement:
    """
    Parse: Set **variable** to _value_.
    
    1. Expect SET keyword
    2. Parse identifier (variable name)
    3. Skip optional "to" keyword
    4. Parse expression (value)
    5. Expect period terminator
    """
```

### 2. Expression Parsing (Pratt Parser)

Expressions use Pratt parsing with operator precedence:

#### Precedence Levels (`enums.py`)

```python
class Precedence(IntEnum):
    LOWEST = 0
    ASSIGNMENT = 1
    TERNARY = 2
    LOGICAL_OR = 3
    LOGICAL_AND = 4
    LOGICAL_NOT = 5
    REL_STRICT_EQ = 6     # ===, !==
    REL_VALUE_EQ = 7      # ==, !=
    REL_SYM_COMP = 8      # equals, not equals
    REL_ASYM_COMP = 9     # <, >, <=, >=
    RELATIONAL = 10
    MATH_ADD_SUB = 11     # +, -
    MATH_PROD_DIV_MOD = 12  # *, /, %
    UNARY_SIMPLIFIED = 13   # -, not
    PREFIX = 14
    GROUP = 15            # (), []
```

#### Expression Parsing Algorithm (lines 302-382)

```python
def _parse_expression(self, precedence: Precedence) -> Expression:
    """
    Core Pratt parsing algorithm:
    
    1. Get prefix parse function for current token
    2. Parse prefix (left side)
    3. While precedence allows:
       a. Get infix parse function
       b. Parse infix with left side
    4. Return complete expression
    """
```

#### Prefix Function Registration (lines 1379-1417)

```python
# Literals
self._prefix_parse_fns[TokenType.LIT_WHOLE_NUMBER] = self._parse_integer_literal
self._prefix_parse_fns[TokenType.LIT_FLOAT] = self._parse_float_literal
self._prefix_parse_fns[TokenType.LIT_TEXT] = self._parse_string_literal
self._prefix_parse_fns[TokenType.LIT_BOOL] = self._parse_boolean_literal
self._prefix_parse_fns[TokenType.KW_EMPTY] = self._parse_empty_literal

# Identifiers and grouping
self._prefix_parse_fns[TokenType.MISC_IDENT] = self._parse_identifier
self._prefix_parse_fns[TokenType.DELIM_LPAREN] = self._parse_grouped_or_tuple

# Prefix operators
self._prefix_parse_fns[TokenType.OP_MINUS] = self._parse_prefix_expression
self._prefix_parse_fns[TokenType.KW_NOT] = self._parse_prefix_expression
```

#### Infix Function Registration (lines 1332-1377)

```python
# Arithmetic operators
for op in [TokenType.OP_PLUS, TokenType.OP_MINUS, 
           TokenType.OP_MULT, TokenType.OP_DIV, TokenType.OP_MOD]:
    self._infix_parse_fns[op] = self._parse_infix_expression

# Comparison operators
for op in [TokenType.OP_LT, TokenType.OP_GT, 
           TokenType.OP_LTE, TokenType.OP_GTE]:
    self._infix_parse_fns[op] = self._parse_infix_expression

# Equality operators (natural language)
for op in [TokenType.OP_EQ, TokenType.OP_NEQ,
           TokenType.OP_STRICT_EQ, TokenType.OP_STRICT_NEQ]:
    self._infix_parse_fns[op] = self._parse_infix_expression
```

### 3. Block Parsing

Blocks use depth-based indentation with `>` markers:

#### Block Parsing Logic (lines 1197-1314)

```python
def _parse_block_statement(self) -> BlockStatement:
    """
    Parse indented block:
    
    1. Count leading '>' symbols for depth
    2. Parse statements at that depth
    3. Stop when depth decreases or block ends
    4. Handle nested blocks recursively
    """
    
    # Example input:
    # > Set x to 5.
    # > If x > 0:
    # >> Say "positive".
    # > Set y to 10.
```

## Error Recovery

### Panic Mode Recovery (lines 278-301)

The parser implements sophisticated error recovery:

```python
def _panic_and_recover(self) -> tuple[ErrorStatement, list[Token]]:
    """
    Panic mode error recovery:
    
    1. Collect error tokens
    2. Skip to synchronization point (period or EOF)
    3. Create ErrorStatement with context
    4. Continue parsing after error
    """
    
    # Synchronization points
    SYNC_TOKENS = {
        TokenType.PUNCT_PERIOD,  # End of statement
        TokenType.MISC_EOF,       # End of file
        TokenType.KW_IF,          # Statement keywords
        TokenType.KW_SET,
        TokenType.KW_GIVE,
        TokenType.KW_CALL,
    }
```

### Error Collection

Errors are collected without stopping parsing:

```python
def _add_error(self, message: str) -> None:
    """Add error to collection for later reporting."""
    self._errors.append(message)

def errors(self) -> list[str]:
    """Get all collected parsing errors."""
    return self._errors
```

## Natural Language Features

### Multi-word Operator Support

The parser handles natural language operators seamlessly:

```python
# Natural language equality
"is equal to"           → TokenType.OP_EQ
"is the same as"        → TokenType.OP_EQ
"is strictly equal to"  → TokenType.OP_STRICT_EQ
"is identical to"       → TokenType.OP_STRICT_EQ

# Natural language inequality  
"is not equal to"       → TokenType.OP_NEQ
"is different from"     → TokenType.OP_NEQ
"does not equal"        → TokenType.OP_NEQ

# Natural language comparison
"is greater than"       → TokenType.OP_GT
"is less than"          → TokenType.OP_LT
"is greater than or equal to" → TokenType.OP_GTE
```

### Stopword Handling

Common English words are automatically skipped:

```python
def _next_token(self) -> None:
    """Advance tokens, skipping stopwords."""
    while self._peek_token and self._is_stopword(self._peek_token):
        self._peek_token = self._token_buffer.advance()
```

Stopwords include: `a`, `an`, `the`, `is`, `are`, `was`, `were`, `be`, `been`

## Usage Examples

### Basic Parsing

```python
from machine_dialect.lexer import Lexer
from machine_dialect.parser import Parser

# Parse a simple program
source = """
Set **x** to _5_.
If **x** is greater than _0_:
> Say _"positive"_.
"""

lexer = Lexer(source)
parser = Parser(lexer)
program = parser.parse_program()

if parser.errors():
    for error in parser.errors():
        print(f"Error: {error}")
else:
    print(f"AST: {program}")
```

### Custom Expression Parsing

```python
# Parse just an expression
lexer = Lexer("_5_ + _10_ * _2_")
parser = Parser(lexer)
parser._next_token()  # Initialize
expression = parser._parse_expression(Precedence.LOWEST)
print(expression)  # (5 + (10 * 2))
```

### Error Recovery Example

```python
# Parser continues after errors
source = """
Set **x** to .           # Missing value
Set **y** to _10_.       # Valid statement
If **x** >               # Incomplete condition
Set **z** to _"test"_.   # Valid statement
"""

lexer = Lexer(source)
parser = Parser(lexer)
program = parser.parse_program()

# Program contains both ErrorStatements and valid statements
print(f"Errors: {len(parser.errors())}")
print(f"Statements: {len(program.statements)}")  # 4 statements
```

## Advanced Features

### 1. Function Call Arguments

Supports both positional and named arguments:

```python
# Positional only
Call **function** with _1_, _2_, _3_.

# Named only
Call **function** with param1: _"value"_, param2: _42_.

# Mixed
Call **function** with _1_, _2_, named: _"value"_.
```

### 2. Parameter Definitions

Methods support typed parameters with defaults:

```python
Action **calculate** with x (number), y (number) = _0_:
> Give back **x** + **y**.
```

### 3. Conditional Expressions

Ternary expressions for inline conditionals:

```python
Set **result** to _"yes"_ if **condition** else _"no"_.
```

## Performance Considerations

### Memory Efficiency

1. **Small Token Buffer**: Only 4 tokens lookahead
1. **Streaming Lexer**: Doesn't tokenize entire file upfront
1. **Lazy Evaluation**: Tokens generated on-demand

### Parsing Speed

1. **Direct Dispatch**: Function pointers avoid switch statements
1. **Precedence Climbing**: Efficient expression parsing
1. **Early Termination**: Stop on unrecoverable errors

## Testing

Comprehensive test suite in `tests/`:

```bash
# Run all parser tests
python -m pytest machine_dialect/parser/tests/ -v

# Specific test categories
python -m pytest machine_dialect/parser/tests/test_expressions.py -v
python -m pytest machine_dialect/parser/tests/test_statements.py -v
python -m pytest machine_dialect/parser/tests/test_error_recovery.py -v
```

## Extension Guide

### Adding New Statements

1. Add token type to lexer
1. Register parsing function:

```python
self._statement_parse_fns[TokenType.KW_NEW] = self._parse_new_statement
```

1. Implement parsing function:

```python
def _parse_new_statement(self) -> Statement:
    # Parse statement structure
    # Return AST node
```

### Adding New Operators

1. Add token type and precedence
1. Register as prefix or infix:

```python
self._infix_parse_fns[TokenType.OP_NEW] = self._parse_infix_expression
```

1. Update precedence map:

```python
self._precedences[TokenType.OP_NEW] = Precedence.MATH_ADD_SUB
```

## Error Messages

The parser provides detailed error messages with context:

```text
Expected identifier after 'Set', got PUNCT_PERIOD at line 1:9
Unexpected token INT in expression at line 3:14
Missing closing parenthesis at line 5:23
Block depth mismatch: expected 1, got 2 at line 7:0
```

## Best Practices

1. **Always Check Errors**: Use `parser.errors()` after parsing
1. **Handle Error Nodes**: AST may contain `ErrorStatement` and `ErrorExpression`
1. **Test Error Cases**: Ensure parser handles malformed input gracefully
1. **Preserve Tokens**: Maintain token references for debugging
1. **Use Type Hints**: Leverage typing for better IDE support

## Related Modules

- **Lexer** (`machine_dialect/lexer/`): Provides token stream
- **AST** (`machine_dialect/ast/`): Node definitions built by parser
- **Errors** (`machine_dialect/errors/`): Exception types for parsing errors
- **REPL** (`machine_dialect/repl/`): Interactive parser testing
