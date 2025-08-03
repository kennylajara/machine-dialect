"""Tests for the violations module."""

from machine_dialect.linter.violations import Violation, ViolationSeverity


class TestViolation:
    """Test the Violation class."""

    def test_violation_creation(self) -> None:
        """Test creating a violation."""
        violation = Violation(
            rule_id="TEST001",
            message="Test violation",
            severity=ViolationSeverity.WARNING,
            line=10,
            column=5,
        )

        assert violation.rule_id == "TEST001"
        assert violation.message == "Test violation"
        assert violation.severity == ViolationSeverity.WARNING
        assert violation.line == 10
        assert violation.column == 5
        assert violation.node is None
        assert violation.fix_suggestion is None

    def test_violation_with_optional_fields(self) -> None:
        """Test violation with optional fields."""
        violation = Violation(
            rule_id="TEST002",
            message="Test with suggestion",
            severity=ViolationSeverity.STYLE,
            line=1,
            column=0,
            fix_suggestion="Add a period",
        )

        assert violation.fix_suggestion == "Add a period"

    def test_violation_string_representation(self) -> None:
        """Test string representation of violations."""
        violation = Violation(
            rule_id="MD101",
            message="Missing period",
            severity=ViolationSeverity.STYLE,
            line=5,
            column=10,
        )

        str_repr = str(violation)
        assert "5:10" in str_repr
        assert "style" in str_repr
        assert "MD101" in str_repr
        assert "Missing period" in str_repr


class TestViolationSeverity:
    """Test the ViolationSeverity enum."""

    def test_severity_values(self) -> None:
        """Test that severity levels have expected values."""
        assert ViolationSeverity.ERROR.value == "error"
        assert ViolationSeverity.WARNING.value == "warning"
        assert ViolationSeverity.INFO.value == "info"
        assert ViolationSeverity.STYLE.value == "style"

    def test_all_severities_defined(self) -> None:
        """Test that all expected severities are defined."""
        expected_severities = {"ERROR", "WARNING", "INFO", "STYLE"}
        actual_severities = {s.name for s in ViolationSeverity}
        assert expected_severities == actual_severities
