"""Tests for semantic analyzer functionality.

This module tests the semantic analysis capabilities including type checking,
variable usage validation, and error detection.
"""

from machine_dialect.errors import MDNameError, MDTypeError
from machine_dialect.parser import Parser
from machine_dialect.semantic.analyzer import SemanticAnalyzer


class TestSemanticAnalyzer:
    """Test semantic analysis functionality."""

    def test_undefined_variable_error(self) -> None:
        """Test error for using undefined variable."""
        source = """
        Set `x` to _5_.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 1
        assert isinstance(errors[0], MDNameError)
        assert "not defined" in str(errors[0])
        assert "Define" in str(errors[0])  # Should suggest Define

    def test_type_mismatch_error(self) -> None:
        """Test error for type mismatch."""
        source = """
        Define `age` as Whole Number.
        Set `age` to _"twenty"_.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 1
        assert isinstance(errors[0], MDTypeError)
        assert "Whole Number" in str(errors[0])
        assert "Text" in str(errors[0])

    def test_redefinition_error(self) -> None:
        """Test error for variable redefinition."""
        source = """
        Define `x` as Whole Number.
        Define `x` as Text.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 1
        assert isinstance(errors[0], MDNameError)
        assert "already defined" in str(errors[0])

    def test_valid_union_type_assignment(self) -> None:
        """Test valid assignment to union type."""
        source = """
        Define `value` as Whole Number or Text.
        Set `value` to _42_.
        Set `value` to _"hello"_.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 0

    def test_invalid_union_type_assignment(self) -> None:
        """Test invalid assignment to union type."""
        source = """
        Define `value` as Whole Number or Text.
        Set `value` to _yes_.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 1
        assert isinstance(errors[0], MDTypeError)
        assert "Yes/No" in str(errors[0])
        assert "Whole Number" in str(errors[0]) or "Text" in str(errors[0])

    def test_default_value_type_check(self) -> None:
        """Test type checking for default values."""
        source = """
        Define `count` as Whole Number (default: _"zero"_).
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 1
        assert isinstance(errors[0], MDTypeError)
        assert "Default value" in str(errors[0])

    def test_uninitialized_variable_use(self) -> None:
        """Test error for using uninitialized variable."""
        source = """
        Define `x` as Whole Number.
        Define `y` as Whole Number.
        Set `y` to `x`.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 1
        assert "before being initialized" in str(errors[0])

    def test_number_type_accepts_int_and_float(self) -> None:
        """Test that Number type accepts both Whole Number and Float."""
        source = """
        Define `value` as Number.
        Set `value` to _42_.
        Set `value` to _3.14_.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 0

    def test_valid_default_value(self) -> None:
        """Test valid default value with matching type."""
        source = """
        Define `count` as Whole Number (default: _0_).
        Define `name` as Text (default: _"John"_).
        Define `active` as Yes/No (default: _yes_).
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 0

    def test_empty_type_compatibility(self) -> None:
        """Test that Empty type works with nullable types."""
        source = """
        Define `optional` as Text or Empty.
        Set `optional` to _"text"_.
        Set `optional` to empty.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 0

    def test_invalid_type_name(self) -> None:
        """Test error for invalid type name."""
        source = """
        Define `x` as String.
        """
        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Parser already catches invalid type names and creates an ErrorStatement
        # So semantic analyzer won't see it
        assert len(parser.errors) == 1
        assert "String" in str(parser.errors[0])

    def test_expression_type_inference(self) -> None:
        """Test type inference for expressions."""
        source = """
        Define `sum` as Whole Number.
        Define `a` as Whole Number.
        Define `b` as Whole Number.
        Set `a` to _5_.
        Set `b` to _10_.
        Set `sum` to `a` + `b`.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        # Should be valid - no errors
        assert len(errors) == 0

    def test_comparison_returns_boolean(self) -> None:
        """Test that comparison operators return Yes/No type."""
        source = """
        Define `result` as Yes/No.
        Define `x` as Whole Number.
        Set `x` to _5_.
        Set `result` to `x` > _3_.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 0

    def test_division_returns_float(self) -> None:
        """Test that division always returns Float type."""
        source = """
        Define `result` as Float.
        Define `x` as Whole Number.
        Define `y` as Whole Number.
        Set `x` to _10_.
        Set `y` to _3_.
        Set `result` to `x` / `y`.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 0

    def test_bitwise_operators_type_inference(self) -> None:
        """Test that bitwise operators return Whole Number type."""
        source = """
        Define `a` as Whole Number.
        Define `b` as Whole Number.
        Define `result` as Whole Number.
        Set `a` to _5_.
        Set `b` to _3_.
        """
        # Note: We can't fully test bitwise operators without parser support
        # but the type inference is ready when the parser supports them
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        assert len(errors) == 0

    def test_arguments_expression_type(self) -> None:
        """Test that Arguments expression returns None for type."""
        from machine_dialect.ast.expressions import Arguments
        from machine_dialect.lexer import Token, TokenType

        analyzer = SemanticAnalyzer()

        # Create an Arguments expression
        args = Arguments(Token(TokenType.DELIM_LPAREN, "(", 1, 1))

        # Type inference should return None for Arguments
        type_info = analyzer._infer_expression_type(args)
        assert type_info is None

    def test_function_return_type_inference(self) -> None:
        """Test that function calls can infer return type from symbol table."""
        # This would require parsing function definitions and calls
        # For now, we just test that the infrastructure is in place
        from machine_dialect.ast import Identifier
        from machine_dialect.ast.call_expression import CallExpression
        from machine_dialect.lexer import Token, TokenType

        analyzer = SemanticAnalyzer()

        # Manually add a function to the symbol table with return type
        analyzer.symbol_table.define("my_func", ["Function"], 1, 1)
        func_info = analyzer.symbol_table.lookup("my_func")
        if func_info:
            func_info.return_type = "Text"  # Set return type

        # Create a call expression
        func_name = Identifier(Token(TokenType.MISC_IDENT, "my_func", 1, 1), "my_func")
        call_expr = CallExpression(Token(TokenType.KW_USE, "use", 1, 1), func_name, None)

        # Type inference should return Text
        type_info = analyzer._infer_expression_type(call_expr)
        assert type_info is not None
        assert type_info.type_name == "Text"

    def test_function_definition_with_return_type(self) -> None:
        """Test that function definitions store return type information."""
        from machine_dialect.ast import Identifier
        from machine_dialect.ast.program import Program
        from machine_dialect.ast.statements import (
            ActionStatement,
            BlockStatement,
        )
        from machine_dialect.lexer import Token, TokenType

        # Create an AST for: Action "add_one" with input `x` as Whole Number, output `result` as Whole Number
        name = Identifier(Token(TokenType.MISC_IDENT, "add_one", 1, 8), "add_one")
        action = ActionStatement(Token(TokenType.KW_ACTION, "action", 1, 1), name)

        # Create input parameter
        from machine_dialect.ast.statements import Output, Parameter

        param_name = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 20), "x")
        input_param = Parameter(Token(TokenType.MISC_IDENT, "x", 1, 20), param_name, type_name="Whole Number")
        action.inputs = [input_param]

        # Create output parameter
        output_name = Identifier(Token(TokenType.MISC_IDENT, "result", 1, 40), "result")
        output_param = Output(Token(TokenType.MISC_IDENT, "result", 1, 40), output_name, type_name="Whole Number")
        action.outputs = [output_param]

        # Create body (empty for simplicity)
        action.body = BlockStatement(Token(TokenType.DELIM_LBRACE, "{", 2, 1))
        action.body.statements = []

        # Create program
        program = Program([action])

        # Analyze
        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        # Should have no errors
        assert len(errors) == 0

        # Function should be defined with return type
        func_info = analyzer.symbol_table.lookup("add_one")
        assert func_info is not None
        assert func_info.type_spec == ["Function"]
        assert func_info.return_type == "Whole Number"

    def test_scoped_definitions(self) -> None:
        """Test variable scoping - variables defined in inner scope not accessible in outer scope."""
        source = """
        Define `x` as Whole Number.
        Set `x` to _5_.

        If _yes_ then:
        > Define `y` as Text.
        > Set `y` to _"hello"_.

        Set `y` to _"world"_.
        """
        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        analyzer = SemanticAnalyzer()
        _, errors = analyzer.analyze(program)

        # Should have one error for accessing 'y' outside its scope
        assert len(errors) == 1
        assert isinstance(errors[0], MDNameError)
        assert "not defined" in str(errors[0])
        assert "y" in str(errors[0])
