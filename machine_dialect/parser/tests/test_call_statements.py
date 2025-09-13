"""Tests for use statements in Machine Dialect™."""

from machine_dialect.ast import (
    Arguments,
    CallStatement,
    Identifier,
    StringLiteral,
    WholeNumberLiteral,
)
from machine_dialect.parser import Parser


class TestCallStatements:
    """Test parsing of use statements."""

    def test_call_without_parameters(self) -> None:
        """Test parsing a use statement without parameters."""
        source = "use `turn alarm off`."

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        assert isinstance(call_stmt.function_name, Identifier)
        assert call_stmt.function_name.value == "turn alarm off"
        assert call_stmt.arguments is None

    def test_call_with_positional_arguments(self) -> None:
        """Test parsing a use statement with positional arguments."""
        source = "use `add numbers` with _5_, _10_."

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

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
        assert isinstance(call_stmt.arguments.positional[0], WholeNumberLiteral)
        assert call_stmt.arguments.positional[0].value == 5

        # Second argument
        assert isinstance(call_stmt.arguments.positional[1], WholeNumberLiteral)
        assert call_stmt.arguments.positional[1].value == 10

    def test_call_with_named_arguments(self) -> None:
        """Test parsing a use statement with named arguments."""
        source = 'use `make noise` where `sound` is _"WEE-OO WEE-OO WEE-OO"_, `volume` is _80_.'

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

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
        assert val0.value == "WEE-OO WEE-OO WEE-OO"

        # Second named argument: volume
        name1, val1 = call_stmt.arguments.named[1]
        assert isinstance(name1, Identifier)
        assert name1.value == "volume"
        assert isinstance(val1, WholeNumberLiteral)
        assert val1.value == 80

    def test_call_with_identifier_as_function_name(self) -> None:
        """Test parsing a use statement with an identifier as the function name."""
        source = 'use `my_function` with _"test"_.'

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 1

        call_stmt = program.statements[0]
        assert isinstance(call_stmt, CallStatement)
        assert isinstance(call_stmt.function_name, Identifier)
        assert call_stmt.function_name.value == "my_function"

    def test_call_without_period(self) -> None:
        """Test that use statement without period fails."""
        source = "use `my_function`"

        parser = Parser()
        parser.parse(source)

        # Should have an error about missing period
        assert len(parser.errors) > 0
        assert any("period" in str(err).lower() for err in parser.errors)

    def test_multiple_call_statements(self) -> None:
        """Test parsing multiple use statements."""
        source = """use `start process`.
use `log message` with _"Process started"_.
use `stop process`.
"""

        parser = Parser()
        program = parser.parse(source, check_semantics=False)

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
