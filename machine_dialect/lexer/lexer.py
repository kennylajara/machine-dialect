from machine_dialect.helpers.validators import is_valid_url
from machine_dialect.lexer.tokens import Token, TokenType, lookup_token_type


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.position = 0
        self.current_char: str | None = self.source[0] if source else None

    def advance(self) -> None:
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

    def read_number(self) -> tuple[str, bool]:
        start_pos = self.position
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

        return self.source[start_pos : self.position], has_dot

    def read_identifier(self) -> str:
        start_pos = self.position
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            self.advance()
        return self.source[start_pos : self.position]

    def read_string(self) -> str:
        quote_char = self.current_char
        start_pos = self.position
        self.advance()  # Skip opening quote

        while self.current_char and self.current_char != quote_char:
            self.advance()

        if self.current_char == quote_char:
            self.advance()  # Skip closing quote

        return self.source[start_pos : self.position]

    def read_backtick_string(self) -> str:
        start_pos = self.position
        self.advance()  # Skip opening backtick

        while self.current_char and self.current_char != "`":
            self.advance()

        if self.current_char == "`":
            self.advance()  # Skip closing backtick

        return self.source[start_pos : self.position]

    def read_triple_backtick_string(self) -> str:
        start_pos = self.position
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

        return self.source[start_pos : self.position]

    def tokenize(self) -> list[Token]:
        tokens = []

        while self.current_char is not None:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Numbers
            if self.current_char.isdigit():
                literal, is_float = self.read_number()
                token_type = TokenType.LIT_FLOAT if is_float else TokenType.LIT_INT
                tokens.append(Token(token_type, literal))
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                literal = self.read_identifier()
                token_type = lookup_token_type(literal)
                tokens.append(Token(token_type, literal))
                continue

            # Strings
            if self.current_char in ('"', "'"):
                literal = self.read_string()
                # Remove quotes from the literal for URL validation
                url_to_validate = literal[1:-1] if len(literal) > 2 else literal
                if is_valid_url(url_to_validate):
                    tokens.append(Token(TokenType.LIT_URL, literal))
                else:
                    tokens.append(Token(TokenType.LIT_TEXT, literal))
                continue

            # Backtick strings
            if self.current_char == "`":
                # Check for triple backticks
                if (
                    self.peek() == "`"
                    and self.position + 2 < len(self.source)
                    and self.source[self.position + 2] == "`"
                ):
                    literal = self.read_triple_backtick_string()
                    tokens.append(Token(TokenType.LIT_TRIPLE_BACKTICK, literal))
                else:
                    literal = self.read_backtick_string()
                    tokens.append(Token(TokenType.LIT_BACKTICK, literal))
                continue

            # Two-character operators
            if self.current_char == "=" and self.peek() == "=":
                tokens.append(Token(TokenType.OP_EQ, "=="))
                self.advance()
                self.advance()
                continue

            if self.current_char == "!" and self.peek() == "=":
                tokens.append(Token(TokenType.OP_NOT_EQ, "!="))
                self.advance()
                self.advance()
                continue

            if self.current_char == "*" and self.peek() == "*":
                tokens.append(Token(TokenType.OP_TWO_STARS, "**"))
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
                tokens.append(Token(token_type, self.current_char))
                self.advance()
                continue

            # If we get here, it's an illegal character
            tokens.append(Token(TokenType.MISC_ILLEGAL, self.current_char))
            self.advance()

        return tokens
