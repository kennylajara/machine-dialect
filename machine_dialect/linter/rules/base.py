"""Base rule class for Machine Dialect™ linting rules.

This module defines the abstract base class that all linting rules
must inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any

from machine_dialect.ast import ASTNode
from machine_dialect.linter.violations import Violation


class Context:
    """Context information passed to rules during linting.

    Attributes:
        filename: The name of the file being linted.
        source_lines: The source code split into lines.
        parent_stack: Stack of parent nodes for context.
    """

    def __init__(self, filename: str, source_code: str) -> None:
        """Initialize the linting context.

        Args:
            filename: The name of the file being linted.
            source_code: The complete source code.
        """
        self.filename = filename
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.parent_stack: list[ASTNode] = []

    def push_parent(self, node: ASTNode) -> None:
        """Push a parent node onto the stack.

        Args:
            node: The parent node to push.
        """
        self.parent_stack.append(node)

    def pop_parent(self) -> ASTNode | None:
        """Pop a parent node from the stack.

        Returns:
            The popped parent node, or None if stack is empty.
        """
        return self.parent_stack.pop() if self.parent_stack else None

    @property
    def current_parent(self) -> ASTNode | None:
        """Get the current parent node without removing it.

        Returns:
            The current parent node, or None if stack is empty.
        """
        return self.parent_stack[-1] if self.parent_stack else None


class Rule(ABC):
    """Abstract base class for linting rules.

    All linting rules must inherit from this class and implement
    the required methods.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Return the unique identifier for this rule.

        Returns:
            A string identifier like "MD001" or "style-naming".
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description of what this rule checks.

        Returns:
            A description of the rule's purpose.
        """
        pass

    @abstractmethod
    def check(self, node: ASTNode, context: Context) -> list[Violation]:
        """Check the given AST node for violations of this rule.

        Args:
            node: The AST node to check.
            context: The linting context with additional information.

        Returns:
            A list of violations found, or empty list if none.
        """
        pass

    def is_enabled(self, config: dict[str, Any]) -> bool:
        """Check if this rule is enabled in the configuration.

        Args:
            config: The linter configuration dictionary.

        Returns:
            True if the rule is enabled, False otherwise.
        """
        # By default, rules are enabled unless explicitly disabled
        rules_config = config.get("rules", {})
        return rules_config.get(self.rule_id, True) is not False
