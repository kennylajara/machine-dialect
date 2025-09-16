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
        expected = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=1)

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
        expected = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=1)

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
            if token.type in (TokenType.LIT_WHOLE_NUMBER, TokenType.LIT_FLOAT):
                numeric_literals.append(token)

        assert len(numeric_literals) == 2

        # First literal is wrapped (underscore wrapping handled by lexer)
        expected_int = Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=12)
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

    def test_wrapped_negative_integer(self) -> None:
        """Test underscore-wrapped negative integer literals."""
        source = "_-42_"
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_WHOLE_NUMBER, "-42", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_wrapped_negative_float(self) -> None:
        """Test underscore-wrapped negative float literals."""
        source = "_-3.14_"
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_FLOAT, "-3.14", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_wrapped_negative_decimal_only(self) -> None:
        """Test underscore-wrapped negative float starting with decimal point."""
        source = "_-.5_"
        lexer = Lexer(source)

        # Expected token
        expected = Token(TokenType.LIT_FLOAT, "-0.5", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_wrapped_positive_decimal_only(self) -> None:
        """Test underscore-wrapped positive float starting with decimal point."""
        source = "_.5_"
        lexer = Lexer(source)

        # Expected token (should normalize .5 to 0.5)
        expected = Token(TokenType.LIT_FLOAT, "0.5", line=1, position=1)

        # Get and verify token
        actual = lexer.next_token()
        assert_expected_token(actual, expected)
        assert is_literal_token(actual)

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_invalid_negative_patterns(self) -> None:
        """Test various invalid negative patterns in underscore literals."""
        # Test _-_ (minus with no number)
        source = "_-_"
        lexer = Lexer(source)

        # Should produce identifier "_" followed by minus and another identifier
        token1 = lexer.next_token()
        assert token1.type == TokenType.MISC_IDENT
        assert token1.literal == "_"

        token2 = lexer.next_token()
        assert token2.type == TokenType.OP_MINUS
        assert token2.literal == "-"

        token3 = lexer.next_token()
        assert token3.type == TokenType.MISC_IDENT
        assert token3.literal == "_"

        assert_eof(lexer.next_token())

    def test_double_negative_invalid(self) -> None:
        """Test that double negative is not valid in underscore literals."""
        source = "_--5_"
        lexer = Lexer(source)

        # Should not parse as a literal
        token1 = lexer.next_token()
        assert token1.type == TokenType.MISC_IDENT
        assert token1.literal == "_"

        # Followed by two minus operators
        token2 = lexer.next_token()
        assert token2.type == TokenType.OP_MINUS

        token3 = lexer.next_token()
        assert token3.type == TokenType.OP_MINUS

        # Then illegal pattern 5_
        token4 = lexer.next_token()
        assert token4.type == TokenType.MISC_ILLEGAL
        assert token4.literal == "5_"

        assert_eof(lexer.next_token())

    def test_negative_in_expression(self) -> None:
        """Test negative literal in an expression context."""
        source = "Set **x** to _-5_."
        lexer = Lexer(source)

        # Collect all tokens
        tokens = []
        while True:
            token = lexer.next_token()
            if token.type == TokenType.MISC_EOF:
                break
            tokens.append(token)

        # Find the negative integer literal
        int_literals = [t for t in tokens if t.type == TokenType.LIT_WHOLE_NUMBER]
        assert len(int_literals) == 1
        assert int_literals[0].literal == "-5"

    def test_malformed_underscore_string_literal(self) -> None:
        """Test malformed underscore string literal like _\"unclosed."""
        source = '_"unclosed.'
        lexer = Lexer(source)

        # This should be treated as a single ILLEGAL token
        token = lexer.next_token()
        assert token.type == TokenType.MISC_ILLEGAL
        assert token.literal == '_"unclosed.'

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_malformed_underscore_single_quote_literal(self) -> None:
        """Test malformed underscore string literal with single quotes."""
        source = "_'unclosed string"
        lexer = Lexer(source)

        # This should be treated as a single ILLEGAL token
        token = lexer.next_token()
        assert token.type == TokenType.MISC_ILLEGAL
        assert token.literal == "_'unclosed string"

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_underscore_string_missing_closing_underscore(self) -> None:
        """Test underscore string literal missing closing underscore."""
        source = '_"complete string"'
        lexer = Lexer(source)

        # Without closing underscore, the opening _ is an identifier
        # and the string is a separate token
        token1 = lexer.next_token()
        assert token1.type == TokenType.MISC_IDENT
        assert token1.literal == "_"

        token2 = lexer.next_token()
        assert token2.type == TokenType.LIT_TEXT
        assert token2.literal == '"complete string"'

        # Verify EOF
        assert_eof(lexer.next_token())

    def test_underscore_with_escaped_quote(self) -> None:
        """Test underscore literal with escaped quote inside."""
        source = '_"text with \\" escaped quote"_'
        lexer = Lexer(source)

        # Should parse correctly as a string literal
        token = lexer.next_token()
        assert token.type == TokenType.LIT_TEXT
        assert token.literal == '"text with \\" escaped quote"'

        # Verify EOF
        assert_eof(lexer.next_token())
