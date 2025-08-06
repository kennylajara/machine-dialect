from machine_dialect.ast import (
    BooleanLiteral,
    ConditionalExpression,
    ErrorExpression,
    ErrorStatement,
    Expression,
    ExpressionStatement,
    FloatLiteral,
    Identifier,
    InfixExpression,
    IntegerLiteral,
    PrefixExpression,
    Program,
    ReturnStatement,
    SetStatement,
    Statement,
    StringLiteral,
)
from machine_dialect.errors.exceptions import MDBaseException, MDNameError, MDSyntaxError
from machine_dialect.errors.messages import (
    EXPECTED_EXPRESSION,
    INVALID_FLOAT_LITERAL,
    INVALID_INTEGER_LITERAL,
    NAME_UNDEFINED,
    NO_PARSE_FUNCTION,
    UNEXPECTED_TOKEN,
    UNEXPECTED_TOKEN_AT_START,
)
from machine_dialect.lexer import Lexer, Token, TokenType
from machine_dialect.parser import Precedence
from machine_dialect.parser.protocols import (
    InfixParseFuncs,
    PostfixParseFuncs,
    PrefixParseFuncs,
)

PRECEDENCES: dict[TokenType, Precedence] = {
    # Ternary conditional
    TokenType.KW_IF: Precedence.TERNARY,
    # Logical operators
    TokenType.KW_OR: Precedence.LOGICAL_OR,
    TokenType.KW_AND: Precedence.LOGICAL_AND,
    # Comparison operators
    TokenType.OP_EQ: Precedence.REL_SYM_COMP,
    TokenType.OP_NOT_EQ: Precedence.REL_SYM_COMP,
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

        # Get tokens from the lexer
        self._tokens = lexer.tokenize()
        self._errors: list[MDBaseException] = []
        self._token_index = 0
        self._panic_count = 0  # Track panic-mode recoveries

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
            even after encountering errors using panic-mode recovery.
        """
        program: Program = Program(statements=[])

        assert self._current_token is not None
        while self._current_token.type != TokenType.MISC_EOF and self._panic_count < 20:
            # Skip standalone periods
            if self._current_token.type == TokenType.PUNCT_PERIOD:
                self._advance_tokens()
                continue

            statement = self._parse_statement()
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
                message=NAME_UNDEFINED.substitute(name=self._peek_token.literal),
                line=self._peek_token.line,
                column=self._peek_token.position,
            )
        else:
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
                message=NAME_UNDEFINED.substitute(name=self._current_token.literal),
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
            if self._current_token.type in self._infix_parse_funcs:
                error_message = UNEXPECTED_TOKEN_AT_START.substitute(token=self._current_token.literal)
            elif self._current_token.type == TokenType.MISC_EOF:
                error_message = EXPECTED_EXPRESSION.substitute(got="<end-of-file>")
            else:
                error_message = NO_PARSE_FUNCTION.substitute(literal=self._current_token.literal)
            syntax_error = MDSyntaxError(
                message=error_message,
                line=self._current_token.line,
                column=self._current_token.position,
            )
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
            error_message = INVALID_FLOAT_LITERAL.substitute(literal=self._current_token.literal)
            error = MDSyntaxError(
                message=error_message,
                line=self._current_token.line,
                column=self._current_token.position,
            )
            self.errors.append(error)
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
            error_message = INVALID_INTEGER_LITERAL.substitute(literal=self._current_token.literal)
            error = MDSyntaxError(
                message=error_message,
                line=self._current_token.line,
                column=self._current_token.position,
            )
            self.errors.append(error)
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
            TokenType.OP_EQ: "==",
            TokenType.OP_NOT_EQ: "!=",
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

        # Parse the condition
        expression.condition = self._parse_expression(Precedence.LOWEST)

        # After parsing expression, we need to advance to the next token
        self._advance_tokens()

        # Check for comma or semicolon before 'else'/'otherwise'
        if self._current_token and self._current_token.type in (TokenType.PUNCT_COMMA, TokenType.PUNCT_SEMICOLON):
            self._advance_tokens()  # Move past comma/semicolon

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

    def _parse_statement(self) -> Statement:
        """Parse a single statement.

        Determines the statement type based on the current token and
        delegates to the appropriate parsing method.

        Returns:
            A Statement AST node (may be an ErrorStatement if parsing fails).
        """
        assert self._current_token is not None

        if self._current_token.type == TokenType.KW_SET:
            return self._parse_let_statement()
        elif self._current_token.type == TokenType.KW_RETURN:
            return self._parse_return_statement()
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
            TokenType.LIT_TRUE: self._parse_boolean_literal,
            TokenType.LIT_FALSE: self._parse_boolean_literal,
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
