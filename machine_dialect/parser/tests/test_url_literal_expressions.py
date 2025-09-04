"""Tests for URL literal expressions in the parser."""

import machine_dialect.ast as ast
from machine_dialect.parser import Parser


class TestURLLiteralExpressions:
    """Test parsing of URL literal expressions."""

    def test_parse_simple_url_literal(self) -> None:
        """Test parsing a simple URL literal."""
        source = '_"https://example.com"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.ExpressionStatement)
        assert isinstance(stmt.expression, ast.URLLiteral)
        assert stmt.expression.value == "https://example.com"

    def test_parse_complex_url_literal(self) -> None:
        """Test parsing a complex URL with query parameters."""
        source = '_"https://api.example.com/v1/users?id=123&active=true#profile"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.ExpressionStatement)
        assert isinstance(stmt.expression, ast.URLLiteral)
        assert stmt.expression.value == "https://api.example.com/v1/users?id=123&active=true#profile"

    def test_parse_ftp_url_literal(self) -> None:
        """Test parsing an FTP URL literal."""
        source = '_"ftp://files.example.com/data.zip"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.ExpressionStatement)
        assert isinstance(stmt.expression, ast.URLLiteral)
        assert stmt.expression.value == "ftp://files.example.com/data.zip"

    def test_parse_mailto_url_literal(self) -> None:
        """Test parsing a mailto URL literal."""
        source = '_"mailto:user@example.com"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.ExpressionStatement)
        assert isinstance(stmt.expression, ast.URLLiteral)
        assert stmt.expression.value == "mailto:user@example.com"

    def test_url_vs_string_distinction(self) -> None:
        """Test that URLs and regular strings are parsed as different types."""
        # Parse URL
        url_source = '_"https://example.com"_.'
        parser1 = Parser()
        url_program = parser1.parse(url_source)

        assert url_program is not None
        url_stmt = url_program.statements[0]
        assert isinstance(url_stmt, ast.ExpressionStatement)
        assert isinstance(url_stmt.expression, ast.URLLiteral)

        # Parse regular string
        string_source = '_"not a url"_.'
        parser2 = Parser()
        string_program = parser2.parse(string_source)

        assert string_program is not None
        string_stmt = string_program.statements[0]
        assert isinstance(string_stmt, ast.ExpressionStatement)
        assert isinstance(string_stmt.expression, ast.StringLiteral)

    def test_url_in_set_statement(self) -> None:
        """Test using a URL literal in a set statement."""
        source = 'Set `api_endpoint` to _"https://api.example.com/v1"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.SetStatement)
        assert stmt.name is not None
        assert stmt.name.value == "api_endpoint"
        assert isinstance(stmt.value, ast.URLLiteral)
        assert stmt.value.value == "https://api.example.com/v1"

    def test_url_with_port(self) -> None:
        """Test parsing URL with port number."""
        source = '_"http://localhost:8080/api"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.ExpressionStatement)
        assert isinstance(stmt.expression, ast.URLLiteral)
        assert stmt.expression.value == "http://localhost:8080/api"

    def test_data_url(self) -> None:
        """Test parsing data URL."""
        source = '_"data:text/plain;base64,SGVsbG8="_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.ExpressionStatement)
        assert isinstance(stmt.expression, ast.URLLiteral)
        assert stmt.expression.value == "data:text/plain;base64,SGVsbG8="

    def test_multiple_urls_in_program(self) -> None:
        """Test parsing multiple URLs in a program."""
        source = """
        Set `primary` to _"https://primary.example.com"_.
        Set `secondary` to _"https://secondary.example.com"_.
        Set `message` to _"Hello, World!"_.
        """
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 3

        # First statement - URL
        stmt1 = program.statements[0]
        assert isinstance(stmt1, ast.SetStatement)
        assert isinstance(stmt1.value, ast.URLLiteral)
        assert stmt1.value.value == "https://primary.example.com"

        # Second statement - URL
        stmt2 = program.statements[1]
        assert isinstance(stmt2, ast.SetStatement)
        assert isinstance(stmt2.value, ast.URLLiteral)
        assert stmt2.value.value == "https://secondary.example.com"

        # Third statement - Regular string
        stmt3 = program.statements[2]
        assert isinstance(stmt3, ast.SetStatement)
        assert isinstance(stmt3.value, ast.StringLiteral)
        assert stmt3.value.value == "Hello, World!"

    def test_url_string_representation(self) -> None:
        """Test the string representation of URL literals."""
        source = '_"https://example.com"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        stmt = program.statements[0]
        assert isinstance(stmt, ast.ExpressionStatement)

        # The string representation should use underscore syntax
        assert str(stmt.expression) == '_"https://example.com"_'

    def test_url_in_call_statement(self) -> None:
        """Test using a URL literal as an argument in a use statement."""
        source = 'Use `fetch` with _"https://api.example.com/data"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.CallStatement)
        assert stmt.function_name is not None
        assert isinstance(stmt.function_name, ast.Identifier)
        assert stmt.function_name.value == "fetch"
        assert stmt.arguments is not None
        assert isinstance(stmt.arguments, ast.Arguments)
        assert len(stmt.arguments.positional) == 1
        assert isinstance(stmt.arguments.positional[0], ast.URLLiteral)
        assert stmt.arguments.positional[0].value == "https://api.example.com/data"

    def test_url_without_scheme_is_string(self) -> None:
        """Test that URLs without schemes are parsed as regular strings."""
        source = '_"example.com"_.'
        parser = Parser()
        program = parser.parse(source)

        assert program is not None
        assert len(program.statements) == 1

        stmt = program.statements[0]
        assert isinstance(stmt, ast.ExpressionStatement)
        # Without a scheme, it should be a StringLiteral, not URLLiteral
        assert isinstance(stmt.expression, ast.StringLiteral)
        assert stmt.expression.value == "example.com"
