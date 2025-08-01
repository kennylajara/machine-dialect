from machine_dialect.lexer.tokens import Token, TokenType


def token(token_type: TokenType, literal: str, line: int = 1, position: int = 0) -> Token:
    """Helper function to create tokens with default line and position values for tests."""
    return Token(token_type, literal, line, position)
