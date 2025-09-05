"""Integration tests for Define statement with symbol table tracking.

These tests verify that the parser properly integrates with the symbol table
to track variable definitions and validate variable usage.
"""


from machine_dialect.ast import DefineStatement, SetStatement
from machine_dialect.errors.exceptions import MDNameError
from machine_dialect.parser import Parser


class TestDefineIntegration:
    """Test integration between Define statements and symbol table."""

    def test_define_then_set_valid(self) -> None:
        """Test that defining a variable allows it to be set."""
        source = """
        Define `count` as Integer.
        Set `count` to _42_.
        """
        parser = Parser()
        program = parser.parse(source)

        # Should parse successfully
        assert len(parser.errors) == 0
        assert len(program.statements) == 2
        assert isinstance(program.statements[0], DefineStatement)
        assert isinstance(program.statements[1], SetStatement)

    def test_set_undefined_variable_error(self) -> None:
        """Test that using undefined variable generates error."""
        source = """
        Set `undefined_var` to _10_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have exactly one error
        assert len(parser.errors) == 1
        error = parser.errors[0]
        assert isinstance(error, MDNameError)
        assert "undefined_var" in str(error)
        assert "not defined" in str(error)

    def test_define_with_default_then_set(self) -> None:
        """Test defining variable with default value then setting it."""
        source = """
        Define `message` as Text (default: _"Hello"_).
        Set `message` to _"World"_.
        """
        parser = Parser()
        program = parser.parse(source)

        # Should parse successfully
        assert len(parser.errors) == 0
        assert len(program.statements) == 2

    def test_multiple_defines_then_sets(self) -> None:
        """Test multiple variable definitions and uses."""
        source = """
        Define `x` as Integer.
        Define `y` as Float.
        Define `name` as Text.
        Set `x` to _10_.
        Set `y` to _3.14_.
        Set `name` to _"Alice"_.
        """
        parser = Parser()
        program = parser.parse(source)

        # Should parse successfully
        assert len(parser.errors) == 0
        assert len(program.statements) == 6

    def test_redefinition_error(self) -> None:
        """Test that redefining a variable generates error."""
        source = """
        Define `x` as Integer.
        Define `x` as Text.
        """
        parser = Parser()
        parser.parse(source)

        # Should have exactly one error for redefinition
        assert len(parser.errors) == 1
        error = parser.errors[0]
        assert isinstance(error, MDNameError)
        assert "already defined" in str(error)

    def test_define_in_different_scopes(self) -> None:
        """Test that variables can be defined in different scopes (future feature)."""
        # This test is a placeholder for when we implement scope handling
        # Currently all variables are in global scope
        source = """
        Define `global_var` as Integer.
        Set `global_var` to _1_.
        """
        parser = Parser()
        parser.parse(source)

        assert len(parser.errors) == 0

    def test_use_before_define_error(self) -> None:
        """Test that using variable before definition generates error."""
        source = """
        Set `x` to _5_.
        Define `x` as Integer.
        """
        parser = Parser()
        parser.parse(source)

        # Should have error for using undefined variable
        assert len(parser.errors) == 1
        error = parser.errors[0]
        assert isinstance(error, MDNameError)
        assert "not defined" in str(error)

    def test_complex_program_with_defines_and_sets(self) -> None:
        """Test a more complex program with multiple defines and sets."""
        source = """
        Define `user_name` as Text.
        Define `user_age` as Integer.
        Define `is_admin` as Yes/No (default: _no_).

        Set `user_name` to _"John Doe"_.
        Set `user_age` to _25_.
        Set `is_admin` to _yes_.

        Define `score` as Float.
        Set `score` to _98.5_.
        """
        parser = Parser()
        program = parser.parse(source)

        # Should parse successfully
        assert len(parser.errors) == 0
        assert len(program.statements) == 8

    def test_undefined_variable_in_expression(self) -> None:
        """Test that undefined variables in expressions generate errors."""
        source = """
        Define `x` as Integer.
        Set `x` to _10_.
        Set `y` to `x` + _5_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have error for undefined variable y
        assert len(parser.errors) == 1
        error = parser.errors[0]
        assert isinstance(error, MDNameError)
        assert "y" in str(error)

    def test_define_with_union_types(self) -> None:
        """Test defining variable with union types."""
        source = """
        Define `flexible` as Integer or Text.
        Set `flexible` to _42_.
        Define `flexible` as Float.
        """
        parser = Parser()
        parser.parse(source)

        # Should have error for redefinition
        assert len(parser.errors) == 1
        error = parser.errors[0]
        assert isinstance(error, MDNameError)
        assert "already defined" in str(error)

    def test_error_recovery_continues_parsing(self) -> None:
        """Test that parser continues after encountering errors."""
        source = """
        Set `undefined1` to _1_.
        Define `valid` as Integer.
        Set `undefined2` to _2_.
        Set `valid` to _100_.
        Set `undefined3` to _3_.
        """
        parser = Parser()
        program = parser.parse(source)

        # Should have 3 errors for undefined variables
        assert len(parser.errors) == 3
        # But should still parse all 5 statements
        assert len(program.statements) == 5

    def test_define_without_type_error(self) -> None:
        """Test that Define without type generates appropriate error."""
        source = """
        Define `x` as.
        """
        parser = Parser()
        parser.parse(source)

        # Should have syntax error
        assert len(parser.errors) > 0

    def test_define_with_invalid_syntax_error(self) -> None:
        """Test that invalid Define syntax generates appropriate error."""
        source = """
        Define as Integer.
        """
        parser = Parser()
        parser.parse(source)

        # Should have syntax error
        assert len(parser.errors) > 0

    def test_multiple_errors_collected(self) -> None:
        """Test that multiple errors are collected in one pass."""
        source = """
        Set `a` to _1_.
        Set `b` to _2_.
        Define `a` as Integer.
        Define `a` as Text.
        Set `c` to _3_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have errors for:
        # 1. 'a' not defined (first Set)
        # 2. 'b' not defined (second Set)
        # 3. 'a' already defined (second Define)
        # 4. 'c' not defined (last Set)
        assert len(parser.errors) == 4
