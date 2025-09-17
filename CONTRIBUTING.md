# Contributing to Machine Dialect™

Thank you for your interest in contributing to Machine Dialect™.\
This guide will help you get started.

## ⚠️ ALPHA PROJECT - BREAKING CHANGES WELCOME ⚠️

> Machine Dialect™ is in ALPHA stage. We encourage breaking changes that improve the design.
> Don't worry about backward compatibility - prioritize correctness and innovation.

## Getting Started

### Prerequisites

- Python (supported version - see [SECURITY.md](SECURITY.md#supported-versions))
- Git
- UV package manager (required - never use pip directly)

### Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/kennylajara/machine-dialect.git
   cd machine-dialect
   ```

2. **Activate virtual environment**

   ```bash
   source .venv/bin/activate  # Linux/Mac/WSL
   # or
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**

   ```bash
   uv sync
   uv pip install -e .
   ```

4. **Verify setup**

   ```bash
   python -m pytest
   mypy machine_dialect --strict
   pre-commit run --all-files
   ```

## Development Workflow

### 1. Code Quality Standards

#### Type Safety

- All functions must have type annotations
- MyPy must pass with `--strict` flag
- Never disable type checking

#### Testing Requirements

1. All features must have comprehensive test coverage
2. Write tests that validate expected behavior
3. Include edge cases and error conditions
4. Run tests frequently during development
5. Ensure all tests pass before committing

#### Documentation

- Google-style docstrings for all modules, classes, and functions
- See `docs/meta/docstrings_guide.md` for examples
- Include Args, Returns, Raises sections where applicable

#### Pre-commit Hooks

All commits must pass pre-commit checks:

- MyPy type checking
- Ruff linting and formatting
- Markdownlint for documentation
- Conventional commit messages

### 2. Making Changes

1. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement feature with tests**
   - Follow existing code patterns
   - Maintain consistency with architecture
   - Add comprehensive docstrings
   - Create tests in appropriate test directory
   - e.g., `machine_dialect/lexer/tests/test_your_feature.py`

3. **Run tests and checks**

   ```bash
   python -m pytest
   mypy machine_dialect --strict
   ruff check machine_dialect
   pre-commit run --all-files
   ```

4. **Commit changes**

   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

## Code Organization

### Directory Structure

```text
machine_dialect/
├── agent/          # AI agent integration
├── ast/            # Abstract Syntax Tree
├── cfg/            # Control Flow Graph
├── codegen/        # Code generation
├── compiler/       # Compilation pipeline
│   └── phases/     # HIR, MIR, optimization, codegen
├── errors/         # Error handling
├── helpers/        # Utility functions
├── lexer/          # Tokenization
├── linter/         # Code linting
├── mir/            # Mid-level IR
│   └── optimizations/  # Optimization passes
├── parser/         # Parsing to AST
├── repl/           # Interactive REPL
├── semantic/       # Semantic analysis
├── tests/          # Integration tests
└── type_checking/  # Type system

machine_dialect_vm/
├── src/
│   ├── bindings/   # Python bindings
│   ├── errors/     # VM error handling
│   ├── instructions/ # Bytecode instructions
│   ├── loader/     # Bytecode loader
│   ├── memory/     # Memory management
│   ├── runtime/    # Runtime system
│   ├── values/     # Value types
│   └── vm/         # Virtual machine core
```

### Key Components

- **Lexer**: Converts source text to tokens
- **Parser**: Builds AST from tokens using recursive descent
- **AST**: Tree representation of program structure
- **HIR**: High-level intermediate representation
- **MIR**: SSA-based mid-level IR for optimization
- **Codegen**: Generates bytecode from MIR
- **VM**: Executes bytecode

## Testing

### Running Tests

```bash
# All tests
python -m pytest

# Specific component
python -m pytest machine_dialect/lexer/tests/ -v

# With coverage
python -m pytest --cov=machine_dialect
```

### Writing Tests

- Place tests in `tests/` subdirectories within each module
- Use descriptive test names: `test_feature_specific_behavior`
- Test both success and error cases
- Include edge cases and boundary conditions

## Commit Guidelines

We use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

Examples:

```bash
git commit -m "feat: add support for while loops"
git commit -m "fix: handle empty literals in parser"
git commit -m "docs: update lexer documentation"
```

## Submitting Pull Requests

1. **Ensure all checks pass**

   ```bash
   pre-commit run --all-files
   python -m pytest
   ```

2. **Update documentation** if needed

3. **Create pull request**
   - Clear description of changes
   - Reference any related issues
   - Include test results

4. **Address review feedback** promptly

## Language Syntax

When adding language features, follow these conventions:

- **Variables**: Use backticks: `` `variable` ``
- **Literals**: Use italics: `_value_`
- **Keywords**: Case-insensitive English words
- **Blocks**: Indent with `>` markers
- **Math**: LaTeX syntax in `$$...$$` (not supported yet)

## Getting Help

- Check existing issues on GitHub
- Review CLAUDE.md for development guidelines
- Look at existing code for patterns
- Ask questions in pull request discussions

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Questions?

Feel free to open an issue for any questions about contributing!
