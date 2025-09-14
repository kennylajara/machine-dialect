from typing import TYPE_CHECKING

from machine_dialect.lexer.tokens import Token, TokenType

if TYPE_CHECKING:
    from machine_dialect.lexer import Lexer


def assert_expected_token(actual: Token, expected: Token) -> None:
    """Assert that an actual token matches the expected token.

    Args:
        actual: The token received from the lexer.
        expected: The expected token.
    """
    assert actual.type == expected.type, f"Token type mismatch: got {actual.type}, expected {expected.type}"
    assert actual.literal == expected.literal, (
        f"Token literal mismatch: got '{actual.literal}', expected '{expected.literal}'"
    )
    assert actual.line == expected.line, f"Token line mismatch: got {actual.line}, expected {expected.line}"
    assert actual.position == expected.position, (
        f"Token position mismatch: got {actual.position}, expected {expected.position}"
    )


def assert_eof(token: Token) -> None:
    """Assert that a token is an EOF token.

    Args:
        token: The token to check.
    """
    assert token.type == TokenType.MISC_EOF, f"Expected EOF token, got {token.type}"


def stream_and_assert_tokens(lexer: "Lexer", expected_tokens: list[Token]) -> None:
    """Stream tokens from lexer and assert they match expected tokens.

    This helper function:
    1. Streams tokens one by one from the lexer
    2. Asserts each token matches the expected token
    3. Verifies the count matches
    4. Asserts EOF is reached after all expected tokens

    Args:
        lexer: The lexer instance to stream tokens from.
        expected_tokens: List of expected tokens (not including EOF).
    """
    actual_count = 0

    for i, expected in enumerate(expected_tokens):
        actual = lexer.next_token()
        assert actual.type != TokenType.MISC_EOF, f"Got EOF at token {i}, expected {len(expected_tokens)} tokens"
        assert_expected_token(actual, expected)
        actual_count += 1

    # Verify we get EOF next
    eof_token = lexer.next_token()
    assert_eof(eof_token)

    # Verify count
    assert actual_count == len(expected_tokens), f"Expected {len(expected_tokens)} tokens, got {actual_count}"


def token(token_type: TokenType, literal: str, line: int = 1, position: int = 0) -> Token:
    """Helper function to create tokens with default line and position values for tests."""
    return Token(token_type, literal, line, position)


def collect_all_tokens(lexer: "Lexer") -> list[Token]:
    """Collect all tokens from lexer until EOF (excluding EOF token).

    This is useful for tests that need to examine all tokens but don't
    want to repeatedly write the streaming loop.

    Args:
        lexer: The lexer instance to stream tokens from.

    Returns:
        List of all tokens excluding the EOF token.
    """
    tokens = []
    token = lexer.next_token()
    while token.type != TokenType.MISC_EOF:
        tokens.append(token)
        token = lexer.next_token()
    return tokens
