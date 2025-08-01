from machine_dialect.ast import (
    Identifier,
    Program,
    SetStatement,
    Statement,
)
from machine_dialect.errors.exceptions import MDBaseException
from machine_dialect.lexer import Lexer, Token, TokenType


class Parser:
    """Parser for Machine Dialect language.

    Transforms a sequence of tokens from the lexer into an Abstract Syntax Tree (AST).
    Also collects any lexical errors from the tokenizer.

    Attributes:
        errors (list[MDBaseException]): List of errors encountered during parsing,
            including lexical errors from the tokenizer.
    """

    def __init__(self, lexer: Lexer) -> None:
        """Initialize the parser with a lexer.

        Args:
            lexer: The lexer instance to get tokens from.
        """
        self._current_token: Token | None = None
        self._peek_token: Token | None = None

        # Get tokens and errors from the lexer
        lexer_errors, self._tokens = lexer.tokenize()
        self.errors: list[MDBaseException] = list(lexer_errors)
        self._token_index = 0

        self._advance_tokens()
        self._advance_tokens()

    def parse(self) -> Program:
        """Parse the tokens into an AST.

        Returns:
            The root Program node of the AST.

        Note:
            Any errors encountered during parsing are added to the
            errors attribute. The parser attempts to continue parsing
            even after encountering errors.
        """
        program: Program = Program(statements=[])

        assert self._current_token is not None
        while self._current_token.type != TokenType.MISC_EOF:
            statement = self._parse_statement()
            if statement is not None:
                program.statements.append(statement)
            self._advance_tokens()

        return program

    def has_errors(self) -> bool:
        """Check if any errors were encountered during parsing.

        Returns:
            True if there are any errors, False otherwise.
        """
        return len(self.errors) > 0

    def _advance_tokens(self) -> None:
        """Advance to the next token in the stream.

        Moves the peek token to current token and reads the next token
        into peek token. If no more tokens are available, sets peek token
        to EOF.
        """
        self._current_token = self._peek_token
        if self._token_index < len(self._tokens):
            self._peek_token = self._tokens[self._token_index]
            self._token_index += 1
        else:
            self._peek_token = Token(TokenType.MISC_EOF, "", line=1, position=0)

    def _expected_token(self, token_type: TokenType) -> bool:
        """Check if the next token matches the expected type and consume it.

        Args:
            token_type: The expected token type.

        Returns:
            True if the token matched and was consumed, False otherwise.
        """
        assert self._peek_token is not None
        if self._peek_token.type == token_type:
            self._advance_tokens()
            return True
        return False

    def _parse_let_statement(self) -> SetStatement | None:
        """Parse a Set statement.

        Expects: Set `identifier` to expression

        Returns:
            A SetStatement AST node if successful, None if parsing fails.
        """
        assert self._current_token is not None
        let_statement = SetStatement(token=self._current_token)

        # Expect backtick identifier like `X`
        if not self._expected_token(TokenType.LIT_BACKTICK):
            return None

        # Extract identifier from backticks
        identifier_value = self._current_token.literal.strip("`")
        let_statement.name = Identifier(token=self._current_token, value=identifier_value)

        # Expect "to" keyword
        if not self._expected_token(TokenType.KW_TO):
            return None

        # TODO: Finish when we know how to parse expressions
        # For now, consume tokens until EOF or next Set statement
        while (
            self._current_token is not None
            and self._current_token.type != TokenType.MISC_EOF
            and self._peek_token is not None
            and self._peek_token.type != TokenType.KW_SET
        ):
            self._advance_tokens()

        return let_statement

    def _parse_statement(self) -> Statement | None:
        """Parse a single statement.

        Determines the statement type based on the current token and
        delegates to the appropriate parsing method.

        Returns:
            A Statement AST node if successful, None if no valid statement found.
        """
        assert self._current_token is not None

        if self._current_token.type == TokenType.KW_SET:
            return self._parse_let_statement()
        else:
            return None
