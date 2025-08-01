# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Project Status

Machine Dialect is a natural language programming project that allows writing code using more natural,
English-like syntax. The project includes a lexer implementation in Python and a Markdown linter in Rust.

## Development Notes

- The project uses Python for the main language implementation
- Test-Driven Development (TDD) is strictly followed
- A Rust-based Markdown linter is included for documentation quality

## Test-Driven Development (TDD)

**IMPORTANT**: This project follows Test-Driven Development (TDD) practices. When working on any implementation:

1. **ALWAYS check for existing tests first** before implementing any feature
1. Tests define the expected behavior - implementation must satisfy the tests
1. Never implement features without corresponding tests
1. If tests fail, fix the implementation to make them pass
1. The test-first approach ensures code quality and correct behavior

## Type Safety and MyPy

**CRITICAL**: This project maintains strict type safety. MyPy errors MUST be fixed before committing:

1. **NEVER disable MyPy checks** - strict typing is enforced for code quality
1. **ALL functions must have type annotations** - no exceptions
1. **Fix MyPy errors immediately** - do not postpone or work around them
1. Type safety prevents runtime errors and improves code maintainability

## Project Structure

```text
machine_dialect/
├── machine_dialect/          # Main Python package
│   ├── lexer/               # Lexer implementation
│   │   ├── __init__.py
│   │   ├── lexer.py         # Main lexer class
│   │   └── tokens.py        # TokenType enum and Token class
│   ├── repl/                # REPL implementation
│   │   ├── tests/           # REPL tests
│   │   │   ├── __init__.py
│   │   │   └── test_repl.py
│   │   ├── __init__.py
│   │   └── repl.py          # Interactive REPL for tokenization
│   └── __main__.py          # Entry point for python -m machine_dialect
├── md_linter/               # Rust-based Markdown linter
│   ├── src/
│   │   ├── main.rs
│   │   ├── config.rs
│   │   └── rules/          # Linting rules
│   │       ├── mod.rs
│   │       └── md013.rs
│   ├── Cargo.toml
│   └── Cargo.lock
├── pyproject.toml           # Python project configuration
├── uv.lock                  # UV package manager lock file
├── CLAUDE.md               # This file - AI assistant guidance
└── README.md               # Project documentation
```

## Getting Started

When working on this project:

1. **Python Development**: The main language implementation is in the `machine_dialect` package
1. **Testing**: Always check for existing tests before implementing features (TDD)
1. **Dependencies**: Use UV package manager for Python dependencies
1. **Linting**: The `md_linter` tool ensures documentation quality

## Development Environment

**IMPORTANT**: Always activate the virtual environment before running any Python commands:

```bash
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows
```

This is crucial for:

- Running tests
- Using development tools (pytest, ruff, mypy)
- Installing dependencies
- Running the application

After activating the virtual environment, install the package in editable mode:

```bash
uv pip install -e .
```

This ensures that `machine_dialect` can be imported in tests and scripts.

## Common Tasks

### Running Tests

```bash
source .venv/bin/activate
python -m pytest machine_dialect/lexer/tests/test_lexer.py -v
```

### Working with the Lexer

- Token types are defined in `machine_dialect/tokens/tokens.py`
- The lexer implementation is in `machine_dialect/lexer/lexer.py`
- All token types use prefixes: `KW_` for keywords, `OP_` for operators, `DELIM_` for delimiters, etc.
