from machine_dialect.lexer import Lexer
from machine_dialect.lexer.tests.helpers import assert_eof, assert_expected_token
from machine_dialect.lexer.tokens import Token, TokenMetaType, TokenType


def is_literal_token(token: Token) -> bool:
    return token.type.meta_type == TokenMetaType.LIT


class TestUnderscoreLiterals:
    def test_wrapped_integer(self) -> None:
        """Test underscore-wrapped integer literals."""
        source = "_42_"
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_INT, "42", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_wrapped_float(self) -> None:
        """Test underscore-wrapped float literals."""
        source = "_3.14_"
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_FLOAT, "3.14", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_wrapped_string(self) -> None:
        """Test underscore-wrapped string literals."""
        source = '_"Hello, World!"_'
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_TEXT, '"Hello, World!"', line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_unwrapped_integer(self) -> None:
        """Test unwrapped integer literals (backward compatibility)."""
        source = "42"
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_INT, "42", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_unwrapped_float(self) -> None:
        """Test unwrapped float literals (backward compatibility)."""
        source = "3.14"
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_FLOAT, "3.14", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_unwrapped_string(self) -> None:
        """Test unwrapped string literals (backward compatibility)."""
        source = '"Hello, World!"'
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_TEXT, '"Hello, World!"', line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_mixed_literals_in_expression(self) -> None:
        """Test both wrapped and unwrapped literals in same expression."""
        source = "Set `x` to _42_ and `y` to 3.14"
        lexer = Lexer(source)

        # Stream tokens and collect numeric literals
        numeric_literals = []
        while True:
            token = lexer.next_token()
            if token.type == TokenType.MISC_EOF:
                break
            if token.type in (TokenType.LIT_INT, TokenType.LIT_FLOAT):
                numeric_literals.append(token)

        assert len(numeric_literals) == 2

        # First literal is wrapped (underscore wrapping handled by lexer)
        expected_int = Token(TokenType.LIT_INT, "42", line=1, position=12)
        assert_expected_token(numeric_literals[0], expected_int)

        # Second literal is unwrapped
        expected_float = Token(TokenType.LIT_FLOAT, "3.14", line=1, position=28)
        assert_expected_token(numeric_literals[1], expected_float)

    def test_underscore_in_identifier(self) -> None:
        """Test that underscores in identifiers don't interfere with literal syntax."""
        source = "_var_name_"
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.MISC_IDENT, "_var_name_", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_incomplete_wrapped_literal(self) -> None:
        """Test incomplete wrapped literal with invalid pattern is marked as illegal."""
        source = "_42"  # Missing closing underscore and starts with _ followed by digits
        lexer = Lexer(source)

        # Get the token
        token = lexer.next_token()

        # Lexer no longer reports errors (parser will handle them)
        assert token.type == TokenType.MISC_ILLEGAL
        assert token.literal == "_42"

        # Verify EOF
        assert_eof(lexer.next_token())
