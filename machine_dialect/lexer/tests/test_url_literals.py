from machine_dialect.lexer import Lexer, Token, TokenType
from machine_dialect.lexer.tests.helpers import collect_all_tokens


class TestURLLiterals:
    """Test URL literal detection in the lexer."""

    def _tokenize_no_errors(self, source: str) -> list[Token]:
        """Helper to tokenize and assert no errors.

        Args:
            source: The source code to tokenize.

        Returns:
            The list of tokens.
        """
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        return tokens

    def test_http_url_detection(self) -> None:
        source = '"http://example.com"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"http://example.com"'

    def test_https_url_detection(self) -> None:
        source = '"https://www.example.com/path"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"https://www.example.com/path"'

    def test_ftp_url_detection(self) -> None:
        source = '"ftp://files.example.com/file.txt"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"ftp://files.example.com/file.txt"'

    def test_url_with_query_params(self) -> None:
        source = '"https://api.example.com/data?key=value&foo=bar"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"https://api.example.com/data?key=value&foo=bar"'

    def test_url_with_fragment(self) -> None:
        source = '"https://example.com/page#section"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"https://example.com/page#section"'

    def test_url_with_port(self) -> None:
        source = '"http://localhost:8080/api"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"http://localhost:8080/api"'

    def test_non_url_string(self) -> None:
        source = '"Hello, World!"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TEXT
        assert tokens[0].literal == '"Hello, World!"'

    def test_invalid_url_format(self) -> None:
        source = '"http://invalid url with spaces"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TEXT
        assert tokens[0].literal == '"http://invalid url with spaces"'

    def test_url_without_scheme(self) -> None:
        source = '"example.com"'
        tokens = self._tokenize_no_errors(source)

        # Without scheme, it should be treated as regular text
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TEXT
        assert tokens[0].literal == '"example.com"'

    def test_single_quoted_url(self) -> None:
        source = "'https://example.com'"
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == "'https://example.com'"

    def test_empty_string(self) -> None:
        source = '""'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TEXT
        assert tokens[0].literal == '""'

    def test_multiple_urls_in_source(self) -> None:
        source = 'Set `url1` to "https://api.example.com" and `url2` to "https://docs.example.com"'
        tokens = self._tokenize_no_errors(source)

        # Find URL tokens
        url_tokens = [t for t in tokens if t.type == TokenType.LIT_URL]
        assert len(url_tokens) == 2
        assert url_tokens[0].literal == '"https://api.example.com"'
        assert url_tokens[1].literal == '"https://docs.example.com"'

    def test_url_with_special_characters(self) -> None:
        source = '"https://example.com/path?q=test+query&id=123#anchor"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"https://example.com/path?q=test+query&id=123#anchor"'

    def test_mailto_url(self) -> None:
        source = '"mailto:user@example.com"'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"mailto:user@example.com"'

    def test_data_url(self) -> None:
        source = '"data:text/plain;base64,SGVsbG8="'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"data:text/plain;base64,SGVsbG8="'

    def test_underscore_wrapped_url(self) -> None:
        """Test URL detection with underscore wrapping (Machine Dialect™ syntax)."""
        source = '_"https://example.com"_'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"https://example.com"'

    def test_underscore_wrapped_non_url(self) -> None:
        """Test that non-URLs with underscores are still text."""
        source = '_"not a url"_'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TEXT
        assert tokens[0].literal == '"not a url"'

    def test_underscore_wrapped_url_with_query(self) -> None:
        """Test complex URL with underscore wrapping."""
        source = '_"https://api.example.com/v1/users?id=123&active=true#profile"_'
        tokens = self._tokenize_no_errors(source)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_URL
        assert tokens[0].literal == '"https://api.example.com/v1/users?id=123&active=true#profile"'
