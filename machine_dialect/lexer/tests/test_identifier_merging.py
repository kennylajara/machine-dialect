"""Tests for identifier merging functionality in the lexer."""

from machine_dialect.lexer import Lexer, TokenType


class TestIdentifierMerging:
    """Test cases for the identifier merging post-processing."""

    def test_merge_consecutive_identifiers(self) -> None:
        """Test merging of consecutive identifier tokens."""
        source = "hello world"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should produce one merged identifier
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "hello world"

    def test_merge_multiple_consecutive_identifiers(self) -> None:
        """Test merging of multiple consecutive identifiers."""
        source = "first middle last name"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should produce one merged identifier
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "first middle last name"

    def test_merge_identifiers_with_stopwords(self) -> None:
        """Test merging identifiers with stopwords in between."""
        source = "info collected by the system"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should produce one merged identifier (with stopwords included)
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "info collected by the system"

    def test_no_merge_illegal_tokens(self) -> None:
        """Test that illegal tokens are NOT merged into identifiers."""
        source = "user@email"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should NOT merge - illegal token stays separate
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "user"
        assert tokens[1].type == TokenType.MISC_ILLEGAL
        assert tokens[1].literal == "@"
        assert tokens[2].type == TokenType.MISC_IDENT
        assert tokens[2].literal == "email"

        # Lexer no longer reports errors (parser will handle them)

    def test_no_merge_with_operators(self) -> None:
        """Test that operators prevent merging."""
        source = "x + y"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should produce separate tokens (y might be stopword)
        assert len(tokens) >= 3
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "x"
        assert tokens[1].type == TokenType.OP_PLUS

    def test_no_merge_with_punctuation(self) -> None:
        """Test that punctuation prevents merging."""
        source = "name, age"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should produce separate tokens
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "name"
        assert tokens[1].type == TokenType.PUNCT_COMMA
        assert tokens[2].type == TokenType.MISC_IDENT
        assert tokens[2].literal == "age"

    def test_leading_stopword_not_merged(self) -> None:
        """Test that leading stopwords are not merged."""
        source = "the username"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should not merge - stopword at start stays separate
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.MISC_STOPWORD
        assert tokens[0].literal == "the"
        assert tokens[1].type == TokenType.MISC_IDENT
        assert tokens[1].literal == "username"

    def test_trailing_stopword_not_merged(self) -> None:
        """Test that trailing stopwords are not merged."""
        source = "username are"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should not merge - stopword at end stays separate
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "username"
        assert tokens[1].type == TokenType.MISC_STOPWORD
        assert tokens[1].literal == "are"

    def test_leading_illegal_token_no_merge(self) -> None:
        """Test that leading illegal tokens are not merged."""
        source = "@illegal"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should not merge - illegal token stays separate
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.MISC_ILLEGAL
        assert tokens[0].literal == "@"
        assert tokens[1].type == TokenType.MISC_IDENT
        assert tokens[1].literal == "illegal"

    def test_position_preserved_after_merge(self) -> None:
        """Test that position information is preserved correctly."""
        source = "hello world"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Merged token should have position of first token
        assert tokens[0].line == 1
        assert tokens[0].position == 0

    def test_complex_merging_scenario(self) -> None:
        """Test complex scenario with multiple merging cases."""
        source = "The username with email address are with the user info collected by the system"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Expected tokens based on the rules
        expected_literals = [
            "The",  # Leading stopword
            "username",  # Identifier
            "with",  # Keyword
            "email address",  # Merged identifiers
            "are",  # Trailing stopword
            "with",  # Keyword
            "the",  # Leading stopword
            "user info collected by the system",  # Merged sequence
        ]

        actual_literals = [t.literal for t in tokens if t.type != TokenType.MISC_EOF]
        assert actual_literals == expected_literals

    def test_arithmetic_expression_not_merged(self) -> None:
        """Test that arithmetic expressions are not affected by merging."""
        source = "payment_period_days - days_since_last_payment"
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Should keep minus operator separate
        assert any(t.type == TokenType.OP_MINUS for t in tokens)

        # Should have separate identifiers
        ident_tokens = [t for t in tokens if t.type == TokenType.MISC_IDENT]
        assert len(ident_tokens) == 2
        assert ident_tokens[0].literal == "payment_period_days"
        assert ident_tokens[1].literal == "days_since_last_payment"
