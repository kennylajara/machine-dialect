# mypy: disable-error-code="comparison-overlap"

import re
from collections.abc import Callable
from copy import copy

from machine_dialect.ast import (
    ActionStatement,
    Arguments,
    BlockStatement,
    CallExpression,
    CallStatement,
    CollectionAccessExpression,
    ConditionalExpression,
    DefineStatement,
    EmptyLiteral,
    ErrorExpression,
    ErrorStatement,
    Expression,
    ExpressionStatement,
    FloatLiteral,
    ForEachStatement,
    Identifier,
    IfStatement,
    InfixExpression,
    InteractionStatement,
    NamedListLiteral,
    OrderedListLiteral,
    Output,
    Parameter,
    PrefixExpression,
    Program,
    ReturnStatement,
    SayStatement,
    SetStatement,
    Statement,
    StringLiteral,
    UnorderedListLiteral,
    URLLiteral,
    UtilityStatement,
    WhileStatement,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.errors.exceptions import MDBaseException, MDNameError, MDSyntaxError, MDTypeError
from machine_dialect.errors.messages import (
    EMPTY_ELSE_BLOCK,
    EMPTY_FOR_EACH_BODY,
    EMPTY_IF_CONSEQUENCE,
    EMPTY_WHILE_BODY,
    EXPECTED_DETAILS_CLOSE,
    EXPECTED_EXPRESSION,
    EXPECTED_FUNCTION_NAME,
    EXPECTED_IDENTIFIER_AFTER,
    EXPECTED_TOKEN,
    EXPECTED_TOKEN_AFTER,
    ILLEGAL_TOKEN,
    INVALID_ARGUMENT_VALUE,
    INVALID_FLOAT_LITERAL,
    INVALID_INTEGER_LITERAL,
    INVALID_TYPE_NAME,
    MISSING_COMMA_BETWEEN_ARGS,
    MISSING_DEPTH_TRANSITION,
    NAME_UNDEFINED,
    NO_PARSE_FUNCTION,
    UNEXPECTED_BLOCK_DEPTH,
    UNEXPECTED_STATEMENT,
    UNEXPECTED_TOKEN_AT_START,
    UNHANDLED_OPERATION,
    VARIABLE_ALREADY_DEFINED,
    VARIABLE_NOT_DEFINED,
    ErrorTemplate,
)
from machine_dialect.lexer import Lexer
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.parser import Precedence
from machine_dialect.parser.protocols import (
    InfixParseFuncs,
    PostfixParseFuncs,
    PrefixParseFuncs,
)
from machine_dialect.parser.symbol_table import SymbolTable
from machine_dialect.parser.token_buffer import TokenBuffer
from machine_dialect.type_checking import TypeSpec, check_type_compatibility, get_type_from_value

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
    TokenType.OP_CARET: Precedence.MATH_EXPONENT,
    # Dictionary extraction operators (postfix-like)
    TokenType.OP_THE_NAMES_OF: Precedence.UNARY_POST_OPERATOR,
    TokenType.OP_THE_CONTENTS_OF: Precedence.UNARY_POST_OPERATOR,
}

TYPING_MAP: dict[TokenType, str] = {
    TokenType.KW_TEXT: "Text",
    TokenType.KW_WHOLE_NUMBER: "Whole Number",
    TokenType.KW_FLOAT: "Float",
    TokenType.KW_NUMBER: "Number",
    TokenType.KW_YES_NO: "Yes/No",
    TokenType.KW_URL: "URL",
    TokenType.KW_DATE: "Date",
    TokenType.KW_DATETIME: "DateTime",
    TokenType.KW_TIME: "Time",
    TokenType.KW_LIST: "List",
    TokenType.KW_ORDERED_LIST: "Ordered List",
    TokenType.KW_UNORDERED_LIST: "Unordered List",
    TokenType.KW_NAMED_LIST: "Named List",
    TokenType.KW_EMPTY: "Empty",
}

__all__ = ["Parser"]


class Parser:
    """Parser for Machine Dialect™ language.

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
        self._symbol_table: SymbolTable = SymbolTable()  # Track variable definitions

        self._prefix_parse_funcs: PrefixParseFuncs = self._register_prefix_funcs()
        self._infix_parse_funcs: InfixParseFuncs = self._register_infix_funcs()
        self._postfix_parse_funcs: PostfixParseFuncs = self._register_postfix_funcs()

    def parse(self, source: str, as_hir: bool = False, check_semantics: bool = True) -> Program:
        """Parse the source code into an AST.

        Args:
            source: The source code to parse.
            as_hir: If True, return a HIR (High level Intermediate Representation).
            check_semantics: If True, perform semantic analysis.

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

        # Skip frontmatter if present
        self._skip_frontmatter()

        # Parse the program
        program: Program = Program(statements=[])

        assert self._current_token is not None
        while self._current_token.type != TokenType.MISC_EOF and self._panic_count < 20:
            # Skip standalone periods
            if self._current_token.type == TokenType.PUNCT_PERIOD:
                self._advance_tokens()
                continue

            # Save the token position before parsing
            token_before = self._current_token

            statement = self._parse_statement()
            program.statements.append(statement)

            # If we haven't advanced past the token we started with, we need to advance
            # This happens when expression parsing leaves us at the last token
            if self._current_token == token_before:
                self._advance_tokens()
            # After parsing a statement, skip any trailing period
            elif self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
                self._advance_tokens()

        # Perform semantic analysis if requested
        if check_semantics and not self._errors:
            from machine_dialect.semantic.analyzer import SemanticAnalyzer

            analyzer = SemanticAnalyzer()
            program, semantic_errors = analyzer.analyze(program)
            self._errors.extend(semantic_errors)

        return program.desugar() if as_hir else program

    def _reset_state(self) -> None:
        """Reset the parser state for a new parse."""
        self._current_token = None
        self._peek_token = None
        self._token_buffer = None
        self._errors = []
        self._panic_count = 0
        self._block_depth = 0
        self._symbol_table = SymbolTable()  # Reset symbol table for new parse

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
        return copy(self._errors)

    def _skip_frontmatter(self) -> None:
        """Skip YAML frontmatter section if present at the beginning of the document.

        Frontmatter starts with --- and ends with another --- on its own line.
        Everything between these delimiters is skipped.
        """
        # Check if we're at the beginning with a frontmatter delimiter
        if self._current_token and self._current_token.type == TokenType.PUNCT_FRONTMATTER:
            # Skip tokens until we find the closing frontmatter delimiter
            self._advance_tokens()

            while self._current_token and self._current_token.type != TokenType.MISC_EOF:
                if self._current_token.type == TokenType.PUNCT_FRONTMATTER:
                    # Found closing delimiter, skip it and exit
                    self._advance_tokens()
                    break
                # Skip any token that's not a closing frontmatter delimiter
                self._advance_tokens()

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

                # Skip stopwords and backslashes
                if self._peek_token.type not in (TokenType.MISC_STOPWORD, TokenType.PUNCT_BACKSLASH):
                    break
        else:
            # No buffer available
            self._peek_token = Token(TokenType.MISC_EOF, "", line=1, position=1)

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

    def _panic_recovery(self, stop_at: list[TokenType] | None = None, stop_at_types: bool = False) -> list[Token]:
        """Unified error recovery: skip tokens until finding synchronization point.

        Args:
            stop_at: Token types to stop at (default: [PERIOD, EOF])
            stop_at_types: If True, also stop at type keywords

        Returns:
            List of tokens that were skipped during recovery.
        """
        self._panic_count += 1  # Always increment to prevent infinite loops

        if stop_at is None:
            stop_at = [TokenType.PUNCT_PERIOD, TokenType.MISC_EOF]

        skipped_tokens = []

        # Skip tokens until finding a synchronization point
        while self._peek_token is not None and self._peek_token.type not in stop_at:
            self._advance_tokens()
            if self._current_token is not None:
                # Check if we should stop at type keywords
                if stop_at_types and self._is_type_token(self._current_token.type):
                    break
                skipped_tokens.append(self._current_token)

        # Advance one more token to move past the last error token
        # This prevents the main loop from trying to parse the last token again
        if self._current_token is not None and self._current_token.type != TokenType.MISC_EOF:
            self._advance_tokens()

        return skipped_tokens

    def _report_error_and_recover(
        self,
        template: ErrorTemplate,
        error_type: str = "syntax",
        expected_token: TokenType | None = None,
        recovery_tokens: list[TokenType] | None = None,
        recovery_to_types: bool = False,
        skip_recovery: bool = False,
        is_expression: bool = False,
        **kwargs: str,
    ) -> ErrorStatement | ErrorExpression:
        """Unified error handling: always adds error to list and returns appropriate error node.

        Args:
            template: ErrorTemplate with the error message
            error_type: Type of error - "syntax", "name", or "type"
            expected_token: Expected token type (for syntax errors)
            recovery_tokens: Specific tokens to recover to
            recovery_to_types: If True, recover to type keywords
            skip_recovery: If True, skip error recovery
            is_expression: If True, return ErrorExpression instead of ErrorStatement
            **kwargs: Template substitution parameters

        Returns:
            ErrorStatement or ErrorExpression with consistent error reporting.
        """
        # Determine which token to use for error reporting
        # If we have an expected_token, we're likely checking peek_token
        # Otherwise, use current_token
        if expected_token and self._peek_token:
            token = self._peek_token or Token(TokenType.MISC_EOF, "", 0, 0)
        else:
            token = self._current_token or Token(TokenType.MISC_EOF, "", 0, 0)

        # Create appropriate error type
        error: MDBaseException
        if error_type == "name":
            error = MDNameError(message=template, line=token.line, column=token.position, **kwargs)
        elif error_type == "type":
            error = MDTypeError(message=template, line=token.line, column=token.position, **kwargs)
        else:  # syntax
            # Special case: if we expected an identifier and got something else
            # Check if it's an illegal token (syntax error) or something else (name error)
            if expected_token == TokenType.MISC_IDENT and token.type != TokenType.MISC_IDENT:
                # If it's an illegal token, it's a syntax error
                if token.type == TokenType.MISC_ILLEGAL:
                    error = MDSyntaxError(
                        message=ILLEGAL_TOKEN,
                        line=token.line,
                        column=token.position,
                        token=token.literal,
                    )
                else:
                    # Otherwise, it's still a name error (e.g., keyword used as identifier)
                    from machine_dialect.errors.messages import ILLEGAL_CHARACTER

                    # Get a human-readable name for the expected token
                    expected_name = "identifier"
                    error = MDNameError(
                        message=ILLEGAL_CHARACTER,
                        line=token.line,
                        column=token.position,
                        expected=expected_name,
                        character=token.literal,
                    )
            else:
                error = MDSyntaxError(message=template, line=token.line, column=token.position, **kwargs)

        # ALWAYS add the error to ensure consistency
        self._errors.append(error)

        # Perform recovery unless explicitly skipped
        skipped = []
        if not skip_recovery:
            skipped = self._panic_recovery(stop_at=recovery_tokens, stop_at_types=recovery_to_types)

        # Get formatted message
        formatted_message = template.format(**kwargs) if kwargs else template.substitute()

        # Return appropriate error node type
        if is_expression:
            return ErrorExpression(token=token, message=formatted_message)
        else:
            return ErrorStatement(token=token, skipped_tokens=skipped, message=formatted_message)

    def _expect_token(
        self,
        token_type: TokenType,
        context: str | None = None,
        error_message: str | None = None,
        error_node: ErrorExpression | None = None,
    ) -> ErrorStatement | ErrorExpression | None:
        """Unified token expectation with automatic error handling.

        Args:
            token_type: Expected token type
            context: Context for error message (e.g., "after 'Set'")
            error_message: Full custom error message (overrides auto-generated)
            error_node: Custom ErrorExpression to return (for expression contexts)

        Returns:
            None if token matches (advances and continues)
            ErrorExpression if error_node provided and token doesn't match
            ErrorStatement if token doesn't match (with appropriate recovery)
        """
        if self._peek_token and self._peek_token.type == token_type:
            self._advance_tokens()
            return None  # Success, continue parsing

        # Token doesn't match - use appropriate error template
        from machine_dialect.errors.messages import EXPECTED_TOKEN, EXPECTED_TOKEN_AFTER

        if context:
            # Use "Expected X after Y" template
            token_name = token_type.name.lower().replace("_", " ")
            template = EXPECTED_TOKEN_AFTER
            kwargs = {"expected": token_name, "after": context}
        else:
            # Use simple "Expected X" template
            token_name = token_type.name.lower().replace("_", " ")
            template = EXPECTED_TOKEN
            # Get the actual token type that was found
            actual_token = self._peek_token if self._peek_token else None
            got_type = actual_token.type.name if actual_token else "EOF"
            kwargs = {"token": token_name, "got_token_type": got_type}

        # Special handling for period (statement terminator)
        skip_recovery = token_type == TokenType.PUNCT_PERIOD

        # Always use _report_error_and_recover for error reporting
        error_statement = self._report_error_and_recover(
            template=template,
            expected_token=token_type,
            skip_recovery=skip_recovery or error_node is not None,  # Skip recovery for expressions too
            error_type="syntax",
            recovery_tokens=None,
            recovery_to_types=False,
            is_expression=False,
            **kwargs,
        )

        # If custom error node provided, return it instead of the ErrorStatement
        if error_node is not None:
            return error_node

        return error_statement

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
            # Report as syntax error, not name error
            result = self._report_error_and_recover(
                template=ILLEGAL_TOKEN,
                error_type="syntax",
                token=self._current_token.literal,
                skip_recovery=True,  # Don't recover - let caller handle advancement
                is_expression=True,
            )
            assert isinstance(result, ErrorExpression)
            return result

        if self._current_token.type not in self._prefix_parse_funcs:
            # Check if it's an infix operator at the start
            # Determine which error template to use and its parameters
            if self._current_token.type in self._infix_parse_funcs:
                error_expr = self._report_error_and_recover(
                    template=UNEXPECTED_TOKEN_AT_START,
                    token=self._current_token.literal,
                    skip_recovery=True,
                    is_expression=True,
                )
            elif self._current_token.type == TokenType.MISC_EOF:
                error_expr = self._report_error_and_recover(
                    template=EXPECTED_EXPRESSION,
                    got="<end-of-file>",
                    skip_recovery=True,
                    is_expression=True,
                )
            else:
                error_expr = self._report_error_and_recover(
                    template=NO_PARSE_FUNCTION,
                    literal=self._current_token.literal,
                    skip_recovery=True,
                    is_expression=True,
                )

            # Advance past the problematic token so we can continue parsing
            if self._current_token.type != TokenType.MISC_EOF:
                self._advance_tokens()
            assert isinstance(error_expr, ErrorExpression)
            return error_expr

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

    def _parse_expression_statement(self) -> ExpressionStatement | ErrorStatement:
        assert self._current_token is not None

        expression = self._parse_expression()

        expression_statement = ExpressionStatement(
            token=self._current_token,
            expression=expression,
        )

        # Require trailing period if not at EOF or if we're in a block
        assert self._peek_token is not None
        if self._peek_token.type != TokenType.MISC_EOF or self._block_depth > 0:
            if error := self._expect_token(TokenType.PUNCT_PERIOD):
                assert isinstance(error, ErrorStatement)
                return error

        # Advance past the last token of the expression
        # Expression parsing leaves us at the last token, not after it
        self._advance_tokens()

        return expression_statement

    def _parse_float_literal(self) -> FloatLiteral | ErrorExpression:
        assert self._current_token is not None

        # The lexer has already validated and cleaned the literal
        # so we can directly parse it as a float
        try:
            value = float(self._current_token.literal)
        except ValueError:
            # This shouldn't happen if the lexer is working correctly
            result = self._report_error_and_recover(
                template=INVALID_FLOAT_LITERAL,
                literal=self._current_token.literal,
                skip_recovery=True,
                is_expression=True,
            )
            assert isinstance(result, ErrorExpression)
            return result

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

    def _parse_identifier_or_keyword_as_identifier(self) -> Identifier | None:
        """Parse an identifier, accepting keywords as identifiers when appropriate.

        This is useful when a keyword appears where we expect an identifier,
        like variable names that happen to match keywords.

        Returns:
            An Identifier AST node, or None if current token can't be used as identifier.
        """
        if not self._current_token:
            return None

        # Accept actual identifiers
        if self._current_token.type == TokenType.MISC_IDENT:
            return self._parse_identifier()

        # Also accept any keyword that has a literal value as an identifier
        # This allows using words like "items", "first", etc. as variable names
        if self._current_token.literal:
            # Create an identifier from the keyword's literal
            return Identifier(
                token=self._current_token,
                value=self._current_token.literal,
            )

        return None

    def _parse_integer_literal(self) -> WholeNumberLiteral | ErrorExpression:
        assert self._current_token is not None

        # The lexer has already validated and cleaned the literal
        # so we can directly parse it as an integer
        try:
            value = int(self._current_token.literal)
        except ValueError:
            # This shouldn't happen if the lexer is working correctly
            result = self._report_error_and_recover(
                template=INVALID_INTEGER_LITERAL,
                literal=self._current_token.literal,
                skip_recovery=True,
                is_expression=True,
            )
            assert isinstance(result, ErrorExpression)
            return result

        return WholeNumberLiteral(
            token=self._current_token,
            value=value,
        )

    def _parse_boolean_literal(self) -> YesNoLiteral:
        """Parse a boolean literal.

        Returns:
            A YesNoLiteral AST node.

        Note:
            The lexer has already validated and provided the canonical
            representation of the boolean literal ("True" or "False").
        """
        assert self._current_token is not None

        # Determine the boolean value based on the token type
        value = self._current_token.type == TokenType.LIT_YES

        return YesNoLiteral(
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

        # Extract the actual string value without quotes
        literal = self._current_token.literal
        if literal.startswith('"') and literal.endswith('"'):
            value = literal[1:-1]
        elif literal.startswith("'") and literal.endswith("'"):
            value = literal[1:-1]
        else:
            # Fallback if no quotes found
            value = literal

        return StringLiteral(
            token=self._current_token,
            value=value,
        )

    def _parse_list_literal(self) -> Expression:
        """Parse a list literal (unordered, ordered, or named).

        Called when current token is the first list item marker after "Set x to:"
        Determines the list type based on the first item marker and
        delegates to the appropriate specialized parser.

        Returns:
            UnorderedListLiteral, OrderedListLiteral, or NamedListLiteral
        """
        # SetStatement has already advanced past the colon to the first list item
        # Current token should be the first list item marker (dash, number, or EOF for empty list)
        if not self._current_token:
            return ErrorExpression(
                token=Token(TokenType.MISC_EOF, "", 0, 0),
                message="Unexpected EOF while parsing list",
            )

        # Save the starting token for error reporting
        list_token = self._current_token

        # List context should already be set by SetStatement

        # Check for empty list (no items)
        current_type = self._current_token.type if self._current_token else None
        if current_type in (None, TokenType.MISC_EOF) or (
            # Also check if we hit a statement terminator or new statement
            current_type in (TokenType.PUNCT_PERIOD, TokenType.KW_SET, TokenType.KW_DEFINE)
        ):
            # Empty list - default to unordered
            return UnorderedListLiteral(token=list_token, elements=[])

        # Skip any stopwords that might appear
        while self._current_token and self._current_token.type in (TokenType.MISC_STOPWORD,):
            self._advance_tokens()
            # Update current type after skipping stopwords
            current_type = self._current_token.type if self._current_token else None

        # Now current_token should be the first list item marker (dash or number)
        # Update current_type after advancing
        current_type = self._current_token.type if self._current_token else None

        # Look at what type of list this is
        if current_type == TokenType.PUNCT_DASH:
            # Check if it's a named list by looking for pattern: dash, key, colon
            # Named lists have patterns like: - _"key"_: value

            # Use the token buffer to peek ahead without advancing
            is_named_list = False

            # We're at the dash, peek_token is the key
            if self._peek_token:
                # Check token after the key using buffer
                if self._token_buffer:
                    # The buffer's current token is the token after our peek_token
                    colon_after_key = self._token_buffer.current()

                    # Check if we have the pattern: dash, key, colon
                    if colon_after_key and colon_after_key.type == TokenType.PUNCT_COLON:
                        # Check if peek_token (the key) is valid for a named list
                        peek_type = self._peek_token.type
                        if peek_type in (
                            TokenType.LIT_TEXT,
                            TokenType.MISC_IDENT,
                            TokenType.KW_NAME,
                            TokenType.KW_CONTENT,
                        ):
                            is_named_list = True
                        elif self._peek_token.literal and self._peek_token.literal.lower() in (
                            "age",
                            "active",
                            "profession",
                        ):
                            is_named_list = True

            result: Expression
            if is_named_list:
                result = self._parse_named_list_literal(list_token)
            else:
                # Not a named list, it's an unordered list
                result = self._parse_unordered_list_literal(list_token)

        # Check if it's an ordered list (number followed by period)
        elif (
            current_type == TokenType.LIT_WHOLE_NUMBER
            and self._peek_token
            and self._peek_token.type == TokenType.PUNCT_PERIOD
        ):
            result = self._parse_ordered_list_literal(list_token)
        else:
            # Invalid list format - return error expression
            result = ErrorExpression(
                token=self._current_token or list_token,
                message=(
                    f"Expected list item marker (dash or number), got "
                    f"{self._current_token.type if self._current_token else 'EOF'}"
                ),
            )

        return result

    def _parse_unordered_list_literal(self, list_token: Token) -> UnorderedListLiteral:
        """Parse an unordered list (dash-prefixed items).

        Args:
            list_token: The token marking the start of the list

        Returns:
            UnorderedListLiteral with parsed items
        """
        items: list[Expression] = []

        # We might not be at the dash yet if we came from lookahead
        # Go back to find the dash
        if self._current_token and self._current_token.type != TokenType.PUNCT_DASH:
            # We're past the dash (probably at 'name' from lookahead), go back
            # Actually, this is complex. Let's just handle where we are.
            pass

        while True:
            # Check if we're at a dash (list item marker)
            if not self._current_token:
                break
            token_type = self._current_token.type
            if token_type != TokenType.PUNCT_DASH:
                break

            # Move past dash
            self._advance_tokens()

            # Parse the item expression
            item = self._parse_expression(Precedence.LOWEST)
            items.append(item)

            # After parsing expression, advance to check for period
            self._advance_tokens()

            # Each list item must end with a period
            if self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
                # Good, we have the required period
                # Now check if there's another list item
                if self._peek_token and self._peek_token.type == TokenType.PUNCT_DASH:
                    # There's another list item, advance to it
                    self._advance_tokens()
                else:
                    # No more list items - we're done
                    break
            else:
                # Missing period after list item - use unified error handling
                from machine_dialect.errors.messages import EXPECTED_TOKEN_AFTER

                self._report_error_and_recover(
                    template=EXPECTED_TOKEN_AFTER,
                    expected_token=TokenType.PUNCT_PERIOD,
                    skip_recovery=True,  # We'll handle recovery manually below
                    expected="period",
                    after="list item",
                )

                # Check if we're at another dash (next item) or done
                if self._current_token and self._current_token.type == TokenType.PUNCT_DASH:
                    # Continue with next item despite missing period
                    continue
                else:
                    # No more items
                    break

        return UnorderedListLiteral(token=list_token, elements=items)

    def _parse_ordered_list_literal(self, list_token: Token) -> OrderedListLiteral:
        """Parse an ordered list (numbered items like 1., 2., etc).

        Args:
            list_token: The token marking the start of the list

        Returns:
            OrderedListLiteral with parsed items
        """
        items: list[Expression] = []

        while True:
            # Check if we're at a number (ordered list item marker)
            if not self._current_token:
                break
            token_type = self._current_token.type
            if token_type != TokenType.LIT_WHOLE_NUMBER:
                break

            # Skip the number
            self._advance_tokens()

            # Check for period after number (this is the list marker period, e.g., "1.")
            if not self._current_token or self._current_token.type != TokenType.PUNCT_PERIOD:
                break

            # Move past the list marker period
            self._advance_tokens()

            # Parse the item expression
            item = self._parse_expression(Precedence.LOWEST)
            items.append(item)

            # After parsing expression, advance to check for item-terminating period
            self._advance_tokens()

            # Each list item must end with a period
            if self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
                # Good, we have the required period
                # Check if there's another list item
                if self._peek_token and self._peek_token.type == TokenType.LIT_WHOLE_NUMBER:
                    # There's another list item, advance to it
                    self._advance_tokens()
                else:
                    # No more list items - we're done
                    break
            else:
                # Missing period after list item - use unified error handling
                from machine_dialect.errors.messages import EXPECTED_TOKEN_AFTER

                self._report_error_and_recover(
                    template=EXPECTED_TOKEN_AFTER,
                    expected_token=TokenType.PUNCT_PERIOD,
                    skip_recovery=True,  # We'll handle recovery manually below
                    expected="period",
                    after="list item",
                )

                # Check if we're at another number (next item) or done
                if self._current_token and self._current_token.type == TokenType.LIT_WHOLE_NUMBER:
                    # Continue with next item despite missing period
                    continue
                else:
                    # No more items
                    break

        return OrderedListLiteral(token=list_token, elements=items)

    def _parse_named_list_literal(self, list_token: Token) -> NamedListLiteral:
        """Parse a named list (dictionary with key:value pairs).

        Format:
        - key1: value1
        - key2: value2

        Args:
            list_token: The token marking the start of the list

        Returns:
            NamedListLiteral with parsed key-value pairs
        """
        entries: list[tuple[str, Expression]] = []

        # Parse entries while we have dash-prefixed lines
        while True:
            # Check if we're at a dash (named list item marker)
            if not self._current_token:
                break
            token_type = self._current_token.type
            if token_type != TokenType.PUNCT_DASH:
                break

            # Move past the dash
            self._advance_tokens()

            # Parse the key (MUST be a string literal)
            key = ""
            current_type_after_dash: TokenType | None = self._current_token.type if self._current_token else None
            if current_type_after_dash == TokenType.LIT_TEXT:
                key = self._current_token.literal.strip('"')
                self._advance_tokens()
            else:
                # Invalid key - named lists require string literal keys only
                if self._current_token:
                    from machine_dialect.errors.messages import INVALID_NAMED_LIST_KEY

                    self._report_error_and_recover(
                        template=INVALID_NAMED_LIST_KEY,
                        error_type="type",
                        literal=self._current_token.literal,
                        recovery_tokens=[TokenType.PUNCT_DASH, TokenType.MISC_EOF],
                    )
                else:
                    self._panic_recovery(stop_at=[TokenType.PUNCT_DASH, TokenType.MISC_EOF])
                continue

            # Expect colon
            current_type_for_colon: TokenType | None = self._current_token.type if self._current_token else None
            if current_type_for_colon != TokenType.PUNCT_COLON:
                # Missing colon, this might be an unordered list item
                # Add error and try to continue
                entries.append(
                    (key, ErrorExpression(token=self._current_token or list_token, message="Expected colon after key"))
                )
                self._panic_recovery(stop_at=[TokenType.PUNCT_DASH, TokenType.MISC_EOF])
                continue

            self._advance_tokens()  # Move past colon

            # Parse the value expression
            value = self._parse_expression(Precedence.LOWEST)
            if not value:
                entries.append(
                    (
                        key,
                        ErrorExpression(token=self._current_token or list_token, message="Expected value after colon"),
                    )
                )
                self._panic_recovery(stop_at=[TokenType.PUNCT_DASH, TokenType.MISC_EOF])
                continue

            # After parsing expression, advance to check for period
            self._advance_tokens()

            # Each named list entry must end with a period
            if self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
                # Good, we have the required period
                entries.append((key, value))
                # Check if there's another entry
                if self._peek_token and self._peek_token.type == TokenType.PUNCT_DASH:
                    # There's another entry, advance to it
                    self._advance_tokens()
                else:
                    # No more entries - we're done
                    break
            else:
                # Missing period after entry - add error but include the entry
                from machine_dialect.errors.messages import EXPECTED_TOKEN_AFTER

                self._report_error_and_recover(
                    template=EXPECTED_TOKEN_AFTER,
                    expected_token=TokenType.PUNCT_PERIOD,
                    skip_recovery=True,  # We'll handle recovery manually below
                    expected="period",
                    after="named list entry",
                )
                entries.append((key, value))

                # Check if we're at another dash (next entry) or done
                if self._current_token and self._current_token.type == TokenType.PUNCT_DASH:
                    # Continue with next entry despite missing period
                    continue
                else:
                    # No more entries
                    break

        return NamedListLiteral(token=list_token, entries=entries)

    def _parse_url_literal(self) -> URLLiteral:
        """Parse a URL literal.

        Returns:
            A URLLiteral AST node.
        """
        assert self._current_token is not None

        # Extract the actual URL value without quotes (like string literals)
        literal = self._current_token.literal
        if literal.startswith('"') and literal.endswith('"'):
            value = literal[1:-1]
        elif literal.startswith("'") and literal.endswith("'"):
            value = literal[1:-1]
        else:
            # Fallback if no quotes found
            value = literal

        return URLLiteral(
            token=self._current_token,
            value=value,
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

    def _parse_ordinal_list_access(self) -> Expression:
        """Parse ordinal list access: '[the] first item of list'.

        Handles both forms:
        - 'the first item of list' (with optional 'the')
        - 'first item of list' (without 'the')

        Returns:
            A CollectionAccessExpression for ordinal access.
        """
        assert self._current_token is not None

        # Check if we're starting with an ordinal directly or with 'the' (stopword)
        if self._current_token.type == TokenType.MISC_STOPWORD and self._current_token.literal.lower() == "the":
            # Skip optional 'the'
            self._advance_tokens()

        # Now we should have an ordinal (first, second, third, last)
        if self._current_token is None or self._current_token.type not in [
            TokenType.KW_FIRST,
            TokenType.KW_SECOND,
            TokenType.KW_THIRD,
            TokenType.KW_LAST,
        ]:
            # Not a valid ordinal access pattern
            return ErrorExpression(
                token=self._current_token or Token(TokenType.MISC_ILLEGAL, "", 0, 0),
                message="Not a valid ordinal access pattern",
            )

        ordinal_token = self._current_token
        ordinal = self._current_token.literal

        # Skip ordinal
        self._advance_tokens()

        # Expect 'item'
        if self._current_token is None or self._current_token.type != TokenType.KW_ITEM:
            msg = f"Expected 'item' after ordinal, got {self._current_token.type if self._current_token else 'EOF'}"
            return ErrorExpression(token=self._current_token or ordinal_token, message=msg)

        # Skip 'item'
        self._advance_tokens()

        # Expect 'of' - check the new current token after advancing
        current = self._current_token
        if current is None or current.type != TokenType.KW_OF:
            msg = f"Expected 'of' after 'item', got {self._current_token.type if self._current_token else 'EOF'}"
            return ErrorExpression(token=self._current_token or ordinal_token, message=msg)

        # Skip 'of'
        self._advance_tokens()

        # Parse the collection expression
        collection = self._parse_expression(Precedence.LOWEST)

        return CollectionAccessExpression(
            token=ordinal_token, collection=collection, accessor=ordinal, access_type="ordinal"
        )

    def _parse_stopword_expression(self) -> Expression:
        """Parse expressions that start with stopwords.

        Handles:
        - 'the' for list access patterns (the first/second/third/last item of)

        Returns:
            An appropriate expression or None if not a valid pattern.
        """
        assert self._current_token is not None

        # Check if it's 'the' which might start various patterns
        if self._current_token.literal.lower() == "the":
            # Look ahead to see if it's followed by an ordinal
            if self._peek_token and self._peek_token.type in [
                TokenType.KW_FIRST,
                TokenType.KW_SECOND,
                TokenType.KW_THIRD,
                TokenType.KW_LAST,
            ]:
                return self._parse_ordinal_list_access()

        # Otherwise, stopwords aren't valid expression starters
        return ErrorExpression(
            token=self._current_token,
            message=f"Unexpected stopword '{self._current_token.literal}' at start of expression",
        )

    def _parse_dict_extraction_prefix(self) -> Expression:
        """Parse dictionary extraction as a prefix operator.

        Examples:
            the names of `person` -> DictExtraction(dictionary=person, extract_type="names")
            the contents of `config` -> DictExtraction(dictionary=config, extract_type="contents")

        Returns:
            A DictExtraction expression.
        """
        assert self._current_token is not None
        operator_token = self._current_token

        # Determine extraction type based on operator
        if operator_token.type == TokenType.OP_THE_NAMES_OF:
            extract_type = "names"
        elif operator_token.type == TokenType.OP_THE_CONTENTS_OF:
            extract_type = "contents"
        else:
            msg = f"Unknown dictionary extraction operator: {operator_token.type}"
            return ErrorExpression(token=operator_token, message=msg)

        # Skip the operator
        self._advance_tokens()

        # Parse the dictionary expression
        dictionary = self._parse_expression(Precedence.UNARY_POST_OPERATOR)

        if dictionary is None:
            msg = "Expected dictionary expression after extraction operator"
            return ErrorExpression(token=self._current_token or operator_token, message=msg)

        # Import here to avoid circular dependency
        from machine_dialect.ast.dict_extraction import DictExtraction

        return DictExtraction(token=operator_token, dictionary=dictionary, extract_type=extract_type)

    def _parse_dict_extraction_infix(self, dictionary: Expression) -> Expression:
        """Parse dictionary extraction as an infix operator.

        Examples:
            `person` the names of -> DictExtraction(dictionary=person, extract_type="names")
            `config` the contents of -> DictExtraction(dictionary=config, extract_type="contents")

        Args:
            dictionary: The dictionary expression to extract from

        Returns:
            A DictExtraction expression.
        """
        assert self._current_token is not None
        operator_token = self._current_token

        # Determine extraction type based on operator
        if operator_token.type == TokenType.OP_THE_NAMES_OF:
            extract_type = "names"
        elif operator_token.type == TokenType.OP_THE_CONTENTS_OF:
            extract_type = "contents"
        else:
            msg = f"Unknown dictionary extraction operator: {operator_token.type}"
            return ErrorExpression(token=operator_token, message=msg)

        # Import here to avoid circular dependency
        from machine_dialect.ast.dict_extraction import DictExtraction

        return DictExtraction(token=operator_token, dictionary=dictionary, extract_type=extract_type)

    # TODO: Refactor this function to an infix expression
    def _parse_possessive_access(self) -> Expression:
        """Parse possessive property access: `person`'s _"name"_.

        When the lexer sees `person`'s, it emits a PUNCT_APOSTROPHE_S token
        with the identifier as the literal. We then need to parse the property name
        as a string literal.

        Returns:
            A CollectionAccessExpression for property access.
        """
        assert self._current_token is not None
        assert self._current_token.type == TokenType.PUNCT_APOSTROPHE_S

        # The literal contains the identifier name (e.g., "person")
        dict_name = self._current_token.literal
        token = self._current_token

        # Create an identifier for the dictionary
        dict_identifier = Identifier(Token(TokenType.MISC_IDENT, dict_name, token.line, token.position), dict_name)

        # Skip the possessive token
        self._advance_tokens()

        # Now we expect a string literal for the property name
        # Note: after _advance_tokens(), current_token has changed from PUNCT_APOSTROPHE_S
        if self._current_token is None or self._current_token.type != TokenType.LIT_TEXT:
            msg = (
                "Expected string literal for property name after possessive, got "
                f"{self._current_token.type if self._current_token else 'EOF'}"
            )
            return ErrorExpression(token=self._current_token or token, message=msg)

        # Extract the property name from the string literal (remove quotes)
        property_literal = self._current_token.literal
        # Remove quotes from the literal
        if property_literal.startswith('"') and property_literal.endswith('"'):
            property_name = property_literal[1:-1]
        elif property_literal.startswith("'") and property_literal.endswith("'"):
            property_name = property_literal[1:-1]
        else:
            property_name = property_literal

        # Note: We do NOT advance past the property name here.
        # Expression parsers should leave current_token AT the last token of the expression,
        # not after it. The caller will advance when needed.

        # Create a collection access expression with property access type
        return CollectionAccessExpression(
            token=token, collection=dict_identifier, accessor=property_name, access_type="property"
        )

    def _parse_numeric_list_access(self) -> Expression:
        """Parse numeric list access: 'item _5_ of list'.

        Returns:
            A CollectionAccessExpression for numeric access.
        """
        assert self._current_token is not None
        assert self._current_token.type == TokenType.KW_ITEM

        item_token = self._current_token

        # Skip 'item'
        self._advance_tokens()

        # Expect a number literal - check the new current token after advancing
        current = self._current_token
        if current is None or current.type != TokenType.LIT_WHOLE_NUMBER:
            msg = f"Expected number after 'item', got {self._current_token.type if self._current_token else 'EOF'}"
            return ErrorExpression(token=self._current_token or item_token, message=msg)

        # Get the index (one-based in Machine Dialect™)
        index = int(self._current_token.literal)

        # Skip number
        self._advance_tokens()

        # Expect 'of' - check the new current token after advancing
        current = self._current_token
        if current is None or current.type != TokenType.KW_OF:
            msg = f"Expected 'of' after number, got {self._current_token.type if self._current_token else 'EOF'}"
            return ErrorExpression(token=self._current_token or item_token, message=msg)

        # Skip 'of'
        self._advance_tokens()

        # Parse the collection expression
        collection = self._parse_expression(Precedence.LOWEST)

        return CollectionAccessExpression(
            token=item_token, collection=collection, accessor=index, access_type="numeric"
        )

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
        assert self._current_token is not None
        if error := self._expect_token(
            TokenType.DELIM_RPAREN,
            error_node=ErrorExpression(token=self._current_token, message="Expected closing parenthesis"),
        ):
            assert isinstance(error, ErrorExpression)
            return error

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

    def _parse_define_statement(self) -> DefineStatement | ErrorStatement:
        """Parse a Define statement.

        Grammar:
            define_statement ::= "Define" identifier "as" type_spec
                               ["(" "default" ":" expression ")"] "."

        Examples:
            Define `x` as Whole Number.
            Define `name` as Text (default: _"Unknown"_).
            Define `value` as Whole Number or Text.

        Returns:
            DefineStatement on success, ErrorStatement on parse error.
        """
        statement_token = self._current_token
        assert statement_token is not None

        # Move past "Define" to get to the identifier
        self._advance_tokens()

        # Check if we have an identifier
        if not self._current_token or self._current_token.type != TokenType.MISC_IDENT:
            # Report error and get recovery result
            error_stmt = self._report_error_and_recover(
                template=EXPECTED_IDENTIFIER_AFTER,
                expected_token=TokenType.MISC_IDENT,
                what="variable",
                after="'Define'",
                recovery_tokens=[TokenType.KW_AS, TokenType.PUNCT_PERIOD, TokenType.MISC_EOF],
            )

            # Try to continue parsing if we recovered at 'as' keyword
            if self._current_token and self._current_token.type == TokenType.KW_AS:
                # Found 'as', try to continue parsing from here
                name = Identifier(statement_token, "<error>")  # Placeholder name
                self._advance_tokens()  # Skip 'as'
                type_spec = self._parse_type_spec()
                if type_spec:
                    return DefineStatement(statement_token, name, type_spec, None)

            assert isinstance(error_stmt, ErrorStatement)
            return error_stmt

        # Parse the identifier
        name = self._parse_identifier()

        # Move past the identifier
        self._advance_tokens()

        # Skip any stopwords between identifier and "as"
        while self._current_token and self._current_token.type == TokenType.MISC_STOPWORD:
            self._advance_tokens()

        # Expect "as" keyword - we should be at "as" now
        # Re-check current_token to help MyPy's type narrowing
        if self._current_token is None or self._current_token.type != TokenType.KW_AS:
            # Report error with recovery to type keywords
            error_stmt = self._report_error_and_recover(
                template=EXPECTED_TOKEN_AFTER,
                expected_token=TokenType.KW_AS,
                expected="'as'",
                after=f"variable name '{name.value}'",
                recovery_to_types=True,
            )

            # If we recovered at a type keyword, try to continue parsing
            if self._current_token and self._is_type_token(self._current_token.type):
                # Found a type, try to continue parsing
                type_spec = self._parse_type_spec()
                if type_spec:
                    # Still register the variable even with syntax error
                    self._register_variable_definition(
                        name.value, type_spec, statement_token.line, statement_token.position
                    )
                    return DefineStatement(statement_token, name, type_spec, None)

            # Need additional recovery if we didn't find a type
            if not isinstance(error_stmt, ErrorStatement):
                # This shouldn't happen, but handle it just in case
                skipped = self._panic_recovery()
                return ErrorStatement(
                    token=statement_token,
                    skipped_tokens=skipped,
                    message=f"Expected 'as' after variable name '{name.value}'",
                )
            return error_stmt

        # Move past "as"
        self._advance_tokens()

        # Parse type specification
        type_spec = self._parse_type_spec()
        if not type_spec:
            # Get the invalid type name token
            invalid_name = self._current_token.literal if self._current_token else "unknown"
            # Generate valid types list from TYPING_MAP
            valid_types = list(TYPING_MAP.values())
            return self._report_error_and_recover(
                template=INVALID_TYPE_NAME,
                name=invalid_name,
                valid_types=", ".join(valid_types),
                expected_token=TokenType.KW_TEXT,  # Use TEXT as representative type
                expected="type name",
                after="'as'",
            )

        # Optional: (default: value) clause
        initial_value = None
        if self._current_token and self._current_token.type == TokenType.DELIM_LPAREN:
            self._advance_tokens()  # Move past "("

            # Expect "default" - we should be at "default" now
            if not self._current_token or self._current_token.type != TokenType.KW_DEFAULT:
                # Report error and handle recovery to closing paren
                error_stmt = self._report_error_and_recover(
                    template=EXPECTED_TOKEN_AFTER,
                    expected_token=TokenType.KW_DEFAULT,
                    expected="'default'",
                    after="'('",
                    recovery_tokens=[TokenType.DELIM_RPAREN, TokenType.PUNCT_PERIOD, TokenType.MISC_EOF],
                )
                # If we found the closing paren, advance past it
                if self._current_token and self._current_token.type == TokenType.DELIM_RPAREN:
                    self._advance_tokens()
                return error_stmt

            # Move past "default"
            self._advance_tokens()

            # Expect ":" - we should be at ":"
            if not self._current_token or self._current_token.type != TokenType.PUNCT_COLON:
                # Report error and handle recovery to closing paren
                error_stmt = self._report_error_and_recover(
                    template=EXPECTED_TOKEN_AFTER,
                    expected_token=TokenType.PUNCT_COLON,
                    expected="':'",
                    after="'default'",
                    recovery_tokens=[TokenType.DELIM_RPAREN, TokenType.PUNCT_PERIOD, TokenType.MISC_EOF],
                )
                # If we found the closing paren, advance past it
                if self._current_token and self._current_token.type == TokenType.DELIM_RPAREN:
                    self._advance_tokens()
                return error_stmt

            # Move past ":"
            self._advance_tokens()

            # Parse the default value expression
            initial_value = self._parse_expression(Precedence.LOWEST)

            # Expect ")" - check if we're at the closing paren
            if self._peek_token and self._peek_token.type != TokenType.DELIM_RPAREN:
                # Report error but don't return - continue to create the statement
                self._report_error_and_recover(
                    template=EXPECTED_TOKEN_AFTER,
                    expected_token=TokenType.DELIM_RPAREN,
                    expected="')'",
                    after="default value",
                    skip_recovery=True,  # Don't recover, continue processing
                )
            elif self._peek_token:
                self._advance_tokens()  # Move to ")"
                self._advance_tokens()  # Skip ")"

        # Check for period at statement end (optional for now)
        if self._peek_token and self._peek_token.type == TokenType.PUNCT_PERIOD:
            self._advance_tokens()  # Move to period

        # Register the variable definition in the symbol table
        self._register_variable_definition(name.value, type_spec, statement_token.line, statement_token.position)

        return DefineStatement(statement_token, name, type_spec, initial_value)

    def _parse_type_spec(self) -> list[str]:
        """Parse type specification, handling union types.

        Grammar:
            type_spec ::= type_name ["or" type_name]*
            type_name ::= "Text" | "Whole Number" | "Float" | "Number" | "Yes/No"
                        | "URL" | "Date" | "DateTime" | "Time" | "List" | "Empty"

        Examples:
            Whole Number -> ["Whole Number"]
            Whole Number or Text -> ["Whole Number", "Text"]
            Number or Yes/No or Empty -> ["Number", "Yes/No", "Empty"]

        Returns:
            List of type names, empty list if no valid type found.
        """
        types = []

        # Parse first type
        type_name = self._parse_type_name()
        if type_name:
            types.append(type_name)
        else:
            return types  # Return empty list if no type found

        # Parse additional types with "or" (for union types)
        while self._current_token and self._current_token.type == TokenType.KW_OR:
            self._advance_tokens()  # Skip "or"

            type_name = self._parse_type_name()
            if type_name:
                types.append(type_name)
            else:
                # If we don't find a type after "or", that's an error
                self._report_error_and_recover(
                    template=EXPECTED_TOKEN_AFTER,
                    expected_token=TokenType.KW_TEXT,  # Use TEXT as representative
                    expected="type name",
                    after="'or'",
                    skip_recovery=True,  # Continue with what we have
                )
                break

        return types

    def _parse_type_name(self) -> str | None:
        """Parse a single type name.

        Only handles keyword-based types as specified in the grammar.

        Returns:
            The type name as a string, or None if current token is not a type.
        """
        if not self._current_token:
            return None

        if self._current_token.type in TYPING_MAP:
            type_name = TYPING_MAP[self._current_token.type]
            self._advance_tokens()
            return type_name

        return None

    def _parse_set_statement(self) -> SetStatement | ErrorStatement | Statement:
        """Parse a Set statement.

        Expects:
        - Set `identifier` to expression
        - Set the second item of `list` to expression
        - Set item _5_ of `list` to expression

        Returns:
            A SetStatement AST node if successful, ErrorStatement if parsing fails.
        """
        from machine_dialect.ast.statements import CollectionMutationStatement

        assert self._current_token is not None
        statement_token = self._current_token  # Save the 'Set' token

        # Check for collection item assignment patterns
        # We need to handle both "Set the first item of" and "Set item _1_ of"
        if self._peek_token:
            # Since stopwords are auto-skipped, after "Set" we might be directly at "first"/"second" etc
            # if the user wrote "Set the first..." because "the" gets skipped
            if self._peek_token.type in (
                TokenType.KW_FIRST,
                TokenType.KW_SECOND,
                TokenType.KW_THIRD,
                TokenType.KW_LAST,
            ):
                # Pattern: Set [the] [ordinal] item of `list` to value
                # "the" was already skipped if present
                self._advance_tokens()  # Move to ordinal

                # We're now at the ordinal
                if not self._current_token or self._current_token.type not in (
                    TokenType.KW_FIRST,
                    TokenType.KW_SECOND,
                    TokenType.KW_THIRD,
                    TokenType.KW_LAST,
                ):
                    return ErrorStatement(
                        token=statement_token, message="Expected ordinal (first, second, third, last)"
                    )

                ordinal = self._current_token.literal.lower()
                self._advance_tokens()  # Move past ordinal

                # Expect "item"
                if self._current_token and self._current_token.type == TokenType.KW_ITEM:
                    self._advance_tokens()  # Move past 'item'

                # Expect "of"
                if self._current_token and self._current_token.type == TokenType.KW_OF:
                    self._advance_tokens()  # Move past 'of'

                # Parse collection identifier
                collection = self._parse_identifier_or_keyword_as_identifier()
                if not collection:
                    error_stmt = self._report_error_and_recover(
                        template=EXPECTED_TOKEN,
                        expected_token=TokenType.MISC_IDENT,
                        token="collection identifier",
                        got_token_type=self._current_token.type.name if self._current_token else "EOF",
                    )
                    assert isinstance(error_stmt, ErrorStatement)
                    return error_stmt
                self._advance_tokens()

                # Expect "to"
                if self._current_token and self._current_token.type == TokenType.KW_TO:
                    self._advance_tokens()

                # Parse the value
                value = self._parse_expression(Precedence.LOWEST)
                self._advance_tokens()

                # Expect period
                if self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
                    if error := self._expect_token(TokenType.PUNCT_PERIOD):
                        assert isinstance(error, ErrorStatement)
                        return error

                return CollectionMutationStatement(
                    token=statement_token,
                    operation="set",
                    collection=collection,
                    value=value,
                    position=ordinal,
                    position_type="ordinal",
                )

            elif self._peek_token.type == TokenType.KW_ITEM:
                # Pattern: Set item _5_ of `list` to value
                self._advance_tokens()  # Move to 'item'
                self._advance_tokens()  # Move past 'item'

                # Parse numeric index
                index = self._parse_expression(Precedence.LOWEST)
                self._advance_tokens()

                # Expect "of"
                if self._current_token and self._current_token.type == TokenType.KW_OF:
                    self._advance_tokens()

                # Parse collection identifier
                collection = self._parse_identifier_or_keyword_as_identifier()
                if not collection:
                    error_stmt = self._report_error_and_recover(
                        template=EXPECTED_TOKEN,
                        expected_token=TokenType.MISC_IDENT,
                        token="collection identifier",
                        got_token_type=self._current_token.type.name if self._current_token else "EOF",
                    )
                    assert isinstance(error_stmt, ErrorStatement)
                    return error_stmt
                self._advance_tokens()

                # Expect "to"
                if self._current_token and self._current_token.type == TokenType.KW_TO:
                    self._advance_tokens()

                # Parse the value
                value = self._parse_expression(Precedence.LOWEST)
                self._advance_tokens()

                # Expect period
                if self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
                    if error := self._expect_token(TokenType.PUNCT_PERIOD):
                        assert isinstance(error, ErrorStatement)
                        return error

                return CollectionMutationStatement(
                    token=statement_token,
                    operation="set",
                    collection=collection,
                    value=value,
                    position=index,
                    position_type="numeric",
                )

        # Normal Set statement: Set `identifier` to expression
        let_statement = SetStatement(token=statement_token)

        # Expect identifier (which may have come from backticks)
        if error := self._expect_token(TokenType.MISC_IDENT, "'Set'"):
            assert isinstance(error, ErrorStatement)
            return error

        # Use the identifier value directly (backticks already stripped by lexer)
        let_statement.name = self._parse_identifier()

        # Variables MUST be defined before use - no exceptions
        variable_defined = self._check_variable_defined(
            let_statement.name.value, let_statement.name.token.line, let_statement.name.token.position
        )

        # Check for "to" or "using" keyword
        assert self._peek_token is not None
        used_using = False  # Track if we used the 'using' branch
        if self._peek_token.type == TokenType.KW_TO:
            # Standard assignment: Set x to value
            self._advance_tokens()  # Move to 'to'

            # Check if this is a list definition (colon after 'to')
            # After advancing, peek_token is now the next token
            next_token_type: TokenType | None = self._peek_token.type if self._peek_token else None
            if next_token_type == TokenType.PUNCT_COLON:
                # This will be a list - set context NOW before advancing
                # This ensures the dash tokens after the colon are properly tokenized
                if self._token_buffer:
                    self._token_buffer.set_list_context(True)

                self._advance_tokens()  # Move past 'to' to the colon

                # Advance past the colon to get to the first list item
                self._advance_tokens()

                # Parse the list - current token should now be the first list item marker
                let_statement.value = self._parse_list_literal()

                # Disable list context after parsing
                if self._token_buffer:
                    self._token_buffer.set_list_context(False)

                # After parsing a list, we're already properly positioned
                # (either at EOF, a period, or the next statement)
                # Set a flag to skip the advance and period check
                used_using = True  # Reuse this flag to skip advance/period check
            else:
                # Not a list, advance past 'to' and parse expression normally
                self._advance_tokens()  # Move past 'to'

                # Check for "blank" keyword for empty collections
                if self._current_token and self._current_token.type == TokenType.KW_BLANK:
                    from machine_dialect.ast import BlankLiteral

                    let_statement.value = BlankLiteral(self._current_token)
                    # Don't advance here - let the normal flow handle it
                else:
                    # Parse the value expression normally
                    let_statement.value = self._parse_expression()

        elif self._peek_token.type == TokenType.KW_USING:
            # Function call assignment: Set x using function_name
            self._advance_tokens()  # Move to 'using'
            self._advance_tokens()  # Move past 'using'
            # Parse a function call (similar to Use statement but returns the value)
            func_call = self._parse_function_call_expression()
            # CallExpression is an Expression, so this is valid
            let_statement.value = func_call
            # Note: _parse_function_call_expression already leaves us at the period,
            # so we'll skip the advance_tokens() call below for this branch
            used_using = True
        else:
            # Report the error using unified error handling
            assert self._peek_token is not None
            error_stmt = self._report_error_and_recover(
                template=EXPECTED_TOKEN,
                expected_token=TokenType.KW_TO,
                token="'to' or 'using' keyword",
                got_token_type=self._peek_token.type.name if self._peek_token else "EOF",
            )
            assert isinstance(error_stmt, ErrorStatement)
            return error_stmt

        # Advance past the last token of the expression
        # Expression parsing leaves us at the last token, not after it
        # BUT: the 'using' branch already leaves us at the period, so skip this
        if not used_using:
            self._advance_tokens()

        # Type-check the assignment if the variable is defined
        if variable_defined and let_statement.value and not isinstance(let_statement.value, ErrorExpression):
            self._validate_assignment_type(
                let_statement.name.value,
                let_statement.value,
                let_statement.name.token.line,
                let_statement.name.token.position,
            )

        # If the expression failed, skip to synchronization point
        if isinstance(let_statement.value, ErrorExpression):
            # Skip remaining tokens until we're at a period or EOF
            while self._current_token is not None and self._current_token.type not in (
                TokenType.PUNCT_PERIOD,
                TokenType.MISC_EOF,
            ):
                self._advance_tokens()

        # Require trailing period if not at EOF or if we're in a block
        # But if we're already at a period (after error recovery), don't expect another
        assert self._peek_token is not None
        if self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
            # Already at period, no need to expect one
            pass
        elif self._peek_token.type != TokenType.MISC_EOF or self._block_depth > 0:
            if error := self._expect_token(TokenType.PUNCT_PERIOD):
                assert isinstance(error, ErrorStatement)
                return error

        return let_statement

    def _parse_return_statement(self) -> ReturnStatement | ErrorStatement:
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

        # Advance past the last token of the expression
        # Expression parsing leaves us at the last token, not after it
        self._advance_tokens()

        # If the expression failed, don't require a period since we're already in error recovery
        if not isinstance(return_statement.return_value, ErrorExpression):
            # Require trailing period if not at EOF or if we're in a block
            # But if we're already at a period (after error recovery), don't expect another
            assert self._peek_token is not None
            if self._current_token and self._current_token.type == TokenType.PUNCT_PERIOD:
                # Already at period, no need to expect one
                pass
            elif self._peek_token.type != TokenType.MISC_EOF or self._block_depth > 0:
                if error := self._expect_token(TokenType.PUNCT_PERIOD):
                    assert isinstance(error, ErrorStatement)
                    return error

        return return_statement

    def _parse_say_statement(self) -> SayStatement | ErrorStatement:
        """Parse a Say or Tell statement.

        Syntax: Say <expression>. or Tell <expression>.

        Returns:
            A SayStatement AST node.
        """
        assert self._current_token is not None
        assert self._current_token.type in (TokenType.KW_SAY, TokenType.KW_TELL)

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
        elif self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
            if error := self._expect_token(TokenType.PUNCT_PERIOD):
                assert isinstance(error, ErrorStatement)
                return error

        return say_statement

    def _parse_collection_mutation_statement(self) -> Statement:
        """Parse a collection mutation statement.

        Handles:
        - Add _value_ to `list`.
        - Remove _value_ from `list`.
        - Set the second item of `list` to _value_.
        - Set item _5_ of `list` to _value_.
        - Insert _value_ at position _3_ in `list`.
        - Empty `list`.

        Returns:
            A CollectionMutationStatement AST node.
        """
        from machine_dialect.ast.statements import CollectionMutationStatement

        assert self._current_token is not None
        start_token = self._current_token
        operation = start_token.literal.lower()

        # Move past the operation keyword
        self._advance_tokens()

        if operation == "add":
            # Two syntaxes:
            # 1. Add _value_ to `list`. (for arrays)
            # 2. Add "key" to `dict` with value _value_. (for named lists)

            # Parse the first value/key
            first_value = self._parse_expression(Precedence.LOWEST)
            self._advance_tokens()

            # Skip "to"
            if self._current_token and self._current_token.type == TokenType.KW_TO:
                self._advance_tokens()

            # Parse the collection
            collection = self._parse_identifier_or_keyword_as_identifier()
            if not collection:
                error_stmt = self._report_error_and_recover(
                    template=EXPECTED_IDENTIFIER_AFTER,
                    expected_token=TokenType.MISC_IDENT,
                    what="collection",
                    after="'Add ... to'",
                )
                assert isinstance(error_stmt, ErrorStatement)
                return error_stmt
            self._advance_tokens()

            # Check if this is dictionary syntax (with value)
            current_token_type = self._current_token.type if self._current_token else None
            if current_token_type == TokenType.KW_WITH:
                self._advance_tokens()

                # Skip "value" if present
                if self._current_token and self._current_token.type == TokenType.KW_VALUE:
                    self._advance_tokens()

                # Parse the actual value
                dict_value = self._parse_expression(Precedence.LOWEST)
                self._advance_tokens()

                # Expect period
                if self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
                    if error := self._expect_token(TokenType.PUNCT_PERIOD):
                        assert isinstance(error, ErrorStatement)
                        return error

                return CollectionMutationStatement(
                    token=start_token,
                    operation="add",
                    collection=collection,
                    value=dict_value,
                    position=first_value,  # The key
                    position_type="key",
                )
            else:
                # Regular array syntax
                # Expect period
                if self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
                    if error := self._expect_token(TokenType.PUNCT_PERIOD):
                        assert isinstance(error, ErrorStatement)
                        return error

                return CollectionMutationStatement(
                    token=start_token,
                    operation="add",
                    collection=collection,
                    value=first_value,
                )

        elif operation == "remove":
            # Two syntaxes:
            # 1. Remove _value_ from `list`. (for arrays - removes by value)
            # 2. Remove "key" from `dict`. (for named lists - removes by key)
            # Note: The semantic analyzer will determine which one based on collection type

            value = self._parse_expression(Precedence.LOWEST)
            self._advance_tokens()

            # Skip "from"
            if self._current_token and self._current_token.type == TokenType.KW_FROM:
                self._advance_tokens()

            # Parse the collection
            collection = self._parse_identifier_or_keyword_as_identifier()
            if not collection:
                return ErrorStatement(
                    token=start_token, message="Expected collection identifier after 'Remove ... from'"
                )
            self._advance_tokens()

            # Expect period
            if self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
                if error := self._expect_token(TokenType.PUNCT_PERIOD):
                    assert isinstance(error, ErrorStatement)
                    return error

            return CollectionMutationStatement(
                token=start_token,
                operation="remove",
                collection=collection,
                value=value,
            )

        elif operation == "insert":
            # Insert _value_ at position _3_ in `list`.
            value = self._parse_expression(Precedence.LOWEST)
            self._advance_tokens()

            # Skip "at"
            if self._current_token and self._current_token.literal and self._current_token.literal.lower() == "at":
                self._advance_tokens()

            # Skip "position" if present
            if self._current_token and self._current_token.literal.lower() == "position":
                self._advance_tokens()

            # Parse the position (should be a number)
            position = self._parse_expression(Precedence.LOWEST)
            self._advance_tokens()

            # Skip "in"
            if self._current_token and self._current_token.type == TokenType.KW_IN:
                self._advance_tokens()

            # Parse the collection
            collection = self._parse_identifier_or_keyword_as_identifier()
            if not collection:
                return ErrorStatement(
                    token=start_token, message="Expected collection identifier after 'Insert ... at position ... in'"
                )
            self._advance_tokens()

            # Expect period
            if self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
                if error := self._expect_token(TokenType.PUNCT_PERIOD):
                    assert isinstance(error, ErrorStatement)
                    return error

            return CollectionMutationStatement(
                token=start_token,
                operation="insert",
                collection=collection,
                value=value,
                position=position,
                position_type="numeric",
            )

        elif operation == "clear":
            # Clear `collection`.
            # Parse the collection identifier
            collection = self._parse_identifier_or_keyword_as_identifier()
            if not collection:
                error_stmt = self._report_error_and_recover(
                    template=EXPECTED_IDENTIFIER_AFTER,
                    expected_token=TokenType.MISC_IDENT,
                    what="collection",
                    after="'Clear'",
                )
                assert isinstance(error_stmt, ErrorStatement)
                return error_stmt

            # Advance past the identifier to check for period
            self._advance_tokens()

            # Expect period
            if self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
                if error := self._expect_token(TokenType.PUNCT_PERIOD):
                    assert isinstance(error, ErrorStatement)
                    return error

            return CollectionMutationStatement(
                token=start_token,
                operation="clear",
                collection=collection,
            )

        elif operation == "update":
            # Update "key" in `dict` to _value_.
            # Parse the key (should be a string literal)
            key = self._parse_expression(Precedence.LOWEST)
            self._advance_tokens()

            # Skip "in"
            if self._current_token and self._current_token.type == TokenType.KW_IN:
                self._advance_tokens()

            # Parse the collection
            collection = self._parse_identifier_or_keyword_as_identifier()
            if not collection:
                error_stmt = self._report_error_and_recover(
                    template=EXPECTED_IDENTIFIER_AFTER,
                    expected_token=TokenType.MISC_IDENT,
                    what="collection",
                    after="'Update ... in'",
                )
                assert isinstance(error_stmt, ErrorStatement)
                return error_stmt
            self._advance_tokens()

            # Skip "to"
            if self._current_token and self._current_token.type == TokenType.KW_TO:
                self._advance_tokens()

            # Parse the value
            value = self._parse_expression(Precedence.LOWEST)
            self._advance_tokens()

            # Expect period
            if self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
                if error := self._expect_token(TokenType.PUNCT_PERIOD):
                    assert isinstance(error, ErrorStatement)
                    return error

            return CollectionMutationStatement(
                token=start_token,
                operation="update",
                collection=collection,
                value=value,
                position=key,  # Using position field to store the key
                position_type="key",
            )

        # Should not reach here
        error_stmt = self._report_error_and_recover(
            template=UNHANDLED_OPERATION, what="collection mutation", operation=operation
        )
        assert isinstance(error_stmt, ErrorStatement)
        return error_stmt

    def _parse_function_call_expression(self) -> Expression:
        """Parse a function call as an expression (for use with 'using' in Set statements).

        Syntax: function_name [with <arguments>] or function_name [where <named arguments>].

        Returns:
            A CallExpression AST node that will be evaluated as an expression.
        """
        assert self._current_token is not None

        # Parse the function name (must be an identifier in backticks)
        if self._current_token and self._current_token.type == TokenType.MISC_IDENT:
            function_name = Identifier(self._current_token, self._current_token.literal)
            call_token = self._current_token
            self._advance_tokens()
        else:
            # Error: expected identifier for function name
            result = self._report_error_and_recover(
                template=EXPECTED_FUNCTION_NAME,
                token_type=str(self._current_token.type) if self._current_token else "EOF",
                skip_recovery=True,
                is_expression=True,
            )
            assert isinstance(result, ErrorExpression)
            return result

        # Create the CallExpression
        call_expression = CallExpression(token=call_token, function_name=function_name)

        # Check for arguments
        if self._current_token and self._current_token.type == TokenType.KW_WITH:
            # Positional arguments
            with_token = self._current_token
            self._advance_tokens()
            call_expression.arguments = self._parse_positional_arguments(with_token)
        elif self._current_token and self._current_token.type == TokenType.KW_WHERE:
            # Named arguments
            where_token = self._current_token
            self._advance_tokens()
            call_expression.arguments = self._parse_named_arguments(where_token)

        return call_expression

    def _parse_call_statement(self) -> CallStatement | ErrorStatement:
        """Parse a Use statement.

        Syntax: use <function> [with <arguments>] or use <function> [where <named arguments>].

        Returns:
            A CallStatement AST node.
        """
        assert self._current_token is not None
        assert self._current_token.type == TokenType.KW_USE

        statement_token = self._current_token

        # Move past 'use'
        self._advance_tokens()

        # Parse the function name (must be an identifier in backticks)
        if self._current_token and self._current_token.type == TokenType.MISC_IDENT:
            function_name = Identifier(self._current_token, self._current_token.literal)
            self._advance_tokens()
        else:
            # Record error for missing or invalid function name
            error_token = self._current_token or Token(TokenType.MISC_EOF, "", 0, 0)
            self._report_error_and_recover(
                template=EXPECTED_FUNCTION_NAME,
                token_type=str(error_token.type),
                skip_recovery=True,  # Continue parsing to find more errors
            )
            function_name = None

        # Check for 'with' or 'where' keyword for arguments
        arguments: Arguments | None = None
        if self._current_token and self._current_token.type == TokenType.KW_WITH:
            # 'with' is for positional arguments
            with_token = self._current_token
            self._advance_tokens()  # Move past 'with'

            # Parse positional arguments
            arguments = self._parse_positional_arguments(with_token)

        elif self._current_token and self._current_token.type == TokenType.KW_WHERE:
            # 'where' is for named arguments
            where_token = self._current_token
            self._advance_tokens()  # Move past 'where'

            # Parse named arguments
            arguments = self._parse_named_arguments(where_token)

        # Create the Call statement
        call_statement = CallStatement(statement_token, function_name, arguments)

        # Expect a period at the end
        if self._peek_token and self._peek_token.type == TokenType.PUNCT_PERIOD:
            self._advance_tokens()
        # But if we're already at a period (after error recovery), don't expect another
        elif self._current_token and self._current_token.type != TokenType.PUNCT_PERIOD:
            if error := self._expect_token(TokenType.PUNCT_PERIOD):
                assert isinstance(error, ErrorStatement)
                return error

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
        elif token.type == TokenType.LIT_WHOLE_NUMBER:
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
        elif token.type in (TokenType.LIT_YES, TokenType.LIT_NO):
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
            self._report_error_and_recover(
                template=INVALID_ARGUMENT_VALUE,
                literal=token.literal,
                skip_recovery=True,  # We'll handle advancement manually
            )
            self._advance_tokens()  # Skip the invalid token
            return None

    def _parse_positional_arguments(self, with_token: Token) -> Arguments:
        """Parse positional arguments after 'with' keyword.

        Syntax: with _value1_, _value2_

        Returns:
            An Arguments AST node with positional arguments.
        """
        arguments = Arguments(with_token)

        while self._current_token and self._current_token.type not in (
            TokenType.PUNCT_PERIOD,
            TokenType.MISC_EOF,
        ):
            # Parse argument value
            value = self._parse_argument_value()
            if value:
                arguments.positional.append(value)

            # Check for comma (optional)
            if self._current_token and self._current_token.type == TokenType.PUNCT_COMMA:
                self._advance_tokens()
            # Check for 'and' (optional)
            elif self._current_token and self._current_token.type == TokenType.KW_AND:
                self._advance_tokens()
            # If no comma or 'and', and we're not at the end, check if another argument follows
            elif self._current_token and self._current_token.type not in (
                TokenType.PUNCT_PERIOD,
                TokenType.MISC_EOF,
            ):
                # Check if this looks like another argument (identifier or literal)
                if self._current_token.type in (
                    TokenType.MISC_IDENT,
                    TokenType.LIT_WHOLE_NUMBER,
                    TokenType.LIT_FLOAT,
                    TokenType.LIT_TEXT,
                    TokenType.LIT_YES,
                    TokenType.LIT_NO,
                    TokenType.KW_EMPTY,
                ):
                    # Report error but continue parsing (error recovery)
                    self._report_error_and_recover(
                        template=MISSING_COMMA_BETWEEN_ARGS,
                        skip_recovery=True,  # Continue parsing the next argument
                    )
                    continue
                else:
                    # Not an argument, stop parsing
                    break

        return arguments

    def _parse_named_arguments(self, where_token: Token) -> Arguments:
        """Parse named arguments after 'where' keyword.

        Syntax: where `param1` is _value1_, `param2` is _value2_

        Returns:
            An Arguments AST node with named arguments.
        """
        arguments = Arguments(where_token)

        while self._current_token and self._current_token.type not in (
            TokenType.PUNCT_PERIOD,
            TokenType.MISC_EOF,
        ):
            # Parse parameter name (should be an identifier in backticks)
            name_expr: Identifier | None = None
            if self._current_token and self._current_token.type == TokenType.MISC_IDENT:
                name_expr = Identifier(self._current_token, self._current_token.literal)
                self._advance_tokens()
            else:
                # Error: expected identifier
                self._report_error_and_recover(
                    template=EXPECTED_TOKEN,
                    expected_token=TokenType.MISC_IDENT,
                    skip_recovery=True,
                    token="parameter name",
                    got_token_type=self._current_token.type.name if self._current_token else "EOF",
                )
                break

            # Expect 'is' keyword - mypy doesn't realize _advance_tokens() changes _current_token
            assert self._current_token is not None  # Help mypy understand
            if self._current_token.type == TokenType.KW_IS:
                self._advance_tokens()
            else:
                self._report_error_and_recover(
                    template=EXPECTED_TOKEN_AFTER,
                    expected_token=TokenType.KW_IS,
                    skip_recovery=True,
                    expected="'is' keyword",
                    after="parameter name",
                )
                break

            # Parse the value
            value = self._parse_argument_value()

            # Add to named arguments if both name and value are valid
            if name_expr and value:
                arguments.named.append((name_expr, value))

            # Check for comma (optional)
            if self._current_token and self._current_token.type == TokenType.PUNCT_COMMA:
                self._advance_tokens()
            # Check for 'and' (optional)
            elif self._current_token and self._current_token.type == TokenType.KW_AND:
                self._advance_tokens()
            # If no comma or 'and', and we're not at the end, break
            elif self._current_token and self._current_token.type not in (
                TokenType.PUNCT_PERIOD,
                TokenType.MISC_EOF,
            ):
                break

        return arguments

    def _parse_if_statement(self) -> IfStatement | ErrorStatement:
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

        # Check for optional comma before 'then'
        if self._peek_token and self._peek_token.type == TokenType.PUNCT_COMMA:
            self._advance_tokens()  # Skip the comma

        # Check for optional 'then' keyword
        if self._peek_token and self._peek_token.type == TokenType.KW_THEN:
            self._advance_tokens()  # Move to 'then'

        # Expect colon
        if error := self._expect_token(TokenType.PUNCT_COLON, "if condition"):
            assert isinstance(error, ErrorStatement)
            return error

        # Parse the consequence block
        # If we're inside a block, nested if statements should have deeper blocks
        expected_depth = self._block_depth + 1
        if_statement.consequence = self._parse_block_statement(expected_depth)

        # Check if the consequence block is empty - this is an error
        if not if_statement.consequence or len(if_statement.consequence.statements) == 0:
            self._report_error_and_recover(
                template=EMPTY_IF_CONSEQUENCE,
                skip_recovery=True,  # No recovery needed, continue parsing
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
                self._report_error_and_recover(
                    template=EMPTY_ELSE_BLOCK,
                    skip_recovery=True,  # No recovery needed, continue parsing
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

    def _parse_while_statement(self) -> WhileStatement | ErrorStatement:
        """Parse a while loop statement.

        Expects: while <condition>: <block>

        Returns:
            A WhileStatement AST node.
        """
        assert self._current_token is not None
        while_statement = WhileStatement(token=self._current_token)

        # Advance past 'while'
        self._advance_tokens()

        # Parse the condition expression
        while_statement.condition = self._parse_expression(Precedence.LOWEST)

        # Expect colon
        if error := self._expect_token(TokenType.PUNCT_COLON, "while condition"):
            assert isinstance(error, ErrorStatement)
            return error

        # Parse the body block
        expected_depth = self._block_depth + 1
        while_statement.body = self._parse_block_statement(expected_depth)

        # Check if the body block is empty - this is an error
        if not while_statement.body or len(while_statement.body.statements) == 0:
            self._report_error_and_recover(
                template=EMPTY_WHILE_BODY,
                skip_recovery=True,  # No recovery needed, continue parsing
            )

        return while_statement

    def _parse_for_each_statement(self) -> ForEachStatement | ErrorStatement:
        """Parse a for-each loop statement.

        Expects: for each <item> in <collection>: <block>

        Returns:
            A ForEachStatement AST node.
        """
        assert self._current_token is not None
        for_statement = ForEachStatement(token=self._current_token)

        # Advance past 'for'
        self._advance_tokens()

        # Expect 'each'
        if self._current_token and self._current_token.type != TokenType.KW_EACH:
            if error := self._expect_token(TokenType.KW_EACH, "'for' keyword"):
                assert isinstance(error, ErrorStatement)
                return error
        self._advance_tokens()  # Move past 'each'

        # Parse the loop variable (item)
        for_statement.item = self._parse_identifier_or_keyword_as_identifier()
        if not for_statement.item:
            error_stmt = self._report_error_and_recover(
                template=EXPECTED_IDENTIFIER_AFTER,
                context="'each'",
                skip_recovery=True,
            )
            assert isinstance(error_stmt, ErrorStatement)
            return error_stmt
        self._advance_tokens()

        # Expect 'in'
        if self._current_token and self._current_token.type != TokenType.KW_IN:
            if error := self._expect_token(TokenType.KW_IN, "loop variable"):
                assert isinstance(error, ErrorStatement)
                return error
        self._advance_tokens()  # Move past 'in'

        # Parse the collection expression
        for_statement.collection = self._parse_expression(Precedence.LOWEST)

        # Expect colon
        if error := self._expect_token(TokenType.PUNCT_COLON, "for-each header"):
            assert isinstance(error, ErrorStatement)
            return error

        # Parse the body block
        expected_depth = self._block_depth + 1
        for_statement.body = self._parse_block_statement(expected_depth)

        # Check if the body block is empty - this is an error
        if not for_statement.body or len(for_statement.body.statements) == 0:
            self._report_error_and_recover(
                template=EMPTY_FOR_EACH_BODY,
                skip_recovery=True,  # No recovery needed, continue parsing
            )

        return for_statement

    def _parse_action_interaction_or_utility(
        self,
    ) -> ActionStatement | InteractionStatement | UtilityStatement | ErrorStatement:
        """Parse an Action, Interaction, or Utility statement.

        Expected format:
        ### **Action**: `name`
        or
        ### **Interaction**: `name`
        or
        ### **Utility**: `name`

        <details>
        <summary>Description</summary>
        > statements
        </details>

        Returns:
            ActionStatement, InteractionStatement, or UtilityStatement node, or ErrorStatement if parsing fails.
        """
        assert self._current_token is not None
        assert self._current_token.type == TokenType.PUNCT_HASH_TRIPLE

        # Save the ### token for the statement
        # hash_token = self._current_token  # Currently unused, but may be needed for error reporting

        # Move past ###
        self._advance_tokens()

        # Expect **Action**, **Interaction**, or **Utility** (wrapped keyword)
        if not self._current_token or self._current_token.type not in (
            TokenType.KW_ACTION,
            TokenType.KW_INTERACTION,
            TokenType.KW_UTILITY,
        ):
            error_stmt = self._report_error_and_recover(
                template=EXPECTED_TOKEN_AFTER, expected="**Action**, **Interaction**, or **Utility**", after="###"
            )
            assert isinstance(error_stmt, ErrorStatement)
            return error_stmt

        statement_type = self._current_token.type
        keyword_token = self._current_token

        # Move past Action/Interaction/Utility keyword
        self._advance_tokens()

        # Expect colon - should be at current position
        if not self._current_token or self._current_token.type != TokenType.PUNCT_COLON:
            error_stmt = self._report_error_and_recover(
                template=EXPECTED_TOKEN_AFTER,
                expected_token=TokenType.PUNCT_COLON,
                expected="':'",
                after="Action/Interaction/Utility",
            )
            assert isinstance(error_stmt, ErrorStatement)
            return error_stmt

        # Move past colon
        self._advance_tokens()

        # Expect backtick-wrapped name
        if not self._current_token or self._current_token.type != TokenType.MISC_IDENT:
            return self._report_error_and_recover(
                template=EXPECTED_TOKEN, expected_token=TokenType.MISC_IDENT, token="identifier in backticks for name"
            )

        name = Identifier(self._current_token, self._current_token.literal)
        self._advance_tokens()

        # Now expect <details> tag - should be at current position
        if not self._current_token or self._current_token.type != TokenType.TAG_DETAILS_START:
            return self._report_error_and_recover(
                template=EXPECTED_TOKEN,
                token="<details> tag",
                got_token_type=self._current_token.type.name if self._current_token else "EOF",
            )

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
                # Check if this is likely a missing depth transition issue
                if self._current_token.type == TokenType.KW_RETURN and self._block_depth > 0:
                    # This looks like a "Give back" statement after nested blocks
                    # The user likely forgot to add a transition line
                    nested_depth = ">" * (self._block_depth + 1)  # The depth they were at (e.g., >>)
                    parent_depth = ">" * self._block_depth  # The depth they need to transition to (e.g., >)
                    self._report_error_and_recover(
                        template=MISSING_DEPTH_TRANSITION,
                        nested_depth=nested_depth,
                        parent_depth=parent_depth,
                        token_type=self._current_token.type.name,
                        skip_recovery=True,  # Continue parsing
                    )
                else:
                    self._report_error_and_recover(
                        template=EXPECTED_DETAILS_CLOSE,
                        token_type=self._current_token.type.name,
                        skip_recovery=True,  # Continue parsing
                    )

        # Check for parameter sections (#### Inputs: and #### Outputs:)
        inputs: list[Parameter] = []
        outputs: list[Parameter] = []

        # Check if we have #### for parameter sections
        if self._current_token and self._current_token.type == TokenType.PUNCT_HASH_QUAD:
            # Parse parameter sections
            inputs, outputs = self._parse_parameter_sections()

        # Create and return the appropriate statement
        if statement_type == TokenType.KW_ACTION:
            return ActionStatement(
                keyword_token, name, inputs=inputs, outputs=outputs, body=body, description=description
            )
        elif statement_type == TokenType.KW_INTERACTION:
            return InteractionStatement(
                keyword_token, name, inputs=inputs, outputs=outputs, body=body, description=description
            )
        elif statement_type == TokenType.KW_UTILITY:
            return UtilityStatement(
                keyword_token, name, inputs=inputs, outputs=outputs, body=body, description=description
            )
        else:
            # This should never happen since we check for valid types above
            return self._report_error_and_recover(template=UNEXPECTED_STATEMENT, type=statement_type)

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

                # TODO: Fix bug where statements after nested if blocks (e.g., after `> >`)
                #  are not properly parsed as part of the parent block. Currently requires
                #  an empty `>` line after the nested block to continue parsing correctly.
                #  Example issue:
                #    > If condition then:
                #    > > Give back value.
                #    > Set `var` to _1_.  # This line may not be parsed correctly
                #  Example working code:
                #    > If condition then:
                #    > > Give back value.
                #    >
                #    > Set `var` to _1_.  # This line may now be parsed correctly
                #  We expect both example codes to be working

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
                self._report_error_and_recover(
                    template=UNEXPECTED_BLOCK_DEPTH,
                    expected=str(expected_depth),
                    actual=str(current_depth),
                    skip_recovery=True,  # We'll handle recovery manually
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
            TokenType.OP_CARET: self._parse_infix_expression,
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
            # Dictionary extraction operators
            TokenType.OP_THE_NAMES_OF: self._parse_dict_extraction_infix,
            TokenType.OP_THE_CONTENTS_OF: self._parse_dict_extraction_infix,
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
            TokenType.LIT_WHOLE_NUMBER: self._parse_integer_literal,
            TokenType.LIT_FLOAT: self._parse_float_literal,
            TokenType.LIT_TEXT: self._parse_string_literal,
            TokenType.LIT_URL: self._parse_url_literal,
            TokenType.LIT_YES: self._parse_boolean_literal,
            TokenType.LIT_NO: self._parse_boolean_literal,
            TokenType.KW_EMPTY: self._parse_empty_literal,
            TokenType.OP_MINUS: self._parse_prefix_expression,
            TokenType.KW_NEGATION: self._parse_prefix_expression,
            TokenType.DELIM_LPAREN: self._parse_grouped_expression,
            # List access patterns
            TokenType.KW_FIRST: self._parse_ordinal_list_access,
            TokenType.KW_SECOND: self._parse_ordinal_list_access,
            TokenType.KW_THIRD: self._parse_ordinal_list_access,
            TokenType.KW_LAST: self._parse_ordinal_list_access,
            TokenType.KW_ITEM: self._parse_numeric_list_access,
            # Handle 'the' stopword for list access
            TokenType.MISC_STOPWORD: self._parse_stopword_expression,
            # Handle possessive syntax
            TokenType.PUNCT_APOSTROPHE_S: self._parse_possessive_access,
            # Dictionary extraction operators can also be prefix
            TokenType.OP_THE_NAMES_OF: self._parse_dict_extraction_prefix,
            TokenType.OP_THE_CONTENTS_OF: self._parse_dict_extraction_prefix,
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
            TokenType.KW_DEFINE: self._parse_define_statement,
            TokenType.KW_SET: self._parse_set_statement,
            TokenType.KW_RETURN: self._parse_return_statement,
            TokenType.KW_IF: self._parse_if_statement,
            TokenType.KW_WHILE: self._parse_while_statement,
            TokenType.KW_FOR: self._parse_for_each_statement,
            TokenType.KW_SAY: self._parse_say_statement,
            TokenType.KW_TELL: self._parse_say_statement,  # Tell is an alias for Say
            TokenType.KW_USE: self._parse_call_statement,
            TokenType.PUNCT_HASH_TRIPLE: self._parse_action_interaction_or_utility,
            TokenType.KW_ADD: self._parse_collection_mutation_statement,
            TokenType.KW_REMOVE: self._parse_collection_mutation_statement,
            TokenType.KW_INSERT: self._parse_collection_mutation_statement,
            TokenType.KW_CLEAR: self._parse_collection_mutation_statement,
            TokenType.KW_UPDATE: self._parse_collection_mutation_statement,
            # Note: KW_EMPTY is not registered here because "empty" as a literal is more common
            # than "Empty `collection`" as a statement. Standalone "empty" will be parsed as an expression.
        }

    def _parse_parameter_sections(self) -> tuple[list[Parameter], list[Output]]:
        """Parse parameter sections (#### Inputs: and #### Outputs:).

        Returns:
            A tuple of (inputs, outputs) - inputs are Parameters, outputs are Outputs.
        """
        inputs: list[Parameter] = []
        outputs: list[Output] = []

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

                        # Parse output list (different format from inputs)
                        outputs = self._parse_output_list()

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

        # Check for (required) or (optional, default: value) or (default: value)
        # TODO: In the future, remove support for explicit required/optional keywords
        # and make it fully implicit based on presence of default value
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

                elif status_token.type == TokenType.KW_DEFAULT:
                    # Handle (default: value) without explicit optional/required
                    # Infer that presence of default means optional
                    is_required = False
                    self._advance_tokens()

                    # Expect colon
                    colon_check = self._current_token
                    if colon_check and colon_check.type == TokenType.PUNCT_COLON:
                        self._advance_tokens()

                        # Parse the default value expression
                        default_value = self._parse_expression(Precedence.LOWEST)

                        # After parsing expression, advance past it
                        self._advance_tokens()

                elif status_token.type == TokenType.KW_REQUIRED:
                    is_required = True
                    self._advance_tokens()
                else:
                    # Unknown token, keep as required
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

    def _parse_output_list(self) -> list[Output]:
        """Parse a list of outputs (lines starting with -).

        Expected format for outputs:
        - `name` **as** Type
        - `name` **as** Type (default: value)

        Returns:
            List of Output objects.
        """
        outputs: list[Output] = []

        while self._current_token and self._current_token.type == TokenType.OP_MINUS:
            # Move past -
            self._advance_tokens()

            # Parse single output
            output = self._parse_output()
            if output:
                outputs.append(output)

        return outputs

    def _parse_output(self) -> Output | None:
        """Parse a single output.

        Expected formats:
        - Returns Type  (simple format)
        - `name` **as** Type
        - `name` **as** Type (default: value)

        Note: Outputs don't have required/optional, only optional defaults.

        Returns:
            An Output object or None if parsing fails.
        """
        if not self._current_token:
            return None

        # Save starting token for error reporting
        start_token = self._current_token

        # Check for simple "Returns Type" format
        if self._current_token.type == TokenType.MISC_IDENT and self._current_token.literal.lower() == "returns":
            self._advance_tokens()

            # Parse type name
            type_name = self._parse_type_name()
            if type_name:
                # Create a simple output with no specific name
                return Output(
                    token=start_token,
                    name=Identifier(start_token, "return_value"),  # Default name
                    type_name=type_name,
                    default_value=EmptyLiteral(start_token),
                )
            else:
                # Failed to parse type, restore position
                return None

        # Otherwise expect identifier in backticks for named output
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

        # Default value (optional)
        default_value: Expression | None = None

        # Check for (default: value)
        paren_token = self._current_token
        if paren_token and paren_token.type == TokenType.DELIM_LPAREN:
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

            # Expect closing paren
            rparen_token = self._current_token
            if rparen_token and rparen_token.type == TokenType.DELIM_RPAREN:
                self._advance_tokens()

        # If no default value was specified, use Empty as the default
        if default_value is None:
            default_value = EmptyLiteral(start_token)

        return Output(
            token=start_token,
            name=name,
            type_name=type_name,
            default_value=default_value,
        )

    def _register_variable_definition(self, name: str, type_spec: list[str], line: int, position: int) -> None:
        """Register a variable definition in the symbol table.

        Args:
            name: Variable name
            type_spec: List of allowed types
            line: Line number
            position: Column position
        """
        try:
            self._symbol_table.define(name, type_spec, line, position)
        except NameError as e:
            # The error message contains info about redefinition
            if "already defined" in str(e):
                # Extract the original definition line from error message
                match = re.search(r"line (\d+)", str(e))
                original_line = int(match.group(1)) if match else line
                self._report_error_and_recover(
                    template=VARIABLE_ALREADY_DEFINED,
                    error_type="name",
                    name=name,
                    original_line=str(original_line),
                    skip_recovery=True,  # No recovery needed for semantic errors
                )
            else:
                # Fallback for other NameError cases
                self._report_error_and_recover(
                    template=NAME_UNDEFINED,
                    error_type="name",
                    name=name,
                    skip_recovery=True,  # No recovery needed for semantic errors
                )

    def _check_variable_defined(self, name: str, line: int, position: int) -> bool:
        """Check if a variable is defined.

        Args:
            name: Variable name
            line: Line number for error reporting
            position: Column position for error reporting

        Returns:
            True if defined, False otherwise
        """
        info = self._symbol_table.lookup(name)
        if not info:
            self._report_error_and_recover(
                template=VARIABLE_NOT_DEFINED,
                error_type="name",
                name=name,
                skip_recovery=True,  # No recovery needed for semantic errors
            )
            return False
        return True

    def _validate_assignment_type(self, variable_name: str, value: Expression, line: int, position: int) -> bool:
        """Validate that an assignment value matches the variable's type.

        Args:
            variable_name: Name of the variable being assigned to
            value: The expression being assigned
            line: Line number for error reporting
            position: Column position for error reporting

        Returns:
            True if type is valid, False otherwise
        """
        # Look up the variable's type specification
        var_info = self._symbol_table.lookup(variable_name)
        if not var_info:
            # Variable not defined - already reported elsewhere
            return False

        # Determine the type of the value being assigned
        value_type = get_type_from_value(value)
        if value_type is None:
            # Can't determine type - allow assignment for now
            # This might be a function call or complex expression
            return True

        # Check if the value's type is compatible with the variable's type spec
        type_spec = TypeSpec(var_info.type_spec)
        is_compatible, _error_msg = check_type_compatibility(value_type, type_spec)

        if not is_compatible:
            # Create a detailed error message
            from machine_dialect.errors.messages import ASSIGNMENT_TYPE_MISMATCH
            from machine_dialect.type_checking import TYPE_DISPLAY_NAMES

            actual_type_name = TYPE_DISPLAY_NAMES.get(value_type, "unknown")
            self._report_error_and_recover(
                template=ASSIGNMENT_TYPE_MISMATCH,
                error_type="type",  # This is a type error
                variable=variable_name,
                expected_type=str(type_spec),
                actual_type=actual_type_name,
                skip_recovery=True,  # No recovery needed for semantic errors
            )
            return False

        # Mark the variable as initialized on successful type check
        self._symbol_table.mark_initialized(variable_name)
        return True

    def _is_type_token(self, token_type: TokenType) -> bool:
        """Check if a token type represents a type keyword.

        Args:
            token_type: The token type to check

        Returns:
            True if it's a type keyword, False otherwise
        """
        return token_type in {
            TokenType.KW_TEXT,
            TokenType.KW_WHOLE_NUMBER,
            TokenType.KW_FLOAT,
            TokenType.KW_NUMBER,
            TokenType.KW_YES_NO,
            TokenType.KW_URL,
            TokenType.KW_DATE,
            TokenType.KW_DATETIME,
            TokenType.KW_TIME,
            TokenType.KW_LIST,
            TokenType.KW_EMPTY,
        }
