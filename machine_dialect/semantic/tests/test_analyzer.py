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
