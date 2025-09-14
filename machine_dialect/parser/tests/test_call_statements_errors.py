"""Tests for error handling in use statements."""

from machine_dialect.ast import Arguments, CallStatement
from machine_dialect.parser import Parser


class TestCallStatementErrors:
    """Test error handling for use statements."""

    def test_call_missing_function_name(self) -> None:
        """Test that use without function name produces an error."""
        source = 'use with _"test"_.'

        parser = Parser()
        parser.parse(source, check_semantics=False)

        assert len(parser.errors) > 0
        error_messages = [str(err).lower() for err in parser.errors]
        assert any(
            ("expected identifier" in msg and "function name" in msg) or ("identifier" in msg and "got" in msg)
            for msg in error_messages
        ), f"Expected error about missing function name, got: {parser.errors}"

    def test_call_with_invalid_function_name_type(self) -> None:
        """Test that use with non-identifier function name produces an error."""
        source = 'use _"not_an_identifier"_ with _"test"_.'

        parser = Parser()
        parser.parse(source, check_semantics=False)

        assert len(parser.errors) > 0
        error_messages = [str(err).lower() for err in parser.errors]
        assert any("expected identifier" in msg or "function name" in msg for msg in error_messages), (
            f"Expected error about invalid function name type, got: {parser.errors}"
        )

    def test_call_without_period(self) -> None:
        """Test that use statement without period produces an error."""
        source = "use `my_function`"

        parser = Parser()
        parser.parse(source, check_semantics=False)

        assert len(parser.errors) > 0
        error_messages = [str(err).lower() for err in parser.errors]
        assert any("period" in msg or "punct_period" in msg for msg in error_messages), (
            f"Expected error about missing period, got: {parser.errors}"
        )

    def test_call_with_invalid_argument_value(self) -> None:
        """Test that use with truly invalid argument value produces an error."""
        source = "use `my_function` with @#$."

        parser = Parser()
        parser.parse(source, check_semantics=False)

        # Should have an error about invalid argument
        assert len(parser.errors) > 0
        error_messages = [str(err).lower() for err in parser.errors]
        assert any("invalid" in msg or "no suitable parse function" in msg for msg in error_messages), (
            f"Expected error about invalid argument, got: {parser.errors}"
        )

    def test_call_with_missing_comma_between_positional_args(self) -> None:
        """Test that missing comma between arguments produces an error."""
        source = 'use `my_function` with `param` _"value"_.'

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Should have an error about missing comma
        assert len(parser.errors) > 0
        error_messages = [str(err).lower() for err in parser.errors]
        assert any("comma" in msg or "unexpected" in msg for msg in error_messages), (
            f"Expected error about missing comma, got: {parser.errors}"
        )

        # Should still parse both arguments (error recovery)
        assert len(program.statements) == 1
        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        if call_stmt.arguments:
            # Should have parsed both as positional arguments despite the error
            assert isinstance(call_stmt.arguments, Arguments)
            assert len(call_stmt.arguments.positional) == 2

    def test_call_with_empty_arguments(self) -> None:
        """Test that use with 'with' but no arguments produces reasonable behavior."""
        source = "use `my_function` with ."

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # This should either produce an error or create an empty arguments list
        if len(parser.errors) > 0:
            # If errors, should be about missing arguments
            error_messages = [str(err).lower() for err in parser.errors]
            assert any("invalid" in msg or "expected" in msg for msg in error_messages)
        else:
            # If no errors, should have empty arguments
            assert len(program.statements) == 1
            call_stmt = program.statements[0]
            assert isinstance(call_stmt, CallStatement)
            assert call_stmt.arguments is not None
            assert isinstance(call_stmt.arguments, Arguments)
            assert len(call_stmt.arguments.positional) == 0
            assert len(call_stmt.arguments.named) == 0

    def test_call_with_duplicate_named_arguments(self) -> None:
        """Test behavior with duplicate named argument keys."""
        source = 'use `my_function` where `param` is _"value1"_, `param` is _"value2"_.'

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Parser currently doesn't check for duplicates, so this should parse successfully
        # but both values should be present
        assert len(parser.errors) == 0, f"Unexpected errors: {parser.errors}"
        assert len(program.statements) == 1
        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        assert call_stmt.arguments is not None
        assert isinstance(call_stmt.arguments, Arguments)
        assert len(call_stmt.arguments.named) == 2
        # Both should have the same name
        name1, _ = call_stmt.arguments.named[0]
        name2, _ = call_stmt.arguments.named[1]
        assert name1.value == "param"
        assert name2.value == "param"

    def test_call_with_missing_comma_between_arguments(self) -> None:
        """Test that missing comma between arguments produces an error."""
        source = 'use `my_function` with _"arg1"_ _"arg2"_.'

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Should produce an error about missing comma
        assert len(parser.errors) > 0
        error_messages = [str(err).lower() for err in parser.errors]
        assert any("comma" in msg or "unexpected" in msg for msg in error_messages), (
            f"Expected error about missing comma, got: {parser.errors}"
        )

        # With error recovery, it should still parse both arguments
        assert len(program.statements) == 1
        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        if call_stmt.arguments:
            # Should have parsed both arguments (with error recovery)
            assert isinstance(call_stmt.arguments, Arguments)
            assert len(call_stmt.arguments.positional) == 2

    def test_call_with_trailing_comma(self) -> None:
        """Test that trailing comma in arguments is handled gracefully."""
        source = 'use `my_function` with _"arg1"_, _"arg2"_,.'

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # Trailing comma should be acceptable or produce a clear error
        if len(parser.errors) == 0:
            assert len(program.statements) == 1
            call_stmt = program.statements[0]
            assert isinstance(call_stmt, CallStatement)
            assert call_stmt.arguments is not None
            assert isinstance(call_stmt.arguments, Arguments)
            assert len(call_stmt.arguments.positional) == 2

    def test_call_with_mixed_valid_and_invalid_arguments(self) -> None:
        """Test error recovery with mixed valid and invalid arguments."""
        # Note: 'invalid' without backticks is actually a valid identifier argument
        # To test truly invalid syntax, we need something that's not a valid token
        source = 'use `my_function` with _"valid"_, , _42_.'

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        # The double comma should cause parsing issues
        # Parser should handle this gracefully
        assert len(program.statements) == 1
        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        # Should have parsed the valid arguments
        if call_stmt.arguments:
            assert isinstance(call_stmt.arguments, Arguments)
            assert len(call_stmt.arguments.positional) >= 1  # At least the first valid one
