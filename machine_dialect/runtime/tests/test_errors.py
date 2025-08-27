"""Tests for the runtime errors module."""

from types import TracebackType
from typing import Any

import pytest

from machine_dialect.runtime.errors import (
    ERROR_MESSAGES,
    ArgumentError,
    DivisionByZeroError,
    NameError,
    RuntimeError,
    TypeError,
    ValueError,
)


class TestRuntimeErrorHierarchy:
    """Tests for the runtime error class hierarchy."""

    def test_runtime_error_base_class(self) -> None:
        """Test that RuntimeError is the base class."""
        error = RuntimeError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"

    def test_type_error_inheritance(self) -> None:
        """Test TypeError inherits from RuntimeError."""
        error = TypeError("type error message")
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)
        assert str(error) == "type error message"

    def test_division_by_zero_error_inheritance(self) -> None:
        """Test DivisionByZeroError inherits from RuntimeError."""
        error = DivisionByZeroError("division by zero")
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)
        assert str(error) == "division by zero"

    def test_name_error_inheritance(self) -> None:
        """Test NameError inherits from RuntimeError."""
        error = NameError("name not found")
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)
        assert str(error) == "name not found"

    def test_argument_error_inheritance(self) -> None:
        """Test ArgumentError inherits from RuntimeError."""
        error = ArgumentError("wrong arguments")
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)
        assert str(error) == "wrong arguments"

    def test_value_error_inheritance(self) -> None:
        """Test ValueError inherits from RuntimeError."""
        error = ValueError("invalid value")
        assert isinstance(error, RuntimeError)
        assert isinstance(error, Exception)
        assert str(error) == "invalid value"


class TestErrorCreation:
    """Tests for creating various error types."""

    def test_runtime_error_creation(self) -> None:
        """Test creating RuntimeError instances."""
        error = RuntimeError()
        assert str(error) == ""

        error = RuntimeError("Custom message")
        assert str(error) == "Custom message"

    def test_type_error_creation(self) -> None:
        """Test creating TypeError instances."""
        error = TypeError()
        assert str(error) == ""

        error = TypeError("Incompatible types")
        assert str(error) == "Incompatible types"

    def test_division_by_zero_error_creation(self) -> None:
        """Test creating DivisionByZeroError instances."""
        error = DivisionByZeroError()
        assert str(error) == ""

        error = DivisionByZeroError("Cannot divide by zero")
        assert str(error) == "Cannot divide by zero"

    def test_name_error_creation(self) -> None:
        """Test creating NameError instances."""
        error = NameError()
        assert str(error) == ""

        error = NameError("Variable 'x' not defined")
        assert str(error) == "Variable 'x' not defined"

    def test_argument_error_creation(self) -> None:
        """Test creating ArgumentError instances."""
        error = ArgumentError()
        assert str(error) == ""

        error = ArgumentError("Expected 2 arguments, got 3")
        assert str(error) == "Expected 2 arguments, got 3"

    def test_value_error_creation(self) -> None:
        """Test creating ValueError instances."""
        error = ValueError()
        assert str(error) == ""

        error = ValueError("Invalid number format")
        assert str(error) == "Invalid number format"


class TestErrorMessages:
    """Tests for the ERROR_MESSAGES template system."""

    def test_error_messages_structure(self) -> None:
        """Test that ERROR_MESSAGES is properly structured."""
        assert isinstance(ERROR_MESSAGES, dict)
        assert len(ERROR_MESSAGES) > 0

        # Check that all values are strings
        for key, message in ERROR_MESSAGES.items():
            assert isinstance(key, str)
            assert isinstance(message, str)
            assert len(message) > 0

    def test_unsupported_operand_type_message(self) -> None:
        """Test the UNSUPPORTED_OPERAND_TYPE message template."""
        template = ERROR_MESSAGES["UNSUPPORTED_OPERAND_TYPE"]

        # Test that it has the expected placeholders
        assert "{operator}" in template
        assert "{left_type}" in template
        assert "{right_type}" in template

        # Test formatting
        formatted = template.format(operator="+", left_type="string", right_type="integer")
        assert "+" in formatted
        assert "string" in formatted
        assert "integer" in formatted

    def test_unsupported_unary_operand_message(self) -> None:
        """Test the UNSUPPORTED_UNARY_OPERAND message template."""
        template = ERROR_MESSAGES["UNSUPPORTED_UNARY_OPERAND"]

        assert "{operator}" in template
        assert "{type}" in template

        formatted = template.format(operator="-", type="string")
        assert "-" in formatted
        assert "string" in formatted

    def test_division_by_zero_message(self) -> None:
        """Test the DIVISION_BY_ZERO message template."""
        message = ERROR_MESSAGES["DIVISION_BY_ZERO"]
        assert message == "Division by zero"

    def test_modulo_by_zero_message(self) -> None:
        """Test the MODULO_BY_ZERO message template."""
        message = ERROR_MESSAGES["MODULO_BY_ZERO"]
        assert message == "Modulo by zero"

    def test_name_undefined_message(self) -> None:
        """Test the NAME_UNDEFINED message template."""
        template = ERROR_MESSAGES["NAME_UNDEFINED"]

        assert "{name}" in template

        formatted = template.format(name="variable_x")
        assert "variable_x" in formatted

    def test_wrong_argument_count_message(self) -> None:
        """Test the WRONG_ARGUMENT_COUNT message template."""
        template = ERROR_MESSAGES["WRONG_ARGUMENT_COUNT"]

        assert "{name}" in template
        assert "{expected}" in template
        assert "{actual}" in template

        formatted = template.format(name="print", expected=2, actual=3)
        assert "print" in formatted
        assert "2" in formatted
        assert "3" in formatted

    def test_invalid_conversion_message(self) -> None:
        """Test the INVALID_CONVERSION message template."""
        template = ERROR_MESSAGES["INVALID_CONVERSION"]

        assert "{from_type}" in template
        assert "{to_type}" in template

        formatted = template.format(from_type="string", to_type="integer")
        assert "string" in formatted
        assert "integer" in formatted

    def test_unknown_operator_messages(self) -> None:
        """Test the unknown operator message templates."""
        # Test UNKNOWN_OPERATOR
        template = ERROR_MESSAGES["UNKNOWN_OPERATOR"]
        assert "{operator}" in template
        formatted = template.format(operator="***")
        assert "***" in formatted

        # Test UNKNOWN_PREFIX_OPERATOR
        template = ERROR_MESSAGES["UNKNOWN_PREFIX_OPERATOR"]
        assert "{operator}" in template
        formatted = template.format(operator="@@")
        assert "@@" in formatted

        # Test UNKNOWN_INFIX_OPERATOR
        template = ERROR_MESSAGES["UNKNOWN_INFIX_OPERATOR"]
        assert "{operator}" in template
        formatted = template.format(operator="<?>")
        assert "<?>" in formatted

    def test_all_message_keys_present(self) -> None:
        """Test that all expected message keys are present."""
        expected_keys = {
            "UNSUPPORTED_OPERAND_TYPE",
            "UNSUPPORTED_UNARY_OPERAND",
            "DIVISION_BY_ZERO",
            "MODULO_BY_ZERO",
            "NAME_UNDEFINED",
            "WRONG_ARGUMENT_COUNT",
            "INVALID_CONVERSION",
            "UNKNOWN_OPERATOR",
            "UNKNOWN_PREFIX_OPERATOR",
            "UNKNOWN_INFIX_OPERATOR",
        }

        assert set(ERROR_MESSAGES.keys()) == expected_keys


class TestErrorUsage:
    """Tests for typical error usage patterns."""

    def test_type_error_with_template(self) -> None:
        """Test TypeError using message template."""
        template = ERROR_MESSAGES["UNSUPPORTED_OPERAND_TYPE"]
        message = template.format(operator="+", left_type="string", right_type="list")

        error = TypeError(message)
        assert "+" in str(error)
        assert "string" in str(error)
        assert "list" in str(error)

    def test_argument_error_with_template(self) -> None:
        """Test ArgumentError using message template."""
        template = ERROR_MESSAGES["WRONG_ARGUMENT_COUNT"]
        message = template.format(name="max", expected=1, actual=0)

        error = ArgumentError(message)
        assert "max" in str(error)
        assert "1" in str(error)
        assert "0" in str(error)

    def test_name_error_with_template(self) -> None:
        """Test NameError using message template."""
        template = ERROR_MESSAGES["NAME_UNDEFINED"]
        message = template.format(name="undefined_function")

        error = NameError(message)
        assert "undefined_function" in str(error)

    def test_value_error_with_template(self) -> None:
        """Test ValueError using message template."""
        template = ERROR_MESSAGES["INVALID_CONVERSION"]
        message = template.format(from_type="string", to_type="float")

        error = ValueError(message)
        assert "string" in str(error)
        assert "float" in str(error)

    def test_division_by_zero_error_usage(self) -> None:
        """Test DivisionByZeroError usage."""
        message = ERROR_MESSAGES["DIVISION_BY_ZERO"]
        error = DivisionByZeroError(message)
        assert str(error) == "Division by zero"

    def test_chained_error_handling(self) -> None:
        """Test error chaining and handling patterns."""

        def inner_function() -> None:
            raise ValueError("Original error")

        def outer_function() -> None:
            try:
                inner_function()
            except ValueError as e:
                raise RuntimeError("Wrapped error") from e

        with pytest.raises(RuntimeError) as exc_info:
            outer_function()

        assert "Wrapped error" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)


class TestErrorFormatting:
    """Tests for error message formatting edge cases."""

    def test_message_with_special_characters(self) -> None:
        """Test error messages with special characters."""
        error = TypeError("Operator '+' failed with types 'string' and 'int'")
        assert "'" in str(error)
        assert "+" in str(error)

    def test_message_with_unicode(self) -> None:
        """Test error messages with Unicode characters."""
        error = NameError("Variable '变量' not found")
        assert "变量" in str(error)

    def test_empty_template_formatting(self) -> None:
        """Test template formatting with empty values."""
        template = ERROR_MESSAGES["UNSUPPORTED_OPERAND_TYPE"]
        formatted = template.format(operator="", left_type="", right_type="")

        # Should still be a valid message, just with empty parts
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_numeric_template_formatting(self) -> None:
        """Test template formatting with numeric values."""
        template = ERROR_MESSAGES["WRONG_ARGUMENT_COUNT"]
        formatted = template.format(name="func", expected=0, actual=1)

        assert "0" in formatted
        assert "1" in formatted
        assert "func" in formatted

    def test_long_message_formatting(self) -> None:
        """Test formatting with very long messages."""
        long_name = "a" * 1000
        template = ERROR_MESSAGES["NAME_UNDEFINED"]
        formatted = template.format(name=long_name)

        assert long_name in formatted
        assert len(formatted) > 1000


class TestErrorContext:
    """Tests for error context and debugging information."""

    def test_error_with_context_info(self) -> None:
        """Test errors that include context information."""

        def create_detailed_error() -> TypeError:
            return TypeError(
                f"Cannot add {str.__name__} and {int.__name__}. "
                f"Supported operations are: string + string, number + number"
            )

        error = create_detailed_error()
        message = str(error)
        assert "str" in message
        assert "int" in message
        assert "Cannot add" in message

    def test_error_stack_preservation(self) -> None:
        """Test that error stack traces are preserved properly."""

        def level3() -> None:
            raise ValueError("Deep error")

        def level2() -> None:
            level3()

        def level1() -> None:
            level2()

        with pytest.raises(ValueError) as exc_info:
            level1()

        # The traceback should show all levels
        tb = exc_info.tb
        assert tb is not None

        # Count the levels in the traceback
        levels = []
        current_tb: TracebackType | None = tb
        while current_tb:
            levels.append(current_tb.tb_frame.f_code.co_name)
            current_tb = current_tb.tb_next

        assert "level3" in levels
        assert "level2" in levels
        assert "level1" in levels

    def test_error_suppression_context(self) -> None:
        """Test error suppression in context managers."""

        class SuppressingContext:
            def __enter__(self) -> "SuppressingContext":
                return self

            def __exit__(
                self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
            ) -> bool:
                if exc_type is ValueError:
                    return True  # Suppress ValueError
                return False

        # Test that ValueError is suppressed
        with SuppressingContext():
            raise ValueError("This should be suppressed")

        # Test that other errors are not suppressed
        with pytest.raises(TypeError):
            with SuppressingContext():
                raise TypeError("This should not be suppressed")


class TestCustomErrorPatterns:
    """Tests for custom error handling patterns."""

    def test_error_with_suggestions(self) -> None:
        """Test errors that include suggestions for fixing."""

        def create_helpful_error(name: str) -> NameError:
            similar_names = ["print", "len", "type"]
            suggestions = ", ".join(f"'{n}'" for n in similar_names)
            return NameError(f"Name '{name}' is not defined. " f"Did you mean one of: {suggestions}?")

        error = create_helpful_error("prnit")
        message = str(error)
        assert "prnit" in message
        assert "Did you mean" in message
        assert "print" in message

    def test_error_aggregation(self) -> None:
        """Test collecting multiple errors into one."""

        def validate_multiple_values(values: list[Any]) -> None:
            errors = []
            for i, value in enumerate(values):
                if not isinstance(value, int | float):
                    errors.append(f"Value at index {i} is not numeric: {type(value).__name__}")

            if errors:
                raise ValueError("Multiple validation errors:\n" + "\n".join(errors))

        with pytest.raises(ValueError) as exc_info:
            validate_multiple_values([1, "bad", 3, None, 5])

        message = str(exc_info.value)
        assert "Multiple validation errors" in message
        assert "index 1" in message
        assert "index 3" in message
        assert "str" in message
        assert "NoneType" in message
