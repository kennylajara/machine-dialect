"""Main linter class for Machine Dialect™.

This module provides the main Linter class that orchestrates the
linting process by running rules against an AST.
"""

from typing import Any

from machine_dialect.ast import (
    ASTNode,
    ExpressionStatement,
    PrefixExpression,
    Program,
    ReturnStatement,
    SetStatement,
)
from machine_dialect.linter.rules import Rule
from machine_dialect.linter.rules.base import Context
from machine_dialect.linter.violations import Violation, ViolationSeverity
from machine_dialect.parser import Parser


class Linter:
    """Main linter class that runs rules against Machine Dialect™ code.

    The linter uses a visitor pattern to traverse the AST and apply
    registered rules to each node.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the linter with optional configuration.

        Args:
            config: Configuration dictionary for the linter.
        """
        self.config = config or {}
        self.rules: list[Rule] = []
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        """Register the default set of linting rules."""
        # Import rules here to avoid circular imports
        from machine_dialect.linter.rules.statement_termination import StatementTerminationRule

        # Add default rules
        self.add_rule(StatementTerminationRule())

    def add_rule(self, rule: Rule) -> None:
        """Add a linting rule to the linter.

        Args:
            rule: The rule instance to add.
        """
        if rule.is_enabled(self.config):
            self.rules.append(rule)

    def lint(self, source_code: str, filename: str = "<stdin>") -> list[Violation]:
        """Lint the given source code.

        Args:
            source_code: The Machine Dialect™ source code to lint.
            filename: The filename for error reporting.

        Returns:
            A list of violations found in the code.
        """
        # Parse the source code
        parser = Parser()
        program = parser.parse(source_code)

        # Include parse errors as violations
        violations: list[Violation] = []
        for error in parser.errors:
            violations.append(
                Violation(
                    rule_id="parse-error",
                    message=str(error),
                    severity=ViolationSeverity.ERROR,
                    line=error._line,
                    column=error._column,
                )
            )

        # If there are parse errors, don't run other rules
        if violations:
            return violations

        # Create context
        context = Context(filename, source_code)

        # Visit the AST and collect violations
        violations.extend(self._visit_node(program, context))

        return violations

    def _visit_node(self, node: ASTNode | None, context: Context) -> list[Violation]:
        """Visit an AST node and its children, applying rules.

        Args:
            node: The AST node to visit.
            context: The linting context.

        Returns:
            A list of violations found.
        """
        if node is None:
            return []

        violations: list[Violation] = []

        # Apply all rules to this node
        for rule in self.rules:
            violations.extend(rule.check(node, context))

        # Visit children based on node type
        context.push_parent(node)

        if isinstance(node, Program):
            for statement in node.statements:
                violations.extend(self._visit_node(statement, context))

        elif isinstance(node, SetStatement):
            violations.extend(self._visit_node(node.name, context))
            violations.extend(self._visit_node(node.value, context))

        elif isinstance(node, ReturnStatement):
            # ReturnStatement doesn't have a value attribute yet (TODO)
            # violations.extend(self._visit_node(node.value, context))
            pass

        elif isinstance(node, ExpressionStatement):
            violations.extend(self._visit_node(node.expression, context))

        elif isinstance(node, PrefixExpression):
            violations.extend(self._visit_node(node.right, context))

        # Literals and identifiers have no children to visit

        context.pop_parent()
        return violations

    def lint_file(self, filepath: str) -> list[Violation]:
        """Lint a file by reading its contents and running the linter.

        Args:
            filepath: Path to the file to lint.

        Returns:
            A list of violations found in the file.
        """
        with open(filepath, encoding="utf-8") as f:
            source_code = f.read()

        return self.lint(source_code, filepath)
