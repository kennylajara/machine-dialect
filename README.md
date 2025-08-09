# Machine Dialect (.md)

**Machine Dialect** is a programming language designed to look like natural language and feel
like structured documentation. It is written in Markdown and intended to be both human-friendly
and AI-native — readable by people, generatable and parsable by machines.

## 🌟 Key Features

- **Natural Language Syntax**: Write code that reads like English
- **Markdown-Based**: Source files are `.md` documents with YAML frontmatter
- **AI-First Design**: Optimized for LLM generation and understanding
- **Human-Supervisable**: Readable by non-programmers, editable in any Markdown editor
- **Type-Safe Implementation**: Strict typing with comprehensive test coverage

## 📋 Table of Contents

- [Why Machine Dialect?](#why-machine-dialect)
- [Philosophy](#philosophy)
- [Language Features](#language-features)
- [Syntax Examples](#syntax-examples)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Development](#development)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Status](#status)

## Why Machine Dialect?

Modern programming languages were made for humans to instruct machines. But now that machines
can understand and generate human-like language, it's time to rethink the language itself.

Machine Dialect is for a future where:

- **AI writes most of the code**, and humans supervise, modify, and approve
- Code is **visually readable**, even by non-programmers
- The structure of the program is as **intuitive as a document**, and lives comfortably inside
  Markdown files

## Philosophy

- ✍️ **Natural structure**: Programs are written as paragraphs, headings, lists — not brackets,
  semicolons, and cryptic symbols
- 🧠 **AI-first**: Syntax is deterministic enough for parsing, but optimized for LLMs to
  generate and understand effortlessly
- 👁️ **Human-supervisable**: Markdown keeps everything readable, diffable, and renderable
- 🪶 **Lightweight**: No ceremony. Just write it like you'd explain it
- 📐 **Math as code**: Mathematical operations are expressed using LaTeX syntax inside `$$...$$` blocks
- 🏷️ **Metadata-aware**: Executable files begin with a YAML frontmatter block that declares intent

## Language Features

### Core Syntax Elements

| Element       | Syntax         | Example                                               |
| ------------- | -------------- | ----------------------------------------------------- |
| **Variables** | Bold text      | `**total**`, `**user_name**`                          |
| **Literals**  | Italic text    | `_42_`, `_"hello"_`, `_true_`, `empty`                |
| **Keywords**  | Plain text     | `set`, `if`, `then`, `else`, `give back`/`gives back` |
| **Blocks**    | `>` prefix     | `> Set **x** to _10_.`                                |
| **Math**      | LaTeX blocks   | `$$\text{result} = x^2 + y$$`                         |
| **Comments**  | HTML comments  | `<!-- This is a comment -->`                          |
| **Lists**     | Markdown lists | `- item1` / `- item2`                                 |

### Operators

Machine Dialect supports both symbolic and natural language operators:

| Operation             | Symbols | Natural Forms (Canonical)                             | Aliases                     | Example                              |
| --------------------- | ------- | ----------------------------------------------------- | --------------------------- | ------------------------------------ |
| Addition              | `+`     | -                                                     | -                           | `_5_ + _3_`                          |
| Subtraction           | `-`     | -                                                     | -                           | `_10_ - _2_`                         |
| Multiplication        | `*`     | -                                                     | -                           | `_4_ * _7_`                          |
| Division              | `/`     | -                                                     | -                           | `_20_ / _4_`                         |
| Greater than          | `>`     | `is greater than`                                     | `is more than`              | `**x** > _5_`                        |
| Less than             | `<`     | `is less than`                                        | `is under`, `is fewer than` | `**y** < _10_`                       |
| Greater or equal      | `>=`    | `is greater than or equal to`                         | `is at least`               | `**score** >= _90_`                  |
| Less or equal         | `<=`    | `is less than or equal to`                            | `is at most`                | `**age** <= _18_`                    |
| **Value Equality**    | -       | `is equal to`, `equals`                               | `is the same as`            | `**status** equals _"active"_`       |
| **Value Inequality**  | -       | `is not equal to`, `does not equal`                   | `is different from`         | `**role** is not equal to _"admin"_` |
| **Strict Equality**   | -       | `is strictly equal to`, `is exactly equal to`         | `is identical to`           | `**x** is strictly equal to _5_`     |
| **Strict Inequality** | -       | `is not strictly equal to`, `is not exactly equal to` | `is not identical to`       | `**y** is not identical to _"5"_`    |
| Assignment            | -       | `to`                                                  | -                           | `Set **x** to _5_`                   |

#### Equality Types

Machine Dialect distinguishes between two types of equality:

- **Value Equality** (`equals`, `is equal to`): Compares values with type coercion. For
  example, `_5_ equals _"5"_` might be true.
- **Strict Equality** (`is strictly equal to`, `is identical to`): Compares both value AND type.
  For example, `_5_ is strictly equal to _"5"_` would be false because one is a number and the
  other is a string.

## Syntax Examples

### Basic Variable Assignment

```markdown
---
exec: true
---
# My Program

Set **total** to _0_.
Set **name** to _"Alice"_.
Set **is_active** to _true_.
Set **result** to empty.
```

### Conditional Statements

```markdown
If **score** is greater than _90_ then:
> Set **grade** to _"A"_.
> Say "Excellent work!".
Otherwise if **score** is greater than _80_ then:
> Set **grade** to _"B"_.
> Say "Good job!".
Otherwise:
> Set **grade** to _"C"_.
> Say "Keep practicing!".
```

### Working with Lists and Loops

```markdown
## Shopping List
- Milk: _3.50_
- Bread: _2.00_
- Eggs: _4.25_

For each **item** in **Shopping List**:
> Add **item** value to **total**.
> Increment **item_count**.

Say "Total cost: $" + **total**.
```

### Mathematical Operations

```markdown
## Calculate Circle Area

Set **radius** to _5_.

Apply formula:
$$
\text{area} = \pi \times \text{radius}^2
$$

Say "The area is: " + **area**.
```

### Functions (Using Headers)

```markdown
## Calculate Average

Given **numbers** as list:

Set **sum** to _0_.
Set **count** to _0_.

For each **num** in **numbers**:
> Add **num** to **sum**.
> Increment **count**.

Give back **sum** divided by **count**.
```

## Installation

### Prerequisites

- Python 3.12 or higher
- UV package manager (recommended) or pip
- Git

### Setup Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/kennylajara/machine-dialect.git
   cd machine_dialect
   ```

1. **Create and activate virtual environment:**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

1. **Install the package in editable mode:**

   ```bash
   # Using UV (recommended)
   uv pip install -e .

   # Or using pip
   pip install -e .
   ```

1. **Install development dependencies:**

   ```bash
   uv sync  # Or: pip install -e ".[dev]"
   ```

1. **Install pre-commit hooks:**

   ```bash
   pre-commit install
   ```

## Quick Start

### Using the REPL

Start the interactive REPL to experiment with parsing and tokenization:

```bash
# Default AST mode - shows parsed Abstract Syntax Tree
python -m machine_dialect

# Token debug mode - shows lexical tokens
python -m machine_dialect --debug-tokens
```

Example session (AST mode):

```text
Machine Dialect REPL v0.1.0
Mode: AST Mode
Type 'exit' to exit, 'help' for help
--------------------------------------------------

md> Set **x** to _42_.

AST:
--------------------------------------------------
  Set `x` to _42_
--------------------------------------------------

md> if **user** equals _"admin"_ then give back _true_.

AST:
--------------------------------------------------
  if `user` equals _"admin"_ then:
> Give back _true_
--------------------------------------------------
```

Example session (Token debug mode):

```text
Machine Dialect REPL v0.1.0
Mode: Token Debug Mode
Type 'exit' to exit, 'help' for help
--------------------------------------------------

md> Set **x** to _42_.

Tokens (6):
--------------------------------------------------
  Type                 | Literal
--------------------------------------------------
  KW_SET               | 'Set'
  MISC_IDENT           | 'x'
  KW_TO                | 'to'
  LIT_INT              | '42'
  PUNCT_PERIOD         | '.'
  MISC_EOF             | ''
--------------------------------------------------
```

### Writing Your First Program

Create a file `hello.md`:

```markdown
---
exec: true
---
# Hello World

Set **greeting** to _"Hello"_.
Set **name** to _"World"_.

Say **greeting** + _", "_ + **name** + _"!"_.
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific component tests
python -m pytest machine_dialect/lexer/tests/ -v
python -m pytest machine_dialect/parser/tests/ -v

# Run with coverage
python -m pytest --cov=machine_dialect
```

### Code Quality Checks

```bash
# Type checking with MyPy
mypy machine_dialect --strict

# Linting and formatting with Ruff
ruff check machine_dialect
ruff format machine_dialect

# Run all pre-commit hooks
pre-commit run --all-files
```

### Development Workflow

1. **Activate virtual environment** before any development:

   ```bash
   source .venv/bin/activate
   ```

1. **Follow Test-Driven Development (TDD)**:

   - Write tests first
   - Implement to make tests pass
   - Refactor while keeping tests green

1. **Ensure type safety**:

   - All functions must have type annotations
   - MyPy must pass with `--strict` mode

1. **Run pre-commit hooks** before committing:

   - All hooks must pass
   - No exceptions or bypasses allowed

## Project Structure

```text
machine_dialect/
├── machine_dialect/         # Main Python package
│   ├── __main__.py         # Entry point for python -m machine_dialect
│   ├── ast/                # Abstract Syntax Tree implementation
│   │   ├── ast_node.py     # Base AST node class
│   │   ├── expressions.py  # Expression AST nodes (includes Arguments)
│   │   ├── literals.py     # Literal value nodes (int, float, string, boolean, empty)
│   │   ├── program.py      # Program AST node
│   │   └── statements.py   # Statement AST nodes (includes Call, Action, Interaction)
│   ├── errors/             # Error handling
│   │   ├── exceptions.py   # Custom exception hierarchy
│   │   └── messages.py     # Error message constants
│   ├── helpers/            # Helper utilities
│   │   ├── stopwords.py    # English stopword definitions
│   │   └── validators.py   # Validation utilities
│   ├── lexer/              # Lexical analysis
│   │   ├── constants.py    # Character-to-token mappings
│   │   ├── lexer.py        # Main lexer implementation
│   │   └── tokens.py       # Token type definitions
│   ├── linter/             # Machine Dialect linter
│   │   └── linter.py       # Linting rules
│   ├── parser/             # Syntax analysis
│   │   ├── enums.py        # Parser enums (precedence, etc.)
│   │   ├── parser.py       # Recursive descent parser
│   │   ├── protocols.py    # Type protocols
│   │   └── token_buffer.py # Token buffering
│   └── repl/               # Interactive REPL
│       └── repl.py         # REPL implementation
├── md_linter/              # Rust-based Markdown linter
│   ├── src/                # Rust source code
│   └── Cargo.toml          # Rust dependencies
├── docs/                   # Documentation
│   └── meta/               # Meta documentation
│       └── docstrings_guide.md  # Google docstrings guide
├── tests/                  # Test files (organized by component)
│   ├── lexer/              # Lexer tests
│   └── parser/             # Parser tests
├── .pre-commit-config.yaml # Pre-commit hook configuration
├── pyproject.toml          # Python project configuration
├── uv.lock                 # UV package manager lock file
├── CLAUDE.md              # AI assistant guidance
└── README.md              # This file
```

### Key Components

- **Lexer**: Streaming tokenizer that converts source text into tokens
- **Parser**: Recursive descent parser with Pratt parsing for expressions
- **AST**: Abstract syntax tree representing program structure
- **REPL**: Interactive environment with AST and token debug modes
- **Error Handler**: Structured error reporting with panic mode recovery
- **Type System**: Strict typing throughout with MyPy validation

## Contributing

We welcome contributions! Please follow these guidelines:

### Development Setup

1. Fork and clone the repository
1. Set up the development environment as described above
1. Create a feature branch: `git checkout -b feature-name`
1. Make your changes following TDD principles
1. Ensure all tests pass and pre-commit hooks succeed
1. Submit a pull request

### Code Standards

- **Test-Driven Development**: Write tests before implementation
- **Type Safety**: All code must be strictly typed
- **Documentation**: Google-style docstrings for all public APIs
- **Pre-commit Hooks**: Must pass before any commit
- **Commit Messages**: Follow conventional commit format

### Testing Requirements

- All new features must have comprehensive tests
- Maintain or improve code coverage
- Tests should be clear and serve as documentation

## Status

> ⚠️ **Alpha Stage**: This project is under active development. The syntax and implementation
> are evolving. Expect breaking changes.

## Acknowledgments

Machine Dialect is inspired by efforts to make programming more accessible and AI-friendly,
including natural language programming research and literate programming concepts.

______________________________________________________________________

For detailed development instructions, see [CLAUDE.md](CLAUDE.md).
For comprehensive examples, check the `examples/` directory (coming soon).
