# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Machine Dialect is a natural language programming language that allows writing code using
English-like syntax in Markdown files (`.md`). It's designed to be AI-first,
human-supervisable, and uses natural document structure instead of traditional programming
syntax.

## Critical Development Requirements

### 1. Test-Driven Development (TDD) - MANDATORY

**ALWAYS follow TDD strictly**:

1. Check for existing tests BEFORE implementing any feature
1. Tests define expected behavior - implementation must satisfy tests
1. Never implement features without corresponding tests
1. If tests fail, fix the implementation (not the tests)

### 2. Type Safety - NO EXCEPTIONS

**ALL code MUST be strictly typed**:

1. NEVER disable MyPy checks
1. ALL functions require type annotations
1. Fix MyPy errors immediately - no workarounds
1. MyPy runs with `--strict` mode

### 3. Pre-commit Hooks - ABSOLUTELY CRITICAL

**NEVER skip or bypass pre-commit hooks**:

1. ALL hooks must pass before ANY commit
1. Includes: MyPy, Ruff, pyupgrade, markdownlint, mdformat, conventional commits
1. Fix all issues immediately - no exceptions
1. The codebase must always be in a clean state

### 4. Documentation Standards

**Google-style docstrings are MANDATORY**:

1. Add docstrings to ALL modules, classes, methods, and functions
1. Follow guide at `docs/meta/docstrings_guide.md`
1. Include: Args, Returns, Raises, Examples sections
1. Don't repeat type information (already in annotations)

## Development Commands

### Setup Environment

```bash
# Always activate virtual environment first
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install package in editable mode
uv pip install -e .
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest machine_dialect/lexer/tests/test_lexer.py -v

# Run parser tests
python -m pytest machine_dialect/parser/tests/test_parser.py -v
```

### Code Quality Checks

```bash
# Run MyPy type checking
mypy machine_dialect --strict

# Run Ruff linting and formatting
ruff check machine_dialect
ruff format machine_dialect

# Run all pre-commit hooks
pre-commit run --all-files
```

### Running the REPL

```bash
# Start interactive REPL in AST mode (default)
python -m machine_dialect

# Start REPL in token debug mode
python -m machine_dialect --debug-tokens
```

## Architecture & Key Components

### Core Language Implementation

1. **Lexer** (`machine_dialect/lexer/`)

   - `tokens.py`: TokenType enum with prefixed naming (`KW_`, `OP_`, `DELIM_`)
   - `lexer.py`: Streaming lexer that generates tokens one at a time
   - Handles natural language keywords (e.g., "is greater than" → OP_GT)
   - Case-insensitive keyword recognition

1. **Parser** (`machine_dialect/parser/`)

   - `parser.py`: Recursive descent parser with Pratt parsing for expressions
   - `token_buffer.py`: Efficient token buffering
   - Supports if statements, blocks (marked with '>'), expressions
   - Panic mode error recovery

1. **AST** (`machine_dialect/ast/`)

   - `ast_node.py`: Base ASTNode abstract class
   - `expressions.py`: Expression nodes (literals, identifiers, operators, arguments)
   - `literals.py`: Literal nodes (integer, float, string, boolean, empty)
   - `statements.py`: Statement nodes (set, give back, if, action, interaction, call)
   - All nodes implement string representation for debugging

1. **Error Handling** (`machine_dialect/errors/`)

   - Custom exception hierarchy with structured error messages
   - Parser supports panic mode recovery

### Language Syntax Features

- **Markdown-based**: Source files are `.md` with YAML frontmatter
- **Variables**: Backticks (`` `variable` ``)
- **Literals**: Italic text (`_value_`), including `empty` for null values
- **Blocks**: Indented with '>' markers for if/else bodies
- **Math**: LaTeX syntax in `$$...$$` blocks
- **Operators**: Symbolic (+, -, \*, /, \<, >, \<=, >=) and natural language forms
  - Value equality: `equals`, `is equal to`, `is the same as`
  - Value inequality: `is not equal to`, `does not equal`, `is different from`
  - Strict equality: `is strictly equal to`, `is exactly equal to`, `is identical to`
  - Strict inequality: `is not strictly equal to`, `is not exactly equal to`, `is not identical to`
- **Statements**:
  - Set: `` Set `variable` to _value_. ``
  - Return: `Give back _value_.` or `Gives back _value_.`
  - Call: `` Call `function` [with arguments]. ``
  - Actions/Interactions: Support parameters with types and default values

### Testing Structure

Tests are organized by component in `tests/` subdirectories:

- **Lexer tests**: Token recognition, keywords, operators, literals
- **Parser tests**: Statement parsing, expression parsing, error recovery
- **AST tests**: Node representations, string formatting
- **Integration tests**: End-to-end functionality

## Important Implementation Notes

1. **Token Prefixes**: All TokenType values use consistent prefixes:

   - `KW_` for keywords (if, then, else, set, to, give back/gives back, call, with, action,
     interaction, empty)
   - `OP_` for operators (+, -, \*, /, \<, >, \<=, >=, equality/inequality, strict equality/inequality)
   - `DELIM_` for delimiters (parentheses, braces)
   - `PUNCT_` for punctuation (period, comma, colon, semicolon, hash)
   - `LIT_` for literals (int, float, text, boolean, url)
   - `MISC_` for miscellaneous (eof, illegal, ident, stopword, comment)

1. **Parser State**: Parser maintains:

   - Current/peek tokens via TokenBuffer
   - Error recovery with panic mode
   - Position tracking for error messages

1. **Stopwords**: Common English words (a, an, the, is, are) are recognized but typically
   ignored in parsing

1. **Case Sensitivity**: Keywords are case-insensitive, identifiers preserve case

## Package Management

- **UV**: Primary package manager (`uv sync`, `uv pip install`)
- **Python 3.12+** required
- **Dependencies**: rfc3986 (URL validation)
- **Dev tools**: pytest, mypy, ruff, pre-commit, pyupgrade

## Auxiliary Tools

### Rust Markdown Linter (`md_linter/`)

Separate Rust tool for Markdown quality checks (MD013 line length rule).

```bash
cd md_linter
cargo build --release
./target/release/md_linter ../docs/
```

### Python Linter (`machine_dialect/linter/`)

Rule-based linter for Machine Dialect code validation.

## Development Focus

When implementing new features, always:

1. Find or write tests first
1. Ensure MyPy passes with --strict
1. Add comprehensive docstrings
1. Run pre-commit hooks before any commit
