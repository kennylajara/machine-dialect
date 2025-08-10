"""Tests for the interpreter evaluator module."""


import pytest

import machine_dialect.ast as ast
from machine_dialect.interpreter.evaluator import Evaluator
from machine_dialect.interpreter.objects import (
    URL,
    Boolean,
    Empty,
    Float,
    Integer,
    Object,
    ObjectType,
    String,
)
from machine_dialect.lexer import Token, TokenType
from machine_dialect.parser import Parser


class TestEvaluatorLiterals:
    """Test evaluation of literal expressions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.evaluator = Evaluator()

    def test_evaluate_integer_literal(self) -> None:
        """Test evaluating an integer literal."""
        token = Token(TokenType.LIT_INT, "42", 1, 0)
        node = ast.IntegerLiteral(token, 42)

        result = self.evaluator.evaluate(node)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.type == ObjectType.INTEGER
        assert result.inspect() == "42"

    def test_evaluate_float_literal(self) -> None:
        """Test evaluating a float literal."""
        token = Token(TokenType.LIT_FLOAT, "3.14", 1, 0)
        node = ast.FloatLiteral(token, 3.14)

        result = self.evaluator.evaluate(node)

        assert result is not None
        assert isinstance(result, Float)
        assert result.type == ObjectType.FLOAT
        assert result.inspect() == "3.14"

    def test_evaluate_boolean_literal_true(self) -> None:
        """Test evaluating a true boolean literal."""
        token = Token(TokenType.LIT_TRUE, "True", 1, 0)
        node = ast.BooleanLiteral(token, True)

        result = self.evaluator.evaluate(node)

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.type == ObjectType.BOOLEAN
        assert result.inspect() == "Yes"

    def test_evaluate_boolean_literal_false(self) -> None:
        """Test evaluating a false boolean literal."""
        token = Token(TokenType.LIT_FALSE, "False", 1, 0)
        node = ast.BooleanLiteral(token, False)

        result = self.evaluator.evaluate(node)

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.type == ObjectType.BOOLEAN
        assert result.inspect() == "No"

    def test_evaluate_empty_literal(self) -> None:
        """Test evaluating an empty literal."""
        token = Token(TokenType.KW_EMPTY, "empty", 1, 0)
        node = ast.EmptyLiteral(token)

        result = self.evaluator.evaluate(node)

        assert result is not None
        assert isinstance(result, Empty)
        assert result.type == ObjectType.EMPTY
        assert result.inspect() == "Empty"

    def test_evaluate_string_literal(self) -> None:
        """Test evaluating a string literal."""
        token = Token(TokenType.LIT_TEXT, '"Hello, World!"', 1, 0)
        node = ast.StringLiteral(token, '"Hello, World!"')

        result = self.evaluator.evaluate(node)

        assert result is not None
        assert isinstance(result, String)
        assert result.type == ObjectType.STRING
        assert result.inspect() == '"Hello, World!"'

    def test_evaluate_url_literal(self) -> None:
        """Test evaluating a URL literal."""
        token = Token(TokenType.LIT_URL, '"https://example.com"', 1, 0)
        node = ast.URLLiteral(token, '"https://example.com"')

        result = self.evaluator.evaluate(node)

        assert result is not None
        assert isinstance(result, URL)
        assert result.type == ObjectType.URL
        assert result.inspect() == '"https://example.com"'


class TestEvaluatorStatements:
    """Test evaluation of statements."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.evaluator = Evaluator()

    def test_evaluate_expression_statement(self) -> None:
        """Test evaluating an expression statement."""
        # Create an expression statement containing an integer literal
        expr = ast.IntegerLiteral(Token(TokenType.LIT_INT, "42", 1, 0), 42)
        stmt = ast.ExpressionStatement(Token(TokenType.LIT_INT, "42", 1, 0), expr)

        result = self.evaluator.evaluate(stmt)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "42"

    def test_evaluate_program_single_statement(self) -> None:
        """Test evaluating a program with a single statement."""
        expr = ast.FloatLiteral(Token(TokenType.LIT_FLOAT, "3.14", 1, 0), 3.14)
        stmt = ast.ExpressionStatement(Token(TokenType.LIT_FLOAT, "3.14", 1, 0), expr)
        program = ast.Program([stmt])

        result = self.evaluator.evaluate(program)

        assert result is not None
        assert isinstance(result, Float)
        assert result.inspect() == "3.14"

    def test_evaluate_program_multiple_statements(self) -> None:
        """Test evaluating a program with multiple statements."""
        # Create multiple statements
        stmt1 = ast.ExpressionStatement(
            Token(TokenType.LIT_INT, "42", 1, 0), ast.IntegerLiteral(Token(TokenType.LIT_INT, "42", 1, 0), 42)
        )
        stmt2 = ast.ExpressionStatement(
            Token(TokenType.LIT_TEXT, '"hello"', 2, 0),
            ast.StringLiteral(Token(TokenType.LIT_TEXT, '"hello"', 2, 0), '"hello"'),
        )
        stmt3 = ast.ExpressionStatement(
            Token(TokenType.LIT_TRUE, "True", 3, 0), ast.BooleanLiteral(Token(TokenType.LIT_TRUE, "True", 3, 0), True)
        )
        program = ast.Program([stmt1, stmt2, stmt3])

        result = self.evaluator.evaluate(program)

        # Should return the result of the last statement
        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_empty_program(self) -> None:
        """Test evaluating an empty program."""
        program = ast.Program([])

        result = self.evaluator.evaluate(program)

        assert result is None


class TestEvaluatorEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.evaluator = Evaluator()

    def test_evaluate_unsupported_node_type(self) -> None:
        """Test evaluating an unsupported node type."""
        # Create a node type that's not handled by the evaluator
        # Using Identifier as an example of an unhandled type
        node = ast.Identifier(Token(TokenType.MISC_IDENT, "x", 1, 0), "x")

        result = self.evaluator.evaluate(node)

        assert result is None

    def test_evaluate_none_expression_in_statement(self) -> None:
        """Test that assertion fails for statement with None expression."""
        # Create an expression statement with None expression
        stmt = ast.ExpressionStatement(Token(TokenType.LIT_INT, "42", 1, 0), None)

        with pytest.raises(AssertionError):
            self.evaluator.evaluate(stmt)


class TestEvaluatorIntegration:
    """Integration tests using the full pipeline."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.evaluator = Evaluator()

    def _parse_and_evaluate(self, source: str) -> Object | None:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)

        if parser.has_errors():
            pytest.fail(f"Parser errors: {parser.errors}")

        return self.evaluator.evaluate(program)

    def test_integrate_integer_literal(self) -> None:
        """Test parsing and evaluating an integer literal."""
        result = self._parse_and_evaluate("_42_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "42"

    def test_integrate_float_literal(self) -> None:
        """Test parsing and evaluating a float literal."""
        result = self._parse_and_evaluate("_3.14_.")

        assert result is not None
        assert isinstance(result, Float)
        assert result.inspect() == "3.14"

    def test_integrate_boolean_true(self) -> None:
        """Test parsing and evaluating a true boolean."""
        result = self._parse_and_evaluate("Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_integrate_boolean_false(self) -> None:
        """Test parsing and evaluating a false boolean."""
        result = self._parse_and_evaluate("No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_integrate_empty(self) -> None:
        """Test parsing and evaluating empty."""
        result = self._parse_and_evaluate("empty.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_integrate_string_literal(self) -> None:
        """Test parsing and evaluating a string literal."""
        result = self._parse_and_evaluate('_"Hello, World!"_.')

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"Hello, World!"'

    def test_integrate_url_literal(self) -> None:
        """Test parsing and evaluating a URL literal."""
        result = self._parse_and_evaluate('_"https://example.com"_.')

        assert result is not None
        assert isinstance(result, URL)
        assert result.inspect() == '"https://example.com"'

    def test_integrate_multiple_statements(self) -> None:
        """Test parsing and evaluating multiple statements."""
        source = """
        _42_.
        _"test"_.
        _3.14_.
        """
        result = self._parse_and_evaluate(source)

        # Should return the last statement's result
        assert result is not None
        assert isinstance(result, Float)
        assert result.inspect() == "3.14"

    def test_integrate_complex_program(self) -> None:
        """Test parsing and evaluating a complex program."""
        source = """
        _100_.
        Yes.
        _"https://api.example.com/v1"_.
        No.
        empty.
        _"final value"_.
        """
        result = self._parse_and_evaluate(source)

        # Should return the last statement's result
        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"final value"'

    def test_integrate_boolean_singleton(self) -> None:
        """Test that boolean singletons work through the full pipeline."""
        # Parse and evaluate two True values
        result1 = self._parse_and_evaluate("Yes.")
        result2 = self._parse_and_evaluate("True.")

        assert result1 is not None
        assert result2 is not None
        # Should be the same singleton instance
        assert result1 is result2

    def test_integrate_empty_singleton(self) -> None:
        """Test that empty singleton works through the full pipeline."""
        # Parse and evaluate two empty values
        result1 = self._parse_and_evaluate("empty.")
        result2 = self._parse_and_evaluate("empty.")

        assert result1 is not None
        assert result2 is not None
        # Should be the same singleton instance
        assert result1 is result2


class TestEvaluatorBooleanVariants:
    """Test evaluation of different boolean representations."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.evaluator = Evaluator()

    def _parse_and_evaluate(self, source: str) -> Object | None:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)

        if parser.has_errors():
            pytest.fail(f"Parser errors: {parser.errors}")

        return self.evaluator.evaluate(program)

    def test_evaluate_yes_keyword(self) -> None:
        """Test evaluating 'Yes' as boolean true."""
        result = self._parse_and_evaluate("Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_no_keyword(self) -> None:
        """Test evaluating 'No' as boolean false."""
        result = self._parse_and_evaluate("No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_evaluate_true_keyword(self) -> None:
        """Test evaluating 'True' as boolean true."""
        result = self._parse_and_evaluate("True.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_false_keyword(self) -> None:
        """Test evaluating 'False' as boolean false."""
        result = self._parse_and_evaluate("False.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"
