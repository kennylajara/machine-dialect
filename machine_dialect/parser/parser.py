from collections.abc import Callable

from machine_dialect.ast import (
    ActionStatement,
    Arguments,
    BlockStatement,
    BooleanLiteral,
    CallStatement,
    ConditionalExpression,
    EmptyLiteral,
    ErrorExpression,
    ErrorStatement,
    Expression,
    ExpressionStatement,
    FloatLiteral,
    Identifier,
    IfStatement,
    InfixExpression,
    IntegerLiteral,
    InteractionStatement,
    Parameter,
    PrefixExpression,
    Program,
    ReturnStatement,
    SayStatement,
    SetStatement,
    Statement,
    StringLiteral,
    URLLiteral,
)
from machine_dialect.errors.exceptions import MDBaseException, MDNameError, MDSyntaxError
from machine_dialect.errors.messages import (
    EMPTY_ELSE_BLOCK,
    EMPTY_IF_CONSEQUENCE,
    EXPECTED_DETAILS_CLOSE,
    EXPECTED_EXPRESSION,
    EXPECTED_FUNCTION_NAME,
    EXPECTED_IDENTIFIER_FOR_NAMED_ARG,
    INVALID_ARGUMENT_VALUE,
    INVALID_FLOAT_LITERAL,
    INVALID_INTEGER_LITERAL,
    NAME_UNDEFINED,
    NO_PARSE_FUNCTION,
    POSITIONAL_AFTER_NAMED,
    UNEXPECTED_BLOCK_DEPTH,
    UNEXPECTED_TOKEN,
    UNEXPECTED_TOKEN_AT_START,
)
from machine_dialect.lexer import Lexer
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.parser import Precedence
from machine_dialect.parser.protocols import (
    InfixParseFuncs,
    PostfixParseFuncs,
    PrefixParseFuncs,
)
from machine_dialect.parser.token_buffer import TokenBuffer

PRECEDENCES: dict[TokenType, Precedence] = {
    # Ternary conditional
    TokenType.KW_IF: Precedence.TERNARY,
    # Logical operators
    TokenType.KW_OR: Precedence.LOGICAL_OR,
    TokenType.KW_AND: Precedence.LOGICAL_AND,
    # Comparison operators
    TokenType.OP_EQ: Precedence.REL_SYM_COMP,
    TokenType.OP_NOT_EQ: Precedence.REL_SYM_COMP,
    TokenType.OP_STRICT_EQ: Precedence.REL_SYM_COMP,
    TokenType.OP_STRICT_NOT_EQ: Precedence.REL_SYM_COMP,
    TokenType.OP_LT: Precedence.REL_ASYM_COMP,
    TokenType.OP_GT: Precedence.REL_ASYM_COMP,
    TokenType.OP_LTE: Precedence.REL_ASYM_COMP,
    TokenType.OP_GTE: Precedence.REL_ASYM_COMP,
    # Arithmetic operators
    TokenType.OP_PLUS: Precedence.MATH_ADD_SUB,
    TokenType.OP_MINUS: Precedence.MATH_ADD_SUB,
    TokenType.OP_STAR: Precedence.MATH_PROD_DIV_MOD,
    TokenType.OP_DIVISION: Precedence.MATH_PROD_DIV_MOD,
}


class Parser:
    """Parser for Machine Dialect language.

    Transforms source code into an Abstract Syntax Tree (AST) by first
    tokenizing it with the lexer and then parsing the tokens.
    Also collects any lexical errors from the tokenizer.

    Attributes:
        errors (list[MDBaseException]): List of errors encountered during parsing,
            including lexical errors from the tokenizer.
    """

    def __init__(self) -> None:
        """Initialize the parser."""
        self._current_token: Token | None = None
        self._peek_token: Token | None = None
        self._token_buffer: TokenBuffer | None = None
        self._errors: list[MDBaseException] = []
        self._panic_count = 0  # Track panic-mode recoveries
        self._block_depth = 0  # Track if we're inside block statements

        self._prefix_parse_funcs: PrefixParseFuncs = self._register_prefix_funcs()
        self._infix_parse_funcs: InfixParseFuncs = self._register_infix_funcs()
        self._postfix_parse_funcs: PostfixParseFuncs = self._register_postfix_funcs()

    def parse(self, source: str) -> Program:
        """Parse the source code into an AST.

        Args:
            source: The source code to parse.

        Returns:
            The root Program node of the AST.

        Note:
            Any errors encountered during parsing are added to the
            errors attribute. The parser attempts to continue parsing
            even after encountering errors using panic-mode recovery.
        """
        # Reset parser state for new parse
        self._reset_state()

        # Create lexer and token buffer for streaming
        lexer = Lexer(source)
        self._token_buffer = TokenBuffer(lexer)

        # Initialize token pointers
        self._advance_tokens()
        self._advance_tokens()

        # Parse the program
        program: Program = Program(statements=[])

        assert self._current_token is not None
        while self._current_token.type != TokenType.MISC_EOF and self._panic_count < 20:
            # Skip standalone periods
            if self._current_token.type == TokenType.PUNCT_PERIOD:
                self._advance_tokens()
                continue

            statement = self._parse_statement()
            program.statements.append(statement)

            # Check if we need to advance
            # If statements with blocks leave the cursor at the next statement
            # Other statements leave the cursor at or after their terminator (period)
            # We should only advance if we're not already at a statement start
            stmt_token_types = list(self._register_statement_functions())
            stmt_token_types.append(TokenType.MISC_EOF)
            if self._current_token and self._current_token.type not in stmt_token_types:
                self._advance_tokens()

        return program

    def _reset_state(self) -> None:
        """Reset the parser state for a new parse."""
        self._current_token = None
        self._peek_token = None
        self._token_buffer = None
        self._errors = []
        self._panic_count = 0
        self._block_depth = 0

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
        into peek token from the buffer. Automatically skips MISC_STOPWORD tokens.
        """
        self._current_token = self._peek_token

        # Skip any stopword tokens
        if self._token_buffer:
            while True:
                self._peek_token = self._token_buffer.current()
                if self._peek_token is None:
                    self._peek_token = Token(TokenType.MISC_EOF, "", line=1, position=1)
                    break

                self._token_buffer.advance()

                # If it's not a stopword, we're done
                if self._peek_token.type != TokenType.MISC_STOPWORD:
                    break
        else:
            # No buffer available
            self._peek_token = Token(TokenType.MISC_EOF, "", line=1, position=1)

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

        Creates and adds an error to the errors list when the parser
        encounters a token different from what was expected. If we expected
        an identifier and got MISC_ILLEGAL, it's a name error. Otherwise,
        it's a syntax error.

        Args:
            token_type: The token type that was expected but not found.
        """
        assert self._peek_token is not None

        # If we expected an identifier and got an illegal token, it's a name error
        error: MDBaseException
        if token_type == TokenType.MISC_IDENT and self._peek_token.type == TokenType.MISC_ILLEGAL:
            error = MDNameError(
                message=NAME_UNDEFINED,
                name=self._peek_token.literal,
                line=self._peek_token.line,
                column=self._peek_token.position,
            )
        else:
            error = MDSyntaxError(
                message=UNEXPECTED_TOKEN,
                token_literal=self._peek_token.literal,
                expected_token_type=token_type,
                received_token_type=self._peek_token.type,
                line=self._peek_token.line,
                column=self._peek_token.position,
            )
        self.errors.append(error)

    def _current_precedence(self) -> Precedence:
        """Get the precedence of the current token.

        Returns:
            The precedence level of the current token, or LOWEST if not found.
        """
        assert self._current_token is not None
        return PRECEDENCES.get(self._current_token.type, Precedence.LOWEST)

    def _peek_precedence(self) -> Precedence:
        """Get the precedence of the peek token.

        Returns:
            The precedence level of the peek token, or LOWEST if not found.
        """
        assert self._peek_token is not None
        return PRECEDENCES.get(self._peek_token.type, Precedence.LOWEST)

    def _panic_mode_recovery(self) -> list[Token]:
        """Enter panic mode: skip tokens until finding a period.

        This allows the parser to recover from errors and continue
        parsing the rest of the input to find more errors. Collects
        all skipped tokens to preserve them in the error statement.

        Returns:
            List of tokens that were skipped during panic recovery.
        """
        self._panic_count += 1
        skipped_tokens = []

        # Skip tokens until the next token is a period or EOF
        while self._peek_token is not None and self._peek_token.type not in (
            TokenType.PUNCT_PERIOD,
            TokenType.MISC_EOF,
        ):
            self._advance_tokens()
            if self._current_token is not None:
                skipped_tokens.append(self._current_token)

        return skipped_tokens

    def _parse_expression(self, precedence: Precedence = Precedence.LOWEST) -> Expression:
        """Parse an expression with a given precedence level.

        Args:
            precedence: The minimum precedence level to parse. Defaults to LOWEST.

        Returns:
            An Expression AST node if successful, ErrorExpression if parsing fails, None if no expression.
        """
        assert self._current_token is not None

        # Handle illegal tokens
        if self._current_token.type == TokenType.MISC_ILLEGAL:
            error_token = self._current_token
            name_error = MDNameError(
                message=NAME_UNDEFINED,
                name=self._current_token.literal,
                line=self._current_token.line,
                column=self._current_token.position,
            )
            self.errors.append(name_error)
            # Advance past the illegal token so we can continue parsing
            self._advance_tokens()
            # Return an ErrorExpression to preserve AST structure
            return ErrorExpression(token=error_token, message=f"Name '{error_token.literal}' is not defined")

        if self._current_token.type not in self._prefix_parse_funcs:
            # Check if it's an infix operator at the start
            error_token = self._current_token
            # Determine which error template to use and its parameters
            if self._current_token.type in self._infix_parse_funcs:
                syntax_error = MDSyntaxError(
                    message=UNEXPECTED_TOKEN_AT_START,
                    token=self._current_token.literal,
                    line=self._current_token.line,
                    column=self._current_token.position,
                )
                error_message = UNEXPECTED_TOKEN_AT_START.substitute(token=self._current_token.literal)
            elif self._current_token.type == TokenType.MISC_EOF:
                syntax_error = MDSyntaxError(
                    message=EXPECTED_EXPRESSION,
                    got="<end-of-file>",
                    line=self._current_token.line,
                    column=self._current_token.position,
                )
                error_message = EXPECTED_EXPRESSION.substitute(got="<end-of-file>")
            else:
                syntax_error = MDSyntaxError(
                    message=NO_PARSE_FUNCTION,
                    literal=self._current_token.literal,
                    line=self._current_token.line,
                    column=self._current_token.position,
                )
                error_message = NO_PARSE_FUNCTION.substitute(literal=self._current_token.literal)

            self.errors.append(syntax_error)
            # Advance past the problematic token so we can continue parsing
            if self._current_token.type != TokenType.MISC_EOF:
                self._advance_tokens()
            # Return an ErrorExpression to preserve AST structure
            return ErrorExpression(token=error_token, message=error_message)

        prefix_parse_fn = self._prefix_parse_funcs[self._current_token.type]

        left_expression = prefix_parse_fn()

        # Handle infix operators
        assert self._peek_token is not None
        while self._peek_token.type != TokenType.PUNCT_PERIOD and precedence < self._peek_precedence():
            if self._peek_token.type not in self._infix_parse_funcs:
                return left_expression

            self._advance_tokens()

            assert self._current_token is not None
            infix_parse_fn = self._infix_parse_funcs[self._current_token.type]
            left_expression = infix_parse_fn(left_expression)

            assert self._peek_token is not None

        return left_expression

    def _parse_expression_statement(self) -> ExpressionStatement:
        assert self._current_token is not None

        expression = self._parse_expression()

        expression_statement = ExpressionStatement(
            token=self._current_token,
            expression=expression,
        )

        # Require trailing period if not at EOF
        assert self._peek_token is not None
        if self._peek_token.type != TokenType.MISC_EOF:
            self._expected_token(TokenType.PUNCT_PERIOD)

        return expression_statement

    def _parse_float_literal(self) -> FloatLiteral | ErrorExpression:
        assert self._current_token is not None

        # The lexer has already validated and cleaned the literal
        # so we can directly parse it as a float
        try:
            value = float(self._current_token.literal)
        except ValueError:
            # This shouldn't happen if the lexer is working correctly
            error = MDSyntaxError(
                message=INVALID_FLOAT_LITERAL,
                literal=self._current_token.literal,
                line=self._current_token.line,
                column=self._current_token.position,
            )
            self.errors.append(error)
            error_message = INVALID_FLOAT_LITERAL.substitute(literal=self._current_token.literal)
            return ErrorExpression(token=self._current_token, message=error_message)

        return FloatLiteral(
            token=self._current_token,
            value=value,
        )

    def _parse_identifier(self) -> Identifier:
        assert self._current_token is not None

        return Identifier(
            token=self._current_token,
            value=self._current_token.literal,
        )

    def _parse_integer_literal(self) -> IntegerLiteral | ErrorExpression:
        assert self._current_token is not None

        # The lexer has already validated and cleaned the literal
        # so we can directly parse it as an integer
        try:
            value = int(self._current_token.literal)
        except ValueError:
            # This shouldn't happen if the lexer is working correctly
            error = MDSyntaxError(
                message=INVALID_INTEGER_LITERAL,
                literal=self._current_token.literal,
                line=self._current_token.line,
                column=self._current_token.position,
            )
            self.errors.append(error)
            error_message = INVALID_INTEGER_LITERAL.substitute(literal=self._current_token.literal)
            return ErrorExpression(token=self._current_token, message=error_message)

        return IntegerLiteral(
            token=self._current_token,
            value=value,
        )

    def _parse_boolean_literal(self) -> BooleanLiteral:
        """Parse a boolean literal.

        Returns:
            A BooleanLiteral AST node.

        Note:
            The lexer has already validated and provided the canonical
            representation of the boolean literal ("True" or "False").
        """
        assert self._current_token is not None

        # Determine the boolean value based on the token type
        value = self._current_token.type == TokenType.LIT_TRUE

        return BooleanLiteral(
            token=self._current_token,
            value=value,
        )

    def _parse_empty_literal(self) -> EmptyLiteral:
        """Parse an empty literal.

        Returns:
            An EmptyLiteral AST node.
        """
        assert self._current_token is not None

        return EmptyLiteral(
            token=self._current_token,
        )

    def _parse_string_literal(self) -> StringLiteral:
        """Parse a string literal.

        Returns:
            A StringLiteral AST node.
        """
        assert self._current_token is not None

        return StringLiteral(
            token=self._current_token,
            value=self._current_token.literal,
        )

    def _parse_url_literal(self) -> URLLiteral:
        """Parse a URL literal.

        Returns:
            A URLLiteral AST node.
        """
        assert self._current_token is not None

        return URLLiteral(
            token=self._current_token,
            value=self._current_token.literal,
        )

    def _parse_prefix_expression(self) -> PrefixExpression:
        """Parse a prefix expression.

        Prefix expressions consist of a prefix operator followed by an expression.
        Examples: -42, not True, --5, not not False

        Returns:
            A PrefixExpression AST node if successful, None if parsing fails.
        """
        assert self._current_token is not None

        # Create the prefix expression with the operator
        expression = PrefixExpression(
            token=self._current_token,
            operator=self._current_token.literal,
        )

        # Advance past the operator
        self._advance_tokens()

        # Parse the right-hand expression with appropriate precedence
        # All unary operators (including 'not') have high precedence
        expression.right = self._parse_expression(Precedence.UNARY_SIMPLIFIED)

        return expression

    def _parse_infix_expression(self, left: Expression) -> InfixExpression:
        """Parse an infix expression.

        Infix expressions consist of a left expression, an infix operator, and a
        right expression. Examples: 5 + 3, x == y, a and b.

        Args:
            left: The left-hand expression that was already parsed.

        Returns:
            An InfixExpression AST node.
        """
        assert self._current_token is not None

        # Map token type to operator string
        operator_map = {
            TokenType.OP_PLUS: "+",
            TokenType.OP_MINUS: "-",
            TokenType.OP_STAR: "*",
            TokenType.OP_DIVISION: "/",
            TokenType.OP_EQ: "equals",
            TokenType.OP_NOT_EQ: "is not",
            TokenType.OP_STRICT_EQ: "is strictly equal to",
            TokenType.OP_STRICT_NOT_EQ: "is not strictly equal to",
            TokenType.OP_LT: "<",
            TokenType.OP_GT: ">",
            TokenType.OP_LTE: "<=",
            TokenType.OP_GTE: ">=",
            TokenType.KW_AND: "and",
            TokenType.KW_OR: "or",
        }

        # Get the operator string
        operator = operator_map.get(self._current_token.type, self._current_token.literal)

        # Create the infix expression with the operator and left operand
        expression = InfixExpression(
            token=self._current_token,
            operator=operator,
            left=left,
        )

        # Get the precedence of this operator
        precedence = self._current_precedence()

        # Advance past the operator
        self._advance_tokens()

        # Parse the right-hand expression
        expression.right = self._parse_expression(precedence)

        return expression

    def _parse_grouped_expression(self) -> Expression:
        """Parse a grouped expression (expression in parentheses).

        Grouped expressions are expressions wrapped in parentheses, which
        can be used to override operator precedence.

        Returns:
            The expression inside the parentheses, or None if parsing fails.
        """
        # Advance past the opening parenthesis
        self._advance_tokens()

        # Parse the inner expression
        expression = self._parse_expression(Precedence.LOWEST)

        # Expect closing parenthesis
        if not self._expected_token(TokenType.DELIM_RPAREN):
            # Return error expression for unclosed parenthesis
            assert self._current_token is not None
            return ErrorExpression(token=self._current_token, message="Expected closing parenthesis")

        return expression

    def _parse_conditional_expression(self, consequence: Expression) -> ConditionalExpression:
        """Parse a conditional (ternary) expression.

        Formats supported:
        - consequence if condition, else alternative
        - consequence if condition, otherwise alternative
        - consequence when condition, else alternative
        - consequence when condition, otherwise alternative
        - consequence if condition; else alternative
        - consequence if condition; otherwise alternative
        - consequence when condition; else alternative
        - consequence when condition; otherwise alternative

        Args:
            consequence: The expression to return if condition is true.

        Returns:
            A ConditionalExpression node.
        """
        assert self._current_token is not None
        # Create the conditional expression with the consequence
        expression = ConditionalExpression(token=self._current_token, consequence=consequence)

        # Move past 'if' or 'when'
        self._advance_tokens()

        # Parse the condition with TERNARY precedence to stop at comma
        expression.condition = self._parse_expression(Precedence.TERNARY)

        # After parsing the condition, we need to advance to the next token
        # _parse_expression leaves us at the last token of the parsed expression
        self._advance_tokens()

        # DEBUG: Print current state
        # print(f"After parsing condition and advancing: current={self._current_token}, peek={self._peek_token}")

        # Check for comma or semicolon before 'else'/'otherwise'
        if self._current_token and self._current_token.type in (TokenType.PUNCT_COMMA, TokenType.PUNCT_SEMICOLON):
            self._advance_tokens()  # Move past comma/semicolon
            # print(f"After advancing past comma/semicolon: current={self._current_token}, peek={self._peek_token}")

        # Expect 'else' or 'otherwise' (both map to KW_ELSE)
        if not self._current_token or self._current_token.type != TokenType.KW_ELSE:
            return expression  # Return incomplete expression if no else clause

        # Move past 'else' or 'otherwise'
        self._advance_tokens()

        # Parse the alternative expression
        expression.alternative = self._parse_expression(Precedence.LOWEST)

        return expression

    def _parse_let_statement(self) -> SetStatement | ErrorStatement:
        """Parse a Set statement.

        Expects: Set `identifier` to expression

        Returns:
            A SetStatement AST node if successful, ErrorStatement if parsing fails.
        """
        assert self._current_token is not None
        statement_token = self._current_token  # Save the 'Set' token
        let_statement = SetStatement(token=statement_token)

        # Expect identifier (which may have come from backticks)
        if not self._expected_token(TokenType.MISC_IDENT):
            skipped = self._panic_mode_recovery()
            return ErrorStatement(
                token=statement_token, skipped_tokens=skipped, message="Expected identifier after 'Set'"
            )

        # Use the identifier value directly (backticks already stripped by lexer)
        let_statement.name = self._parse_identifier()

        # Expect "to" keyword
        if not self._expected_token(TokenType.KW_TO):
            skipped = self._panic_mode_recovery()
            return ErrorStatement(token=statement_token, skipped_tokens=skipped, message="Expected 'to' keyword")

        # Advance to the expression
        self._advance_tokens()

        # Parse the value expression
        let_statement.value = self._parse_expression()

        # If the expression failed, skip to synchronization point
        if isinstance(let_statement.value, ErrorExpression):
            # Skip remaining tokens until we're at a period or EOF
            while self._current_token is not None and self._current_token.type not in (
                TokenType.PUNCT_PERIOD,
                TokenType.MISC_EOF,
            ):
                self._advance_tokens()

        # Require trailing period if not at EOF
        # But if we're already at a period (after error recovery), don't expect another
        assert self._peek_token is not None
        if self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
            # Already at period, no need to expect one
            pass
        elif self._peek_token.type != TokenType.MISC_EOF:
            self._expected_token(TokenType.PUNCT_PERIOD)

        return let_statement

    def _parse_return_statement(self) -> ReturnStatement:
        """Parse a return statement.

        Expects: give back expression or gives back expression

        Returns:
            A ReturnStatement AST node.
        """
        assert self._current_token is not None
        return_statement = ReturnStatement(token=self._current_token)

        # Advance past "give back" or "gives back"
        self._advance_tokens()

        # Parse the return value expression
        return_statement.return_value = self._parse_expression()

        # Require trailing period if not at EOF
        # But if we're already at a period (after error recovery), don't expect another
        assert self._peek_token is not None
        if self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
            # Already at period, no need to expect one
            pass
        elif self._peek_token.type != TokenType.MISC_EOF:
            self._expected_token(TokenType.PUNCT_PERIOD)

        return return_statement

    def _parse_say_statement(self) -> SayStatement:
        """Parse a Say statement.

        Syntax: Say <expression>.

        Returns:
            A SayStatement AST node.
        """
        assert self._current_token is not None
        assert self._current_token.type == TokenType.KW_SAY

        statement_token = self._current_token

        # Move past 'Say'
        self._advance_tokens()

        # Parse the expression to output
        expression = self._parse_expression(Precedence.LOWEST)

        # Create the Say statement
        say_statement = SayStatement(statement_token, expression)

        # Expect a period at the end
        if self._peek_token and self._peek_token.type == TokenType.PUNCT_PERIOD:
            self._advance_tokens()
        # But if we're already at a period (after error recovery), don't expect another
        elif self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:  # type: ignore[comparison-overlap]
            self._expected_token(TokenType.PUNCT_PERIOD)

        return say_statement

    def _parse_call_statement(self) -> CallStatement:
        """Parse a Call statement.

        Syntax: call <function> [with <arguments>].

        Returns:
            A CallStatement AST node.
        """
        assert self._current_token is not None
        assert self._current_token.type == TokenType.KW_CALL

        statement_token = self._current_token

        # Move past 'call'
        self._advance_tokens()

        # Parse the function name (must be an identifier in backticks)
        if self._current_token and self._current_token.type == TokenType.MISC_IDENT:  # type: ignore[comparison-overlap]
            function_name = Identifier(self._current_token, self._current_token.literal)
            self._advance_tokens()
        else:
            # Record error for missing or invalid function name
            error_token = self._current_token or Token(TokenType.MISC_EOF, "", 0, 0)
            self.errors.append(
                MDSyntaxError(
                    message=EXPECTED_FUNCTION_NAME,
                    token_type=str(error_token.type),
                    line=error_token.line,
                    column=error_token.position,
                )
            )
            function_name = None

        # Check for 'with' keyword for arguments
        arguments: Arguments | None = None
        if self._current_token and self._current_token.type == TokenType.KW_WITH:  # type: ignore[comparison-overlap]
            # Save 'with' token for Arguments node
            with_token = self._current_token
            self._advance_tokens()  # Move past 'with'

            # Parse arguments
            arguments = self._parse_arguments_with_token(with_token)

        # Create the Call statement
        call_statement = CallStatement(statement_token, function_name, arguments)

        # Expect a period at the end
        if self._peek_token and self._peek_token.type == TokenType.PUNCT_PERIOD:
            self._advance_tokens()
        # But if we're already at a period (after error recovery), don't expect another
        elif self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:  # type: ignore[comparison-overlap]
            self._expected_token(TokenType.PUNCT_PERIOD)

        return call_statement

    def _parse_argument_value(self) -> Expression | None:
        """Parse a single argument value (literal or identifier).

        Returns:
            The parsed expression or None if invalid.
        """
        if not self._current_token:
            return None

        token = self._current_token

        # Parse based on token type
        value: Expression | None = None
        if token.type == TokenType.MISC_IDENT:
            # Identifier
            value = Identifier(token, token.literal)
            self._advance_tokens()
            return value
        elif token.type == TokenType.LIT_INT:
            # Integer literal
            int_value = self._parse_integer_literal()
            self._advance_tokens()
            return int_value
        elif token.type == TokenType.LIT_FLOAT:
            # Float literal
            float_value = self._parse_float_literal()
            self._advance_tokens()
            return float_value
        elif token.type == TokenType.LIT_TEXT:
            # String literal
            str_value = self._parse_string_literal()
            self._advance_tokens()
            return str_value
        elif token.type == TokenType.LIT_URL:
            # URL literal
            url_value = self._parse_url_literal()
            self._advance_tokens()
            return url_value
        elif token.type in (TokenType.LIT_TRUE, TokenType.LIT_FALSE):
            # Boolean literal
            bool_value = self._parse_boolean_literal()
            self._advance_tokens()
            return bool_value
        elif token.type == TokenType.KW_EMPTY:
            # Empty literal
            empty_value = self._parse_empty_literal()
            self._advance_tokens()
            return empty_value
        else:
            # Unknown token type for argument
            self.errors.append(
                MDSyntaxError(
                    message=INVALID_ARGUMENT_VALUE,
                    literal=token.literal,
                    line=token.line,
                    column=token.position,
                )
            )
            self._advance_tokens()  # Skip the invalid token
            return None

    def _parse_arguments_with_token(self, with_token: Token) -> Arguments:
        """Parse function call arguments.

        Arguments can be:
        - Positional: _value1_, _value2_
        - Named: `param1`: _value1_, `param2`: _value2_
        - Mixed: _value1_, `param`: _value2_ (positional must come first)

        Returns:
            An Arguments AST node.
        """
        # Create Arguments node with the 'with' token
        arguments = Arguments(with_token)
        has_named = False  # Track if we've seen named arguments

        while self._current_token and self._current_token.type not in (
            TokenType.PUNCT_PERIOD,
            TokenType.MISC_EOF,
            TokenType.DELIM_RPAREN,
        ):
            # Check if this is a named argument (next token is colon after an identifier/string)
            if self._peek_token and self._peek_token.type == TokenType.PUNCT_COLON:
                # This is a named argument
                has_named = True

                # Parse the parameter name (should be an identifier in backticks)
                if self._current_token and self._current_token.type == TokenType.MISC_IDENT:
                    name_expr = Identifier(self._current_token, self._current_token.literal)
                    self._advance_tokens()
                else:
                    name_expr = None

                # Verify it's an identifier
                if not isinstance(name_expr, Identifier):
                    # Record error for invalid named argument
                    error_token = self._current_token or Token(TokenType.MISC_EOF, "", 0, 0)
                    self.errors.append(
                        MDSyntaxError(
                            message=EXPECTED_IDENTIFIER_FOR_NAMED_ARG,
                            type_name=type(name_expr).__name__ if name_expr else "None",
                            line=error_token.line,
                            column=error_token.position,
                        )
                    )
                    # Try to recover by skipping to next comma or period
                    self._panic_mode_recovery()
                    break

                # Skip the colon
                if self._current_token and self._current_token.type == TokenType.PUNCT_COLON:
                    self._advance_tokens()

                # Parse the value
                value = self._parse_argument_value()

                # Add to named arguments if both name and value are valid
                if name_expr and value:
                    arguments.named.append((name_expr, value))
            else:
                # This is a positional argument
                if has_named:
                    # Error: positional argument after named argument
                    error_token = self._current_token or Token(TokenType.MISC_EOF, "", 0, 0)
                    self.errors.append(
                        MDSyntaxError(
                            message=POSITIONAL_AFTER_NAMED,
                            line=error_token.line,
                            column=error_token.position,
                        )
                    )
                    # Try to recover by skipping to next comma or period
                    self._panic_mode_recovery()
                    break

                # Parse the value
                value = self._parse_argument_value()

                # Add to positional arguments if valid
                if value:
                    arguments.positional.append(value)

            # Check for comma separator
            if self._current_token and self._current_token.type == TokenType.PUNCT_COMMA:
                self._advance_tokens()  # Skip comma
            elif self._current_token and self._current_token.type not in (
                TokenType.PUNCT_PERIOD,
                TokenType.MISC_EOF,
            ):
                # No comma but not at the end either - missing comma error
                error_token = self._current_token
                self.errors.append(
                    MDSyntaxError(
                        message=UNEXPECTED_TOKEN,
                        token_literal=error_token.literal,
                        expected_token_type=TokenType.PUNCT_COMMA,
                        received_token_type=error_token.type,
                        line=error_token.line,
                        column=error_token.position,
                    )
                )
                # Try to recover by continuing to parse the next argument or ending
                # Check if the next token looks like it could be an argument
                if self._current_token.type in (
                    TokenType.LIT_INT,
                    TokenType.LIT_FLOAT,
                    TokenType.LIT_TEXT,
                    TokenType.LIT_URL,
                    TokenType.LIT_TRUE,
                    TokenType.LIT_FALSE,
                    TokenType.MISC_IDENT,
                    TokenType.KW_EMPTY,
                ):
                    # Looks like another argument, continue parsing
                    continue
                else:
                    # Doesn't look like an argument, stop parsing arguments
                    break

        return arguments

    def _parse_if_statement(self) -> IfStatement:
        """Parse an if statement with block statements.

        Expects: if/when/whenever <condition> [then]: <block> [else/otherwise: <block>]

        Returns:
            An IfStatement AST node.
        """
        assert self._current_token is not None
        if_statement = IfStatement(token=self._current_token)

        # Advance past 'if', 'when', or 'whenever'
        self._advance_tokens()

        # Parse the condition expression
        if_statement.condition = self._parse_expression(Precedence.LOWEST)

        # Check for optional 'then' keyword
        if self._peek_token and self._peek_token.type == TokenType.KW_THEN:
            self._advance_tokens()  # Move to 'then'

        # Expect colon
        if not self._expected_token(TokenType.PUNCT_COLON):
            # Create error statement if no colon
            return IfStatement(token=if_statement.token, condition=if_statement.condition)

        # Parse the consequence block
        # If we're inside a block, nested if statements should have deeper blocks
        expected_depth = self._block_depth + 1
        if_statement.consequence = self._parse_block_statement(expected_depth)

        # Check if the consequence block is empty - this is an error
        if not if_statement.consequence or len(if_statement.consequence.statements) == 0:
            self._errors.append(
                MDSyntaxError(
                    line=if_statement.token.line,
                    column=if_statement.token.position,
                    message=EMPTY_IF_CONSEQUENCE,
                )
            )

        # Check for else/otherwise clause
        if self._current_token and self._current_token.type == TokenType.KW_ELSE:
            # Check if next token is colon
            if self._peek_token and self._peek_token.type == TokenType.PUNCT_COLON:
                self._advance_tokens()  # Move past else to colon
                self._advance_tokens()  # Move past colon
            else:
                # No colon after else, return without alternative
                return if_statement

            # Parse the alternative block
            if_statement.alternative = self._parse_block_statement(expected_depth)

            # Check if the alternative block is empty - this is also an error
            if not if_statement.alternative or len(if_statement.alternative.statements) == 0:
                self._errors.append(
                    MDSyntaxError(
                        line=self._current_token.line if self._current_token else if_statement.token.line,
                        column=self._current_token.position if self._current_token else if_statement.token.position,
                        message=EMPTY_ELSE_BLOCK,
                    )
                )
        elif self._block_depth == 0:
            # No else clause and we're at top level (not inside a block)
            # Check if we're at a '>' token that was part of the block we just parsed
            # If so, don't rewind as it would re-parse block content
            if (
                self._current_token
                and self._current_token.type == TokenType.OP_GT
                and if_statement.consequence
                and if_statement.consequence.depth > 0
            ):
                # We're at a '>' that was part of the block, don't rewind
                pass
            elif self._current_token and self._current_token.type != TokenType.MISC_EOF:
                # With streaming, we can't back up tokens
                # The block parsing should have left us in the right position
                pass

        return if_statement

    def _parse_action_or_interaction(self) -> ActionStatement | InteractionStatement | ErrorStatement:
        """Parse an Action or Interaction statement.

        Expected format:
        ### **Action**: `name`
        or
        ### **Interaction**: `name`

        <details>
        <summary>Description</summary>
        > statements
        </details>

        Returns:
            ActionStatement or InteractionStatement node, or ErrorStatement if parsing fails.
        """
        assert self._current_token is not None
        assert self._current_token.type == TokenType.PUNCT_HASH_TRIPLE

        # Save the ### token for the statement
        hash_token = self._current_token

        # Move past ###
        self._advance_tokens()

        # Expect **Action** or **Interaction** (wrapped keyword)
        if not self._current_token or self._current_token.type not in (TokenType.KW_ACTION, TokenType.KW_INTERACTION):
            skipped = self._panic_mode_recovery()
            return ErrorStatement(
                token=hash_token, skipped_tokens=skipped, message="Expected **Action** or **Interaction** after ###"
            )

        is_action = self._current_token.type == TokenType.KW_ACTION  # type: ignore[comparison-overlap]
        keyword_token = self._current_token

        # Move past Action/Interaction keyword
        self._advance_tokens()

        # Expect colon - should be at current position
        if not self._current_token or self._current_token.type != TokenType.PUNCT_COLON:  # type: ignore[comparison-overlap]
            skipped = self._panic_mode_recovery()
            return ErrorStatement(
                token=keyword_token, skipped_tokens=skipped, message="Expected ':' after Action/Interaction"
            )

        # Move past colon
        self._advance_tokens()

        # Expect backtick-wrapped name
        if not self._current_token or self._current_token.type != TokenType.MISC_IDENT:
            skipped = self._panic_mode_recovery()
            return ErrorStatement(
                token=keyword_token, skipped_tokens=skipped, message="Expected identifier in backticks for name"
            )

        name = Identifier(self._current_token, self._current_token.literal)
        self._advance_tokens()

        # Now expect <details> tag - should be at current position
        if not self._current_token or self._current_token.type != TokenType.TAG_DETAILS_START:
            skipped = self._panic_mode_recovery()
            return ErrorStatement(token=keyword_token, skipped_tokens=skipped, message="Expected <details> tag")

        # Move past <details>
        self._advance_tokens()

        # Check for <summary> tag and extract description
        description = ""
        if self._current_token and self._current_token.type == TokenType.TAG_SUMMARY_START:
            self._advance_tokens()
            # The next token should be a comment with the description
            if self._current_token and self._current_token.type == TokenType.MISC_COMMENT:
                description = self._current_token.literal
                self._advance_tokens()
            # Expect </summary>
            if self._current_token and self._current_token.type == TokenType.TAG_SUMMARY_END:
                self._advance_tokens()

        # Parse the body (block of statements with > prefix)
        body = self._parse_block_statement()

        # Expect </details> tag - should be at current position after block parsing
        if self._current_token and self._current_token.type == TokenType.TAG_DETAILS_END:
            self._advance_tokens()
        else:
            # If we're not at </details>, something went wrong with block parsing
            # Create an error but don't panic recover
            if self._current_token:
                self._errors.append(
                    MDSyntaxError(
                        line=self._current_token.line,
                        column=self._current_token.position,
                        message=EXPECTED_DETAILS_CLOSE,
                        token_type=self._current_token.type.name,
                    )
                )

        # Check for parameter sections (#### Inputs: and #### Outputs:)
        inputs: list[Parameter] = []
        outputs: list[Parameter] = []

        # Check if we have #### for parameter sections
        if self._current_token and self._current_token.type == TokenType.PUNCT_HASH_QUAD:
            # Parse parameter sections
            inputs, outputs = self._parse_parameter_sections()

        # Create and return the appropriate statement
        if is_action:
            return ActionStatement(
                keyword_token, name, inputs=inputs, outputs=outputs, body=body, description=description
            )
        else:
            return InteractionStatement(
                keyword_token, name, inputs=inputs, outputs=outputs, body=body, description=description
            )

    def _parse_block_statement(self, expected_depth: int = 1) -> BlockStatement:
        """Parse a block of statements marked by '>' symbols.

        A block contains statements that start with one or more '>' symbols.
        The number of '>' symbols determines the depth of the block.
        The block ends when we encounter a statement with fewer '>' symbols
        or a statement without '>' symbols.

        Args:
            expected_depth: The expected depth for this block (number of '>' symbols).
                           Defaults to 1 for top-level blocks.

        Returns:
            A BlockStatement AST node.
        """
        assert self._current_token is not None
        block_token = self._current_token
        block = BlockStatement(token=block_token, depth=expected_depth)

        # Track that we're entering a block
        self._block_depth += 1

        # Tell the token buffer we're in a block
        if self._token_buffer:
            self._token_buffer.set_block_context(True)

        # If we're at a colon, it's the start of a block - advance past it
        if self._current_token.type == TokenType.PUNCT_COLON:
            self._advance_tokens()

        # Parse statements in the block
        while self._current_token and self._current_token.type != TokenType.MISC_EOF:
            # Note: With streaming tokens, we can't save/restore positions

            # Count the depth at the start of the current line
            current_depth = 0
            original_line = self._current_token.line if self._current_token else 0

            # Check if we're at '>' tokens
            if self._current_token.type == TokenType.OP_GT:
                # Count '>' tokens only on the current line
                current_line = self._current_token.line
                while (
                    self._current_token
                    and self._current_token.type == TokenType.OP_GT
                    and self._current_token.line == current_line
                ):
                    current_depth += 1
                    self._advance_tokens()

            # Check depth against expected depth
            if current_depth == 0:
                # No '>' means we've exited the block
                break
            elif current_depth < expected_depth:
                # We've exited the block due to lower depth
                # We've already consumed the '>' tokens while counting depth
                # The parent block needs to handle this line's content
                # But first check if this is an empty line (only '>')
                if self._current_token and self._current_token.line != original_line:
                    # Empty line - we consumed all tokens on the line
                    # Just break and let parent continue from next line
                    break
                else:
                    # Not empty - there's content after the '>'
                    # With streaming, we can't back up - the tokens are already consumed
                    # This means nested blocks need special handling
                    break
            elif current_depth > expected_depth:
                # Nested block or error - for now treat as error
                self._errors.append(
                    MDSyntaxError(
                        line=self._current_token.line if self._current_token else 0,
                        column=self._current_token.position if self._current_token else 0,
                        message=UNEXPECTED_BLOCK_DEPTH,
                        expected=expected_depth,
                        actual=current_depth,
                    )
                )
                # Skip to next line
                while self._current_token and self._current_token.type not in (
                    TokenType.PUNCT_PERIOD,
                    TokenType.MISC_EOF,
                    TokenType.OP_GT,
                ):
                    self._advance_tokens()
                continue

            # After depth check, check if this was an empty line (just '>' with no content)
            # Empty line is when we counted '>' but are no longer on the same line
            if current_depth > 0 and self._current_token and self._current_token.line != original_line:
                # The line only had '>' markers, skip to next line
                continue

            # Check for tokens that would indicate we've left the block
            if self._current_token and self._current_token.type in (
                TokenType.MISC_EOF,
                TokenType.KW_ELSE,  # 'else' would be outside the block
            ):
                break  # We've exited the block

            # Parse the statement
            statement = self._parse_statement()
            block.statements.append(statement)

            # Skip the period if present
            if self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
                self._advance_tokens()

        # Track that we're exiting a block
        self._block_depth -= 1

        # Tell the token buffer we're no longer in a block
        if self._token_buffer:
            self._token_buffer.set_block_context(self._block_depth > 0)

        return block

    def _parse_statement(self) -> Statement:
        """Parse a single statement.

        Determines the statement type based on the current token and
        delegates to the appropriate parsing method.

        Returns:
            A Statement AST node (may be an ErrorStatement if parsing fails).
        """
        assert self._current_token is not None

        stmt_funcs = self._register_statement_functions()
        if self._current_token.type in stmt_funcs:
            return stmt_funcs[self._current_token.type]()
        else:
            return self._parse_expression_statement()

    def _register_infix_funcs(self) -> InfixParseFuncs:
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
        return {
            # Arithmetic operators
            TokenType.OP_PLUS: self._parse_infix_expression,
            TokenType.OP_MINUS: self._parse_infix_expression,
            TokenType.OP_STAR: self._parse_infix_expression,
            TokenType.OP_DIVISION: self._parse_infix_expression,
            # Comparison operators
            TokenType.OP_EQ: self._parse_infix_expression,
            TokenType.OP_NOT_EQ: self._parse_infix_expression,
            TokenType.OP_STRICT_EQ: self._parse_infix_expression,
            TokenType.OP_STRICT_NOT_EQ: self._parse_infix_expression,
            TokenType.OP_LT: self._parse_infix_expression,
            TokenType.OP_GT: self._parse_infix_expression,
            TokenType.OP_LTE: self._parse_infix_expression,
            TokenType.OP_GTE: self._parse_infix_expression,
            # Logical operators
            TokenType.KW_AND: self._parse_infix_expression,
            TokenType.KW_OR: self._parse_infix_expression,
            # Conditional/ternary expressions
            TokenType.KW_IF: self._parse_conditional_expression,
        }

    def _register_prefix_funcs(self) -> PrefixParseFuncs:
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
                TokenType.LIT_TEXT: self._parse_string_literal,
                TokenType.OP_MINUS: self._parse_prefix_expression,
                TokenType.KW_NOT: self._parse_prefix_expression,
                TokenType.DELIM_LPAREN: self._parse_grouped_expression,
            }
        """
        return {
            TokenType.MISC_IDENT: self._parse_identifier,
            TokenType.LIT_INT: self._parse_integer_literal,
            TokenType.LIT_FLOAT: self._parse_float_literal,
            TokenType.LIT_TEXT: self._parse_string_literal,
            TokenType.LIT_URL: self._parse_url_literal,
            TokenType.LIT_TRUE: self._parse_boolean_literal,
            TokenType.LIT_FALSE: self._parse_boolean_literal,
            TokenType.KW_EMPTY: self._parse_empty_literal,
            TokenType.OP_MINUS: self._parse_prefix_expression,
            TokenType.KW_NEGATION: self._parse_prefix_expression,
            TokenType.DELIM_LPAREN: self._parse_grouped_expression,
        }

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

    def _register_statement_functions(self) -> dict[TokenType, Callable[[], Statement]]:
        """Register statement parsing functions for each token type."""
        return {
            TokenType.KW_SET: self._parse_let_statement,
            TokenType.KW_RETURN: self._parse_return_statement,
            TokenType.KW_IF: self._parse_if_statement,
            TokenType.KW_SAY: self._parse_say_statement,
            TokenType.KW_CALL: self._parse_call_statement,
            TokenType.PUNCT_HASH_TRIPLE: self._parse_action_or_interaction,
        }

    def _parse_parameter_sections(self) -> tuple[list[Parameter], list[Parameter]]:
        """Parse parameter sections (#### Inputs: and #### Outputs:).

        Returns:
            A tuple of (inputs, outputs) lists of parameters.
        """
        inputs: list[Parameter] = []
        outputs: list[Parameter] = []

        while self._current_token and self._current_token.type == TokenType.PUNCT_HASH_QUAD:
            # Move past ####
            self._advance_tokens()

            # Check if it's Inputs or Outputs
            current = self._current_token
            if current:
                if current.type == TokenType.KW_INPUTS:
                    # Move past "Inputs"
                    self._advance_tokens()

                    # Expect colon
                    colon_token = self._current_token
                    if colon_token and colon_token.type == TokenType.PUNCT_COLON:
                        self._advance_tokens()

                        # Parse input parameters (lines starting with -)
                        inputs = self._parse_parameter_list()

                elif current.type == TokenType.KW_OUTPUTS:
                    # Move past "Outputs"
                    self._advance_tokens()

                    # Expect colon
                    colon_token2 = self._current_token
                    if colon_token2 and colon_token2.type == TokenType.PUNCT_COLON:
                        self._advance_tokens()

                        # Parse output parameters
                        outputs = self._parse_parameter_list()

                else:
                    # Not a parameter section, break
                    break

        return inputs, outputs

    def _parse_parameter_list(self) -> list[Parameter]:
        """Parse a list of parameters (lines starting with -).

        Expected format:
        - `name` **as** Type (required)
        - `name` **as** Type (optional, default: value)

        Returns:
            List of Parameter objects.
        """
        parameters: list[Parameter] = []

        while self._current_token and self._current_token.type == TokenType.OP_MINUS:
            # Move past -
            self._advance_tokens()

            # Parse single parameter
            param = self._parse_parameter()
            if param:
                parameters.append(param)

        return parameters

    def _parse_parameter(self) -> Parameter | None:
        """Parse a single parameter.

        Expected format:
        `name` **as** Type (required)
        `name` **as** Type (optional, default: value)

        Returns:
            A Parameter object or None if parsing fails.
        """
        if not self._current_token:
            return None

        # Save starting token for error reporting
        start_token = self._current_token

        # Expect identifier in backticks
        if self._current_token.type != TokenType.MISC_IDENT:
            return None

        name = Identifier(self._current_token, self._current_token.literal)
        self._advance_tokens()

        # Expect "as" keyword
        current = self._current_token
        if not current or current.type != TokenType.KW_AS:
            return None
        self._advance_tokens()

        # Parse type name (could be multi-word like "Whole Number")
        type_name = self._parse_type_name()
        if not type_name:
            return None

        # Default values
        is_required = True
        default_value: Expression | None = None

        # Check for (required) or (optional, default: value)
        paren_token = self._current_token
        if paren_token and paren_token.type == TokenType.DELIM_LPAREN:
            self._advance_tokens()

            status_token = self._current_token
            if status_token:
                if status_token.type == TokenType.KW_OPTIONAL:
                    is_required = False
                    self._advance_tokens()

                    # Check for default value
                    comma_token = self._current_token
                    if comma_token and comma_token.type == TokenType.PUNCT_COMMA:
                        self._advance_tokens()

                        # Expect "default"
                        default_token = self._current_token
                        if default_token and default_token.type == TokenType.KW_DEFAULT:
                            self._advance_tokens()

                            # Expect colon
                            colon_check = self._current_token
                            if colon_check and colon_check.type == TokenType.PUNCT_COLON:
                                self._advance_tokens()

                                # Parse the default value expression
                                default_value = self._parse_expression(Precedence.LOWEST)

                                # After parsing expression, advance past it
                                self._advance_tokens()

                else:
                    is_required = True
                    self._advance_tokens()

            # Expect closing paren
            rparen_token = self._current_token
            if rparen_token and rparen_token.type == TokenType.DELIM_RPAREN:
                self._advance_tokens()

        return Parameter(
            token=start_token,
            name=name,
            type_name=type_name,
            is_required=is_required,
            default_value=default_value,
        )

    def _parse_type_name(self) -> str | None:
        """Parse a type name which could be single or multi-word.

        Examples: "Text", "Number", "Whole Number", "Status"

        Returns:
            The type name as a string or None if not found.
        """
        if not self._current_token:
            return None

        # Check for known type keywords
        type_keywords = {
            TokenType.KW_TEXT: "Text",
            TokenType.KW_NUMBER: "Number",
            TokenType.KW_WHOLE_NUMBER: "Whole Number",
            TokenType.KW_STATUS: "Status",
            TokenType.KW_BOOL: "Boolean",
            TokenType.KW_INT: "Integer",
            TokenType.KW_FLOAT: "Float",
            TokenType.KW_URL: "URL",
            TokenType.KW_DATE: "Date",
            TokenType.KW_DATETIME: "DateTime",
            TokenType.KW_TIME: "Time",
            TokenType.KW_LIST: "List",
        }

        if self._current_token.type in type_keywords:
            type_name = type_keywords[self._current_token.type]
            self._advance_tokens()
            return type_name

        # If it's an identifier, use it as the type name
        if self._current_token.type == TokenType.MISC_IDENT:
            type_name = self._current_token.literal
            self._advance_tokens()
            return type_name

        return None
