# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Project Status

Machine Dialect is a natural language programming project that allows writing code using more
natural,
English-like syntax. The project includes a lexer implementation in Python and a Markdown linter
in Rust.

## Development Notes

- The project uses Python for the main language implementation
- Test-Driven Development (TDD) is strictly followed
- A Rust-based Markdown linter is included for documentation quality

## Test-Driven Development (TDD)

**IMPORTANT**: This project follows Test-Driven Development (TDD) practices. When working on any
implementation:

1. **ALWAYS check for existing tests first** before implementing any feature
1. Tests define the expected behavior - implementation must satisfy the tests
1. Never implement features without corresponding tests
1. If tests fail, fix the implementation to make them pass
1. The test-first approach ensures code quality and correct behavior

## Type Safety and MyPy

**CRITICAL**: This project maintains strict type safety. MyPy errors MUST be fixed before
committing:

1. **NEVER disable MyPy checks** - strict typing is enforced for code quality
1. **ALL functions must have type annotations** - no exceptions
1. **Fix MyPy errors immediately** - do not postpone or work around them
1. Type safety prevents runtime errors and improves code maintainability

## Pre-commit Hooks and Code Quality

**ABSOLUTELY CRITICAL - NO EXCEPTIONS**: All pre-commit hooks MUST pass before ANY code changes:

1. **NEVER SKIP PRE-COMMIT HOOKS** - This is an absolute requirement, no matter what
1. **MyPy MUST ALWAYS PASS** - No type errors are acceptable under any circumstances
1. **ALL pre-commit checks are MANDATORY** - Including but not limited to:
   - MyPy type checking
   - Ruff formatting and linting
   - Test execution
   - Any other configured hooks
1. **DO NOT BYPASS OR DISABLE** any pre-commit hooks, even temporarily
1. **FIX ALL ISSUES IMMEDIATELY** - If pre-commit fails, fix the issues before proceeding
1. **NO COMMITS WITH FAILING CHECKS** - The codebase must always be in a clean state

Remember: Pre-commit hooks exist to maintain code quality. Skipping them defeats their purpose and
compromises the integrity of the codebase.

## Documentation Standards

**MANDATORY**: All Python code in this project MUST include comprehensive docstrings following
Google style:

1. **ALWAYS add docstrings** to all modules, classes, methods, and functions
1. **Follow Google style docstrings** as documented in `docs/meta/google_docstrings_guide.md`
1. **Include all relevant sections**: Args, Returns, Raises, Examples, etc.
1. **With type annotations**, don't repeat type information in docstrings
1. **Document all public APIs** - no exceptions

See the complete guide at `docs/meta/google_docstrings_guide.md` for detailed examples and
formatting requirements.

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
