"""Tests for MIR type system."""

from machine_dialect.mir.mir_types import (
    MIRType,
    coerce_types,
    get_binary_op_result_type,
    get_unary_op_result_type,
    infer_type,
    is_comparable_type,
    is_numeric_type,
)


class TestMIRTypes:
    """Test MIR type system functionality."""

    def test_type_string_representation(self) -> None:
        """Test string representation of types."""
        assert str(MIRType.INT) == "int"
        assert str(MIRType.FLOAT) == "float"
        assert str(MIRType.STRING) == "string"
        assert str(MIRType.BOOL) == "bool"
        assert str(MIRType.EMPTY) == "empty"
        assert str(MIRType.FUNCTION) == "function"

    def test_infer_type(self) -> None:
        """Test type inference from Python values."""
        # Primitives
        assert infer_type(42) == MIRType.INT
        assert infer_type(3.14) == MIRType.FLOAT
        assert infer_type("hello") == MIRType.STRING
        assert infer_type(True) == MIRType.BOOL
        assert infer_type(False) == MIRType.BOOL
        assert infer_type(None) == MIRType.EMPTY

        # URLs
        assert infer_type("http://example.com") == MIRType.URL
        assert infer_type("https://example.com") == MIRType.URL
        assert infer_type("ftp://example.com") == MIRType.URL
        assert infer_type("file:///path/to/file") == MIRType.URL

        # Unknown types
        assert infer_type([1, 2, 3]) == MIRType.UNKNOWN
        assert infer_type({"key": "value"}) == MIRType.UNKNOWN

    def test_is_numeric_type(self) -> None:
        """Test numeric type checking."""
        assert is_numeric_type(MIRType.INT)
        assert is_numeric_type(MIRType.FLOAT)
        assert not is_numeric_type(MIRType.STRING)
        assert not is_numeric_type(MIRType.BOOL)
        assert not is_numeric_type(MIRType.EMPTY)

    def test_is_comparable_type(self) -> None:
        """Test comparable type checking."""
        assert is_comparable_type(MIRType.INT)
        assert is_comparable_type(MIRType.FLOAT)
        assert is_comparable_type(MIRType.STRING)
        assert is_comparable_type(MIRType.BOOL)
        assert not is_comparable_type(MIRType.EMPTY)
        assert not is_comparable_type(MIRType.FUNCTION)

    def test_coerce_types(self) -> None:
        """Test type coercion rules."""
        # Same types - no coercion
        assert coerce_types(MIRType.INT, MIRType.INT) == MIRType.INT
        assert coerce_types(MIRType.STRING, MIRType.STRING) == MIRType.STRING

        # Numeric coercion
        assert coerce_types(MIRType.INT, MIRType.FLOAT) == MIRType.FLOAT
        assert coerce_types(MIRType.FLOAT, MIRType.INT) == MIRType.FLOAT

        # String concatenation
        assert coerce_types(MIRType.STRING, MIRType.INT) == MIRType.STRING
        assert coerce_types(MIRType.BOOL, MIRType.STRING) == MIRType.STRING

        # Invalid coercion
        assert coerce_types(MIRType.INT, MIRType.BOOL) is None
        assert coerce_types(MIRType.FUNCTION, MIRType.EMPTY) is None

    def test_get_binary_op_result_type(self) -> None:
        """Test binary operation result type inference."""
        # Comparison operators always return bool
        assert get_binary_op_result_type("==", MIRType.INT, MIRType.INT) == MIRType.BOOL
        assert get_binary_op_result_type("!=", MIRType.STRING, MIRType.STRING) == MIRType.BOOL
        assert get_binary_op_result_type(">", MIRType.FLOAT, MIRType.INT) == MIRType.BOOL
        assert get_binary_op_result_type("<=", MIRType.INT, MIRType.FLOAT) == MIRType.BOOL

        # Logical operators return bool
        assert get_binary_op_result_type("and", MIRType.BOOL, MIRType.BOOL) == MIRType.BOOL
        assert get_binary_op_result_type("or", MIRType.BOOL, MIRType.BOOL) == MIRType.BOOL

        # Arithmetic operators
        assert get_binary_op_result_type("+", MIRType.INT, MIRType.INT) == MIRType.INT
        assert get_binary_op_result_type("-", MIRType.FLOAT, MIRType.FLOAT) == MIRType.FLOAT
        assert get_binary_op_result_type("*", MIRType.INT, MIRType.FLOAT) == MIRType.FLOAT
        assert get_binary_op_result_type("/", MIRType.INT, MIRType.INT) == MIRType.INT
        assert get_binary_op_result_type("**", MIRType.FLOAT, MIRType.INT) == MIRType.FLOAT

        # String concatenation
        assert get_binary_op_result_type("+", MIRType.STRING, MIRType.INT) == MIRType.STRING

        # Error cases
        assert get_binary_op_result_type("+", MIRType.BOOL, MIRType.FUNCTION) == MIRType.ERROR

        # Unknown operator
        assert get_binary_op_result_type("unknown", MIRType.INT, MIRType.INT) == MIRType.UNKNOWN

    def test_get_unary_op_result_type(self) -> None:
        """Test unary operation result type inference."""
        # Negation
        assert get_unary_op_result_type("-", MIRType.INT) == MIRType.INT
        assert get_unary_op_result_type("-", MIRType.FLOAT) == MIRType.FLOAT
        assert get_unary_op_result_type("-", MIRType.STRING) == MIRType.ERROR
        assert get_unary_op_result_type("-", MIRType.BOOL) == MIRType.ERROR

        # Logical not
        assert get_unary_op_result_type("not", MIRType.BOOL) == MIRType.BOOL
        assert get_unary_op_result_type("not", MIRType.INT) == MIRType.BOOL
        assert get_unary_op_result_type("not", MIRType.STRING) == MIRType.BOOL

        # Unknown operator
        assert get_unary_op_result_type("unknown", MIRType.INT) == MIRType.UNKNOWN
