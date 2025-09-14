"""Tests for strict equality operators in the lexer.

This module tests that the lexer correctly recognizes strict equality
and strict inequality operators in their various natural language forms.
"""

import pytest

from machine_dialect.lexer import Lexer
from machine_dialect.lexer.tokens import TokenType


class TestStrictEqualityOperators:
    """Test the lexer's handling of strict equality operators."""

    @pytest.mark.parametrize(
        "source,expected_token_type,expected_literal",
        [
            # Strict equality operators
            ("is strictly equal to", TokenType.OP_STRICT_EQ, "is strictly equal to"),
            ("is exactly equal to", TokenType.OP_STRICT_EQ, "is exactly equal to"),
            ("is identical to", TokenType.OP_STRICT_EQ, "is identical to"),
            # Strict inequality operators
            ("is not strictly equal to", TokenType.OP_STRICT_NOT_EQ, "is not strictly equal to"),
            ("is not exactly equal to", TokenType.OP_STRICT_NOT_EQ, "is not exactly equal to"),
            ("is not identical to", TokenType.OP_STRICT_NOT_EQ, "is not identical to"),
            # Value equality (for comparison)
            ("is equal to", TokenType.OP_EQ, "is equal to"),
            ("equals", TokenType.OP_EQ, "equals"),
            ("is the same as", TokenType.OP_EQ, "is the same as"),
            # Value inequality (for comparison)
            ("is not equal to", TokenType.OP_NOT_EQ, "is not equal to"),
            ("does not equal", TokenType.OP_NOT_EQ, "does not equal"),
            ("is different from", TokenType.OP_NOT_EQ, "is different from"),
        ],
    )
    def test_strict_equality_operators(
        self, source: str, expected_token_type: TokenType, expected_literal: str
    ) -> None:
        """Test that strict equality operators are correctly tokenized.

        Args:
            source: The source string containing the operator.
            expected_token_type: The expected token type.
            expected_literal: The expected literal value.
        """
        lexer = Lexer(source)
        token = lexer.next_token()

        assert token.type == expected_token_type
        assert token.literal == expected_literal

    def test_strict_equality_in_expression(self) -> None:
        """Test strict equality operators in complete expressions."""
        source = "if x is strictly equal to 5 then give back Yes"
        lexer = Lexer(source)

        expected_tokens = [
            (TokenType.KW_IF, "if"),
            (TokenType.MISC_IDENT, "x"),
            (TokenType.OP_STRICT_EQ, "is strictly equal to"),
            (TokenType.LIT_WHOLE_NUMBER, "5"),
            (TokenType.KW_THEN, "then"),
            (TokenType.KW_RETURN, "give back"),
            (TokenType.LIT_YES, "Yes"),
            (TokenType.MISC_EOF, ""),
        ]

        for expected_type, expected_literal in expected_tokens:
            token = lexer.next_token()
            assert token.type == expected_type
            assert token.literal == expected_literal

    def test_strict_inequality_in_expression(self) -> None:
        """Test strict inequality operators in complete expressions."""
        source = "if `value` is not identical to `null` then `process`"
        lexer = Lexer(source)

        expected_tokens = [
            (TokenType.KW_IF, "if"),
            (TokenType.MISC_IDENT, "value"),
            (TokenType.OP_STRICT_NOT_EQ, "is not identical to"),
            (TokenType.MISC_IDENT, "null"),
            (TokenType.KW_THEN, "then"),
            (TokenType.MISC_IDENT, "process"),
            (TokenType.MISC_EOF, ""),
        ]

        for expected_type, expected_literal in expected_tokens:
            token = lexer.next_token()
            assert token.type == expected_type
            assert token.literal == expected_literal

    def test_mixed_equality_operators(self) -> None:
        """Test that different equality operators are distinguished correctly."""
        source = "`a` equals `b` and `c` is strictly equal to `d`"
        lexer = Lexer(source)

        expected_tokens = [
            (TokenType.MISC_IDENT, "a"),
            (TokenType.OP_EQ, "equals"),
            (TokenType.MISC_IDENT, "b"),
            (TokenType.KW_AND, "and"),
            (TokenType.MISC_IDENT, "c"),
            (TokenType.OP_STRICT_EQ, "is strictly equal to"),
            (TokenType.MISC_IDENT, "d"),
            (TokenType.MISC_EOF, ""),
        ]

        for expected_type, expected_literal in expected_tokens:
            token = lexer.next_token()
            assert token.type == expected_type
            assert token.literal == expected_literal

    def test_case_insensitive_strict_operators(self) -> None:
        """Test that strict operators are case-insensitive."""
        test_cases = [
            ("Is Strictly Equal To", TokenType.OP_STRICT_EQ),
            ("IS EXACTLY EQUAL TO", TokenType.OP_STRICT_EQ),
            ("Is Identical To", TokenType.OP_STRICT_EQ),
            ("IS NOT STRICTLY EQUAL TO", TokenType.OP_STRICT_NOT_EQ),
            ("Is Not Exactly Equal To", TokenType.OP_STRICT_NOT_EQ),
            ("is NOT identical TO", TokenType.OP_STRICT_NOT_EQ),
        ]

        for source, expected_type in test_cases:
            lexer = Lexer(source)
            token = lexer.next_token()
            assert token.type == expected_type
