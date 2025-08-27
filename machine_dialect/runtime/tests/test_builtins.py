"""Tests for the runtime builtins module."""

import math
from typing import Any
from unittest.mock import patch

import pytest

from machine_dialect.runtime.builtins import (
    BUILTIN_FUNCTIONS,
    BuiltinFunction,
    builtin_abs,
    builtin_bool,
    builtin_float,
    builtin_int,
    builtin_is_empty,
    builtin_len,
    builtin_max,
    builtin_min,
    builtin_print,
    builtin_round,
    builtin_say,
    builtin_str,
    builtin_type,
    call_builtin,
    get_builtin,
    register_builtin,
)
from machine_dialect.runtime.errors import (
    ArgumentError,
)
from machine_dialect.runtime.errors import (
    NameError as MDNameError,
)
from machine_dialect.runtime.errors import (
    ValueError as MDValueError,
)
from machine_dialect.runtime.types import MachineDialectType


class MockInterpreterValue:
    """Mock interpreter value object for testing."""

    def __init__(self, value: Any, type_val: MachineDialectType) -> None:
        self.value = value
        self.type = type_val

    def inspect(self) -> str:
        """Mock inspect method."""
        return f"<MockValue: {self.value}>"


class MockEmpty:
    """Mock empty object."""

    pass


class TestBuiltinPrint:
    """Tests for builtin_print function."""

    def test_print_single_value(self) -> None:
        """Test printing a single value."""
        with patch("builtins.print") as mock_print:
            builtin_print(42)
            mock_print.assert_called_once_with("42")

    def test_print_multiple_values(self) -> None:
        """Test printing multiple values."""
        with patch("builtins.print") as mock_print:
            builtin_print("Hello", 42, True, None)
            mock_print.assert_called_once_with("Hello", "42", "Yes", "empty")

    def test_print_empty_call(self) -> None:
        """Test printing with no arguments."""
        with patch("builtins.print") as mock_print:
            builtin_print()
            mock_print.assert_called_once_with()

    def test_print_interpreter_objects(self) -> None:
        """Test printing interpreter objects."""
        int_obj = MockInterpreterValue(42, MachineDialectType.INTEGER)
        str_obj = MockInterpreterValue("hello", MachineDialectType.STRING)

        with patch("builtins.print") as mock_print:
            builtin_print(int_obj, str_obj)
            mock_print.assert_called_once_with("<MockValue: 42>", "<MockValue: hello>")

    def test_print_special_values(self) -> None:
        """Test printing special values."""
        with patch("builtins.print") as mock_print:
            builtin_print(float("inf"), float("-inf"), float("nan"))
            mock_print.assert_called_once_with("inf", "-inf", "nan")


class TestBuiltinSay:
    """Tests for builtin_say function (alias for print)."""

    def test_say_calls_print(self) -> None:
        """Test that say is an alias for print."""
        with patch("builtins.print") as mock_print:
            builtin_say("Hello", "world")
            mock_print.assert_called_once_with("Hello", "world")


class TestBuiltinType:
    """Tests for builtin_type function."""

    def test_type_primitive_values(self) -> None:
        """Test type detection for primitive values."""
        assert builtin_type(None) == "empty"
        assert builtin_type(True) == "boolean"
        assert builtin_type(False) == "boolean"
        assert builtin_type(42) == "integer"
        assert builtin_type(3.14) == "float"
        assert builtin_type("hello") == "text"
        assert builtin_type("http://example.com") == "url"

    def test_type_interpreter_objects(self) -> None:
        """Test type detection for interpreter objects."""
        int_obj = MockInterpreterValue(42, MachineDialectType.INTEGER)
        str_obj = MockInterpreterValue("hello", MachineDialectType.STRING)

        assert builtin_type(int_obj) == "integer"
        assert builtin_type(str_obj) == "text"

    def test_type_callable_objects(self) -> None:
        """Test type detection for callable objects."""
        assert builtin_type(lambda x: x) == "function"
        assert builtin_type(print) == "function"

    def test_type_unknown_objects(self) -> None:
        """Test type detection for unknown objects."""
        assert builtin_type([1, 2, 3]) == "unknown"
        assert builtin_type({"key": "value"}) == "unknown"


class TestBuiltinLen:
    """Tests for builtin_len function."""

    def test_len_string(self) -> None:
        """Test length of strings."""
        assert builtin_len("hello") == 5
        assert builtin_len("") == 0
        assert builtin_len("   ") == 3

    def test_len_list(self) -> None:
        """Test length of lists."""
        assert builtin_len([1, 2, 3]) == 3
        assert builtin_len([]) == 0
        assert builtin_len([None, "", 0]) == 3

    def test_len_tuple(self) -> None:
        """Test length of tuples."""
        assert builtin_len((1, 2, 3)) == 3
        assert builtin_len(()) == 0

    def test_len_dict(self) -> None:
        """Test length of dictionaries."""
        assert builtin_len({"a": 1, "b": 2}) == 2
        assert builtin_len({}) == 0

    def test_len_interpreter_string(self) -> None:
        """Test length of interpreter string objects."""
        str_obj = MockInterpreterValue("hello", MachineDialectType.STRING)
        assert builtin_len(str_obj) == 5

    def test_len_invalid_type(self) -> None:
        """Test error for types without length."""
        with pytest.raises(MDValueError, match="Cannot get length of"):
            builtin_len(42)

        with pytest.raises(MDValueError, match="Cannot get length of"):
            builtin_len(None)

        with pytest.raises(MDValueError, match="Cannot get length of"):
            builtin_len(True)


class TestBuiltinStr:
    """Tests for builtin_str function."""

    def test_str_primitive_values(self) -> None:
        """Test string conversion of primitive values."""
        assert builtin_str(None) == "empty"
        assert builtin_str(True) == "Yes"
        assert builtin_str(False) == "No"
        assert builtin_str(42) == "42"
        assert builtin_str(3.14) == "3.14"
        assert builtin_str("hello") == "hello"

    def test_str_interpreter_objects(self) -> None:
        """Test string conversion of interpreter objects."""
        int_obj = MockInterpreterValue(42, MachineDialectType.INTEGER)
        str_obj = MockInterpreterValue("hello", MachineDialectType.STRING)

        assert builtin_str(int_obj) == "<MockValue: 42>"
        assert builtin_str(str_obj) == "<MockValue: hello>"

    def test_str_objects_with_inspect(self) -> None:
        """Test string conversion of objects with inspect method."""
        obj = MockInterpreterValue("test", MachineDialectType.STRING)
        assert builtin_str(obj) == "<MockValue: test>"  # Uses inspect method

    def test_str_special_floats(self) -> None:
        """Test string conversion of special float values."""
        assert builtin_str(float("inf")) == "inf"
        assert builtin_str(float("-inf")) == "-inf"
        assert builtin_str(float("nan")) == "nan"

    def test_str_collections(self) -> None:
        """Test string conversion of collections."""
        assert builtin_str([1, 2, 3]) == "[1, 2, 3]"
        assert builtin_str({"a": 1}) == "{'a': 1}"


class TestBuiltinInt:
    """Tests for builtin_int function."""

    def test_int_from_integer(self) -> None:
        """Test integer conversion from integers."""
        assert builtin_int(42) == 42
        assert builtin_int(-100) == -100
        assert builtin_int(0) == 0

    def test_int_from_float(self) -> None:
        """Test integer conversion from floats."""
        assert builtin_int(3.14) == 3
        assert builtin_int(3.9) == 3
        assert builtin_int(-2.5) == -2
        assert builtin_int(0.0) == 0

    def test_int_from_string(self) -> None:
        """Test integer conversion from strings."""
        assert builtin_int("42") == 42
        assert builtin_int("-100") == -100
        assert builtin_int("  42  ") == 42
        assert builtin_int("3.0") == 3
        assert builtin_int("3.14") == 3

    def test_int_from_boolean(self) -> None:
        """Test integer conversion from booleans."""
        assert builtin_int(True) == 1
        assert builtin_int(False) == 0

    def test_int_from_none(self) -> None:
        """Test integer conversion from None."""
        assert builtin_int(None) == 0

    def test_int_from_interpreter_objects(self) -> None:
        """Test integer conversion from interpreter objects."""
        int_obj = MockInterpreterValue(42, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(3.14, MachineDialectType.FLOAT)
        str_obj = MockInterpreterValue("123", MachineDialectType.STRING)

        assert builtin_int(int_obj) == 42
        assert builtin_int(float_obj) == 3
        assert builtin_int(str_obj) == 123

    def test_int_invalid_conversion(self) -> None:
        """Test invalid integer conversions."""
        with pytest.raises(MDValueError):
            builtin_int("hello")

        with pytest.raises(MDValueError):
            builtin_int("")

        with pytest.raises(MDValueError):
            builtin_int(float("inf"))

        with pytest.raises(MDValueError):
            builtin_int(float("nan"))


class TestBuiltinFloat:
    """Tests for builtin_float function."""

    def test_float_from_float(self) -> None:
        """Test float conversion from floats."""
        assert builtin_float(3.14) == 3.14
        assert builtin_float(-2.5) == -2.5
        assert builtin_float(0.0) == 0.0

    def test_float_from_integer(self) -> None:
        """Test float conversion from integers."""
        assert builtin_float(42) == 42.0
        assert builtin_float(-100) == -100.0
        assert builtin_float(0) == 0.0

    def test_float_from_string(self) -> None:
        """Test float conversion from strings."""
        assert builtin_float("3.14") == 3.14
        assert builtin_float("-2.5") == -2.5
        assert builtin_float("42") == 42.0
        assert builtin_float("  3.14  ") == 3.14
        assert builtin_float("1e5") == 100000.0

    def test_float_from_boolean(self) -> None:
        """Test float conversion from booleans."""
        assert builtin_float(True) == 1.0
        assert builtin_float(False) == 0.0

    def test_float_from_none(self) -> None:
        """Test float conversion from None."""
        assert builtin_float(None) == 0.0

    def test_float_special_values(self) -> None:
        """Test float conversion of special value strings."""
        assert builtin_float("inf") == float("inf")
        assert builtin_float("-inf") == float("-inf")
        assert math.isnan(builtin_float("nan"))

    def test_float_from_interpreter_objects(self) -> None:
        """Test float conversion from interpreter objects."""
        int_obj = MockInterpreterValue(42, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(3.14, MachineDialectType.FLOAT)
        str_obj = MockInterpreterValue("2.5", MachineDialectType.STRING)

        assert builtin_float(int_obj) == 42.0
        assert builtin_float(float_obj) == 3.14
        assert builtin_float(str_obj) == 2.5

    def test_float_invalid_conversion(self) -> None:
        """Test invalid float conversions."""
        with pytest.raises(MDValueError, match="Cannot convert"):
            builtin_float("hello")

        with pytest.raises(MDValueError, match="Cannot convert"):
            builtin_float("")

        with pytest.raises(MDValueError, match="Cannot convert"):
            builtin_float("12.34.56")


class TestBuiltinBool:
    """Tests for builtin_bool function."""

    def test_bool_from_boolean(self) -> None:
        """Test boolean conversion from booleans."""
        assert builtin_bool(True) is True
        assert builtin_bool(False) is False

    def test_bool_from_numeric(self) -> None:
        """Test boolean conversion from numeric values."""
        assert builtin_bool(0) is False
        assert builtin_bool(1) is True
        assert builtin_bool(-1) is True
        assert builtin_bool(0.0) is False
        assert builtin_bool(3.14) is True

    def test_bool_from_string(self) -> None:
        """Test boolean conversion from strings."""
        assert builtin_bool("") is False
        assert builtin_bool("hello") is True
        assert builtin_bool(" ") is True

    def test_bool_from_none(self) -> None:
        """Test boolean conversion from None."""
        assert builtin_bool(None) is False

    def test_bool_from_interpreter_objects(self) -> None:
        """Test boolean conversion from interpreter objects."""
        true_bool = MockInterpreterValue(True, MachineDialectType.BOOLEAN)
        false_bool = MockInterpreterValue(False, MachineDialectType.BOOLEAN)
        zero_int = MockInterpreterValue(0, MachineDialectType.INTEGER)

        assert builtin_bool(true_bool) is True
        assert builtin_bool(false_bool) is False
        assert builtin_bool(zero_int) is False

    def test_bool_special_floats(self) -> None:
        """Test boolean conversion of special float values."""
        assert builtin_bool(float("inf")) is True
        assert builtin_bool(float("-inf")) is True
        assert builtin_bool(float("nan")) is True


class TestBuiltinAbs:
    """Tests for builtin_abs function."""

    def test_abs_integer(self) -> None:
        """Test absolute value of integers."""
        assert builtin_abs(5) == 5
        assert builtin_abs(-5) == 5
        assert builtin_abs(0) == 0

    def test_abs_float(self) -> None:
        """Test absolute value of floats."""
        assert builtin_abs(3.14) == 3.14
        assert builtin_abs(-3.14) == 3.14
        assert builtin_abs(0.0) == 0.0

    def test_abs_type_preservation(self) -> None:
        """Test that abs preserves integer type."""
        result = builtin_abs(-5)
        assert isinstance(result, int)
        assert result == 5

        result = builtin_abs(-3.14)
        assert isinstance(result, float)
        assert result == 3.14

    def test_abs_interpreter_objects(self) -> None:
        """Test absolute value with interpreter objects."""
        int_obj = MockInterpreterValue(-7, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(-3.14, MachineDialectType.FLOAT)

        assert builtin_abs(int_obj) == 7
        assert builtin_abs(float_obj) == 3.14

    def test_abs_special_floats(self) -> None:
        """Test absolute value with special floats."""
        assert builtin_abs(float("inf")) == float("inf")
        assert builtin_abs(float("-inf")) == float("inf")
        assert math.isnan(builtin_abs(float("nan")))

    def test_abs_invalid_type(self) -> None:
        """Test error for non-numeric types."""
        with pytest.raises(MDValueError, match="Cannot get absolute value"):
            builtin_abs("hello")

        with pytest.raises(MDValueError, match="Cannot get absolute value"):
            builtin_abs(None)


class TestBuiltinMin:
    """Tests for builtin_min function."""

    def test_min_integers(self) -> None:
        """Test minimum of integers."""
        assert builtin_min(5, 3, 8, 1) == 1
        assert builtin_min(42) == 42
        assert builtin_min(-5, -3, -8) == -8

    def test_min_floats(self) -> None:
        """Test minimum of floats."""
        assert builtin_min(3.14, 2.71, 1.41) == 1.41
        assert builtin_min(-1.5, -2.5) == -2.5

    def test_min_mixed_numeric(self) -> None:
        """Test minimum of mixed numeric types."""
        assert builtin_min(5, 3.14, 2, 4.5) == 2
        assert builtin_min(3.14, 2, 4.5, 1) == 1

    def test_min_interpreter_objects(self) -> None:
        """Test minimum with interpreter objects."""
        int_obj = MockInterpreterValue(3, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(2.5, MachineDialectType.FLOAT)

        result = builtin_min(5, int_obj, float_obj, 4)
        assert result == float_obj

    def test_min_special_floats(self) -> None:
        """Test minimum with special float values."""
        assert builtin_min(1, float("inf")) == 1
        assert builtin_min(float("-inf"), 1) == float("-inf")

        # NaN comparisons
        result = builtin_min(float("nan"), 1, 2)
        assert math.isnan(result.value if hasattr(result, "value") else result)

    def test_min_no_arguments(self) -> None:
        """Test error for no arguments."""
        with pytest.raises(ArgumentError, match="requires at least one argument"):
            builtin_min()


class TestBuiltinMax:
    """Tests for builtin_max function."""

    def test_max_integers(self) -> None:
        """Test maximum of integers."""
        assert builtin_max(5, 3, 8, 1) == 8
        assert builtin_max(42) == 42
        assert builtin_max(-5, -3, -8) == -3

    def test_max_floats(self) -> None:
        """Test maximum of floats."""
        assert builtin_max(3.14, 2.71, 1.41) == 3.14
        assert builtin_max(-1.5, -2.5) == -1.5

    def test_max_mixed_numeric(self) -> None:
        """Test maximum of mixed numeric types."""
        assert builtin_max(5, 3.14, 2, 4.5) == 5
        assert builtin_max(3.14, 2, 4.5, 6) == 6

    def test_max_interpreter_objects(self) -> None:
        """Test maximum with interpreter objects."""
        int_obj = MockInterpreterValue(7, MachineDialectType.INTEGER)
        float_obj = MockInterpreterValue(2.5, MachineDialectType.FLOAT)

        result = builtin_max(5, int_obj, float_obj, 4)
        assert result == int_obj

    def test_max_special_floats(self) -> None:
        """Test maximum with special float values."""
        assert builtin_max(1, float("inf")) == float("inf")
        assert builtin_max(float("-inf"), 1) == 1

        # NaN comparisons
        result = builtin_max(float("nan"), 1, 2)
        assert math.isnan(result.value if hasattr(result, "value") else result)

    def test_max_no_arguments(self) -> None:
        """Test error for no arguments."""
        with pytest.raises(ArgumentError, match="requires at least one argument"):
            builtin_max()


class TestBuiltinIsEmpty:
    """Tests for builtin_is_empty function."""

    def test_is_empty_none(self) -> None:
        """Test that None is empty."""
        assert builtin_is_empty(None) is True

    def test_is_empty_empty_object(self) -> None:
        """Test that Empty objects are empty."""

        class Empty:
            def __init__(self) -> None:
                self.type = type("MockType", (), {"name": "EMPTY"})()

        assert builtin_is_empty(Empty()) is True

    def test_is_empty_non_empty_values(self) -> None:
        """Test that other values are not empty."""
        assert builtin_is_empty(False) is False  # Boolean False is not empty
        assert builtin_is_empty(0) is False
        assert builtin_is_empty("") is False  # Empty string is not empty
        assert builtin_is_empty([]) is False
        assert builtin_is_empty(42) is False
        assert builtin_is_empty("hello") is False

    def test_is_empty_interpreter_objects(self) -> None:
        """Test is_empty with interpreter objects."""
        int_obj = MockInterpreterValue(42, MachineDialectType.INTEGER)
        assert builtin_is_empty(int_obj) is False


class TestBuiltinRound:
    """Tests for builtin_round function."""

    def test_round_default_precision(self) -> None:
        """Test rounding with default precision (0)."""
        assert builtin_round(3.14) == 3
        assert builtin_round(3.6) == 4
        assert builtin_round(-2.5) == -2  # Python's banker's rounding
        assert builtin_round(-3.5) == -4

    def test_round_with_precision(self) -> None:
        """Test rounding with specified precision."""
        assert builtin_round(3.14159, 2) == 3.14
        assert builtin_round(3.14159, 0) == 3
        assert builtin_round(1234.5678, -1) == 1230.0
        assert builtin_round(1234.5678, -2) == 1200.0

    def test_round_integer_input(self) -> None:
        """Test rounding integer inputs."""
        assert builtin_round(42) == 42
        assert builtin_round(42, 2) == 42.0

        # With precision 0, integer input returns integer
        result = builtin_round(42, 0)
        assert isinstance(result, int)
        assert result == 42

    def test_round_interpreter_objects(self) -> None:
        """Test rounding with interpreter objects."""
        float_obj = MockInterpreterValue(3.14159, MachineDialectType.FLOAT)
        int_precision = MockInterpreterValue(2, MachineDialectType.INTEGER)

        assert builtin_round(float_obj, int_precision) == 3.14
        assert builtin_round(float_obj) == 3

    def test_round_special_floats(self) -> None:
        """Test rounding special float values."""
        assert builtin_round(float("inf")) == float("inf")
        assert builtin_round(float("-inf")) == float("-inf")
        assert math.isnan(builtin_round(float("nan")))

    def test_round_invalid_value(self) -> None:
        """Test error for non-numeric values."""
        with pytest.raises(MDValueError, match="Cannot round"):
            builtin_round("hello")

        with pytest.raises(MDValueError, match="Cannot round"):
            builtin_round(None)

    def test_round_invalid_precision(self) -> None:
        """Test error for non-integer precision."""
        with pytest.raises(MDValueError, match="Precision must be an integer"):
            builtin_round(3.14, 2.5)

        with pytest.raises(MDValueError, match="Precision must be an integer"):
            builtin_round(3.14, "2")


class TestBuiltinFunctionRegistry:
    """Tests for the built-in function registry system."""

    def test_builtin_functions_registry(self) -> None:
        """Test that all built-in functions are registered."""
        expected_functions = {
            "print",
            "say",
            "type",
            "len",
            "str",
            "int",
            "float",
            "bool",
            "abs",
            "min",
            "max",
            "is_empty",
            "round",
        }

        assert set(BUILTIN_FUNCTIONS.keys()) == expected_functions

        # Check that all entries are BuiltinFunction instances
        for func_name, func in BUILTIN_FUNCTIONS.items():
            assert isinstance(func, BuiltinFunction)
            assert func.name == func_name
            assert callable(func.func)

    def test_get_builtin_existing(self) -> None:
        """Test getting existing built-in functions."""
        print_func = get_builtin("print")
        assert print_func is not None
        assert print_func.name == "print"
        assert print_func.func == builtin_print
        assert print_func.arity == -1

    def test_get_builtin_nonexistent(self) -> None:
        """Test getting non-existent built-in function."""
        assert get_builtin("nonexistent") is None

    def test_register_builtin(self) -> None:
        """Test registering a new built-in function."""

        def my_func(x: int) -> int:
            return x * 2

        register_builtin("double", my_func, 1, "Double a number")

        registered = get_builtin("double")
        assert registered is not None
        assert registered.name == "double"
        assert registered.func == my_func
        assert registered.arity == 1
        assert registered.description == "Double a number"

        # Clean up
        del BUILTIN_FUNCTIONS["double"]

    def test_call_builtin_existing(self) -> None:
        """Test calling existing built-in functions."""
        assert call_builtin("type", 42) == "integer"
        assert call_builtin("abs", -5) == 5

        # Test variadic function
        with patch("builtins.print") as mock_print:
            call_builtin("print", "Hello", "World")
            mock_print.assert_called_once_with("Hello", "World")

    def test_call_builtin_nonexistent(self) -> None:
        """Test calling non-existent built-in function."""
        with pytest.raises(MDNameError, match="not defined"):
            call_builtin("nonexistent", 42)

    def test_call_builtin_wrong_arity(self) -> None:
        """Test calling built-in function with wrong number of arguments."""
        # type() expects exactly 1 argument
        with pytest.raises(ArgumentError, match="expects 1 arguments, got 0"):
            call_builtin("type")

        with pytest.raises(ArgumentError, match="expects 1 arguments, got 2"):
            call_builtin("type", 42, "extra")

    def test_call_builtin_variadic_functions(self) -> None:
        """Test calling variadic built-in functions."""
        # print is variadic (arity -1), should accept any number of args
        with patch("builtins.print") as mock_print:
            call_builtin("print")  # 0 args OK
            call_builtin("print", "one")  # 1 arg OK
            call_builtin("print", "one", "two", "three")  # 3 args OK
            assert mock_print.call_count == 3

    def test_builtin_function_descriptions(self) -> None:
        """Test that built-in functions have proper descriptions."""
        for func in BUILTIN_FUNCTIONS.values():
            assert func.description  # Should not be empty
            assert isinstance(func.description, str)
            assert len(func.description) > 0

    def test_builtin_function_arities(self) -> None:
        """Test that built-in functions have correct arities."""
        # Fixed arity functions
        assert BUILTIN_FUNCTIONS["type"].arity == 1
        assert BUILTIN_FUNCTIONS["len"].arity == 1
        assert BUILTIN_FUNCTIONS["str"].arity == 1
        assert BUILTIN_FUNCTIONS["int"].arity == 1
        assert BUILTIN_FUNCTIONS["float"].arity == 1
        assert BUILTIN_FUNCTIONS["bool"].arity == 1
        assert BUILTIN_FUNCTIONS["abs"].arity == 1
        assert BUILTIN_FUNCTIONS["is_empty"].arity == 1

        # Variadic functions
        assert BUILTIN_FUNCTIONS["print"].arity == -1
        assert BUILTIN_FUNCTIONS["say"].arity == -1
        assert BUILTIN_FUNCTIONS["min"].arity == -1
        assert BUILTIN_FUNCTIONS["max"].arity == -1
        assert BUILTIN_FUNCTIONS["round"].arity == -1  # 1 or 2 args


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_string_operations(self) -> None:
        """Test operations with empty strings."""
        assert builtin_len("") == 0
        assert builtin_str("") == ""
        assert builtin_bool("") is False

    def test_zero_operations(self) -> None:
        """Test operations with zero values."""
        assert builtin_bool(0) is False
        assert builtin_bool(0.0) is False
        assert builtin_abs(0) == 0
        assert builtin_abs(0.0) == 0.0
        assert builtin_int(0) == 0
        assert builtin_float(0) == 0.0

    def test_large_number_operations(self) -> None:
        """Test operations with large numbers."""
        large_int = 999999999999999999
        large_float = 1e100

        assert builtin_str(large_int) == str(large_int)
        assert builtin_abs(large_int) == large_int
        assert builtin_abs(-large_int) == large_int
        assert builtin_str(large_float) == str(large_float)

    def test_unicode_string_operations(self) -> None:
        """Test operations with Unicode strings."""
        unicode_str = "Hello, 世界! 🌍"
        assert builtin_len(unicode_str) == 12  # Length includes Unicode chars
        assert builtin_str(unicode_str) == unicode_str
        assert builtin_bool(unicode_str) is True
