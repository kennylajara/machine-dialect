from ast import Expression
from collections.abc import Callable

from machine_dialect.ast import (
    Identifier,
    Program,
    ReturnStatement,
    SetStatement,
    Statement,
)
from machine_dialect.errors.exceptions import MDBaseException, MDSyntaxError
from machine_dialect.errors.messages import UNEXPECTED_TOKEN
from machine_dialect.lexer import Lexer, Token, TokenType

PrefixParseFunc = Callable[[], Expression | None]
InfixParseFunc = Callable[[Expression], Expression | None]
PostfixParseFunc = Callable[[Expression], Expression | None]
PrefixParseFuncs = dict[TokenType, PrefixParseFunc]
InfixParseFuncs = dict[TokenType, InfixParseFunc]
PostfixParseFuncs = dict[TokenType, PostfixParseFunc]


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
        self._errors: list[MDBaseException] = list(lexer_errors)
        self._token_index = 0

        self._prefix_parse_funcs: PrefixParseFuncs = self._register_prefix_funcs()
        self._infix_parse_funcs: InfixParseFuncs = self._register_infix_funcs()
        self._postfix_parse_funcs: PostfixParseFuncs = self._register_postfix_funcs()

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
        return len(self._errors) > 0

    @property
    def errors(self) -> list[MDBaseException]:
        """Get the list of errors encountered during parsing.

        This includes both lexical errors from the tokenizer and syntax errors
        from the parser. Errors are collected in the order they were encountered.

        Returns:
            List of MDBaseException instances representing all errors found
            during lexical analysis and parsing.
        """
        return self._errors

    def _advance_tokens(self) -> None:
        """Advance to the next token in the stream.

        Moves the peek token to current token and reads the next token
        into peek token. If no more tokens are available, sets peek token
        to EOF. Automatically skips MISC_STOPWORD tokens.
        """
        self._current_token = self._peek_token

        # Skip any stopword tokens
        while self._token_index < len(self._tokens):
            self._peek_token = self._tokens[self._token_index]
            self._token_index += 1

            # If it's not a stopword, we're done
            if self._peek_token.type != TokenType.MISC_STOPWORD:
                break
        else:
            # No more tokens available
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

        self._expected_token_error(token_type)
        return False

    def _expected_token_error(self, token_type: TokenType) -> None:
        """Record an error for an unexpected token.

        Creates and adds a syntax error to the errors list when the parser
        encounters a token different from what was expected.

        Args:
            token_type: The token type that was expected but not found.
        """
        assert self._peek_token is not None
        error_message = UNEXPECTED_TOKEN.substitute(
            token_literal=self._peek_token.literal,
            expected_token_type=token_type,
            received_token_type=self._peek_token.type,
        )
        error = MDSyntaxError(
            message=error_message,
            line=self._peek_token.line,
            column=self._peek_token.position,
        )
        self.errors.append(error)

    def _parse_let_statement(self) -> SetStatement | None:
        """Parse a Set statement.

        Expects: Set `identifier` to expression

        Returns:
            A SetStatement AST node if successful, None if parsing fails.
        """
        assert self._current_token is not None
        let_statement = SetStatement(token=self._current_token)

        # Expect identifier (which may have come from backticks)
        if not self._expected_token(TokenType.MISC_IDENT):
            return None

        # Use the identifier value directly (backticks already stripped by lexer)
        identifier_value = self._current_token.literal
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
            and self._peek_token.type != TokenType.PUNCT_PERIOD
        ):
            self._advance_tokens()

        return let_statement

    def _parse_return_statement(self) -> ReturnStatement | None:
        """Parse a return statement.

        Expects: give back expression or gives back expression

        Returns:
            A ReturnStatement AST node if successful, None if parsing fails.
        """
        assert self._current_token is not None
        return_statement = ReturnStatement(token=self._current_token)

        # TODO: Finish when we know how to parse expressions
        # For now, consume tokens until EOF or next statement keyword
        assert self._current_token is not None
        while self._current_token.type not in [TokenType.MISC_EOF, TokenType.PUNCT_PERIOD]:
            self._advance_tokens()
            assert self._current_token is not None

        return return_statement

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
        elif self._current_token.type == TokenType.KW_RETURN:
            return self._parse_return_statement()
        else:
            return None

    @staticmethod
    def _register_infix_funcs() -> InfixParseFuncs:
        """Register infix parsing functions for each token type.

        Infix parsing functions handle expressions where an operator appears
        between operands (e.g., "1 + 2", "a * b"). Each function takes the
        left-hand expression as an argument and returns the complete expression.

        The parser uses these functions when it encounters a token in the middle
        of an expression. For example, when parsing "1 + 2", after parsing "1",
        the parser sees "+" and calls the registered infix function for PLUS,
        passing "1" as the left operand.

        Returns:
            Dictionary mapping TokenType to InfixParseFunc callbacks.
            Each callback signature: (left: Expression) -> Optional[Expression]

        Example:
            When implemented, might look like:
            return {
                TokenType.OP_PLUS: self._parse_infix_expression,
                TokenType.OP_MINUS: self._parse_infix_expression,
                TokenType.OP_MULTIPLY: self._parse_infix_expression,
                TokenType.DELIM_LPAREN: self._parse_call_expression,
            }
        """
        return {}

    @staticmethod
    def _register_prefix_funcs() -> PrefixParseFuncs:
        """Register prefix parsing functions for each token type.

        Prefix parsing functions handle expressions that start with a specific
        token type. This includes literals (numbers, strings), identifiers,
        prefix operators (e.g., "-5", "not true"), and grouped expressions
        (parentheses).

        The parser calls these functions when it encounters a token at the
        beginning of an expression. For example, when parsing "-5", the parser
        sees "-" and calls the registered prefix function for MINUS.

        Returns:
            Dictionary mapping TokenType to PrefixParseFunc callbacks.
            Each callback signature: () -> Optional[Expression]

        Example:
            When implemented, might look like:
            return {
                TokenType.LIT_IDENTIFIER: self._parse_identifier,
                TokenType.LIT_NUMBER: self._parse_number_literal,
                TokenType.LIT_STRING: self._parse_string_literal,
                TokenType.OP_MINUS: self._parse_prefix_expression,
                TokenType.KW_NOT: self._parse_prefix_expression,
                TokenType.DELIM_LPAREN: self._parse_grouped_expression,
            }
        """
        return {}

    @staticmethod
    def _register_postfix_funcs() -> PostfixParseFuncs:
        """Register postfix parsing functions for each token type.

        Postfix parsing functions handle expressions where an operator appears
        after the operand (e.g., "i++", "factorial!", array indexing "arr[0]").
        Each function takes the left-hand expression as an argument and returns
        the complete expression.

        The parser uses these functions when it encounters a token after a
        complete expression. For example, when parsing "i++", after parsing "i",
        the parser sees "++" and calls the registered postfix function for
        INCREMENT, passing "i" as the operand.

        Returns:
            Dictionary mapping TokenType to PostfixParseFunc callbacks.
            Each callback signature: (left: Expression) -> Optional[Expression]

        Example:
            When implemented, might look like:
            return {
                TokenType.OP_INCREMENT: self._parse_postfix_expression,
                TokenType.OP_DECREMENT: self._parse_postfix_expression,
                TokenType.OP_FACTORIAL: self._parse_postfix_expression,
                TokenType.DELIM_LBRACKET: self._parse_index_expression,
                TokenType.PUNCT_QUESTION: self._parse_ternary_expression,
            }
        """
        return {}
