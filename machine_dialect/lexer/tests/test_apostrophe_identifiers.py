"""Tests for apostrophe support in identifiers."""

from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tokens import TokenType, is_valid_identifier


class TestApostropheIdentifiers:
    """Test apostrophe support in identifiers."""

    def test_valid_apostrophe_identifiers(self) -> None:
        """Test that valid apostrophe patterns are accepted."""
        valid_identifiers = [
            "don't",
            "can't",
            "won't",
            "I'm",
            "it's",
            "person's",
            "person's name",
            "I don't like",
            "can't wait",
            "won't stop",
            "it's working",
            "user's data",
            "server's response",
        ]

        for identifier in valid_identifiers:
            assert is_valid_identifier(identifier), f"'{identifier}' should be valid"

    def test_invalid_apostrophe_identifiers(self) -> None:
        """Test that invalid apostrophe patterns are rejected."""
        invalid_identifiers = [
            "'hello",  # Starts with apostrophe
            "hello'",  # Ends with apostrophe
            "'",  # Just apostrophe
            "hello 'world",  # Word starts with apostrophe
            "hello world'",  # Word ends with apostrophe
            "'hello world",  # Starts with apostrophe
            "hello world'",  # Ends with apostrophe
        ]

        for identifier in invalid_identifiers:
            assert not is_valid_identifier(identifier), f"'{identifier}' should be invalid"

    def test_backtick_identifiers_with_apostrophes(self) -> None:
        """Test that backtick-wrapped identifiers with apostrophes work correctly."""
        test_cases = [
            ("Set `don't` to _true_.", "don't", TokenType.MISC_IDENT),
            ("Set `I'm happy` to _yes_.", "I'm happy", TokenType.MISC_IDENT),
            ('Set `person\'s name` to _"John"_.', "person's name", TokenType.MISC_IDENT),
            ("Set `I don't like` to _no_.", "I don't like", TokenType.MISC_IDENT),
            ("Set `can't wait` to _true_.", "can't wait", TokenType.MISC_IDENT),
        ]

        for source, expected_ident, expected_type in test_cases:
            lexer = Lexer(source)

            # Skip "Set"
            token = lexer.next_token()
            assert token.type == TokenType.KW_SET

            # Get the identifier
            token = lexer.next_token()
            assert token.type == expected_type, f"Expected {expected_type}, got {token.type}"
            assert token.literal == expected_ident, f"Expected '{expected_ident}', got '{token.literal}'"

    def test_invalid_apostrophe_patterns_in_backticks(self) -> None:
        """Test that invalid apostrophe patterns still fail in backticks."""
        invalid_sources = [
            "`'hello`",  # Starts with apostrophe
            "`hello'`",  # Ends with apostrophe
            "`hello 'world`",  # Word starts with apostrophe
            "`hello world'`",  # Word ends with apostrophe
        ]

        for source in invalid_sources:
            lexer = Lexer(source)
            token = lexer.next_token()
            # Should return MISC_ILLEGAL since the identifier is invalid
            assert token.type == TokenType.MISC_ILLEGAL, f"Source '{source}' should produce MISC_ILLEGAL"

    def test_apostrophe_s_possessive(self) -> None:
        """Test that possessive 's pattern works correctly."""
        # Test with our new syntax: possessive followed by string literal
        source = '`person`\'s "name"'
        lexer = Lexer(source)

        # Should get the possessive token
        token = lexer.next_token()
        assert token.type == TokenType.PUNCT_APOSTROPHE_S
        assert token.literal == "person"

        # Next should be a string literal
        token = lexer.next_token()
        assert token.type == TokenType.LIT_TEXT
        assert token.literal == '"name"'

        # Also test with a non-keyword identifier in backticks
        source2 = "`person`'s `property`"
        lexer2 = Lexer(source2)

        token = lexer2.next_token()
        assert token.type == TokenType.PUNCT_APOSTROPHE_S
        assert token.literal == "person"

        token = lexer2.next_token()
        assert token.type == TokenType.MISC_IDENT
        assert token.literal == "property"

    def test_mixed_valid_characters(self) -> None:
        """Test identifiers with mixed valid characters including apostrophes."""
        valid_identifiers = [
            "user_1's_data",
            "don't-stop",
            "can't_wait_2",
            "person's-item",
            "it's_working-now",
        ]

        for identifier in valid_identifiers:
            assert is_valid_identifier(identifier), f"'{identifier}' should be valid"
