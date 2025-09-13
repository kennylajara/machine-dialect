"""Statement termination rule for Machine Dialect™.

This rule checks that all statements are properly terminated with periods.
"""

from machine_dialect.ast import (
    ASTNode,
    ExpressionStatement,
    ReturnStatement,
    SetStatement,
)
from machine_dialect.linter.rules.base import Context, Rule
from machine_dialect.linter.violations import Violation, ViolationSeverity


class StatementTerminationRule(Rule):
    """Check that all statements end with periods.

    Machine Dialect™ requires statements to be terminated with periods.
    This rule checks that the source code follows this convention.
    """

    @property
    def rule_id(self) -> str:
        """Return the rule identifier."""
        return "MD101"

    @property
    def description(self) -> str:
        """Return the rule description."""
        return "Statements must end with periods"

    def check(self, node: ASTNode, context: Context) -> list[Violation]:
        """Check if statements are properly terminated.

        Args:
            node: The AST node to check.
            context: The linting context.

        Returns:
            A list of violations found.
        """
        violations: list[Violation] = []

        # Only check statement nodes
        if not isinstance(node, SetStatement | ReturnStatement | ExpressionStatement):
            return violations

        # Get the token that represents this statement
        token = node.token
        if not token:
            return violations

        # Find the line in the source code
        if token.line <= len(context.source_lines):
            line = context.source_lines[token.line - 1]

            # Find where this statement likely ends
            # This is a simplified check - in reality we'd need more sophisticated logic
            # For now, check if there's a period after the statement

            # Skip if this is not the last statement on the line
            # (simplified check - just look for period somewhere after the token position)
            remaining_line = line[token.position :]

            # Check if there's any non-whitespace after the statement before a period
            found_period = False
            found_content = False

            for char in remaining_line:
                if char == ".":
                    found_period = True
                    break
                elif not char.isspace():
                    found_content = True

            # If we found content but no period, it's likely missing termination
            # This is a heuristic and may have false positives
            # Exception: statements at EOF don't require periods
            is_last_line = token.line == len(context.source_lines)
            is_last_statement_on_line = not any(
                line[i:].strip() for i in range(token.position + len(remaining_line.rstrip()), len(line))
            )
            is_at_eof = is_last_line and is_last_statement_on_line

            if found_content and not found_period and not is_at_eof:
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        message="Statement should end with a period",
                        severity=ViolationSeverity.STYLE,
                        line=token.line,
                        column=token.position + len(remaining_line.rstrip()),
                        node=node,
                        fix_suggestion="Add a period at the end of the statement",
                    )
                )

        return violations
