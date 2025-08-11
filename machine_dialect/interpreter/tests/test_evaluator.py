"""Tests for the interpreter evaluator module."""


import pytest

import machine_dialect.ast as ast
from machine_dialect.interpreter.evaluator import evaluate
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

    def test_evaluate_integer_literal(self) -> None:
        """Test evaluating an integer literal."""
        token = Token(TokenType.LIT_INT, "42", 1, 0)
        node = ast.IntegerLiteral(token, 42)

        result = evaluate(node)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.type == ObjectType.INTEGER
        assert result.inspect() == "42"

    def test_evaluate_float_literal(self) -> None:
        """Test evaluating a float literal."""
        token = Token(TokenType.LIT_FLOAT, "3.14", 1, 0)
        node = ast.FloatLiteral(token, 3.14)

        result = evaluate(node)

        assert result is not None
        assert isinstance(result, Float)
        assert result.type == ObjectType.FLOAT
        assert result.inspect() == "3.14"

    def test_evaluate_boolean_literal_true(self) -> None:
        """Test evaluating a true boolean literal."""
        token = Token(TokenType.LIT_TRUE, "True", 1, 0)
        node = ast.BooleanLiteral(token, True)

        result = evaluate(node)

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.type == ObjectType.BOOLEAN
        assert result.inspect() == "Yes"

    def test_evaluate_boolean_literal_false(self) -> None:
        """Test evaluating a false boolean literal."""
        token = Token(TokenType.LIT_FALSE, "False", 1, 0)
        node = ast.BooleanLiteral(token, False)

        result = evaluate(node)

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.type == ObjectType.BOOLEAN
        assert result.inspect() == "No"

    def test_evaluate_empty_literal(self) -> None:
        """Test evaluating an empty literal."""
        token = Token(TokenType.KW_EMPTY, "empty", 1, 0)
        node = ast.EmptyLiteral(token)

        result = evaluate(node)

        assert result is not None
        assert isinstance(result, Empty)
        assert result.type == ObjectType.EMPTY
        assert result.inspect() == "Empty"

    def test_evaluate_string_literal(self) -> None:
        """Test evaluating a string literal."""
        token = Token(TokenType.LIT_TEXT, '"Hello, World!"', 1, 0)
        node = ast.StringLiteral(token, '"Hello, World!"')

        result = evaluate(node)

        assert result is not None
        assert isinstance(result, String)
        assert result.type == ObjectType.STRING
        assert result.inspect() == '"Hello, World!"'

    def test_evaluate_url_literal(self) -> None:
        """Test evaluating a URL literal."""
        token = Token(TokenType.LIT_URL, '"https://example.com"', 1, 0)
        node = ast.URLLiteral(token, '"https://example.com"')

        result = evaluate(node)

        assert result is not None
        assert isinstance(result, URL)
        assert result.type == ObjectType.URL
        assert result.inspect() == '"https://example.com"'


class TestEvaluatorStatements:
    """Test evaluation of statements."""

    def test_evaluate_expression_statement(self) -> None:
        """Test evaluating an expression statement."""
        # Create an expression statement containing an integer literal
        expr = ast.IntegerLiteral(Token(TokenType.LIT_INT, "42", 1, 0), 42)
        stmt = ast.ExpressionStatement(Token(TokenType.LIT_INT, "42", 1, 0), expr)

        result = evaluate(stmt)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "42"

    def test_evaluate_program_single_statement(self) -> None:
        """Test evaluating a program with a single statement."""
        expr = ast.FloatLiteral(Token(TokenType.LIT_FLOAT, "3.14", 1, 0), 3.14)
        stmt = ast.ExpressionStatement(Token(TokenType.LIT_FLOAT, "3.14", 1, 0), expr)
        program = ast.Program([stmt])

        result = evaluate(program)

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

        result = evaluate(program)

        # Should return the result of the last statement
        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_empty_program(self) -> None:
        """Test evaluating an empty program."""
        program = ast.Program([])

        result = evaluate(program)

        assert result is None


class TestEvaluatorEdgeCases:
    """Test edge cases and error conditions."""

    def test_evaluate_unsupported_node_type(self) -> None:
        """Test evaluating an unsupported node type."""
        # Create a node type that's not handled by the evaluator
        # Using Identifier as an example of an unhandled type
        node = ast.Identifier(Token(TokenType.MISC_IDENT, "x", 1, 0), "x")

        result = evaluate(node)

        assert result is None

    def test_evaluate_none_expression_in_statement(self) -> None:
        """Test that assertion fails for statement with None expression."""
        # Create an expression statement with None expression
        stmt = ast.ExpressionStatement(Token(TokenType.LIT_INT, "42", 1, 0), None)

        with pytest.raises(AssertionError):
            evaluate(stmt)


class TestEvaluatorIntegration:
    """Integration tests using the full pipeline."""

    def _parse_and_evaluate(self, source: str) -> Object | None:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)

        if parser.has_errors():
            pytest.fail(f"Parser errors: {parser.errors}")

        return evaluate(program)

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

    def _parse_and_evaluate(self, source: str) -> Object | None:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)

        if parser.has_errors():
            pytest.fail(f"Parser errors: {parser.errors}")

        return evaluate(program)

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


class TestEvaluatorPrefixExpressions:
    """Test evaluation of prefix expressions."""

    def _parse_and_evaluate(self, source: str) -> Object | None:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)

        if parser.has_errors():
            pytest.fail(f"Parser errors: {parser.errors}")

        return evaluate(program)

    def test_evaluate_minus_integer(self) -> None:
        """Test evaluating minus prefix with integer."""
        result = self._parse_and_evaluate("-_42_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "-42"

    def test_evaluate_minus_negative_integer(self) -> None:
        """Test evaluating minus prefix with negative integer."""
        # Now that we support negative literals in italic format, test it
        result = self._parse_and_evaluate("-_-42_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "42"  # Minus of negative is positive

    def test_evaluate_minus_float(self) -> None:
        """Test evaluating minus prefix with float."""
        result = self._parse_and_evaluate("-_3.14_.")

        assert result is not None
        assert isinstance(result, Float)
        assert result.inspect() == "-3.14"

    def test_evaluate_minus_negative_float(self) -> None:
        """Test evaluating minus prefix with negative float."""
        # Now that we support negative literals in italic format, test it
        result = self._parse_and_evaluate("-_-3.14_.")

        assert result is not None
        assert isinstance(result, Float)
        assert result.inspect() == "3.14"  # Minus of negative is positive

    def test_evaluate_minus_boolean(self) -> None:
        """Test evaluating minus prefix with boolean returns Empty."""
        result = self._parse_and_evaluate("-Yes.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_minus_string(self) -> None:
        """Test evaluating minus prefix with string returns Empty."""
        result = self._parse_and_evaluate('-_"hello"_.')

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_minus_url(self) -> None:
        """Test evaluating minus prefix with URL returns Empty."""
        result = self._parse_and_evaluate('-_"https://example.com"_.')

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_minus_empty(self) -> None:
        """Test evaluating minus prefix with empty returns Empty."""
        result = self._parse_and_evaluate("-empty.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_not_boolean_true(self) -> None:
        """Test evaluating not prefix with true boolean."""
        result = self._parse_and_evaluate("not Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_evaluate_not_boolean_false(self) -> None:
        """Test evaluating not prefix with false boolean."""
        result = self._parse_and_evaluate("not No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_not_integer(self) -> None:
        """Test evaluating not prefix with integer returns Empty."""
        result = self._parse_and_evaluate("not _42_.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_not_float(self) -> None:
        """Test evaluating not prefix with float returns Empty."""
        result = self._parse_and_evaluate("not _3.14_.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_not_string(self) -> None:
        """Test evaluating not prefix with string returns Empty."""
        result = self._parse_and_evaluate('not _"hello"_.')

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_not_url(self) -> None:
        """Test evaluating not prefix with URL returns Empty."""
        result = self._parse_and_evaluate('not _"https://example.com"_.')

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_not_empty(self) -> None:
        """Test evaluating not prefix with empty returns Empty."""
        result = self._parse_and_evaluate("not empty.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_double_not_boolean(self) -> None:
        """Test evaluating double not with boolean."""
        result = self._parse_and_evaluate("not not Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_unsupported_prefix_operator(self) -> None:
        """Test evaluating unsupported prefix operator returns Empty."""
        # Create a prefix expression with an unsupported operator
        token = Token(TokenType.OP_PLUS, "+", 1, 0)
        right = ast.IntegerLiteral(Token(TokenType.LIT_INT, "42", 1, 2), 42)
        prefix_expr = ast.PrefixExpression(token, "+")
        prefix_expr.right = right
        stmt = ast.ExpressionStatement(token, prefix_expr)

        result = evaluate(stmt)

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_prefix_with_none_right(self) -> None:
        """Test that assertion fails for prefix expression with None right."""
        # Create a prefix expression with None right
        token = Token(TokenType.OP_MINUS, "-", 1, 0)
        prefix_expr = ast.PrefixExpression(token, "-")
        prefix_expr.right = None  # Explicitly set right to None
        stmt = ast.ExpressionStatement(token, prefix_expr)

        with pytest.raises(AssertionError):
            evaluate(stmt)


class TestEvaluatorIfStatements:
    """Test evaluation of if statements."""

    def _parse_and_evaluate(self, source: str) -> Object | None:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)

        if parser.has_errors():
            pytest.fail(f"Parser errors: {parser.errors}")

        return evaluate(program)

    def test_evaluate_if_true_no_else(self) -> None:
        """Test if statement with true condition and no else."""
        source = """
        If Yes then:
        > _42_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "42"

    def test_evaluate_if_false_no_else(self) -> None:
        """Test if statement with false condition and no else."""
        source = """
        If No then:
        > _42_.
        """
        result = self._parse_and_evaluate(source)

        # When condition is false and no else block, evaluator returns None
        assert result is None

    def test_evaluate_if_true_with_else(self) -> None:
        """Test if statement with true condition and else."""
        source = """
        If Yes then:
        > _42_.
        Else:
        > _99_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "42"

    def test_evaluate_if_false_with_else(self) -> None:
        """Test if statement with false condition and else."""
        source = """
        If No then:
        > _42_.
        Else:
        > _99_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "99"

    def test_evaluate_if_with_expression_condition(self) -> None:
        """Test if statement with expression as condition."""
        source = """
        If _5_ is greater than _3_ then:
        > _"yes"_.
        Else:
        > _"no"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"yes"'

    def test_evaluate_if_with_complex_condition(self) -> None:
        """Test if statement with complex boolean expression."""
        source = """
        If Yes and No or Yes then:
        > _100_.
        Else:
        > _-100_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "100"

    def test_evaluate_nested_if_statements(self) -> None:
        """Test nested if statements."""
        source = """
        If Yes then:
        > If No then:
        > > _1_.
        > Else:
        > > _2_.
        Else:
        > _3_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "2"

    def test_evaluate_if_with_multiple_statements_in_block(self) -> None:
        """Test if statement with multiple statements in consequence."""
        source = """
        If Yes then:
        > _10_.
        > _20_.
        > _30_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "30"

    def test_evaluate_if_else_with_multiple_statements(self) -> None:
        """Test if-else with multiple statements in both branches."""
        source = """
        If No then:
        > _"a"_.
        > _"b"_.
        Else:
        > _"c"_.
        > _"d"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"d"'

    def test_evaluate_if_with_comparison_operators(self) -> None:
        """Test if statement with various comparison operators."""
        # Test less than
        source = """
        If _3_ < _5_ then:
        > _"less"_.
        """
        result = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"less"'

        # Test greater than or equal
        source = """
        If _5_ >= _5_ then:
        > _"gte"_.
        """
        result = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"gte"'

        # Test equality
        source = """
        If _42_ equals _42_ then:
        > _"equal"_.
        """
        result = self._parse_and_evaluate(source)
        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"equal"'

    def test_evaluate_if_with_not_operator(self) -> None:
        """Test if statement with not operator in condition."""
        source = """
        If not No then:
        > _"success"_.
        Else:
        > _"failure"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"success"'

    def test_evaluate_if_with_empty_blocks(self) -> None:
        """Test if statement with empty consequence block."""
        # Parser doesn't allow empty blocks, so test with single empty statement
        source = """
        If Yes then:
        > empty.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_if_non_boolean_condition(self) -> None:
        """Test if statement with non-boolean condition returns Empty."""
        source = """
        If _42_ then:
        > _"yes"_.
        Else:
        > _"no"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_if_with_string_comparison(self) -> None:
        """Test if statement with string comparison."""
        source = """
        If _"hello"_ equals _"hello"_ then:
        > Yes.
        Else:
        > No.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_if_with_mixed_types_in_blocks(self) -> None:
        """Test if statement with different types in consequence and alternative."""
        source = """
        If Yes then:
        > _42_.
        Else:
        > _"string"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "42"

    def test_evaluate_chained_if_else_if(self) -> None:
        """Test chained if-else if pattern."""
        # Simulate else-if with nested if in else block
        source = """
        If No then:
        > _1_.
        Else:
        > If No then:
        > > _2_.
        > Else:
        > > _3_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "3"

    def test_evaluate_if_with_arithmetic_in_condition(self) -> None:
        """Test if statement with arithmetic expression in condition."""
        source = """
        If _2_ + _2_ equals _4_ then:
        > _"math works"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"math works"'

    def test_evaluate_if_with_empty_literal_condition(self) -> None:
        """Test if statement with empty literal as condition."""
        source = """
        If empty then:
        > _"yes"_.
        Else:
        > _"no"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"


class TestEvaluatorReturnStatements:
    """Test evaluation of return statements."""

    def _parse_and_evaluate(self, source: str) -> Object | None:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)

        if parser.has_errors():
            pytest.fail(f"Parser errors: {parser.errors}")

        return evaluate(program)

    def test_return_integer(self) -> None:
        """Test returning an integer value."""
        result = self._parse_and_evaluate("Give back _42_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "42"

    def test_return_float(self) -> None:
        """Test returning a float value."""
        result = self._parse_and_evaluate("Give back _3.14_.")

        assert result is not None
        assert isinstance(result, Float)
        assert result.inspect() == "3.14"

    def test_return_string(self) -> None:
        """Test returning a string value."""
        result = self._parse_and_evaluate('Give back _"hello world"_.')

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"hello world"'

    def test_return_boolean_true(self) -> None:
        """Test returning boolean true."""
        result = self._parse_and_evaluate("Give back Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_return_boolean_false(self) -> None:
        """Test returning boolean false."""
        result = self._parse_and_evaluate("Give back No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_return_empty(self) -> None:
        """Test returning empty."""
        result = self._parse_and_evaluate("Give back empty.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_return_url(self) -> None:
        """Test returning a URL."""
        result = self._parse_and_evaluate('Give back _"https://example.com"_.')

        assert result is not None
        assert isinstance(result, URL)
        assert result.inspect() == '"https://example.com"'

    def test_gives_back_variant(self) -> None:
        """Test 'Gives back' variant of return statement."""
        result = self._parse_and_evaluate("Gives back _100_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "100"

    def test_return_with_expression(self) -> None:
        """Test returning result of an expression."""
        result = self._parse_and_evaluate("Give back _5_ + _3_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "8"

    def test_return_with_comparison(self) -> None:
        """Test returning result of a comparison."""
        result = self._parse_and_evaluate("Give back _5_ > _3_.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_return_with_logical_expression(self) -> None:
        """Test returning result of logical expression."""
        result = self._parse_and_evaluate("Give back Yes and No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_return_with_prefix_expression(self) -> None:
        """Test returning result of prefix expression."""
        result = self._parse_and_evaluate("Give back -_42_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "-42"

    def test_return_stops_execution(self) -> None:
        """Test that return stops execution of subsequent statements."""
        source = """
        Give back _1_.
        _2_.
        _3_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "1"

    def test_multiple_returns(self) -> None:
        """Test that only first return executes."""
        source = """
        Give back _"first"_.
        Give back _"second"_.
        Give back _"third"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"first"'

    def test_return_in_if_true_branch(self) -> None:
        """Test return inside true branch of if statement."""
        source = """
        If Yes then:
        > Give back _"from if"_.
        _"after if"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"from if"'

    def test_return_in_if_false_branch(self) -> None:
        """Test return inside false branch of if statement."""
        source = """
        If No then:
        > Give back _"from if"_.
        _"after if"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"after if"'

    def test_return_in_else_branch(self) -> None:
        """Test return inside else branch."""
        source = """
        If No then:
        > _"in if"_.
        Else:
        > Give back _"from else"_.
        _"after if-else"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"from else"'

    def test_return_in_both_branches(self) -> None:
        """Test return in both if and else branches."""
        source = """
        If Yes then:
        > Give back _10_.
        Else:
        > Give back _20_.
        _30_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "10"

    def test_return_in_nested_if(self) -> None:
        """Test return in nested if statement."""
        source = """
        If Yes then:
        > If Yes then:
        > > Give back _"nested"_.
        > Give back _"outer"_.
        Give back _"main"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"nested"'

    def test_conditional_return(self) -> None:
        """Test conditional return based on expression."""
        source = """
        If _10_ > _5_ then:
        > Give back _"greater"_.
        Give back _"not greater"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"greater"'

    def test_return_before_other_statements(self) -> None:
        """Test return before other statements in block."""
        source = """
        If Yes then:
        > _"first statement"_.
        > Give back _"returned"_.
        > _"never executed"_.
        """
        result = self._parse_and_evaluate(source)

        assert result is not None
        assert isinstance(result, String)
        assert result.inspect() == '"returned"'

    def test_return_complex_expression(self) -> None:
        """Test returning complex nested expression."""
        result = self._parse_and_evaluate("Give back (_5_ + _3_) * _2_ - _1_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "15"

    def test_return_with_not_expression(self) -> None:
        """Test returning result of not expression."""
        result = self._parse_and_evaluate("Give back not Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_empty_program_with_only_return(self) -> None:
        """Test program with only a return statement."""
        result = self._parse_and_evaluate("Give back _999_.")

        assert result is not None
        assert isinstance(result, Integer)
        assert result.inspect() == "999"


class TestEvaluatorLogicalOperators:
    """Test evaluation of logical operators (and, or)."""

    def _parse_and_evaluate(self, source: str) -> Object | None:
        """Helper to parse and evaluate source code."""
        parser = Parser()
        program = parser.parse(source)

        if parser.has_errors():
            pytest.fail(f"Parser errors: {parser.errors}")

        return evaluate(program)

    def test_evaluate_and_true_true(self) -> None:
        """Test True and True evaluates to True."""
        result = self._parse_and_evaluate("Yes and Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_and_true_false(self) -> None:
        """Test True and False evaluates to False."""
        result = self._parse_and_evaluate("Yes and No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_evaluate_and_false_true(self) -> None:
        """Test False and True evaluates to False."""
        result = self._parse_and_evaluate("No and Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_evaluate_and_false_false(self) -> None:
        """Test False and False evaluates to False."""
        result = self._parse_and_evaluate("No and No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_evaluate_or_true_true(self) -> None:
        """Test True or True evaluates to True."""
        result = self._parse_and_evaluate("Yes or Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_or_true_false(self) -> None:
        """Test True or False evaluates to True."""
        result = self._parse_and_evaluate("Yes or No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_or_false_true(self) -> None:
        """Test False or True evaluates to True."""
        result = self._parse_and_evaluate("No or Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_or_false_false(self) -> None:
        """Test False or False evaluates to False."""
        result = self._parse_and_evaluate("No or No.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "No"

    def test_evaluate_complex_logical_expression(self) -> None:
        """Test complex logical expression with multiple operators."""
        result = self._parse_and_evaluate("Yes and No or Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"  # (True and False) or True = False or True = True

    def test_evaluate_nested_logical_with_not(self) -> None:
        """Test logical operators combined with not."""
        result = self._parse_and_evaluate("not No and Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"  # (not False) and True = True and True = True

    def test_evaluate_logical_with_parentheses(self) -> None:
        """Test logical operators with parentheses."""
        result = self._parse_and_evaluate("Yes and (No or Yes).")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"  # True and (False or True) = True and True = True

    def test_evaluate_and_with_non_boolean_left(self) -> None:
        """Test and operator with non-boolean left operand returns Empty."""
        result = self._parse_and_evaluate("_42_ and Yes.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_and_with_non_boolean_right(self) -> None:
        """Test and operator with non-boolean right operand returns Empty."""
        result = self._parse_and_evaluate("Yes and _42_.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_or_with_non_boolean_left(self) -> None:
        """Test or operator with non-boolean left operand returns Empty."""
        result = self._parse_and_evaluate('_"text"_ or No.')

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_or_with_non_boolean_right(self) -> None:
        """Test or operator with non-boolean right operand returns Empty."""
        result = self._parse_and_evaluate("No or _3.14_.")

        assert result is not None
        assert isinstance(result, Empty)
        assert result.inspect() == "Empty"

    def test_evaluate_chain_of_ands(self) -> None:
        """Test chain of and operators."""
        result = self._parse_and_evaluate("Yes and Yes and Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"

    def test_evaluate_chain_of_ors(self) -> None:
        """Test chain of or operators."""
        result = self._parse_and_evaluate("No or No or Yes.")

        assert result is not None
        assert isinstance(result, Boolean)
        assert result.inspect() == "Yes"
