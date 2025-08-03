# Machine Dialect Linter

A comprehensive linting tool for Machine Dialect code that helps maintain consistent code style
and catch common errors.

## Overview

The Machine Dialect linter analyzes your Machine Dialect code to:

- Enforce consistent coding style
- Detect syntax errors early
- Suggest improvements for code quality

## Installation

The linter is included with the Machine Dialect package. No separate installation is required.

```bash
# Install Machine Dialect (if not already installed)
uv pip install -e .
```

## Usage

### Command Line Interface

The linter can be run from the command line:

```bash
# Lint a single file
python -m machine_dialect.linter file.md

# Lint multiple files
python -m machine_dialect.linter file1.md file2.md

# List available rules
python -m machine_dialect.linter --list-rules

# Use a configuration file
python -m machine_dialect.linter -c .mdlint.json file.md

# Show only errors (quiet mode)
python -m machine_dialect.linter -q file.md
```

### Programmatic Usage

You can also use the linter programmatically in your Python code:

```python
from machine_dialect.linter import Linter

# Create a linter instance
linter = Linter()

# Lint source code
source = "42"
violations = linter.lint(source)

# Print violations
for violation in violations:
    print(f"{violation.line}:{violation.column} {violation.rule_id}: {violation.message}")

# Lint a file
violations = linter.lint_file("example.md")
```

## Architecture

The linter follows a modular architecture with these key components:

### Core Components

1. **Linter**: The main orchestrator that manages rules and runs the linting process
1. **Rule**: Abstract base class for all linting rules
1. **Violation**: Represents a linting issue found in the code
1. **Context**: Provides contextual information to rules during linting

### How It Works

1. **Parsing**: The linter first parses the Machine Dialect code into an Abstract Syntax Tree (AST)
1. **Visitor Pattern**: It traverses the AST using a visitor pattern
1. **Rule Application**: Each registered rule is applied to relevant AST nodes
1. **Violation Collection**: Rules return violations they find
1. **Reporting**: Violations are formatted and reported to the user

## Available Rules

### Rule Numbering Convention

Machine Dialect follows a specific numbering convention for linting rules:

- **MD001-MD099**: Reserved for traditional Markdown rules, designed to be compatible with
  [markdownlint](https://github.com/DavidAnson/markdownlint/tree/main)
- **MD101+**: Machine Dialect specific rules

This allows Machine Dialect files to be linted with both traditional Markdown linters and
Machine Dialect specific rules without conflicts.

### MD101: Statement Termination

**Description**: Statements must end with periods

**Severity**: STYLE

**Example**:

```markdown
# Bad
42
True

# Good
42.
True.
```

## Configuration

The linter can be configured using a JSON configuration file. Create a `.mdlint.json` file in
your project root:

```json
{
  "rules": {
    "MD101": true
  }
}
```

### Configuration Options

- `rules`: Object mapping rule IDs to boolean values (true = enabled, false = disabled)

## Creating Custom Rules

You can create custom linting rules by extending the `Rule` base class:

```python
from machine_dialect.ast import ASTNode
from machine_dialect.linter.rules.base import Rule, Context
from machine_dialect.linter.violations import Violation, ViolationSeverity

class MyCustomRule(Rule):
    @property
    def rule_id(self) -> str:
        return "CUSTOM001"

    @property
    def description(self) -> str:
        return "My custom rule description"

    def check(self, node: ASTNode, context: Context) -> list[Violation]:
        violations = []

        # Your rule logic here
        # Check the node and return violations if found

        return violations

# Add the rule to a linter
linter = Linter()
linter.add_rule(MyCustomRule())
```

## Violation Severities

The linter supports four severity levels:

1. **ERROR**: Critical issues that must be fixed
1. **WARNING**: Potential problems that should be reviewed
1. **INFO**: Informational messages
1. **STYLE**: Style and formatting issues

## Integration with Development Workflow

### Pre-commit Hook

You can integrate the linter into your Git workflow by adding it as a pre-commit hook:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run linter on staged Machine Dialect files
files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.md$')
if [ -n "$files" ]; then
    python -m machine_dialect.linter $files
    if [ $? -ne 0 ]; then
        echo "Linting failed. Please fix the issues before committing."
        exit 1
    fi
fi
```

### Continuous Integration

Add the linter to your CI pipeline:

```yaml
# GitHub Actions example
- name: Lint Machine Dialect code
  run: |
    python -m machine_dialect.linter **/*.md
```

## Testing

The linter includes comprehensive tests organized as follows:

```text
machine_dialect/linter/tests/
├── test_linter.py          # Core linter functionality tests
├── test_rules.py           # General rule testing
├── test_violations.py      # Violation class tests
└── mdrules/               # Rule-specific tests
    └── test_md101_statement_termination.py
    └── ...
```

Run tests with:

```bash
pytest machine_dialect/linter/tests/ -v
```

## Future Enhancements

The linter is designed to be extensible. Planned enhancements include:

- Additional built-in rules for common patterns
- Support for inline rule suppression comments
- Performance optimization for large files
- Integration with popular editors (VS Code, Vim, etc.)
- Support for YAML/TOML configuration files
- Automatic fix application (--fix flag)
- Rule categories and severity customization

## Contributing

When contributing new rules, please:

1. Follow the rule ID naming convention:
   - Use MD001-MD099 only for traditional Markdown compatibility rules
   - Use MD101+ for Machine Dialect specific rules
1. Include comprehensive tests in the `mdrules/` directory
1. Document the rule with clear examples
1. Ensure the rule has appropriate severity level
1. Add fix suggestions when possible

## API Reference

### Linter Class

```python
class Linter:
    def __init__(self, config: dict[str, Any] | None = None) -> None
    def add_rule(self, rule: Rule) -> None
    def lint(self, source_code: str, filename: str = "<stdin>") -> list[Violation]
    def lint_file(self, filepath: str) -> list[Violation]
```

### Rule Abstract Base Class

```python
class Rule(ABC):
    @property
    @abstractmethod
    def rule_id(self) -> str

    @property
    @abstractmethod
    def description(self) -> str

    @abstractmethod
    def check(self, node: ASTNode, context: Context) -> list[Violation]

    def is_enabled(self, config: dict[str, Any]) -> bool
```

### Violation Class

```python
@dataclass
class Violation:
    rule_id: str
    message: str
    severity: ViolationSeverity
    line: int
    column: int
    node: ASTNode | None = None
    fix_suggestion: str | None = None
```

## License

The Machine Dialect linter is part of the Machine Dialect project and shares its license.
