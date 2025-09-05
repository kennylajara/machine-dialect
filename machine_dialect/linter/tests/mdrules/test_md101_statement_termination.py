"""Tests specifically for MD101: Statement Termination rule."""

import pytest

from machine_dialect.ast import ExpressionStatement, ReturnStatement, SetStatement
from machine_dialect.lexer import Token, TokenType
from machine_dialect.linter import Linter
from machine_dialect.linter.rules.base import Context
from machine_dialect.linter.rules.statement_termination import StatementTerminationRule
from machine_dialect.linter.violations import ViolationSeverity


class TestMD101StatementTermination:
    """Test MD101: Statement Termination rule."""

    def test_rule_metadata(self) -> None:
        """Test that MD101 has correct metadata."""
        rule = StatementTerminationRule()
        assert rule.rule_id == "MD101"
        assert "period" in rule.description.lower()
        assert "statement" in rule.description.lower()

    @pytest.mark.parametrize(
        ("source", "expected_violations"),
        [
            # Valid cases - no violations
            ("42.", 0),
            ("True.", 0),
            ("not False.", 0),
            ("-123.", 0),
            ("Set `x` to 42.", 0),
            ("give back 42.", 0),
            ("gives back True.", 0),
            # Valid cases - no period needed at EOF
            ("42", 0),
            ("True", 0),
            ("not False", 0),
            ("-123", 0),
            # Multiple statements
            ("42. True.", 0),
            # Note: These now generate parse errors, not MD101 violations
            # because periods are mandatory (except at EOF) at the parser level
            ("42\nTrue.", 0),  # Parse error, not MD101
            ("42.\nTrue", 0),  # Valid: second line at EOF
            ("42\nTrue", 0),  # Parse error, not MD101
        ],
    )
    def test_full_integration(self, source: str, expected_violations: int) -> None:
        """Test MD101 through the full linter integration."""
        linter = Linter()
        violations = linter.lint(source)

        # Filter for MD101 violations only
        md101_violations = [v for v in violations if v.rule_id == "MD101"]
        assert len(md101_violations) == expected_violations

        # All MD101 violations should be STYLE severity
        for violation in md101_violations:
            assert violation.severity == ViolationSeverity.STYLE
            assert "period" in violation.message.lower()

    def test_statements_with_complex_content(self) -> None:
        """Test MD101 with complex statement content."""
        rule = StatementTerminationRule()

        # Test with expression that has operators
        token = Token(TokenType.OP_MINUS, "-", line=1, position=0)
        node = ExpressionStatement(token=token, expression=None)

        # Source: "-42 + 5" (no period, at EOF - valid)
        context = Context("test.md", "-42 + 5")
        violations = rule.check(node, context)
        assert len(violations) == 0  # No period needed at EOF

        # Source: "-42 + 5." (with period)
        context = Context("test.md", "-42 + 5.")
        violations = rule.check(node, context)
        assert len(violations) == 0

    def test_set_statements(self) -> None:
        """Test MD101 specifically with Set statements."""
        rule = StatementTerminationRule()

        # Create a Set statement node
        token = Token(TokenType.KW_SET, "Set", line=1, position=0)
        node = SetStatement(token=token)

        # Test without period (at EOF - valid)
        context = Context("test.md", "Set `x` to 42")
        violations = rule.check(node, context)
        assert len(violations) == 0  # No period needed at EOF

        # Test with period
        context = Context("test.md", "Set `x` to 42.")
        violations = rule.check(node, context)
        assert len(violations) == 0

    def test_return_statements(self) -> None:
        """Test MD101 specifically with Return statements."""
        rule = StatementTerminationRule()

        # Create a Return statement node
        token = Token(TokenType.KW_RETURN, "give back", line=1, position=0)
        node = ReturnStatement(token=token)

        # Test without period (at EOF - valid)
        context = Context("test.md", "give back 42")
        violations = rule.check(node, context)
        assert len(violations) == 0  # No period needed at EOF

        # Test with period
        context = Context("test.md", "give back 42.")
        violations = rule.check(node, context)
        assert len(violations) == 0

    def test_multiline_source(self) -> None:
        """Test MD101 with multiline source code."""
        rule = StatementTerminationRule()

        source = """42.
True
-5.
not False"""

        # Test line 2 (True without period)
        token = Token(TokenType.LIT_YES, "True", line=2, position=0)
        node = ExpressionStatement(token=token, expression=None)
        context = Context("test.md", source)
        violations = rule.check(node, context)
        assert len(violations) == 1
        assert violations[0].line == 2

        # Test line 4 (not False without period, at EOF - valid)
        token = Token(TokenType.KW_NEGATION, "not", line=4, position=0)
        node = ExpressionStatement(token=token, expression=None)
        violations = rule.check(node, context)
        assert len(violations) == 0  # No period needed at EOF

    def test_fix_suggestion(self) -> None:
        """Test that MD101 provides fix suggestions."""
        rule = StatementTerminationRule()

        # Test with a statement not at EOF
        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=0)
        node = ExpressionStatement(token=token, expression=None)
        context = Context("test.md", "42\nTrue.")  # Not at EOF

        violations = rule.check(node, context)
        assert len(violations) == 1
        assert violations[0].fix_suggestion is not None
        assert "period" in violations[0].fix_suggestion.lower()

    def test_edge_cases(self) -> None:
        """Test MD101 edge cases."""
        rule = StatementTerminationRule()

        # Empty line
        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=0)
        node = ExpressionStatement(token=token, expression=None)
        context = Context("test.md", "")
        violations = rule.check(node, context)
        assert len(violations) == 0  # No crash on empty source

        # Line number out of bounds
        token = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=10, position=0)
        node = ExpressionStatement(token=token, expression=None)
        context = Context("test.md", "42")
        violations = rule.check(node, context)
        assert len(violations) == 0  # No crash on invalid line number

    def test_disabled_rule(self) -> None:
        """Test that MD101 can be disabled."""
        # Test with MD101 disabled
        config = {"rules": {"MD101": False}}
        linter = Linter(config)

        source = "42"  # Missing period
        violations = linter.lint(source)

        # Should have no violations since MD101 is disabled
        assert len(violations) == 0
