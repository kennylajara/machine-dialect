"""Tests for MIR type system."""

import unittest

from machine_dialect.mir.mir_types import (
    MIRType,
    coerce_types,
    get_binary_op_result_type,
    get_unary_op_result_type,
    infer_type,
    is_comparable_type,
    is_numeric_type,
)


class TestMIRTypes(unittest.TestCase):
    """Test MIR type system functionality."""

    def test_type_string_representation(self) -> None:
        """Test string representation of types."""
        self.assertEqual(str(MIRType.INT), "int")
        self.assertEqual(str(MIRType.FLOAT), "float")
        self.assertEqual(str(MIRType.STRING), "string")
        self.assertEqual(str(MIRType.BOOL), "bool")
        self.assertEqual(str(MIRType.EMPTY), "empty")
        self.assertEqual(str(MIRType.FUNCTION), "function")

    def test_infer_type(self) -> None:
        """Test type inference from Python values."""
        # Primitives
        self.assertEqual(infer_type(42), MIRType.INT)
        self.assertEqual(infer_type(3.14), MIRType.FLOAT)
        self.assertEqual(infer_type("hello"), MIRType.STRING)
        self.assertEqual(infer_type(True), MIRType.BOOL)
        self.assertEqual(infer_type(False), MIRType.BOOL)
        self.assertEqual(infer_type(None), MIRType.EMPTY)

        # URLs
        self.assertEqual(infer_type("http://example.com"), MIRType.URL)
        self.assertEqual(infer_type("https://example.com"), MIRType.URL)
        self.assertEqual(infer_type("ftp://example.com"), MIRType.URL)
        self.assertEqual(infer_type("file:///path/to/file"), MIRType.URL)

        # Unknown types
        self.assertEqual(infer_type([1, 2, 3]), MIRType.UNKNOWN)
        self.assertEqual(infer_type({"key": "value"}), MIRType.UNKNOWN)

    def test_is_numeric_type(self) -> None:
        """Test numeric type checking."""
        self.assertTrue(is_numeric_type(MIRType.INT))
        self.assertTrue(is_numeric_type(MIRType.FLOAT))
        self.assertFalse(is_numeric_type(MIRType.STRING))
        self.assertFalse(is_numeric_type(MIRType.BOOL))
        self.assertFalse(is_numeric_type(MIRType.EMPTY))

    def test_is_comparable_type(self) -> None:
        """Test comparable type checking."""
        self.assertTrue(is_comparable_type(MIRType.INT))
        self.assertTrue(is_comparable_type(MIRType.FLOAT))
        self.assertTrue(is_comparable_type(MIRType.STRING))
        self.assertTrue(is_comparable_type(MIRType.BOOL))
        self.assertFalse(is_comparable_type(MIRType.EMPTY))
        self.assertFalse(is_comparable_type(MIRType.FUNCTION))

    def test_coerce_types(self) -> None:
        """Test type coercion rules."""
        # Same types - no coercion
        self.assertEqual(coerce_types(MIRType.INT, MIRType.INT), MIRType.INT)
        self.assertEqual(coerce_types(MIRType.STRING, MIRType.STRING), MIRType.STRING)

        # Numeric coercion
        self.assertEqual(coerce_types(MIRType.INT, MIRType.FLOAT), MIRType.FLOAT)
        self.assertEqual(coerce_types(MIRType.FLOAT, MIRType.INT), MIRType.FLOAT)

        # String concatenation
        self.assertEqual(coerce_types(MIRType.STRING, MIRType.INT), MIRType.STRING)
        self.assertEqual(coerce_types(MIRType.BOOL, MIRType.STRING), MIRType.STRING)

        # Invalid coercion
        self.assertIsNone(coerce_types(MIRType.INT, MIRType.BOOL))
        self.assertIsNone(coerce_types(MIRType.FUNCTION, MIRType.EMPTY))

    def test_get_binary_op_result_type(self) -> None:
        """Test binary operation result type inference."""
        # Comparison operators always return bool
        self.assertEqual(get_binary_op_result_type("==", MIRType.INT, MIRType.INT), MIRType.BOOL)
        self.assertEqual(get_binary_op_result_type("!=", MIRType.STRING, MIRType.STRING), MIRType.BOOL)
        self.assertEqual(get_binary_op_result_type(">", MIRType.FLOAT, MIRType.INT), MIRType.BOOL)
        self.assertEqual(get_binary_op_result_type("<=", MIRType.INT, MIRType.FLOAT), MIRType.BOOL)

        # Logical operators return bool
        self.assertEqual(get_binary_op_result_type("and", MIRType.BOOL, MIRType.BOOL), MIRType.BOOL)
        self.assertEqual(get_binary_op_result_type("or", MIRType.BOOL, MIRType.BOOL), MIRType.BOOL)

        # Arithmetic operators
        self.assertEqual(get_binary_op_result_type("+", MIRType.INT, MIRType.INT), MIRType.INT)
        self.assertEqual(get_binary_op_result_type("-", MIRType.FLOAT, MIRType.FLOAT), MIRType.FLOAT)
        self.assertEqual(get_binary_op_result_type("*", MIRType.INT, MIRType.FLOAT), MIRType.FLOAT)
        self.assertEqual(get_binary_op_result_type("/", MIRType.INT, MIRType.INT), MIRType.INT)
        self.assertEqual(get_binary_op_result_type("**", MIRType.FLOAT, MIRType.INT), MIRType.FLOAT)

        # String concatenation
        self.assertEqual(get_binary_op_result_type("+", MIRType.STRING, MIRType.INT), MIRType.STRING)

        # Error cases
        self.assertEqual(get_binary_op_result_type("+", MIRType.BOOL, MIRType.FUNCTION), MIRType.ERROR)

        # Unknown operator
        self.assertEqual(get_binary_op_result_type("unknown", MIRType.INT, MIRType.INT), MIRType.UNKNOWN)

    def test_get_unary_op_result_type(self) -> None:
        """Test unary operation result type inference."""
        # Negation
        self.assertEqual(get_unary_op_result_type("-", MIRType.INT), MIRType.INT)
        self.assertEqual(get_unary_op_result_type("-", MIRType.FLOAT), MIRType.FLOAT)
        self.assertEqual(get_unary_op_result_type("-", MIRType.STRING), MIRType.ERROR)
        self.assertEqual(get_unary_op_result_type("-", MIRType.BOOL), MIRType.ERROR)

        # Logical not
        self.assertEqual(get_unary_op_result_type("not", MIRType.BOOL), MIRType.BOOL)
        self.assertEqual(get_unary_op_result_type("not", MIRType.INT), MIRType.BOOL)
        self.assertEqual(get_unary_op_result_type("not", MIRType.STRING), MIRType.BOOL)

        # Unknown operator
        self.assertEqual(get_unary_op_result_type("unknown", MIRType.INT), MIRType.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
