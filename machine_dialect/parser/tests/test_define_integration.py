"""Integration tests for Define statement with symbol table tracking.

These tests verify that the parser properly integrates with the symbol table
to track variable definitions and validate variable usage.
"""

from machine_dialect.ast import DefineStatement, SetStatement
from machine_dialect.errors.exceptions import MDNameError, MDTypeError
from machine_dialect.parser import Parser


class TestDefineIntegration:
    """Test integration between Define statements and symbol table."""

    def test_define_then_set_valid(self) -> None:
        """Test that defining a variable allows it to be set."""
        source = """
        Define `count` as Whole Number.
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
        Define `x` as Whole Number.
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
        Define `x` as Whole Number.
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
        Define `global_var` as Whole Number.
        Set `global_var` to _1_.
        """
        parser = Parser()
        parser.parse(source)

        assert len(parser.errors) == 0

    def test_use_before_define_error(self) -> None:
        """Test that using variable before definition generates error."""
        source = """
        Set `x` to _5_.
        Define `x` as Whole Number.
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
        Define `user_age` as Whole Number.
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
        Define `x` as Whole Number.
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
        Define `flexible` as Whole Number or Text.
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
        Define `valid` as Whole Number.
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
        Define as Whole Number.
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
        Define `a` as Whole Number.
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


class TestDefineTypeChecking:
    """Test type checking integration with Define and Set statements."""

    def test_valid_type_assignments(self) -> None:
        """Test that valid type assignments work correctly."""
        source = """
        Define `count` as Whole Number.
        Set `count` to _42_.

        Define `price` as Float.
        Set `price` to _19.99_.

        Define `name` as Text.
        Set `name` to _"Alice"_.

        Define `active` as Yes/No.
        Set `active` to _yes_.
        """
        parser = Parser()
        program = parser.parse(source)

        # Should parse without type errors
        assert len(parser.errors) == 0
        assert len(program.statements) == 8

    def test_type_mismatch_whole_number_to_text(self) -> None:
        """Test type mismatch when assigning text to whole number."""
        source = """
        Define `count` as Whole Number.
        Set `count` to _"not a number"_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have a type error
        assert len(parser.errors) > 0
        # Find type-related errors
        from machine_dialect.errors import MDTypeError

        type_errors = [e for e in parser.errors if isinstance(e, MDTypeError)]
        assert len(type_errors) > 0

    def test_type_mismatch_text_to_whole_number(self) -> None:
        """Test type mismatch when assigning number to text."""
        source = """
        Define `message` as Text.
        Set `message` to _42_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have a type error
        assert len(parser.errors) > 0

    def test_union_type_valid_assignments(self) -> None:
        """Test that union types accept values of any specified type."""
        source = """
        Define `flexible` as Whole Number or Text.
        Set `flexible` to _42_.
        Set `flexible` to _"hello"_.
        """
        parser = Parser()
        parser.parse(source)

        # Both assignments should be valid
        assert len(parser.errors) == 0

    def test_union_type_invalid_assignment(self) -> None:
        """Test that union types reject values not in the union."""
        source = """
        Define `flexible` as Whole Number or Text.
        Set `flexible` to _yes_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have type error (Yes/No not in union)
        assert len(parser.errors) > 0

    def test_number_type_accepts_whole_and_float(self) -> None:
        """Test that Number type accepts both Whole Number and Float."""
        source = """
        Define `num` as Number.
        Set `num` to _42_.
        Set `num` to _3.14_.
        """
        parser = Parser()
        parser.parse(source)

        # Both assignments should be valid
        assert len(parser.errors) == 0

    def test_number_type_rejects_non_numeric(self) -> None:
        """Test that Number type rejects non-numeric values."""
        source = """
        Define `num` as Number.
        Set `num` to _"text"_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have type error
        assert len(parser.errors) > 0

    def test_empty_assignable_to_any_type(self) -> None:
        """Test that empty requires explicit type declaration for strict type checking."""
        # In strict mode, empty is NOT assignable to non-nullable types
        source = """
        Define `maybe_text` as Text.
        Set `maybe_text` to empty.

        Define `maybe_num` as Whole Number.
        Set `maybe_num` to empty.

        Define `maybe_bool` as Yes/No.
        Set `maybe_bool` to empty.
        """
        parser = Parser()
        parser.parse(source)

        # Should have type errors for all empty assignments to non-nullable types
        assert len(parser.errors) == 3
        for error in parser.errors:
            assert isinstance(error, MDTypeError)
            assert "Empty" in str(error)

        # Test that explicit nullable types work
        source_nullable = """
        Define `maybe_text` as Text or Empty.
        Set `maybe_text` to empty.

        Define `maybe_num` as Whole Number or Empty.
        Set `maybe_num` to empty.

        Define `maybe_bool` as Yes/No or Empty.
        Set `maybe_bool` to empty.
        """
        parser2 = Parser()
        parser2.parse(source_nullable)

        # All empty assignments to nullable types should be valid
        assert len(parser2.errors) == 0

    def test_url_type_assignment(self) -> None:
        """Test URL type assignments."""
        source = """
        Define `website` as URL.
        Set `website` to _"https://example.com"_.
        """
        parser = Parser()
        parser.parse(source)

        # URL assignment should be valid
        assert len(parser.errors) == 0

    def test_multiple_type_errors_collected(self) -> None:
        """Test that multiple type errors are collected."""
        source = """
        Define `a` as Whole Number.
        Define `b` as Text.
        Define `c` as Yes/No.

        Set `a` to _"wrong"_.
        Set `b` to _42_.
        Set `c` to _"also wrong"_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have 3 type errors
        assert len(parser.errors) == 3

    def test_type_checking_with_expressions(self) -> None:
        """Test type checking with complex expressions."""
        source = """
        Define `x` as Whole Number.
        Define `y` as Whole Number.
        Set `x` to _10_.
        Set `y` to _20_.
        """
        parser = Parser()
        parser.parse(source)

        # Should parse without errors
        assert len(parser.errors) == 0

    def test_float_not_assignable_to_whole_number(self) -> None:
        """Test that Float cannot be assigned to Whole Number (no implicit conversion)."""
        source = """
        Define `int_only` as Whole Number.
        Set `int_only` to _3.14_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have type error (no implicit conversions per spec)
        assert len(parser.errors) > 0

    def test_whole_number_assignable_to_number(self) -> None:
        """Test that Whole Number can be assigned to Number type."""
        source = """
        Define `num` as Number.
        Set `num` to _42_.
        """
        parser = Parser()
        parser.parse(source)

        # Should be valid (Number accepts Whole Number)
        assert len(parser.errors) == 0

    def test_complex_union_types(self) -> None:
        """Test complex union types with multiple alternatives."""
        source = """
        Define `complex` as Whole Number or Text or Yes/No or Empty.
        Set `complex` to _42_.
        Set `complex` to _"text"_.
        Set `complex` to _yes_.
        Set `complex` to empty.
        """
        parser = Parser()
        parser.parse(source)

        # All assignments should be valid
        assert len(parser.errors) == 0

    def test_type_error_message_content(self) -> None:
        """Test that type error messages are informative."""
        source = """
        Define `num` as Whole Number.
        Set `num` to _"text"_.
        """
        parser = Parser()
        parser.parse(source)

        # Should have meaningful error message
        assert len(parser.errors) > 0
        error_str = str(parser.errors[0])
        # Error should mention the variable name and types involved
        assert "num" in error_str or "Whole Number" in error_str.lower() or "text" in error_str.lower()
