from machine_dialect.ast import (
    Identifier,
    Program,
    SetStatement,
    Statement,
)
from machine_dialect.lexer import Lexer, Token, TokenType


class Parser:
    def __init__(self, lexer: Lexer) -> None:
        self._current_token: Token | None = None
        self._peek_token: Token | None = None
        self._tokens = list(lexer.tokenize())
        self._token_index = 0

        self._advance_tokens()
        self._advance_tokens()

    def parse(self) -> Program:
        program: Program = Program(statements=[])

        assert self._current_token is not None
        while self._current_token.type != TokenType.MISC_EOF:
            statement = self._parse_statement()
            if statement is not None:
                program.statements.append(statement)
            self._advance_tokens()

        return program

    def _advance_tokens(self) -> None:
        self._current_token = self._peek_token
        if self._token_index < len(self._tokens):
            self._peek_token = self._tokens[self._token_index]
            self._token_index += 1
        else:
            self._peek_token = Token(TokenType.MISC_EOF, "")

    def _expected_token(self, token_type: TokenType) -> bool:
        assert self._peek_token is not None
        if self._peek_token.type == token_type:
            self._advance_tokens()

            return True

        return False

    def _parse_let_statement(self) -> SetStatement | None:
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
        assert self._current_token is not None

        if self._current_token.type == TokenType.KW_SET:
            return self._parse_let_statement()
        else:
            return None
