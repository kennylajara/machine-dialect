# Machine Dialect (.md)

**Machine Dialect** is a programming language designed to look like natural language and feel like
structured documentation. It is written in Markdown and intended to be both human-friendly and AI-
native — readable by people, generatable and parsable by machines.

## Why?

Modern programming languages were made for humans to instruct machines. But now that machines can
understand and generate human-like language, it’s time to rethink the language itself.

Machine Dialect is for a future where:

- **AI writes most of the code**, and humans supervise, modify, and approve.
- Code is **visually readable**, even by non-programmers.
- The structure of the program is as **intuitive as a document**, and lives comfortably inside
  Markdown files.

## Philosophy

- ✍️ **Natural structure**: Programs are written as paragraphs, headings, lists — not brackets,
  semicolons, and cryptic symbols.
- 🧠 **AI-first**: Syntax is deterministic enough for parsing, but optimized for LLMs to generate and
  understand effortlessly.
- 👁️ **Human-supervisable**: Markdown keeps everything readable, diffable, and renderable.
- 🪶 **Lightweight**: No ceremony. Just write it like you'd explain it.
- 📐 **Math as code**: Mathematical operations are expressed using LaTeX syntax inside `$$...$$`
  blocks. This keeps formulas readable, renderable, and easy to evaluate with symbolic math engines
  like SymPy or MathJax.
- 🏷️ **Metadata-aware**: Executable files begin with a YAML frontmatter block (`---`) that declares
  intent (e.g. `exec: true`). This convention is widely supported by other tools and safely ignored by
  standard Markdown renderers, making it easy to difference executable files from context-only files.

## Features

- Functions are declared using Markdown headers.
- Each sentence is an instruction — terminated with a period.
- Markdown lists represent arrays or sets depending on.
- Key-value pairs are written like definitions: `**Label**: Value`.
- Variables, values, and calls are identified with lightweight formatting rules (e.g. **bold** for
  variables, _italics_ for constants).
- All source files are `.md` and can be opened in any Markdown editor.

## Example

```markdown
---
exec: true
---
# Shopping Calculator

## Initialize variables
Set **total** to _0_.
Set **item count** to _0_.

## Items
- Banana: _15_
- Toothpaste: _30_
- Notebook: _120_

## Compute total
Add all **Items** values to **total**.
Count all **Items**, store _them_ in **item count**.
Apply formula:

$$
\text{average} = \frac{\text{total}}{\text{itemCount}}
$$

## Results
Print: "You have spent: " + **total**.
Print: "Average per item: " + **average**.
```

## How It Works

- Markdown structure defines the hierarchy.
- The interpreter parses sentences line by line and infers instructions.
- AI models can generate this structure with very little training.
- Humans can preview and edit it using standard Markdown tools.

## Project Structure

```text
machine_dialect/
├── machine_dialect/         # Main Python package
│   ├── __main__.py          # Entry point for python -m machine_dialect
│   ├── ast/                 # Abstract Syntax Tree implementation
│   │   ├── __init__.py
│   │   ├── ast_node.py      # Base AST node class
│   │   ├── expressions.py   # Expression AST nodes
│   │   ├── program.py       # Program AST node
│   │   └── statements.py    # Statement AST nodes
│   ├── helpers/             # Helper utilities
│   │   ├── __init__.py
│   │   └── validators.py    # Validation utilities
│   ├── lexer/               # Lexer implementation
│   │   ├── __init__.py
│   │   ├── lexer.py         # Main lexer class
│   │   ├── tests/           # Lexer tests
│   │   │   ├── __init__.py
│   │   │   ├── test_lexer.py         # Main lexer tests
│   │   │   └── test_url_literals.py  # URL literal tests
│   │   └── tokens.py        # TokenType enum and Token class definitions
│   ├── parser/              # Parser implementation
│   │   ├── __init__.py
│   │   ├── parser.py        # Main parser class
│   │   └── tests/           # Parser tests
│   │       ├── __init__.py
│   │       ├── test_program.py         # Program parsing tests
│   │       └── test_set_statements.py  # Set statement tests
│   └── repl/                # REPL implementation
│       ├── __init__.py
│       ├── repl.py          # Interactive REPL for tokenization
│       └── tests/           # REPL tests
│           ├── __init__.py
│           └── test_repl.py
├── machine_dialect.egg-info/  # Python package metadata
├── md_linter/               # Rust-based Markdown linter
│   ├── src/
│   │   ├── main.rs
│   │   ├── config.rs
│   │   └── rules/          # Linting rules
│   │       ├── mod.rs
│   │       └── md013.rs
│   ├── target/              # Rust build artifacts (gitignored)
│   ├── Cargo.toml
│   └── Cargo.lock
├── pyproject.toml           # Python project configuration
├── uv.lock                  # UV package manager lock file
├── CLAUDE.md               # AI assistant guidance
└── README.md               # This file
```

### Key Components

- **Lexer**: Tokenizes Machine Dialect source code into structured tokens
- **Tokens**: Defines all token types with clear prefixes (KW_for keywords, OP\_ for operators, etc.)
- **Tests**: Comprehensive test suite following Test-Driven Development (TDD)
- **MD Linter**: Ensures consistent formatting of Machine Dialect source files

## Status

> ⚠️ This project is a prototype. We're exploring syntax design, parsing strategies, and possible
> runtimes. Expect breaking changes. Contributions welcome.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- UV package manager for Python
- Rust (optional, for the Markdown linter)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/machine_dialect.git
   cd machine_dialect
   ```

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

1. Install dependencies:

   ```bash
   uv sync
   ```

### Running Tests

```bash
python -m pytest machine_dialect/lexer/tests/test_lexer.py -v
```

### Using the REPL

Start the interactive REPL to tokenize Machine Dialect code:

```bash
python -m machine_dialect
# or
python machine_dialect/repl/repl.py
```

Example REPL session:

```text
md> if x > 0 then return true

Tokens (7):
--------------------------------------------------
  Type                 | Literal
--------------------------------------------------
  KW_IF                | 'if'
  MISC_IDENT           | 'x'
  OP_GT                | '>'
  LIT_INT              | '0'
  KW_THEN              | 'then'
  MISC_IDENT           | 'return'
  KW_TRUE              | 'true'
--------------------------------------------------
```

## Goals

- Define a minimal, deterministic grammar.
- Build a compiler and/or interpreter in Python.
- Support a virtual machine or bytecode executor.
- Eventually: build a Rust-based interpreter for performance.
