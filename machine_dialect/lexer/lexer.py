from machine_dialect.errors.exceptions import MDNameError
from machine_dialect.errors.messages import NAME_UNDEFINED
from machine_dialect.helpers.validators import is_valid_url
from machine_dialect.lexer.tokens import Token, TokenType, lookup_token_type


def is_literal_token(token: Token) -> bool:
    """Check if a token represents a literal value."""
    return token.type in (TokenType.LIT_INT, TokenType.LIT_FLOAT, TokenType.LIT_TEXT, TokenType.LIT_URL)


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 0
        self.current_char: str | None = self.source[0] if source else None

    def advance(self) -> None:
        if self.current_char == "\n":
            self.line += 1
            self.column = 0
        else:
            self.column += 1

        self.position += 1
        if self.position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.position]

    def peek(self) -> str | None:
        peek_pos = self.position + 1
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]

    def skip_whitespace(self) -> None:
        while self.current_char and self.current_char.isspace():
            self.advance()

    def read_number(self) -> tuple[str, bool, int, int]:
        start_pos = self.position
        start_line = self.line
        start_column = self.column
        has_dot = False

        while self.current_char and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                # Only allow one decimal point
                if has_dot:
                    break
                # Check if next character is a digit
                next_char = self.peek()
                if not next_char or not next_char.isdigit():
                    break
                has_dot = True
            self.advance()

        return self.source[start_pos : self.position], has_dot, start_line, start_column

    def read_identifier(self) -> tuple[str, int, int]:
        start_pos = self.position
        start_line = self.line
        start_column = self.column
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            self.advance()
        return self.source[start_pos : self.position], start_line, start_column

    def check_multi_word_keyword(self, first_word: str, line: int, pos: int) -> tuple[str | None, int]:
        """Check if the identifier starts a multi-word keyword.

        Args:
            first_word: The first word that was read
            line: Line number of the first word
            pos: Column position of the first word

        Returns:
            Tuple of (multi_word_keyword, end_position) if found, otherwise (None, current_position)
        """
        # Save current state
        saved_position = self.position
        saved_line = self.line
        saved_column = self.column
        saved_char = self.current_char

        # Skip whitespace after first word
        start_whitespace = self.position
        while self.current_char and self.current_char.isspace() and self.current_char != "\n":
            self.advance()

        # If we hit newline or no whitespace, not a multi-word keyword
        if self.position == start_whitespace or not self.current_char or not self.current_char.isalpha():
            # Restore state
            self.position = saved_position
            self.line = saved_line
            self.column = saved_column
            self.current_char = saved_char
            return None, self.position

        # Read the next word
        next_word_start = self.position
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            self.advance()

        second_word = self.source[next_word_start : self.position]
        two_words = f"{first_word} {second_word}"

        # Check if it's a multi-word keyword
        if lookup_token_type(two_words) != TokenType.MISC_IDENT:
            return two_words, self.position

        # Not a multi-word keyword, restore state
        self.position = saved_position
        self.line = saved_line
        self.column = saved_column
        self.current_char = saved_char
        return None, self.position

    def read_string(self) -> tuple[str, int, int]:
        quote_char = self.current_char
        start_pos = self.position
        start_line = self.line
        start_column = self.column
        self.advance()  # Skip opening quote

        while self.current_char and self.current_char != quote_char:
            self.advance()

        if self.current_char == quote_char:
            self.advance()  # Skip closing quote

        return self.source[start_pos : self.position], start_line, start_column

    def read_backtick_string(self) -> tuple[str, int, int]:
        start_pos = self.position
        start_line = self.line
        start_column = self.column
        self.advance()  # Skip opening backtick

        while self.current_char and self.current_char != "`":
            self.advance()

        if self.current_char == "`":
            self.advance()  # Skip closing backtick

        return self.source[start_pos : self.position], start_line, start_column

    def read_triple_backtick_string(self) -> tuple[str, int, int]:
        start_pos = self.position
        start_line = self.line
        start_column = self.column
        # Skip opening triple backticks
        self.advance()  # First `
        self.advance()  # Second `
        self.advance()  # Third `

        # Look for closing triple backticks
        while self.current_char:
            if (
                self.current_char == "`"
                and self.peek() == "`"
                and self.position + 2 < len(self.source)
                and self.source[self.position + 2] == "`"
            ):
                # Skip closing triple backticks
                self.advance()
                self.advance()
                self.advance()
                break
            self.advance()

        return self.source[start_pos : self.position], start_line, start_column

    def tokenize_number(self, line: int, pos: int) -> Token:
        """Tokenize a number and return the appropriate token."""
        literal, is_float, _, _ = self.read_number()
        token_type = TokenType.LIT_FLOAT if is_float else TokenType.LIT_INT
        return Token(token_type, literal, line, pos)

    def tokenize_string(self, line: int, pos: int) -> Token:
        """Tokenize a string and return the appropriate token."""
        literal, _, _ = self.read_string()
        # Remove quotes from the literal for URL validation
        url_to_validate = literal[1:-1] if len(literal) > 2 else literal
        if is_valid_url(url_to_validate):
            return Token(TokenType.LIT_URL, literal, line, pos)
        else:
            return Token(TokenType.LIT_TEXT, literal, line, pos)

    def read_underscore_literal(self) -> tuple[str, TokenType, int, int] | None:
        """Read an underscore-wrapped literal (e.g., _42_, _"Hello"_, _3.14_).

        Returns:
            Tuple of (literal, token_type, line, column) if valid literal found,
            None otherwise.
        """
        if self.current_char != "_":
            return None

        start_pos = self.position
        start_line = self.line
        start_column = self.column

        self.advance()  # Skip opening underscore

        # Check what's inside the underscores
        if self.current_char is None:
            # Restore position if incomplete
            self.position = start_pos
            self.line = start_line
            self.column = start_column
            self.current_char = self.source[self.position] if self.position < len(self.source) else None
            return None

        # Handle numbers
        if self.current_char and self.current_char.isdigit():
            # Use the helper function
            num_token = self.tokenize_number(self.line, self.column)

            # Check for closing underscore
            if self.current_char == "_":
                self.advance()  # Skip closing underscore
                full_literal = self.source[start_pos : self.position]
                return full_literal, num_token.type, start_line, start_column

        # Handle strings
        elif self.current_char in ('"', "'"):
            # Use the helper function
            str_token = self.tokenize_string(self.line, self.column)

            # Check for closing underscore
            if self.current_char == "_":
                self.advance()  # Skip closing underscore
                full_literal = self.source[start_pos : self.position]
                return full_literal, str_token.type, start_line, start_column

        # Not a valid underscore literal, restore position
        self.position = start_pos
        self.line = start_line
        self.column = start_column
        self.current_char = self.source[self.position] if self.position < len(self.source) else None
        return None

    def tokenize(self) -> tuple[list[MDNameError], list[Token]]:
        errors: list[MDNameError] = []
        tokens: list[Token] = []

        while self.current_char is not None:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Check for underscore-wrapped literals first
            if self.current_char == "_":
                literal_result = self.read_underscore_literal()
                if literal_result:
                    literal, token_type, line, pos = literal_result
                    tokens.append(Token(token_type, literal, line, pos))
                    continue
                # If not a literal, fall through to identifier handling

            # Numbers (both wrapped and unwrapped are allowed)
            if self.current_char.isdigit():
                line, pos = self.line, self.column
                token = self.tokenize_number(line, pos)
                tokens.append(token)
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                literal, line, pos = self.read_identifier()

                # Check for multi-word keywords
                multi_word, _ = self.check_multi_word_keyword(literal, line, pos)
                if multi_word:
                    token_type = lookup_token_type(multi_word)
                    tokens.append(Token(token_type, multi_word, line, pos))
                else:
                    token_type = lookup_token_type(literal)
                    tokens.append(Token(token_type, literal, line, pos))
                continue

            # Strings
            if self.current_char in ('"', "'"):
                line, pos = self.line, self.column
                token = self.tokenize_string(line, pos)
                tokens.append(token)
                continue

            # Backtick strings
            if self.current_char == "`":
                # Check for triple backticks
                if (
                    self.peek() == "`"
                    and self.position + 2 < len(self.source)
                    and self.source[self.position + 2] == "`"
                ):
                    literal, line, pos = self.read_triple_backtick_string()
                    tokens.append(Token(TokenType.LIT_TRIPLE_BACKTICK, literal, line, pos))
                else:
                    literal, line, pos = self.read_backtick_string()
                    tokens.append(Token(TokenType.LIT_BACKTICK, literal, line, pos))
                continue

            # Two-character operators
            if self.current_char == "=" and self.peek() == "=":
                line, pos = self.line, self.column
                tokens.append(Token(TokenType.OP_EQ, "==", line, pos))
                self.advance()
                self.advance()
                continue

            if self.current_char == "!" and self.peek() == "=":
                line, pos = self.line, self.column
                tokens.append(Token(TokenType.OP_NOT_EQ, "!=", line, pos))
                self.advance()
                self.advance()
                continue

            if self.current_char == "*" and self.peek() == "*":
                line, pos = self.line, self.column
                tokens.append(Token(TokenType.OP_TWO_STARS, "**", line, pos))
                self.advance()
                self.advance()
                continue

            # Single-character tokens
            char_to_token = {
                "+": TokenType.OP_PLUS,
                "-": TokenType.OP_MINUS,
                "*": TokenType.OP_STAR,
                "/": TokenType.OP_DIVISION,
                "=": TokenType.OP_ASSIGN,
                "<": TokenType.OP_LT,
                ">": TokenType.OP_GT,
                "!": TokenType.OP_NEGATION,
                "(": TokenType.DELIM_LPAREN,
                ")": TokenType.DELIM_RPAREN,
                "{": TokenType.DELIM_LBRACE,
                "}": TokenType.DELIM_RBRACE,
                ";": TokenType.PUNCT_SEMICOLON,
                ",": TokenType.PUNCT_COMMA,
                ".": TokenType.PUNCT_PERIOD,
                ":": TokenType.PUNCT_COLON,
                "#": TokenType.PUNCT_HASH,
            }

            if self.current_char in char_to_token:
                token_type = char_to_token[self.current_char]
                line, pos = self.line, self.column
                tokens.append(Token(token_type, self.current_char, line, pos))
                self.advance()
                continue

            # If we get here, it's an illegal character
            line, pos = self.line, self.column
            token = Token(TokenType.MISC_ILLEGAL, self.current_char, line, pos)
            tokens.append(token)
            errors.append(
                MDNameError(
                    message=NAME_UNDEFINED.substitute(name=self.current_char),
                    line=line,
                    column=pos,
                )
            )
            self.advance()

        return errors, tokens
