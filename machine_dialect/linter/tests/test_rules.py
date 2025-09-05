"""Tests for individual linting rules."""

from machine_dialect.ast import ExpressionStatement, WholeNumberLiteral
from machine_dialect.lexer import Token, TokenType
from machine_dialect.linter.rules.base import Context
from machine_dialect.linter.rules.statement_termination import StatementTerminationRule
from machine_dialect.linter.violations import ViolationSeverity


class TestStatementTerminationRule:
    """Test the statement termination rule."""

    def test_rule_properties(self) -> None:
        """Test rule ID and description."""
        rule = StatementTerminationRule()
        assert rule.rule_id == "MD101"
        assert "period" in rule.description.lower()

    def test_valid_statement_with_period(self) -> None:
        """Test that statements ending with periods pass."""
        rule = StatementTerminationRule()

        # Create a mock expression statement
        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=1)
        node = ExpressionStatement(token=token, expression=WholeNumberLiteral(token=token, value=42))

        # Create context with source that has a period
        context = Context("test.md", "42.")

        violations = rule.check(node, context)
        assert len(violations) == 0

    def test_missing_period(self) -> None:
        """Test that statements without periods at EOF are valid."""
        rule = StatementTerminationRule()

        # Create a mock expression statement
        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=1)
        node = ExpressionStatement(token=token, expression=WholeNumberLiteral(token=token, value=42))

        # Create context with source that lacks a period (at EOF - valid)
        context = Context("test.md", "42")

        violations = rule.check(node, context)
        assert len(violations) == 0  # No period needed at EOF

        # Test with statement not at EOF (should have violation)
        context = Context("test.md", "42\n100.")
        violations = rule.check(node, context)
        assert len(violations) == 1
        assert violations[0].rule_id == "MD101"
        assert violations[0].severity == ViolationSeverity.STYLE
        assert violations[0].line == 1

    def test_multiple_statements_on_line(self) -> None:
        """Test handling of multiple statements on one line."""
        rule = StatementTerminationRule()

        # First statement in "42. 100"
        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=1)
        node = ExpressionStatement(token=token, expression=WholeNumberLiteral(token=token, value=42))

        context = Context("test.md", "42. 100")

        # First statement has a period, so no violation
        violations = rule.check(node, context)
        assert len(violations) == 0

    def test_statement_with_whitespace(self) -> None:
        """Test statements with trailing whitespace."""
        rule = StatementTerminationRule()

        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=1)
        node = ExpressionStatement(token=token, expression=WholeNumberLiteral(token=token, value=42))

        # Test with trailing whitespace but no period (at EOF - valid)
        context = Context("test.md", "42   ")

        violations = rule.check(node, context)
        assert len(violations) == 0  # No period needed at EOF

    def test_non_statement_nodes(self) -> None:
        """Test that non-statement nodes are ignored."""
        rule = StatementTerminationRule()

        # Test with a literal node (not a statement)
        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=1)
        node = WholeNumberLiteral(token=token, value=42)

        context = Context("test.md", "42")

        # Should not check non-statement nodes
        violations = rule.check(node, context)
        assert len(violations) == 0

    def test_rule_enabled_by_default(self) -> None:
        """Test that rules are enabled by default."""
        rule = StatementTerminationRule()
        assert rule.is_enabled({})
        assert rule.is_enabled({"rules": {}})

    def test_rule_can_be_disabled(self) -> None:
        """Test that rules can be disabled in config."""
        rule = StatementTerminationRule()

        config = {"rules": {"MD101": False}}
        assert not rule.is_enabled(config)

        config = {"rules": {"MD101": True}}
        assert rule.is_enabled(config)
