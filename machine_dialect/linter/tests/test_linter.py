"""Tests for the main linter functionality."""

from pathlib import Path

from machine_dialect.linter import Linter, Violation, ViolationSeverity


class TestLinter:
    """Test the main Linter class."""

    def test_linter_initialization(self) -> None:
        """Test that linter initializes with default rules."""
        linter = Linter()
        assert len(linter.rules) > 0
        assert any(rule.rule_id == "MD101" for rule in linter.rules)

    def test_linter_with_config(self) -> None:
        """Test linter initialization with configuration."""
        config = {"rules": {"MD101": False}}
        linter = Linter(config)

        # MD101 should not be in the rules list
        assert not any(rule.rule_id == "MD101" for rule in linter.rules)

    def test_lint_parse_errors(self) -> None:
        """Test that parse errors are reported as violations."""
        source = "* 42"  # Invalid - no prefix parse function for *

        linter = Linter()
        violations = linter.lint(source)

        assert len(violations) > 0
        assert any(v.rule_id == "parse-error" for v in violations)
        assert any(v.severity == ViolationSeverity.ERROR for v in violations)

    def test_lint_stops_on_parse_errors(self) -> None:
        """Test that linter doesn't run rules when there are parse errors."""
        source = "* 42"  # Parse error

        # Even with missing period, we should only get parse errors
        linter = Linter()
        violations = linter.lint(source)

        # All violations should be parse errors
        assert all(v.rule_id == "parse-error" for v in violations)

    def test_lint_file(self, tmp_path: Path) -> None:
        """Test linting a file from disk."""
        # Create a temporary file
        test_file = tmp_path / "test.md"
        test_file.write_text("42.")

        linter = Linter()
        violations = linter.lint_file(str(test_file))

        # Should have no violations
        assert len(violations) == 0

    def test_add_rule(self) -> None:
        """Test adding custom rules to the linter."""
        from machine_dialect.ast import ASTNode
        from machine_dialect.linter.rules.base import Context, Rule

        class CustomRule(Rule):
            @property
            def rule_id(self) -> str:
                return "CUSTOM001"

            @property
            def description(self) -> str:
                return "Custom test rule"

            def check(self, node: ASTNode, context: Context) -> list[Violation]:
                return []

        linter = Linter()
        initial_count = len(linter.rules)

        linter.add_rule(CustomRule())
        assert len(linter.rules) == initial_count + 1
        assert any(rule.rule_id == "CUSTOM001" for rule in linter.rules)
