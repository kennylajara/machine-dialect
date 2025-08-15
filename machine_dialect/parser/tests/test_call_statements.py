"""Tests for call statements in Machine Dialect."""

from machine_dialect.ast import (
    Arguments,
    CallStatement,
    Identifier,
    IntegerLiteral,
    StringLiteral,
)
from machine_dialect.parser import Parser


class TestCallStatements:
    """Test parsing of call statements."""

    def test_call_without_parameters(self) -> None:
        """Test parsing a call statement without parameters."""
        source = "call `turn alarm off`."

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        assert isinstance(call_stmt.function_name, Identifier)
        assert call_stmt.function_name.value == "turn alarm off"
        assert call_stmt.arguments is None

    def test_call_with_positional_arguments(self) -> None:
        """Test parsing a call statement with positional arguments."""
        source = "call `add numbers` with _5_, _10_."

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        assert isinstance(call_stmt.function_name, Identifier)
        assert call_stmt.function_name.value == "add numbers"

        assert call_stmt.arguments is not None
        assert isinstance(call_stmt.arguments, Arguments)
        # Should have 2 positional arguments
        assert len(call_stmt.arguments.positional) == 2
        assert len(call_stmt.arguments.named) == 0

        # First argument
        assert isinstance(call_stmt.arguments.positional[0], IntegerLiteral)
        assert call_stmt.arguments.positional[0].value == 5

        # Second argument
        assert isinstance(call_stmt.arguments.positional[1], IntegerLiteral)
        assert call_stmt.arguments.positional[1].value == 10

    def test_call_with_named_arguments(self) -> None:
        """Test parsing a call statement with named arguments."""
        source = 'call `make noise` with `sound`: _"WEE-OO WEE-OO WEE-OO"_, `volume`: _80_.'

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        assert isinstance(call_stmt.function_name, Identifier)
        assert call_stmt.function_name.value == "make noise"

        assert call_stmt.arguments is not None
        assert isinstance(call_stmt.arguments, Arguments)
        # Should have 2 named arguments
        assert len(call_stmt.arguments.positional) == 0
        assert len(call_stmt.arguments.named) == 2

        # First named argument: sound
        name0, val0 = call_stmt.arguments.named[0]
        assert isinstance(name0, Identifier)
        assert name0.value == "sound"
        assert isinstance(val0, StringLiteral)
        assert val0.value == '"WEE-OO WEE-OO WEE-OO"'

        # Second named argument: volume
        name1, val1 = call_stmt.arguments.named[1]
        assert isinstance(name1, Identifier)
        assert name1.value == "volume"
        assert isinstance(val1, IntegerLiteral)
        assert val1.value == 80

    def test_call_with_identifier_as_function_name(self) -> None:
        """Test parsing a call statement with an identifier as the function name."""
        source = 'call `my_function` with _"test"_.'

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        assert isinstance(call_stmt.function_name, Identifier)
        assert call_stmt.function_name.value == "my_function"

    def test_call_with_mixed_arguments(self) -> None:
        """Test parsing a call statement with mix of positional and named arguments."""
        source = 'call `process` with _"data"_, _42_, `format`: _"json"_.'

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        assert isinstance(call_stmt.function_name, Identifier)
        assert call_stmt.function_name.value == "process"

        assert call_stmt.arguments is not None
        assert isinstance(call_stmt.arguments, Arguments)
        # Should have 2 positional and 1 named argument
        assert len(call_stmt.arguments.positional) == 2
        assert len(call_stmt.arguments.named) == 1

        # First positional argument
        assert isinstance(call_stmt.arguments.positional[0], StringLiteral)
        assert call_stmt.arguments.positional[0].value == '"data"'

        # Second positional argument
        assert isinstance(call_stmt.arguments.positional[1], IntegerLiteral)
        assert call_stmt.arguments.positional[1].value == 42

        # Named argument: format
        name, val = call_stmt.arguments.named[0]
        assert isinstance(name, Identifier)
        assert name.value == "format"
        assert isinstance(val, StringLiteral)
        assert val.value == '"json"'

    def test_call_without_period(self) -> None:
        """Test that call statement without period fails."""
        source = "call `my_function`"

        parser = Parser()
        parser.parse(source)

        # Should have an error about missing period
        assert len(parser.errors) > 0
        assert any("period" in str(err).lower() for err in parser.errors)

    def test_multiple_call_statements(self) -> None:
        """Test parsing multiple call statements."""
        source = """call `start process`.
call `log message` with _"Process started"_.
call `stop process`.
"""

        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 3

        # First call
        call1 = program.statements[0]
        assert isinstance(call1, CallStatement)
        assert isinstance(call1.function_name, Identifier)
        assert call1.function_name.value == "start process"
        assert call1.arguments is None

        # Second call
        call2 = program.statements[1]
        assert isinstance(call2, CallStatement)
        assert isinstance(call2.function_name, Identifier)
        assert call2.function_name.value == "log message"
        assert call2.arguments is not None

        # Third call
        call3 = program.statements[2]
        assert isinstance(call3, CallStatement)
        assert isinstance(call3.function_name, Identifier)
        assert call3.function_name.value == "stop process"
        assert call3.arguments is None

    def test_keyword_before_positional_arguments_fails(self) -> None:
        """Test that keyword arguments before positional arguments produces an error."""
        source = 'call `process` with `format`: _"json"_, _"data"_.'

        parser = Parser()
        parser.parse(source)

        # Should have an error about argument ordering
        assert len(parser.errors) > 0
        error_messages = [str(err).lower() for err in parser.errors]
        assert any(
            ("keyword" in msg and "positional" in msg)
            or ("named" in msg and "positional" in msg)
            or ("argument" in msg and "order" in msg)
            for msg in error_messages
        ), f"Expected error about argument ordering, got: {parser.errors}"
