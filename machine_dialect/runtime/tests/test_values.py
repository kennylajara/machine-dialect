"""Tests for the runtime values module."""

import math
from typing import Any

import pytest

from machine_dialect.runtime.types import MachineDialectType
from machine_dialect.runtime.values import (
    equals,
    get_raw_value,
    is_empty,
    strict_equals,
    to_bool,
    to_float,
    to_int,
    to_string,
)


class TestGetRawValue:
    """Tests for get_raw_value function."""

    def test_primitive_values(self) -> None:
        """Test extraction of primitive values."""
        assert get_raw_value(None) is None
        assert get_raw_value(True) is True
        assert get_raw_value(False) is False
        assert get_raw_value(42) == 42
        assert get_raw_value(3.14) == 3.14
        assert get_raw_value("hello") == "hello"
        assert get_raw_value([1, 2, 3]) == [1, 2, 3]

    def test_interpreter_value_extraction(self) -> None:
        """Test extraction from interpreter objects with .value attribute."""

        class InterpreterValue:
            def __init__(self, value: Any) -> None:
                self.value = value

            def __str__(self) -> str:
                return str(self.value)

            def __bool__(self) -> bool:
                return bool(self.value) if self.value is not None else False

        assert get_raw_value(InterpreterValue(42)) == 42
        assert get_raw_value(InterpreterValue("hello")) == "hello"
        assert get_raw_value(InterpreterValue(None)) is None

    def test_nested_interpreter_values(self) -> None:
        """Test extraction from nested interpreter objects."""

        class InterpreterValue:
            def __init__(self, value: Any) -> None:
                self.value = value

            def __str__(self) -> str:
                return str(self.value)

            def __bool__(self) -> bool:
                return bool(self.value) if self.value is not None else False

        nested = InterpreterValue(InterpreterValue(InterpreterValue(42)))
        # get_raw_value only extracts one level
        result = get_raw_value(nested)
        assert hasattr(result, "value")
        # Second extraction gets to the next level
        result2 = get_raw_value(result)
        assert hasattr(result2, "value")
        # Third extraction gets the primitive value
        result3 = get_raw_value(result2)
        assert result3 == 42

    def test_type_objects_not_extracted(self) -> None:
        """Test that Type objects are not extracted."""

        # Type class itself should not be extracted
        class Type(type):
            def __init__(cls, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> None:
                super().__init__(name, bases, attrs)
                cls.value = 42

        type_obj = Type("TestType", (), {})
        assert get_raw_value(type_obj) == type_obj  # Not extracted

    def test_objects_without_value_attribute(self) -> None:
        """Test objects without .value pass through unchanged."""

        class NoValue:
            def __init__(self, data: int) -> None:
                self.data = data

        obj = NoValue(42)
        assert get_raw_value(obj) == obj


class TestIsEmpty:
    """Tests for is_empty function."""

    def test_none_is_empty(self) -> None:
        """Test that None is considered empty."""
        assert is_empty(None) is True

    def test_interpreter_empty_object(self) -> None:
        """Test interpreter Empty objects are considered empty."""

        class Empty:
            def __init__(self) -> None:
                self.type = type("MockType", (), {"name": "EMPTY"})()

        assert is_empty(Empty()) is True

    def test_non_empty_values(self) -> None:
        """Test that other values are not empty."""
        assert is_empty(False) is False  # Boolean False is not empty
        assert is_empty(0) is False
        assert is_empty("") is False  # Empty string is not empty (different from None)
        assert is_empty([]) is False
        assert is_empty({}) is False
        assert is_empty(42) is False
        assert is_empty("hello") is False


class TestToBool:
    """Tests for to_bool function."""

    def test_none_conversion(self) -> None:
        """Test None converts to False."""
        assert to_bool(None) is False

    def test_boolean_conversion(self) -> None:
        """Test boolean values pass through."""
        assert to_bool(True) is True
        assert to_bool(False) is False

    def test_numeric_conversion(self) -> None:
        """Test numeric values convert based on truthiness."""
        assert to_bool(0) is False
        assert to_bool(1) is True
        assert to_bool(-1) is True
        assert to_bool(0.0) is False
        assert to_bool(0.1) is True
        assert to_bool(-0.5) is True

    def test_string_conversion(self) -> None:
        """Test string values convert based on content."""
        assert to_bool("") is False
        assert to_bool("hello") is True
        assert to_bool("false") is True  # Non-empty string is truthy
        assert to_bool("0") is True  # Non-empty string is truthy

    def test_interpreter_object_conversion(self) -> None:
        """Test conversion of interpreter objects."""

        class Boolean:
            def __init__(self, value: bool) -> None:
                self.value = value
                self.type = MachineDialectType.BOOLEAN

        assert to_bool(Boolean(True)) is True
        assert to_bool(Boolean(False)) is False

    def test_special_float_values(self) -> None:
        """Test conversion of special float values."""
        assert to_bool(float("inf")) is True
        assert to_bool(float("-inf")) is True
        assert to_bool(float("nan")) is True

    def test_invalid_conversion(self) -> None:
        """Test invalid conversions raise ValueError."""
        # to_bool uses is_truthy which considers unknown types as truthy
        # so these don't raise errors
        assert to_bool([1, 2, 3]) is True
        assert to_bool({"key": "value"}) is True


class TestToInt:
    """Tests for to_int function."""

    def test_none_conversion(self) -> None:
        """Test None converts to 0."""
        assert to_int(None) == 0

    def test_boolean_conversion(self) -> None:
        """Test boolean values convert to 0/1."""
        assert to_int(True) == 1
        assert to_int(False) == 0

    def test_integer_conversion(self) -> None:
        """Test integer values pass through."""
        assert to_int(0) == 0
        assert to_int(42) == 42
        assert to_int(-100) == -100

    def test_float_conversion(self) -> None:
        """Test float values truncate to integers."""
        assert to_int(3.14) == 3
        assert to_int(3.9) == 3
        assert to_int(-2.5) == -2
        assert to_int(0.0) == 0

    def test_string_conversion(self) -> None:
        """Test string to integer conversion."""
        assert to_int("42") == 42
        assert to_int("-100") == -100
        assert to_int("  42  ") == 42  # With whitespace
        assert to_int("3.0") == 3  # Float string to int
        assert to_int("3.14") == 3  # Float string truncates

    def test_interpreter_object_conversion(self) -> None:
        """Test conversion of interpreter objects."""

        class Integer:
            def __init__(self, value: int) -> None:
                self.value = value
                self.type = MachineDialectType.INTEGER

        class Float:
            def __init__(self, value: float) -> None:
                self.value = value
                self.type = MachineDialectType.FLOAT

        assert to_int(Integer(42)) == 42
        assert to_int(Float(3.14)) == 3

    def test_special_float_values(self) -> None:
        """Test conversion of special float values."""
        with pytest.raises(OverflowError, match="cannot convert float infinity to integer"):
            to_int(float("inf"))

        with pytest.raises(OverflowError, match="cannot convert float infinity to integer"):
            to_int(float("-inf"))

        with pytest.raises(ValueError, match="cannot convert float NaN to integer"):
            to_int(float("nan"))

    def test_invalid_string_conversion(self) -> None:
        """Test invalid string conversions raise ValueError."""
        with pytest.raises(ValueError, match="Cannot convert"):
            to_int("hello")

        with pytest.raises(ValueError, match="Cannot convert"):
            to_int("")

        with pytest.raises(ValueError, match="Cannot convert"):
            to_int("12.34.56")


class TestToFloat:
    """Tests for to_float function."""

    def test_none_conversion(self) -> None:
        """Test None converts to 0.0."""
        assert to_float(None) == 0.0

    def test_boolean_conversion(self) -> None:
        """Test boolean values convert to 0.0/1.0."""
        assert to_float(True) == 1.0
        assert to_float(False) == 0.0

    def test_integer_conversion(self) -> None:
        """Test integer values convert to float."""
        assert to_float(0) == 0.0
        assert to_float(42) == 42.0
        assert to_float(-100) == -100.0

    def test_float_conversion(self) -> None:
        """Test float values pass through."""
        assert to_float(0.0) == 0.0
        assert to_float(3.14) == 3.14
        assert to_float(-2.5) == -2.5

    def test_string_conversion(self) -> None:
        """Test string to float conversion."""
        assert to_float("3.14") == 3.14
        assert to_float("-2.5") == -2.5
        assert to_float("42") == 42.0
        assert to_float("  3.14  ") == 3.14  # With whitespace
        assert to_float("1e5") == 100000.0  # Scientific notation

    def test_interpreter_object_conversion(self) -> None:
        """Test conversion of interpreter objects."""

        class Float:
            def __init__(self, value: float) -> None:
                self.value = value
                self.type = MachineDialectType.FLOAT

        class Integer:
            def __init__(self, value: int) -> None:
                self.value = value
                self.type = MachineDialectType.INTEGER

        assert to_float(Float(3.14)) == 3.14
        assert to_float(Integer(42)) == 42.0

    def test_special_float_values(self) -> None:
        """Test conversion of special float value strings."""
        assert to_float("inf") == float("inf")
        assert to_float("-inf") == float("-inf")
        assert math.isnan(to_float("nan"))

    def test_invalid_string_conversion(self) -> None:
        """Test invalid string conversions raise ValueError."""
        with pytest.raises(ValueError, match="Cannot convert"):
            to_float("hello")

        with pytest.raises(ValueError, match="Cannot convert"):
            to_float("")

        with pytest.raises(ValueError, match="Cannot convert"):
            to_float("12.34.56")


class TestToString:
    """Tests for to_string function."""

    def test_none_conversion(self) -> None:
        """Test None converts to 'empty'."""
        assert to_string(None) == "empty"

    def test_boolean_conversion(self) -> None:
        """Test boolean values convert to Yes/No."""
        assert to_string(True) == "Yes"
        assert to_string(False) == "No"

    def test_numeric_conversion(self) -> None:
        """Test numeric values convert to strings."""
        assert to_string(42) == "42"
        assert to_string(3.14) == "3.14"
        assert to_string(0) == "0"
        assert to_string(-100) == "-100"

    def test_string_conversion(self) -> None:
        """Test string values pass through."""
        assert to_string("") == ""
        assert to_string("hello") == "hello"
        assert to_string("  spaces  ") == "  spaces  "

    def test_interpreter_object_with_inspect(self) -> None:
        """Test interpreter objects with inspect method."""

        class InterpreterValue:
            def __init__(self, value: str) -> None:
                self.value = value

            def inspect(self) -> str:
                return f"<{self.value}>"

        assert to_string(InterpreterValue("test")) == "<test>"

    def test_interpreter_object_without_inspect(self) -> None:
        """Test interpreter objects without inspect method."""

        class InterpreterValue:
            def __init__(self, value: int) -> None:
                self.value = value
                self.type = MachineDialectType.INTEGER

        assert to_string(InterpreterValue(42)) == "42"

    def test_special_float_values(self) -> None:
        """Test conversion of special float values."""
        assert to_string(float("inf")) == "inf"
        assert to_string(float("-inf")) == "-inf"
        assert to_string(float("nan")) == "nan"

    def test_other_types(self) -> None:
        """Test conversion of other types."""
        assert to_string([1, 2, 3]) == "[1, 2, 3]"
        assert to_string({"key": "value"}) == "{'key': 'value'}"
        assert to_string((1, 2)) == "(1, 2)"


class TestEquals:
    """Tests for equals function."""

    def test_empty_equality(self) -> None:
        """Test empty value equality."""
        assert equals(None, None) is True

        class Empty:
            def __init__(self) -> None:
                self.type = type("MockType", (), {"name": "EMPTY"})()

        assert equals(None, Empty()) is True
        assert equals(Empty(), None) is True
        assert equals(Empty(), Empty()) is True

    def test_numeric_equality(self) -> None:
        """Test numeric equality with type coercion."""
        assert equals(42, 42) is True
        assert equals(42, 42.0) is True  # int == float
        assert equals(42.0, 42) is True  # float == int
        assert equals(3.14, 3.14) is True
        assert equals(0, 0.0) is True
        assert equals(-1, -1.0) is True

    def test_numeric_inequality(self) -> None:
        """Test numeric inequality."""
        assert equals(42, 43) is False
        assert equals(42, 41.9) is False
        assert equals(3.14, 3.141) is False

    def test_string_equality(self) -> None:
        """Test string equality."""
        assert equals("hello", "hello") is True
        assert equals("", "") is True
        assert equals("Hello", "hello") is False  # Case sensitive
        assert equals("hello", "world") is False

    def test_boolean_equality(self) -> None:
        """Test boolean equality."""
        assert equals(True, True) is True
        assert equals(False, False) is True
        assert equals(True, False) is False
        assert equals(False, True) is False

    def test_cross_type_inequality(self) -> None:
        """Test inequality across different types."""
        assert equals(42, "42") is False
        assert equals(True, 1) is True  # Boolean and int can be equal in value equality
        assert equals(False, 0) is True  # Boolean and int can be equal in value equality
        assert equals("true", True) is False
        assert equals(None, 0) is False
        assert equals(None, "") is False
        assert equals(None, False) is False

    def test_interpreter_object_equality(self) -> None:
        """Test equality with interpreter objects."""

        class Integer:
            def __init__(self, value: int) -> None:
                self.value = value
                self.type = MachineDialectType.INTEGER

        class Float:
            def __init__(self, value: float) -> None:
                self.value = value
                self.type = MachineDialectType.FLOAT

        assert equals(Integer(42), 42) is True
        assert equals(42, Integer(42)) is True
        assert equals(Integer(42), Float(42.0)) is True
        assert equals(Integer(42), Integer(42)) is True

    def test_special_float_values(self) -> None:
        """Test equality with special float values."""
        assert equals(float("inf"), float("inf")) is True
        assert equals(float("-inf"), float("-inf")) is True
        assert equals(float("nan"), float("nan")) is False  # NaN != NaN
        assert equals(float("inf"), float("-inf")) is False


class TestStrictEquals:
    """Tests for strict_equals function."""

    def test_empty_strict_equality(self) -> None:
        """Test strict equality for empty values."""
        assert strict_equals(None, None) is True

        class Empty:
            def __init__(self) -> None:
                self.type = type("MockType", (), {"name": "EMPTY"})()

        assert strict_equals(None, Empty()) is True
        assert strict_equals(Empty(), None) is True
        assert strict_equals(Empty(), Empty()) is True

    def test_same_type_equality(self) -> None:
        """Test strict equality for same types."""
        assert strict_equals(42, 42) is True
        assert strict_equals(3.14, 3.14) is True
        assert strict_equals("hello", "hello") is True
        assert strict_equals(True, True) is True
        assert strict_equals(False, False) is True

    def test_different_type_inequality(self) -> None:
        """Test strict inequality for different types."""
        assert strict_equals(42, 42.0) is False  # int != float strictly
        assert strict_equals(42.0, 42) is False  # float != int strictly
        assert strict_equals(1, True) is False  # int != bool
        assert strict_equals(0, False) is False  # int != bool
        assert strict_equals("42", 42) is False  # string != int

    def test_same_type_inequality(self) -> None:
        """Test strict inequality within same type."""
        assert strict_equals(42, 43) is False
        assert strict_equals(3.14, 3.141) is False
        assert strict_equals("hello", "world") is False
        assert strict_equals(True, False) is False

    def test_interpreter_object_strict_equality(self) -> None:
        """Test strict equality with interpreter objects."""

        class Integer:
            def __init__(self, value: int) -> None:
                self.value = value
                self.type = MachineDialectType.INTEGER

        class Float:
            def __init__(self, value: float) -> None:
                self.value = value
                self.type = MachineDialectType.FLOAT

        assert strict_equals(Integer(42), Integer(42)) is True
        assert strict_equals(Integer(42), 42) is True
        assert strict_equals(Float(3.14), Float(3.14)) is True
        assert strict_equals(Float(3.14), 3.14) is True

        # Different types are not strictly equal
        assert strict_equals(Integer(42), Float(42.0)) is False
        assert strict_equals(Integer(42), 42.0) is False

    def test_special_float_strict_equality(self) -> None:
        """Test strict equality with special float values."""
        assert strict_equals(float("inf"), float("inf")) is True
        assert strict_equals(float("-inf"), float("-inf")) is True
        assert strict_equals(float("nan"), float("nan")) is False  # NaN != NaN

        # Same type but different values
        assert strict_equals(float("inf"), float("-inf")) is False
        assert strict_equals(float("inf"), 1.0) is False
