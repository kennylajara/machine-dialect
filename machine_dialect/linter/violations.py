"""Violation representation for the Machine Dialect™ linter.

This module defines the Violation class used to represent linting issues
found in Machine Dialect™ code.
"""

from dataclasses import dataclass
from enum import Enum

from machine_dialect.ast import ASTNode


class ViolationSeverity(Enum):
    """Severity levels for linting violations."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STYLE = "style"


@dataclass
class Violation:
    """Represents a linting violation found in Machine Dialect™ code.

    Attributes:
        rule_id: Unique identifier for the rule that was violated.
        message: Human-readable description of the violation.
        severity: The severity level of the violation.
        line: Line number where the violation occurred.
        column: Column number where the violation occurred.
        node: The AST node associated with the violation (optional).
        fix_suggestion: Suggested fix for the violation (optional).
    """

    rule_id: str
    message: str
    severity: ViolationSeverity
    line: int
    column: int
    node: ASTNode | None = None
    fix_suggestion: str | None = None

    def __str__(self) -> str:
        """Return a formatted string representation of the violation.

        Returns:
            A string in the format: "line:column severity rule_id: message"
        """
        location = f"{self.line}:{self.column}"
        return f"{location} {self.severity.value} {self.rule_id}: {self.message}"
