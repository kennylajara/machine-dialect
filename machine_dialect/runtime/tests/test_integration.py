"""Integration tests for the runtime module.

These tests verify that all components work together correctly
and test realistic usage scenarios.
"""

import math
from typing import Any
from unittest.mock import patch

import pytest

from machine_dialect.runtime.builtins import call_builtin
from machine_dialect.runtime.errors import (
    ArgumentError,
    DivisionByZeroError,
)
from machine_dialect.runtime.errors import (
    NameError as MDNameError,
)
from machine_dialect.runtime.errors import (
    TypeError as MDTypeError,
)
from machine_dialect.runtime.errors import (
    ValueError as MDValueError,
)
from machine_dialect.runtime.operators import (
    add,
    divide,
    equals,
    greater_than,
    less_than,
    logical_and,
    logical_not,
    logical_or,
    multiply,
    power,
    strict_equals,
    subtract,
)
from machine_dialect.runtime.types import MachineDialectType, get_type, is_numeric, is_truthy
from machine_dialect.runtime.values import get_raw_value, to_float, to_int, to_string


class MockInterpreter:
    """Mock interpreter for integration testing."""

    def __init__(self) -> None:
        self.variables: dict[str, Any] = {}
        self.call_stack: list[str] = []

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable in the interpreter."""
        self.variables[name] = value

    def get_variable(self, name: str) -> Any:
        """Get a variable from the interpreter."""
        if name not in self.variables:
            raise MDNameError(f"Name '{name}' is not defined")
        return self.variables[name]

    def call_function(self, name: str, *args: Any) -> Any:
        """Call a built-in function."""
        return call_builtin(name, *args)


class MockValue:
    """Mock value object that represents interpreter values."""

    def __init__(self, value: Any, type_val: MachineDialectType) -> None:
        self.value = value
        self.type = type_val

    def __repr__(self) -> str:
        return f"MockValue({self.value}, {self.type})"


class TestArithmeticOperationsIntegration:
    """Integration tests for arithmetic operations."""

    def test_complex_arithmetic_expression(self) -> None:
        """Test complex arithmetic expressions."""
        # Simulate: (5 + 3) * 2 - 10 / 2
        result1 = add(5, 3)  # 8
        result2 = multiply(result1, 2)  # 16
        result3 = divide(10, 2)  # 5.0
        final_result = subtract(result2, result3)  # 11.0

        assert final_result == 11.0

    def test_mixed_type_arithmetic_chain(self) -> None:
        """Test chained operations with mixed types."""
        # Start with integer, add float, multiply by integer
        result = add(10, 3.5)  # 13.5
        result = multiply(result, 2)  # 27.0
        result = subtract(result, 2.5)  # 24.5

        assert result == 24.5
        assert isinstance(result, float)

    def test_power_operations_chain(self) -> None:
        """Test chained power operations."""
        # 2^3^2 = 2^(3^2) = 2^9 = 512
        exp_result = power(3, 2)  # 9
        final_result = power(2, exp_result)  # 512

        assert final_result == 512
        assert isinstance(final_result, int)

    def test_interpreter_value_arithmetic(self) -> None:
        """Test arithmetic with interpreter value objects."""
        int_val = MockValue(15, MachineDialectType.INTEGER)
        float_val = MockValue(2.5, MachineDialectType.FLOAT)

        result = add(int_val, float_val)  # 17.5
        result = multiply(result, 2)  # 35.0
        result = divide(result, 7)  # 5.0

        assert result == 5.0

    def test_error_propagation_in_arithmetic(self) -> None:
        """Test that errors propagate correctly in arithmetic chains."""
        # Division by zero should stop the chain
        with pytest.raises(DivisionByZeroError):
            result = add(5, 3)  # 8
            result = multiply(result, 2)  # 16
            divide(result, 0)  # Should raise error

    def test_special_float_arithmetic_integration(self) -> None:
        """Test arithmetic operations with special float values."""
        inf = float("inf")
        neg_inf = float("-inf")
        nan = float("nan")

        # inf operations
        assert add(inf, 100) == inf
        assert multiply(inf, 2) == inf
        assert divide(inf, 2) == inf

        # -inf operations
        assert subtract(0, inf) == neg_inf
        assert multiply(neg_inf, -1) == inf

        # NaN operations
        assert math.isnan(add(nan, 1))
        assert math.isnan(multiply(nan, 0))


class TestLogicalOperationsIntegration:
    """Integration tests for logical operations."""

    def test_complex_logical_expression(self) -> None:
        """Test complex logical expressions."""
        # (True AND False) OR (5 > 3)
        and_result = logical_and(True, False)  # False
        comparison_result = greater_than(5, 3)  # True
        final_result = logical_or(and_result, comparison_result)  # True

        assert final_result is True

    def test_short_circuit_evaluation_simulation(self) -> None:
        """Test logical operations that would short-circuit in real evaluation."""
        # Simulate: False AND (divide by zero)
        # In real short-circuit evaluation, the division wouldn't happen
        # But we need to test the logical operation itself
        false_val = False

        # Test that we can determine the result without evaluating the second part
        if not is_truthy(false_val):
            result = False  # Short-circuit: AND with False is always False
        else:
            result = logical_and(false_val, divide(1, 0))  # This wouldn't execute

        assert result is False

    def test_truthiness_with_different_types(self) -> None:
        """Test logical operations with various truthy/falsy values."""
        values = [
            (0, False),
            (1, True),
            ("", False),
            ("hello", True),
            (None, False),
            ([], True),  # Empty list is truthy (unknown type)
            (float("nan"), True),  # NaN is truthy
        ]

        for value, expected in values:
            assert is_truthy(value) == expected
            assert logical_not(value) == (not expected)

    def test_comparison_chain_integration(self) -> None:
        """Test chained comparison operations."""
        # Test: 1 < 5 < 10
        comp1 = less_than(1, 5)  # True
        comp2 = less_than(5, 10)  # True
        result = logical_and(comp1, comp2)  # True

        assert result is True

        # Test: 10 < 5 < 20
        comp1 = less_than(10, 5)  # False
        comp2 = less_than(5, 20)  # True
        result = logical_and(comp1, comp2)  # False

        assert result is False


class TestEqualityOperationsIntegration:
    """Integration tests for equality operations."""

    def test_equality_vs_strict_equality(self) -> None:
        """Test the difference between value and strict equality."""
        # Value equality allows type coercion
        assert equals(42, 42.0) is True
        assert equals(0, False) is True  # Both are numeric, value equality allows this

        # Strict equality requires same type and value
        assert strict_equals(42, 42.0) is False  # Different types
        assert strict_equals(42, 42) is True  # Same type and value

    def test_equality_with_interpreter_values(self) -> None:
        """Test equality operations with interpreter values."""
        int_val = MockValue(42, MachineDialectType.INTEGER)
        float_val = MockValue(42.0, MachineDialectType.FLOAT)
        str_val = MockValue("42", MachineDialectType.STRING)

        # Value equality with type coercion
        assert equals(int_val, 42) is True
        assert equals(int_val, float_val) is True  # 42 == 42.0
        assert equals(int_val, str_val) is False  # Different types

        # Strict equality without type coercion
        assert strict_equals(int_val, 42) is True
        assert strict_equals(int_val, float_val) is False  # Different types
        assert strict_equals(int_val, str_val) is False

    def test_nan_equality_edge_cases(self) -> None:
        """Test NaN equality edge cases."""
        nan1 = float("nan")
        nan2 = float("nan")

        # NaN is not equal to anything, including itself
        assert equals(nan1, nan2) is False
        assert strict_equals(nan1, nan2) is False
        assert equals(nan1, nan1) is False

        # But NaN is truthy
        assert is_truthy(nan1) is True


class TestTypeSystemIntegration:
    """Integration tests for the type system."""

    def test_type_detection_and_conversion_chain(self) -> None:
        """Test type detection followed by conversion operations."""
        values = [42, 3.14, "123", True, None]

        for value in values:
            if is_numeric(value):
                # Test numeric conversions
                int_val = to_int(value)
                float_val = to_float(value)
                assert isinstance(int_val, int)
                assert isinstance(float_val, float)

            # All values can be converted to string
            str_val = to_string(value)
            assert isinstance(str_val, str)

    def test_interpreter_value_type_system(self) -> None:
        """Test type system with interpreter values."""
        values = [
            MockValue(42, MachineDialectType.INTEGER),
            MockValue(3.14, MachineDialectType.FLOAT),
            MockValue("hello", MachineDialectType.STRING),
            MockValue(True, MachineDialectType.BOOLEAN),
        ]

        for value in values:
            detected_type = get_type(value)
            assert detected_type == value.type

            raw_value = get_raw_value(value)
            assert raw_value == value.value

    def test_type_preservation_in_operations(self) -> None:
        """Test that operations preserve types correctly."""
        # Integer operations should preserve int when possible
        result = add(5, 3)
        assert isinstance(result, int)

        result = multiply(4, 7)
        assert isinstance(result, int)

        result = power(2, 3)
        assert isinstance(result, int)

        # Operations with floats should return floats
        result = add(5, 3.0)
        assert isinstance(result, float)

        # Division always returns float
        result = divide(6, 2)
        assert isinstance(result, float)
        assert result == 3.0


class TestBuiltinFunctionIntegration:
    """Integration tests for built-in functions."""

    def test_builtin_function_chaining(self) -> None:
        """Test chaining built-in function calls."""
        # abs(int(float("-3.14")))
        str_val = "-3.14"
        float_result = call_builtin("float", str_val)  # -3.14
        int_result = call_builtin("int", float_result)  # -3
        abs_result = call_builtin("abs", int_result)  # 3

        assert abs_result == 3
        assert isinstance(abs_result, int)

    def test_builtin_with_arithmetic_operations(self) -> None:
        """Test built-ins combined with arithmetic operations."""
        # max(5, 3) + min(10, 7) * 2
        max_result = call_builtin("max", 5, 3)  # 5
        min_result = call_builtin("min", 10, 7)  # 7
        mult_result = multiply(min_result, 2)  # 14
        final_result = add(max_result, mult_result)  # 19

        assert final_result == 19

    def test_type_checking_with_operations(self) -> None:
        """Test type() builtin with various operations."""
        values = [
            (42, "integer"),
            (3.14, "float"),
            ("hello", "text"),
            (True, "boolean"),
            (None, "empty"),
        ]

        for value, expected_type in values:
            detected_type = call_builtin("type", value)
            assert detected_type == expected_type

            # Test that operations preserve type detection
            if expected_type in ("integer", "float"):
                doubled = multiply(value, 2)
                doubled_type = call_builtin("type", doubled)

                if expected_type == "integer":
                    assert doubled_type == "integer"
                else:
                    assert doubled_type == "float"

    def test_conversion_builtin_integration(self) -> None:
        """Test conversion built-ins with type system."""
        test_cases = [
            ("42", "int", 42, "integer"),
            ("3.14", "float", 3.14, "float"),
            (42, "str", "42", "text"),
            (0, "bool", False, "boolean"),
            (1, "bool", True, "boolean"),
        ]

        for input_val, func_name, expected_val, expected_type in test_cases:
            result = call_builtin(func_name, input_val)
            assert result == expected_val

            result_type = call_builtin("type", result)
            assert result_type == expected_type

    def test_print_integration_with_conversions(self) -> None:
        """Test print function with various value conversions."""
        with patch("builtins.print") as mock_print:
            # Test printing different types
            values = [42, 3.14, "hello", True, None, float("inf")]
            call_builtin("print", *values)

            # Check that all values were converted to strings properly
            expected_args = ["42", "3.14", "hello", "Yes", "empty", "inf"]
            mock_print.assert_called_once_with(*expected_args)


class TestErrorHandlingIntegration:
    """Integration tests for error handling across components."""

    def test_error_propagation_chain(self) -> None:
        """Test that errors propagate correctly through operation chains."""
        # Test division by zero in a chain
        with pytest.raises(DivisionByZeroError):
            result = add(5, 3)  # 8
            result = multiply(result, 2)  # 16
            result = divide(result, 0)  # Should raise error
            add(result, 1)  # This shouldn't execute

    def test_type_error_in_operations(self) -> None:
        """Test type errors in various operations."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            add([], {})

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            less_than("hello", 5)

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            multiply(None, 3)

    def test_builtin_function_errors(self) -> None:
        """Test error handling in built-in functions."""
        # Test wrong argument count
        with pytest.raises(ArgumentError, match="expects 1 arguments, got 0"):
            call_builtin("type")

        # Test invalid conversions
        with pytest.raises(MDValueError, match="Cannot convert"):
            call_builtin("int", "hello")

        # Test function not found
        with pytest.raises(MDNameError, match="not defined"):
            call_builtin("nonexistent")

    def test_nested_error_handling(self) -> None:
        """Test error handling in nested operations."""

        def complex_operation(a: Any, b: Any, c: Any) -> Any:
            """Simulate a complex operation that might fail at various points."""
            # This could fail with type error
            result1 = add(a, b)

            # This could fail with division by zero
            result2 = divide(result1, c)

            # This could fail with invalid conversion
            return call_builtin("int", result2)

        # Test successful case
        result = complex_operation(5, 3, 2)
        assert result == 4  # int((5+3)/2) = int(4.0) = 4

        # Test division by zero
        with pytest.raises(DivisionByZeroError):
            complex_operation(5, 3, 0)

        # Test type error
        with pytest.raises(MDTypeError):
            complex_operation("hello", 3, 2)


class TestRealWorldScenarios:
    """Integration tests for realistic usage scenarios."""

    def test_calculator_simulation(self) -> None:
        """Simulate a simple calculator with various operations."""
        interpreter = MockInterpreter()

        # Set some variables
        interpreter.set_variable("x", 10)
        interpreter.set_variable("y", 3)
        interpreter.set_variable("pi", 3.14159)

        # Perform calculations
        x = interpreter.get_variable("x")
        y = interpreter.get_variable("y")
        pi = interpreter.get_variable("pi")

        # x + y * pi
        result1 = multiply(y, pi)  # 9.42477
        result2 = add(x, result1)  # 19.42477
        interpreter.set_variable("result", result2)

        # Check result
        final_result = interpreter.get_variable("result")
        assert abs(final_result - 19.42477) < 0.00001

    def test_data_validation_scenario(self) -> None:
        """Test a data validation scenario."""

        def validate_and_process(data: list[Any]) -> list[Any]:
            """Validate and process a list of values."""
            results = []

            for item in data:
                # Check if numeric
                if not is_numeric(item):
                    raise MDValueError(f"Non-numeric value: {item}")

                # Convert to float and take absolute value
                float_val = to_float(item)
                abs_val = call_builtin("abs", float_val)

                # Round to 2 decimal places
                rounded = call_builtin("round", abs_val, 2)
                results.append(rounded)

            return results

        # Test with valid data
        data = [1, -2.5, 3.14159, 0, -10.7]
        results = validate_and_process(data)
        expected = [1.0, 2.5, 3.14, 0.0, 10.7]

        for result, expected_val in zip(results, expected, strict=True):
            assert abs(result - expected_val) < 0.001

        # Test with invalid data
        with pytest.raises(MDValueError):
            validate_and_process([1, 2, "hello", 4])

    def test_string_processing_scenario(self) -> None:
        """Test string processing with type conversions."""

        def process_string_numbers(text_list: list[str]) -> float | None:
            """Process a list of string numbers."""
            total = 0
            count = 0

            for text in text_list:
                try:
                    # Try to convert to number
                    if "." in text:
                        num = call_builtin("float", text)
                    else:
                        num = call_builtin("int", text)

                    total = add(total, num)
                    count += 1
                except MDValueError:
                    # Skip invalid numbers
                    continue

            if count == 0:
                return None

            return float(divide(total, count))  # Average

        # Test with valid strings
        strings = ["10", "20.5", "5", "15.5", "invalid", "7"]
        result = process_string_numbers(strings)
        # Average of [10, 20.5, 5, 15.5, 7] = 58 / 5 = 11.6
        assert result is not None
        assert abs(result - 11.6) < 0.001

    def test_comparison_and_filtering_scenario(self) -> None:
        """Test comparison operations for filtering."""

        def filter_values(values: list[Any], min_val: Any, max_val: Any) -> list[Any]:
            """Filter values within a range."""
            filtered = []

            for value in values:
                # Check if value is in range: min_val <= value <= max_val
                min_check = logical_or(greater_than(value, min_val), equals(value, min_val))
                max_check = logical_or(less_than(value, max_val), equals(value, max_val))

                if logical_and(min_check, max_check):
                    filtered.append(value)

            return filtered

        values = [1, 5, 10, 15, 20, 25, 30]
        filtered = filter_values(values, 10, 25)
        expected = [10, 15, 20, 25]

        assert filtered == expected

    def test_mathematical_function_simulation(self) -> None:
        """Test simulation of mathematical functions."""

        def quadratic_formula(a: Any, b: Any, c: Any) -> list[Any]:
            """Solve quadratic equation ax² + bx + c = 0."""
            # Calculate discriminant: b² - 4ac
            b_squared = power(b, 2)
            four_ac = multiply(multiply(4, a), c)
            discriminant = subtract(b_squared, four_ac)

            if less_than(discriminant, 0):
                raise MDValueError("No real solutions (negative discriminant)")

            # Calculate square root of discriminant
            sqrt_discriminant = power(discriminant, 0.5)

            # Calculate two solutions
            neg_b = subtract(0, b)
            two_a = multiply(2, a)

            x1 = divide(add(neg_b, sqrt_discriminant), two_a)
            x2 = divide(subtract(neg_b, sqrt_discriminant), two_a)

            return [x1, x2]

        # Test: x² - 5x + 6 = 0 (solutions: x = 2, 3)
        solutions = quadratic_formula(1, -5, 6)
        solutions.sort()  # Sort to ensure consistent order

        assert abs(solutions[0] - 2.0) < 0.001
        assert abs(solutions[1] - 3.0) < 0.001

        # Test case with no real solutions
        with pytest.raises(MDValueError, match="No real solutions"):
            quadratic_formula(1, 1, 1)  # x² + x + 1 = 0


class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""

    def test_large_number_operations(self) -> None:
        """Test operations with very large numbers."""
        large_int = 999999999999999999
        large_float = 1e100

        # Test that operations complete successfully
        result = add(large_int, 1)
        assert result == large_int + 1

        result = multiply(large_float, 2)
        assert result == large_float * 2

        # Test string conversion
        str_result = call_builtin("str", large_int)
        assert str(large_int) == str_result

    def test_deep_operation_nesting(self) -> None:
        """Test deeply nested operations."""
        # Build up a complex nested expression
        result = 1
        for i in range(10):
            result = add(result, multiply(i, 2))

        # result = 1 + 0*2 + 1*2 + 2*2 + ... + 9*2
        # result = 1 + 0 + 2 + 4 + 6 + 8 + 10 + 12 + 14 + 16 + 18 = 91
        assert result == 91

    def test_type_conversion_chain(self) -> None:
        """Test long chains of type conversions."""
        # Start with a string, convert through multiple types
        value = "123"

        # string -> int -> float -> string -> int -> bool -> string
        value = call_builtin("int", value)  # 123
        value = call_builtin("float", value)  # 123.0
        value = call_builtin("str", value)  # "123.0"
        value = call_builtin("float", value)  # 123.0
        value = call_builtin("int", value)  # 123
        value = call_builtin("bool", value)  # True
        value = call_builtin("str", value)  # "Yes"

        assert value == "Yes"
