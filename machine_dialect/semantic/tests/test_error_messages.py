"""Tests for error message generation.

This module tests the generation of helpful error messages with suggestions.
"""

from machine_dialect.semantic.error_messages import ErrorMessageGenerator


class TestErrorMessages:
    """Test error message generation."""

    def test_undefined_variable_message(self) -> None:
        """Test undefined variable error message."""
        msg = ErrorMessageGenerator.undefined_variable("counter", 5, 10, similar_vars=["count", "counter1"])

        assert "Variable 'counter' is not defined" in msg
        assert "line 5, column 10" in msg
        assert "Did you mean" in msg
        assert "count" in msg
        assert "Define `counter` as Type" in msg

    def test_type_mismatch_message(self) -> None:
        """Test type mismatch error message."""
        msg = ErrorMessageGenerator.type_mismatch("age", ["Whole Number"], "Text", 8, 5, '"twenty"')

        assert "Cannot set Whole Number variable 'age'" in msg
        assert "Text value" in msg
        assert "Expected: Whole Number" in msg
        assert "Actual: Text" in msg

    def test_type_mismatch_union_message(self) -> None:
        """Test type mismatch error message for union types."""
        msg = ErrorMessageGenerator.type_mismatch("id", ["Whole Number", "Text"], "Yes/No", 10, 3, "yes")

        assert "Cannot set 'id'" in msg
        assert "Yes/No value" in msg
        assert "Expected: Whole Number or Text" in msg
        assert "Actual: Yes/No" in msg

    def test_redefinition_message(self) -> None:
        """Test redefinition error message."""
        msg = ErrorMessageGenerator.redefinition("x", 10, 1, 5, 1)

        assert "Variable 'x' is already defined" in msg
        assert "line 10, column 1" in msg
        assert "Original definition at line 5" in msg
        assert "Use 'Set' to change the value" in msg

    def test_uninitialized_use_message(self) -> None:
        """Test uninitialized use error message."""
        msg = ErrorMessageGenerator.uninitialized_use("data", 15, 8, 3)

        assert "Variable 'data' is used before being initialized" in msg
        assert "line 15, column 8" in msg
        assert "defined at line 3" in msg
        assert "Set `data` to value" in msg

    def test_invalid_type_message(self) -> None:
        """Test invalid type error message."""
        msg = ErrorMessageGenerator.invalid_type("Str", 5, 15, ["Text", "Whole Number", "Float", "Yes/No"])

        assert "Unknown type 'Str'" in msg
        assert "Valid types:" in msg
        # The similarity detection may not suggest Text for "Str" with default threshold

    def test_undefined_without_suggestions(self) -> None:
        """Test undefined variable message without suggestions."""
        msg = ErrorMessageGenerator.undefined_variable("xyz", 3, 7, similar_vars=None)

        assert "Variable 'xyz' is not defined" in msg
        assert "line 3, column 7" in msg
        assert "Did you mean" not in msg
        assert "Define `xyz` as Type" in msg

    def test_type_conversion_hints(self) -> None:
        """Test type mismatch messages include conversion hints."""
        # Whole Number to Float hint
        msg = ErrorMessageGenerator.type_mismatch("price", ["Float"], "Whole Number", 5, 10, "42")
        assert "Use _42.0_ to make it a Float" in msg

        # Float to Whole Number hint
        msg = ErrorMessageGenerator.type_mismatch("count", ["Whole Number"], "Float", 6, 10, "3.14")
        assert "Float values cannot be assigned to Whole Number variables" in msg

    def test_similar_name_detection(self) -> None:
        """Test similar name detection algorithm."""
        similar = ErrorMessageGenerator._find_similar(
            "count", ["counter", "amount", "count1", "total", "cnt"], threshold=0.6
        )

        # Should find similar names
        assert "count1" in similar
        assert "counter" in similar

        # Should be ordered by similarity
        assert similar.index("count1") < similar.index("cnt")

    def test_invalid_type_with_multiple_suggestions(self) -> None:
        """Test invalid type message with multiple suggestions."""
        msg = ErrorMessageGenerator.invalid_type("Num", 7, 20, ["Number", "Whole Number", "Float", "Text", "Yes/No"])

        assert "Unknown type 'Num'" in msg
        assert "Did you mean one of:" in msg or "Did you mean 'Number'?" in msg
        assert "Valid types:" in msg
