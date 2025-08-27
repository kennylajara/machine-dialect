"""Tests for the runtime operators module."""

import math
from typing import Any

import pytest

from machine_dialect.runtime.errors import DivisionByZeroError
from machine_dialect.runtime.errors import TypeError as MDTypeError
from machine_dialect.runtime.operators import (
    add,
    divide,
    equals,
    greater_than,
    greater_than_or_equal,
    less_than,
    less_than_or_equal,
    logical_and,
    logical_not,
    logical_or,
    modulo,
    multiply,
    negate,
    not_equals,
    power,
    strict_equals,
    strict_not_equals,
    subtract,
)
from machine_dialect.runtime.types import MachineDialectType


class MockInterpreterValue:
    """Mock interpreter value object for testing."""

    def __init__(self, value: Any, type_val: MachineDialectType) -> None:
        self.value = value
        self.type = type_val


class TestAdd:
    """Tests for add function."""

    def test_integer_addition(self) -> None:
        """Test integer addition."""
        assert add(5, 3) == 8
        assert add(-2, 7) == 5
        assert add(0, 0) == 0
        assert add(-5, -3) == -8

    def test_float_addition(self) -> None:
        """Test float addition."""
        assert add(3.14, 2.86) == pytest.approx(6.0)
        assert add(-1.5, 2.5) == pytest.approx(1.0)
        assert add(0.0, 0.0) == 0.0

    def test_mixed_numeric_addition(self) -> None:
        """Test mixed int and float addition."""
        assert add(5, 3.5) == 8.5
        assert add(2.5, 7) == 9.5
        assert add(-3, 1.5) == -1.5

    def test_string_concatenation(self) -> None:
        """Test string concatenation."""
        assert add("hello", " world") == "hello world"
        assert add("", "test") == "test"
        assert add("test", "") == "test"
        assert add("", "") == ""

    def test_string_with_number(self) -> None:
        """Test string concatenation with numbers."""
        assert add("Value: ", 42) == "Value: 42"
        assert add(42, " is the answer") == "42 is the answer"
        assert add("Pi is ", 3.14) == "Pi is 3.14"

    def test_interpreter_object_addition(self) -> None:
        """Test addition with interpreter objects."""
        int_obj = MockInterpreterValue(5, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(3.5, MachineDialectType.FLOAT)

        assert add(int_obj, 3) == 8
        assert add(5, int_obj) == 10
        assert add(int_obj, float_obj) == 8.5

    def test_special_float_addition(self) -> None:
        """Test addition with special float values."""
        inf = float("inf")
        neg_inf = float("-inf")
        nan = float("nan")

        assert add(inf, 1) == inf
        assert add(neg_inf, 1) == neg_inf
        assert math.isnan(add(nan, 1))
        assert math.isnan(add(inf, neg_inf))

    def test_type_preservation(self) -> None:
        """Test that integer type is preserved when adding integers."""
        result = add(3, 4)
        assert isinstance(result, int)
        assert result == 7

    def test_invalid_operands(self) -> None:
        """Test error handling for invalid operands."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            add([], {})

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            add(None, object())


class TestSubtract:
    """Tests for subtract function."""

    def test_integer_subtraction(self) -> None:
        """Test integer subtraction."""
        assert subtract(8, 3) == 5
        assert subtract(-2, 7) == -9
        assert subtract(0, 0) == 0
        assert subtract(-5, -3) == -2

    def test_float_subtraction(self) -> None:
        """Test float subtraction."""
        assert subtract(6.0, 2.86) == pytest.approx(3.14)
        assert subtract(-1.5, 2.5) == pytest.approx(-4.0)
        assert subtract(0.0, 0.0) == 0.0

    def test_mixed_numeric_subtraction(self) -> None:
        """Test mixed int and float subtraction."""
        assert subtract(8, 3.5) == 4.5
        assert subtract(2.5, 7) == -4.5
        assert subtract(-3, -1.5) == -1.5

    def test_interpreter_object_subtraction(self) -> None:
        """Test subtraction with interpreter objects."""
        int_obj = MockInterpreterValue(10, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(3.5, MachineDialectType.FLOAT)

        assert subtract(int_obj, 3) == 7
        assert subtract(15, int_obj) == 5
        assert subtract(int_obj, float_obj) == 6.5

    def test_special_float_subtraction(self) -> None:
        """Test subtraction with special float values."""
        inf = float("inf")
        neg_inf = float("-inf")
        nan = float("nan")

        assert subtract(inf, 1) == inf
        assert subtract(1, neg_inf) == inf
        assert math.isnan(subtract(nan, 1))
        assert math.isnan(subtract(inf, inf))

    def test_type_preservation(self) -> None:
        """Test that integer type is preserved when subtracting integers."""
        result = subtract(7, 3)
        assert isinstance(result, int)
        assert result == 4

    def test_invalid_operands(self) -> None:
        """Test error handling for invalid operands."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            subtract("hello", "world")

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            subtract(5, "test")


class TestMultiply:
    """Tests for multiply function."""

    def test_integer_multiplication(self) -> None:
        """Test integer multiplication."""
        assert multiply(5, 3) == 15
        assert multiply(-2, 7) == -14
        assert multiply(0, 100) == 0
        assert multiply(-5, -3) == 15

    def test_float_multiplication(self) -> None:
        """Test float multiplication."""
        assert multiply(3.14, 2.0) == pytest.approx(6.28)
        assert multiply(-1.5, 2.5) == pytest.approx(-3.75)
        assert multiply(0.0, 100.0) == 0.0

    def test_mixed_numeric_multiplication(self) -> None:
        """Test mixed int and float multiplication."""
        assert multiply(5, 2.5) == 12.5
        assert multiply(2.5, 4) == 10.0
        assert multiply(-3, 1.5) == -4.5

    def test_interpreter_object_multiplication(self) -> None:
        """Test multiplication with interpreter objects."""
        int_obj = MockInterpreterValue(6, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(2.5, MachineDialectType.FLOAT)

        assert multiply(int_obj, 3) == 18
        assert multiply(4, int_obj) == 24
        assert multiply(int_obj, float_obj) == 15.0

    def test_special_float_multiplication(self) -> None:
        """Test multiplication with special float values."""
        inf = float("inf")
        neg_inf = float("-inf")
        nan = float("nan")

        assert multiply(inf, 2) == inf
        assert multiply(neg_inf, -2) == inf
        assert multiply(inf, 0) != multiply(inf, 0)  # inf * 0 = nan
        assert math.isnan(multiply(nan, 1))

    def test_type_preservation(self) -> None:
        """Test that integer type is preserved when multiplying integers."""
        result = multiply(3, 4)
        assert isinstance(result, int)
        assert result == 12

    def test_invalid_operands(self) -> None:
        """Test error handling for invalid operands."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            multiply("hello", 3)

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            multiply([], {})


class TestDivide:
    """Tests for divide function."""

    def test_integer_division(self) -> None:
        """Test integer division (always returns float)."""
        assert divide(8, 2) == 4.0
        assert divide(7, 2) == 3.5
        assert divide(-8, 2) == -4.0
        assert divide(8, -2) == -4.0

    def test_float_division(self) -> None:
        """Test float division."""
        assert divide(6.28, 2.0) == pytest.approx(3.14)
        assert divide(-1.5, 0.5) == -3.0
        assert divide(0.0, 1.0) == 0.0

    def test_mixed_numeric_division(self) -> None:
        """Test mixed int and float division."""
        assert divide(10, 2.5) == 4.0
        assert divide(7.5, 3) == 2.5
        assert divide(-9, 1.5) == -6.0

    def test_interpreter_object_division(self) -> None:
        """Test division with interpreter objects."""
        int_obj = MockInterpreterValue(12, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(2.5, MachineDialectType.FLOAT)

        assert divide(int_obj, 3) == 4.0
        assert divide(15, int_obj) == 1.25
        assert divide(int_obj, float_obj) == 4.8

    def test_special_float_division(self) -> None:
        """Test division with special float values."""
        inf = float("inf")
        neg_inf = float("-inf")
        nan = float("nan")

        assert divide(inf, 2) == inf
        assert divide(1, inf) == 0.0
        assert divide(neg_inf, -1) == inf
        assert math.isnan(divide(nan, 1))
        assert math.isnan(divide(inf, inf))

    def test_division_by_zero(self) -> None:
        """Test division by zero raises error."""
        with pytest.raises(DivisionByZeroError, match="Division by zero"):
            divide(5, 0)

        with pytest.raises(DivisionByZeroError, match="Division by zero"):
            divide(3.14, 0.0)

        with pytest.raises(DivisionByZeroError, match="Division by zero"):
            divide(-7, 0)

    def test_invalid_operands(self) -> None:
        """Test error handling for invalid operands."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            divide("hello", 2)

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            divide(5, "test")


class TestModulo:
    """Tests for modulo function."""

    def test_integer_modulo(self) -> None:
        """Test integer modulo."""
        assert modulo(8, 3) == 2
        assert modulo(10, 2) == 0
        assert modulo(-7, 3) == 2  # Python-style modulo
        assert modulo(7, -3) == -2

    def test_float_modulo(self) -> None:
        """Test float modulo."""
        assert modulo(5.5, 2.0) == pytest.approx(1.5)
        assert modulo(7.0, 3.0) == pytest.approx(1.0)
        # Note: Python modulo with negative numbers follows sign of divisor
        assert modulo(-5.5, 2.5) == pytest.approx(2.0)  # -5.5 % 2.5 = 2.0

    def test_mixed_numeric_modulo(self) -> None:
        """Test mixed int and float modulo."""
        assert modulo(7, 2.5) == pytest.approx(2.0)
        assert modulo(7.5, 3) == pytest.approx(1.5)

    def test_interpreter_object_modulo(self) -> None:
        """Test modulo with interpreter objects."""
        int_obj = MockInterpreterValue(10, MachineDialectType.INTEGER)

        assert modulo(int_obj, 3) == 1
        assert modulo(17, int_obj) == 7

    def test_type_preservation(self) -> None:
        """Test that integer type is preserved when both operands are integers."""
        result = modulo(7, 3)
        assert isinstance(result, int)
        assert result == 1

    def test_modulo_by_zero(self) -> None:
        """Test modulo by zero raises error."""
        with pytest.raises(DivisionByZeroError, match="Modulo by zero"):
            modulo(5, 0)

        with pytest.raises(DivisionByZeroError, match="Modulo by zero"):
            modulo(3.14, 0.0)

    def test_invalid_operands(self) -> None:
        """Test error handling for invalid operands."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            modulo("hello", 2)

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            modulo(5, "test")


class TestPower:
    """Tests for power function."""

    def test_integer_power(self) -> None:
        """Test integer exponentiation."""
        assert power(2, 3) == 8
        assert power(5, 2) == 25
        assert power(10, 0) == 1
        assert power(-3, 2) == 9
        assert power(-2, 3) == -8

    def test_float_power(self) -> None:
        """Test float exponentiation."""
        assert power(2.0, 3.0) == 8.0
        assert power(2.5, 2.0) == 6.25
        assert power(4.0, 0.5) == pytest.approx(2.0)

    def test_mixed_numeric_power(self) -> None:
        """Test mixed int and float exponentiation."""
        assert power(2, 3.0) == 8.0
        assert power(4.0, 2) == 16.0
        assert power(9, 0.5) == pytest.approx(3.0)

    def test_negative_exponent(self) -> None:
        """Test negative exponents."""
        assert power(2, -3) == 0.125
        assert power(4, -0.5) == pytest.approx(0.5)
        assert power(0.5, -2) == 4.0

    def test_interpreter_object_power(self) -> None:
        """Test power with interpreter objects."""
        int_obj = MockInterpreterValue(3, MachineDialectType.INTEGER)

        assert power(int_obj, 2) == 9
        assert power(2, int_obj) == 8

    def test_type_preservation(self) -> None:
        """Test that integer type is preserved for non-negative integer exponents."""
        result = power(3, 4)
        assert isinstance(result, int)
        assert result == 81

    def test_special_cases(self) -> None:
        """Test special power cases."""
        assert power(0, 5) == 0
        assert power(1, 100) == 1
        assert power(-1, 2) == 1
        assert power(-1, 3) == -1

    def test_invalid_operands(self) -> None:
        """Test error handling for invalid operands."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            power("hello", 2)

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            power(2, "test")


class TestNegate:
    """Tests for negate function."""

    def test_integer_negation(self) -> None:
        """Test integer negation."""
        assert negate(5) == -5
        assert negate(-3) == 3
        assert negate(0) == 0

    def test_float_negation(self) -> None:
        """Test float negation."""
        assert negate(3.14) == -3.14
        assert negate(-2.5) == 2.5
        assert negate(0.0) == 0.0

    def test_negative_zero_handling(self) -> None:
        """Test handling of negative zero."""
        assert negate(0) == 0
        assert negate(0.0) == -0.0

        # Check that type is preserved
        result_int = negate(0)
        assert isinstance(result_int, int)

        result_float = negate(0.0)
        assert isinstance(result_float, float)

    def test_interpreter_object_negation(self) -> None:
        """Test negation with interpreter objects."""
        int_obj = MockInterpreterValue(7, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(3.14, MachineDialectType.FLOAT)

        assert negate(int_obj) == -7
        assert negate(float_obj) == -3.14

    def test_special_float_negation(self) -> None:
        """Test negation with special float values."""
        assert negate(float("inf")) == float("-inf")
        assert negate(float("-inf")) == float("inf")
        assert math.isnan(negate(float("nan")))

    def test_invalid_operands(self) -> None:
        """Test error handling for invalid operands."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            negate("hello")

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            negate(None)


class TestLogicalNot:
    """Tests for logical_not function."""

    def test_boolean_not(self) -> None:
        """Test logical NOT with boolean values."""
        assert logical_not(True) is False
        assert logical_not(False) is True

    def test_numeric_not(self) -> None:
        """Test logical NOT with numeric values."""
        assert logical_not(0) is True
        assert logical_not(1) is False
        assert logical_not(-1) is False
        assert logical_not(0.0) is True
        assert logical_not(3.14) is False

    def test_string_not(self) -> None:
        """Test logical NOT with string values."""
        assert logical_not("") is True
        assert logical_not("hello") is False
        assert logical_not(" ") is False

    def test_none_not(self) -> None:
        """Test logical NOT with None."""
        assert logical_not(None) is True

    def test_interpreter_object_not(self) -> None:
        """Test logical NOT with interpreter objects."""
        false_bool = MockInterpreterValue(False, MachineDialectType.BOOLEAN)
        true_bool = MockInterpreterValue(True, MachineDialectType.BOOLEAN)
        zero_int = MockInterpreterValue(0, MachineDialectType.INTEGER)

        assert logical_not(false_bool) is True
        assert logical_not(true_bool) is False
        assert logical_not(zero_int) is True

    def test_special_float_not(self) -> None:
        """Test logical NOT with special float values."""
        assert logical_not(float("inf")) is False
        assert logical_not(float("-inf")) is False
        assert logical_not(float("nan")) is False


class TestLogicalAnd:
    """Tests for logical_and function."""

    def test_boolean_and(self) -> None:
        """Test logical AND with boolean values."""
        assert logical_and(True, True) is True
        assert logical_and(True, False) is False
        assert logical_and(False, True) is False
        assert logical_and(False, False) is False

    def test_mixed_value_and(self) -> None:
        """Test logical AND with mixed values."""
        assert logical_and(1, "hello") is True
        assert logical_and(0, "hello") is False
        assert logical_and("hello", 0) is False
        assert logical_and("", None) is False

    def test_interpreter_object_and(self) -> None:
        """Test logical AND with interpreter objects."""
        true_bool = MockInterpreterValue(True, MachineDialectType.BOOLEAN)
        false_bool = MockInterpreterValue(False, MachineDialectType.BOOLEAN)

        assert logical_and(true_bool, True) is True
        assert logical_and(false_bool, True) is False


class TestLogicalOr:
    """Tests for logical_or function."""

    def test_boolean_or(self) -> None:
        """Test logical OR with boolean values."""
        assert logical_or(True, True) is True
        assert logical_or(True, False) is True
        assert logical_or(False, True) is True
        assert logical_or(False, False) is False

    def test_mixed_value_or(self) -> None:
        """Test logical OR with mixed values."""
        assert logical_or(1, "hello") is True
        assert logical_or(0, "hello") is True
        assert logical_or("hello", 0) is True
        assert logical_or("", None) is False

    def test_interpreter_object_or(self) -> None:
        """Test logical OR with interpreter objects."""
        true_bool = MockInterpreterValue(True, MachineDialectType.BOOLEAN)
        false_bool = MockInterpreterValue(False, MachineDialectType.BOOLEAN)

        assert logical_or(true_bool, False) is True
        assert logical_or(false_bool, False) is False


class TestEquals:
    """Tests for equals function."""

    def test_numeric_equality(self) -> None:
        """Test numeric equality with type coercion."""
        assert equals(42, 42) is True
        assert equals(42, 42.0) is True
        assert equals(42.0, 42) is True
        assert equals(3.14, 3.14) is True
        assert equals(0, 0.0) is True

    def test_numeric_inequality(self) -> None:
        """Test numeric inequality."""
        assert equals(42, 43) is False
        assert equals(3.14, 3.141) is False

    def test_string_equality(self) -> None:
        """Test string equality."""
        assert equals("hello", "hello") is True
        assert equals("", "") is True
        assert equals("Hello", "hello") is False

    def test_boolean_equality(self) -> None:
        """Test boolean equality."""
        assert equals(True, True) is True
        assert equals(False, False) is True
        assert equals(True, False) is False

    def test_cross_type_inequality(self) -> None:
        """Test inequality across different types."""
        assert equals(42, "42") is False
        assert equals(True, 1) is True  # Boolean and int can be equal in value equality
        assert equals(None, 0) is False

    def test_interpreter_object_equality(self) -> None:
        """Test equality with interpreter objects."""
        int_obj = MockInterpreterValue(42, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(42.0, MachineDialectType.FLOAT)

        assert equals(int_obj, 42) is True
        assert equals(42, int_obj) is True
        assert equals(int_obj, float_obj) is True

    def test_special_float_equality(self) -> None:
        """Test equality with special float values."""
        assert equals(float("inf"), float("inf")) is True
        assert equals(float("-inf"), float("-inf")) is True
        assert equals(float("nan"), float("nan")) is False  # NaN != NaN


class TestNotEquals:
    """Tests for not_equals function."""

    def test_not_equals_basic(self) -> None:
        """Test basic not equals functionality."""
        assert not_equals(42, 43) is True
        assert not_equals(42, 42) is False
        assert not_equals("hello", "world") is True
        assert not_equals("hello", "hello") is False

    def test_not_equals_with_coercion(self) -> None:
        """Test not equals with type coercion."""
        assert not_equals(42, 42.0) is False
        assert not_equals(42, "42") is True


class TestStrictEquals:
    """Tests for strict_equals function."""

    def test_same_type_equality(self) -> None:
        """Test strict equality for same types."""
        assert strict_equals(42, 42) is True
        assert strict_equals(3.14, 3.14) is True
        assert strict_equals("hello", "hello") is True
        assert strict_equals(True, True) is True

    def test_different_type_inequality(self) -> None:
        """Test strict inequality for different types."""
        assert strict_equals(42, 42.0) is False
        assert strict_equals(1, True) is False
        assert strict_equals("42", 42) is False

    def test_same_type_inequality(self) -> None:
        """Test strict inequality within same type."""
        assert strict_equals(42, 43) is False
        assert strict_equals("hello", "world") is False

    def test_special_float_strict_equality(self) -> None:
        """Test strict equality with special float values."""
        assert strict_equals(float("inf"), float("inf")) is True
        assert strict_equals(float("nan"), float("nan")) is False


class TestStrictNotEquals:
    """Tests for strict_not_equals function."""

    def test_strict_not_equals_basic(self) -> None:
        """Test basic strict not equals functionality."""
        assert strict_not_equals(42, 42.0) is True  # Different types
        assert strict_not_equals(42, 42) is False  # Same type and value
        assert strict_not_equals(1, True) is True  # Different types


class TestComparisons:
    """Tests for comparison operators."""

    def test_less_than(self) -> None:
        """Test less than operator."""
        assert less_than(3, 5) is True
        assert less_than(5, 3) is False
        assert less_than(3, 3) is False
        assert less_than(2.5, 3) is True
        assert less_than(3, 2.5) is False

    def test_greater_than(self) -> None:
        """Test greater than operator."""
        assert greater_than(5, 3) is True
        assert greater_than(3, 5) is False
        assert greater_than(3, 3) is False
        assert greater_than(3.5, 3) is True
        assert greater_than(3, 3.5) is False

    def test_less_than_or_equal(self) -> None:
        """Test less than or equal operator."""
        assert less_than_or_equal(3, 5) is True
        assert less_than_or_equal(5, 3) is False
        assert less_than_or_equal(3, 3) is True
        assert less_than_or_equal(2.5, 3) is True

    def test_greater_than_or_equal(self) -> None:
        """Test greater than or equal operator."""
        assert greater_than_or_equal(5, 3) is True
        assert greater_than_or_equal(3, 5) is False
        assert greater_than_or_equal(3, 3) is True
        assert greater_than_or_equal(3.5, 3) is True

    def test_comparison_with_interpreter_objects(self) -> None:
        """Test comparisons with interpreter objects."""
        int_obj = MockInterpreterValue(5, MachineDialectType.INTEGER)

        assert less_than(int_obj, 10) is True
        assert greater_than(int_obj, 3) is True
        assert less_than_or_equal(int_obj, 5) is True
        assert greater_than_or_equal(int_obj, 5) is True

    def test_comparison_with_special_floats(self) -> None:
        """Test comparisons with special float values."""
        inf = float("inf")
        neg_inf = float("-inf")
        nan = float("nan")

        assert greater_than(inf, 1000000) is True
        assert less_than(neg_inf, -1000000) is True

        # NaN comparisons are always False
        assert less_than(nan, 1) is False
        assert greater_than(nan, 1) is False
        assert less_than_or_equal(nan, 1) is False
        assert greater_than_or_equal(nan, 1) is False

    def test_comparison_invalid_operands(self) -> None:
        """Test error handling for invalid comparison operands."""
        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            less_than("hello", "world")

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            greater_than(5, "test")

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            less_than_or_equal(None, 5)

        with pytest.raises(MDTypeError, match="Unsupported operand type"):
            greater_than_or_equal([], 5)
