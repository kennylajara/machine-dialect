"""Tests for the runtime type system module."""


from machine_dialect.runtime.types import (
    MachineDialectType,
    coerce_to_number,
    get_type,
    get_type_name,
    is_numeric,
    is_truthy,
)


class TestGetType:
    """Tests for get_type function."""

    def test_none_type(self) -> None:
        """Test None returns EMPTY type."""
        assert get_type(None) == MachineDialectType.EMPTY

    def test_boolean_type(self) -> None:
        """Test boolean values return BOOLEAN type."""
        assert get_type(True) == MachineDialectType.BOOLEAN
        assert get_type(False) == MachineDialectType.BOOLEAN

    def test_integer_type(self) -> None:
        """Test integer values return INTEGER type."""
        assert get_type(0) == MachineDialectType.INTEGER
        assert get_type(42) == MachineDialectType.INTEGER
        assert get_type(-100) == MachineDialectType.INTEGER

    def test_float_type(self) -> None:
        """Test float values return FLOAT type."""
        assert get_type(0.0) == MachineDialectType.FLOAT
        assert get_type(3.14) == MachineDialectType.FLOAT
        assert get_type(-2.5) == MachineDialectType.FLOAT
        assert get_type(float("inf")) == MachineDialectType.FLOAT
        assert get_type(float("-inf")) == MachineDialectType.FLOAT
        assert get_type(float("nan")) == MachineDialectType.FLOAT

    def test_string_type(self) -> None:
        """Test string values return STRING type."""
        assert get_type("") == MachineDialectType.STRING
        assert get_type("hello") == MachineDialectType.STRING
        assert get_type("123") == MachineDialectType.STRING

    def test_url_type(self) -> None:
        """Test URL strings return URL type."""
        assert get_type("http://example.com") == MachineDialectType.URL
        assert get_type("https://example.com") == MachineDialectType.URL
        assert get_type("ftp://example.com") == MachineDialectType.URL
        assert get_type("file:///path/to/file") == MachineDialectType.URL

    def test_url_with_complex_structure(self) -> None:
        """Test URLs with query params and fragments."""
        assert get_type("http://example.com/path?query=1#fragment") == MachineDialectType.URL
        assert get_type("https://user:pass@host.com:8080/path") == MachineDialectType.URL

    def test_callable_type(self) -> None:
        """Test callable objects return FUNCTION type."""
        assert get_type(lambda x: x) == MachineDialectType.FUNCTION
        assert get_type(print) == MachineDialectType.FUNCTION
        assert get_type(TestGetType) == MachineDialectType.FUNCTION
        assert get_type(self.test_callable_type) == MachineDialectType.FUNCTION

    def test_interpreter_object_with_type(self) -> None:
        """Test objects with .type attribute from interpreter."""

        class InterpreterValue:
            def __init__(self, type_val: MachineDialectType) -> None:
                self.type = type_val

        assert get_type(InterpreterValue(MachineDialectType.INTEGER)) == MachineDialectType.INTEGER
        assert get_type(InterpreterValue(MachineDialectType.STRING)) == MachineDialectType.STRING

    def test_unknown_type(self) -> None:
        """Test objects without recognized types return UNKNOWN."""
        assert get_type([]) == MachineDialectType.UNKNOWN
        assert get_type({}) == MachineDialectType.UNKNOWN
        assert get_type(set()) == MachineDialectType.UNKNOWN
        assert get_type(object()) == MachineDialectType.UNKNOWN


class TestGetTypeName:
    """Tests for get_type_name function."""

    def test_type_names(self) -> None:
        """Test human-readable type names."""
        assert get_type_name(None) == "empty"
        assert get_type_name(True) == "boolean"
        assert get_type_name(42) == "integer"
        assert get_type_name(3.14) == "float"
        assert get_type_name("hello") == "text"
        assert get_type_name("http://example.com") == "url"
        assert get_type_name(lambda: None) == "function"
        assert get_type_name([]) == "unknown"


class TestIsTruthy:
    """Tests for is_truthy function."""

    def test_falsy_values(self) -> None:
        """Test values that are considered falsy."""
        assert not is_truthy(None)
        assert not is_truthy(False)
        assert not is_truthy(0)
        assert not is_truthy(0.0)
        assert not is_truthy("")

    def test_truthy_values(self) -> None:
        """Test values that are considered truthy."""
        assert is_truthy(True)
        assert is_truthy(1)
        assert is_truthy(-1)
        assert is_truthy(0.1)
        assert is_truthy("hello")
        assert is_truthy(" ")  # Non-empty string
        assert is_truthy([])  # Empty list is truthy (not a recognized type)
        assert is_truthy({})  # Empty dict is truthy (not a recognized type)

    def test_interpreter_empty_object(self) -> None:
        """Test interpreter Empty objects are falsy."""

        class Empty:
            def __init__(self) -> None:
                self.type = type("MockType", (), {"name": "EMPTY"})()

        empty_obj = Empty()
        assert not is_truthy(empty_obj)

    def test_interpreter_boolean_object(self) -> None:
        """Test interpreter Boolean objects."""

        class Boolean:
            def __init__(self, value: bool) -> None:
                self.value = value
                self.type = MachineDialectType.BOOLEAN

        assert is_truthy(Boolean(True))
        assert not is_truthy(Boolean(False))

    def test_interpreter_numeric_objects(self) -> None:
        """Test interpreter numeric objects."""

        class Integer:
            def __init__(self, value: int) -> None:
                self.value = value
                self.type = MachineDialectType.INTEGER

        class Float:
            def __init__(self, value: float) -> None:
                self.value = value
                self.type = MachineDialectType.FLOAT

        assert is_truthy(Integer(1))
        assert not is_truthy(Integer(0))
        assert is_truthy(Float(0.1))
        assert not is_truthy(Float(0.0))

    def test_interpreter_string_object(self) -> None:
        """Test interpreter String objects."""

        class String:
            def __init__(self, value: str) -> None:
                self.value = value
                self.type = MachineDialectType.STRING

        assert is_truthy(String("hello"))
        assert not is_truthy(String(""))

    def test_special_float_values(self) -> None:
        """Test special float values."""
        assert is_truthy(float("inf"))
        assert is_truthy(float("-inf"))
        assert is_truthy(float("nan"))  # NaN is truthy


class TestIsNumeric:
    """Tests for is_numeric function."""

    def test_numeric_types(self) -> None:
        """Test values that are considered numeric."""
        assert is_numeric(0)
        assert is_numeric(42)
        assert is_numeric(-100)
        assert is_numeric(0.0)
        assert is_numeric(3.14)
        assert is_numeric(-2.5)
        assert is_numeric(float("inf"))
        assert is_numeric(float("-inf"))
        assert is_numeric(float("nan"))

    def test_non_numeric_types(self) -> None:
        """Test values that are not considered numeric."""
        assert not is_numeric(None)
        assert not is_numeric(True)  # Boolean is not numeric
        assert not is_numeric(False)
        assert not is_numeric("")
        assert not is_numeric("123")
        assert not is_numeric([])
        assert not is_numeric({})

    def test_interpreter_numeric_objects(self) -> None:
        """Test interpreter numeric objects."""

        class Integer:
            def __init__(self, value: int) -> None:
                self.value = value
                self.type = MachineDialectType.INTEGER

        class Float:
            def __init__(self, value: float) -> None:
                self.value = value
                self.type = MachineDialectType.FLOAT

        assert is_numeric(Integer(42))
        assert is_numeric(Float(3.14))

    def test_interpreter_non_numeric_objects(self) -> None:
        """Test interpreter non-numeric objects."""

        class String:
            def __init__(self, value: str) -> None:
                self.value = value
                self.type = MachineDialectType.STRING

        class Boolean:
            def __init__(self, value: bool) -> None:
                self.value = value
                self.type = MachineDialectType.BOOLEAN

        assert not is_numeric(String("123"))
        assert not is_numeric(Boolean(True))


class TestCoerceToNumber:
    """Tests for coerce_to_number function."""

    def test_integer_coercion(self) -> None:
        """Test integer values pass through."""
        assert coerce_to_number(0) == 0
        assert coerce_to_number(42) == 42
        assert coerce_to_number(-100) == -100

    def test_float_coercion(self) -> None:
        """Test float values pass through."""
        assert coerce_to_number(0.0) == 0.0
        assert coerce_to_number(3.14) == 3.14
        assert coerce_to_number(-2.5) == -2.5

    def test_string_to_integer_coercion(self) -> None:
        """Test string to integer conversion."""
        assert coerce_to_number("0") == 0
        assert coerce_to_number("42") == 42
        assert coerce_to_number("-100") == -100
        assert coerce_to_number("  42  ") == 42  # With whitespace

    def test_string_to_float_coercion(self) -> None:
        """Test string to float conversion."""
        assert coerce_to_number("3.14") == 3.14
        assert coerce_to_number("-2.5") == -2.5
        assert coerce_to_number("0.0") == 0.0
        assert coerce_to_number("  3.14  ") == 3.14  # With whitespace

    def test_string_integer_with_decimal_point(self) -> None:
        """Test strings like '3.0' convert to integers."""
        assert coerce_to_number("3.0") == 3
        assert coerce_to_number("42.0") == 42
        assert coerce_to_number("-10.0") == -10

    def test_scientific_notation(self) -> None:
        """Test scientific notation conversion."""
        assert coerce_to_number("1e5") == 100000.0
        assert coerce_to_number("1.5e2") == 150.0
        assert coerce_to_number("1E-2") == 0.01

    def test_boolean_coercion(self) -> None:
        """Test boolean to number conversion."""
        assert coerce_to_number(True) == 1
        assert coerce_to_number(False) == 0

    def test_invalid_string_coercion(self) -> None:
        """Test invalid strings return None."""
        assert coerce_to_number("") is None
        assert coerce_to_number("hello") is None
        assert coerce_to_number("12.34.56") is None
        assert coerce_to_number("1 2 3") is None

    def test_none_coercion(self) -> None:
        """Test None returns None."""
        assert coerce_to_number(None) is None

    def test_interpreter_object_coercion(self) -> None:
        """Test interpreter object value extraction."""

        class Integer:
            def __init__(self, value: int) -> None:
                self.value = value
                self.type = MachineDialectType.INTEGER

        class String:
            def __init__(self, value: str) -> None:
                self.value = value
                self.type = MachineDialectType.STRING

        assert coerce_to_number(Integer(42)) == 42
        assert coerce_to_number(String("123")) == 123
        assert coerce_to_number(String("3.14")) == 3.14
        assert coerce_to_number(String("hello")) is None

    def test_special_float_strings(self) -> None:
        """Test special float value strings."""
        # These special strings are NOT supported by coerce_to_number
        result = coerce_to_number("inf")
        assert result is None

        result = coerce_to_number("-inf")
        assert result is None

        result = coerce_to_number("nan")
        assert result is None

    def test_edge_cases(self) -> None:
        """Test edge cases for number coercion."""
        # Very large numbers
        assert coerce_to_number("999999999999999999") == 999999999999999999

        # Very small numbers
        assert coerce_to_number("0.000000000001") == 0.000000000001

        # Negative zero
        assert coerce_to_number("-0") == 0
        assert coerce_to_number("-0.0") == -0.0
