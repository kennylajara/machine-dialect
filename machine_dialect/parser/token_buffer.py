"""Token buffer for streaming tokens from lexer to parser.

This module provides a TokenBuffer class that maintains a small buffer of tokens
and streams them from the lexer to the parser on demand, instead of generating
all tokens upfront.
"""


from machine_dialect.lexer.tokens import Token, TokenType

# Buffer size constant - number of tokens to keep in the buffer
BUFFER_SIZE = 4


class TokenBuffer:
    """Buffer for streaming tokens from lexer to parser.

    Maintains a small buffer of tokens and fetches new tokens from the lexer
    as needed. This allows for memory-efficient parsing of large files.

    Attributes:
        _lexer: The lexer instance to get tokens from.
        _buffer: Internal buffer of tokens.
        _eof_reached: Whether EOF has been reached.
    """

    def __init__(self, lexer) -> None:  # type: ignore
        """Initialize the token buffer with a lexer.

        Args:
            lexer: The lexer instance to stream tokens from.
        """
        from machine_dialect.lexer import Lexer

        self._lexer: Lexer = lexer
        self._buffer: list[Token] = []
        self._eof_reached = False
        self._in_block = False  # Track block context

        # Pre-fill the buffer
        self._fill_buffer()

    def _fill_buffer(self) -> None:
        """Fill the buffer with tokens from the lexer up to BUFFER_SIZE."""
        while len(self._buffer) < BUFFER_SIZE and not self._eof_reached:
            token = self._get_next_token()
            if token is not None:
                self._buffer.append(token)
                if token.type == TokenType.MISC_EOF:
                    self._eof_reached = True
            else:
                # No more tokens available
                self._eof_reached = True
                # Add EOF token if buffer is empty
                if not self._buffer:
                    self._buffer.append(
                        Token(TokenType.MISC_EOF, "", line=self._lexer.line, position=self._lexer.column)
                    )

    def _get_next_token(self) -> Token | None:
        """Get the next token from the lexer.

        Returns:
            The next token, or None if no more tokens are available.
        """
        # Pass the block context to the lexer
        return self._lexer.next_token(in_block=self._in_block)

    def current(self) -> Token | None:
        """Get the current token without consuming it.

        Returns:
            The current token, or None if no tokens are available.
        """
        if self._buffer:
            return self._buffer[0]
        return None

    def peek(self, offset: int = 1) -> Token | None:
        """Peek at a token at the given offset without consuming tokens.

        Args:
            offset: How many tokens ahead to look (1 = next token).

        Returns:
            The token at the given offset, or None if not available.
        """
        # Ensure we have enough tokens in the buffer
        while len(self._buffer) <= offset and not self._eof_reached:
            token = self._get_next_token()
            if token is not None:
                self._buffer.append(token)
                if token.type == TokenType.MISC_EOF:
                    self._eof_reached = True
            else:
                self._eof_reached = True
                break

        if offset < len(self._buffer):
            return self._buffer[offset]

        # Return EOF token if we're past the buffer
        return Token(TokenType.MISC_EOF, "", line=self._lexer.line, position=self._lexer.column)

    def advance(self) -> None:
        """Consume the current token and advance to the next one."""
        if self._buffer:
            self._buffer.pop(0)
            # Refill the buffer to maintain BUFFER_SIZE tokens
            self._fill_buffer()

    def has_tokens(self) -> bool:
        """Check if there are more tokens available.

        Returns:
            True if there are tokens available, False otherwise.
        """
        return bool(self._buffer)

    def set_block_context(self, in_block: bool) -> None:
        """Set the block parsing context.

        Args:
            in_block: Whether we're currently parsing inside a block.
        """
        self._in_block = in_block
