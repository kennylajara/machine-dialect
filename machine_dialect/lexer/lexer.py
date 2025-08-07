from machine_dialect.helpers.validators import is_valid_url
from machine_dialect.lexer.constants import CHAR_TO_TOKEN_MAP
from machine_dialect.lexer.tokens import Token, TokenMetaType, TokenType, lookup_token_type


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

    def peek(self, offset: int = 1) -> str | None:
        peek_pos = self.position + offset
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

        # Check for contractions like 't or 's
        peek_char = self.peek()
        if self.current_char == "'" and peek_char and peek_char.isalpha():
            self.advance()  # Skip apostrophe
            while self.current_char and self.current_char.isalpha():
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

        words = [first_word]
        longest_match = None
        longest_match_position = self.position
        longest_match_line = self.line
        longest_match_column = self.column
        longest_match_char = self.current_char

        # Try to build progressively longer multi-word sequences
        while True:
            # Skip whitespace
            start_whitespace = self.position
            while self.current_char and self.current_char.isspace() and self.current_char != "\n":
                self.advance()

            # If we hit newline or no whitespace, stop looking
            if self.position == start_whitespace or not self.current_char:
                break

            # Check if next character could start a word
            if not (self.current_char.isalpha() or self.current_char == "'"):
                break

            # Read the next word
            next_word_start = self.position
            if self.current_char == "'":
                # Handle contractions like "isn't", "doesn't"
                self.advance()  # Skip apostrophe
                while self.current_char and self.current_char.isalpha():
                    self.advance()
            else:
                while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
                    self.advance()

            next_word = self.source[next_word_start : self.position]
            words.append(next_word)

            # Check if this multi-word sequence is a keyword
            multi_word = " ".join(words)
            token_type, _ = lookup_token_type(multi_word)
            # Only accept real keywords/operators, not identifiers, illegals, or stopwords
            if token_type not in (TokenType.MISC_IDENT, TokenType.MISC_ILLEGAL, TokenType.MISC_STOPWORD):
                longest_match = multi_word
                longest_match_position = self.position
                longest_match_line = self.line
                longest_match_column = self.column
                longest_match_char = self.current_char

        # If we found a match, restore position to end of the match
        if longest_match:
            self.position = longest_match_position
            self.line = longest_match_line
            self.column = longest_match_column
            self.current_char = longest_match_char
            return longest_match, longest_match_position

        # No match found, restore state
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
            if self.current_char == "`" and self.peek() == "`" and self.peek(2) == "`":
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
        return Token(token_type, "0" + literal if literal.startswith(".") else literal, line, pos)

    def tokenize_string(self, line: int, pos: int) -> Token:
        """Tokenize a string and return the appropriate token."""
        literal, _, _ = self.read_string()
        # Remove quotes from the literal for URL validation
        url_to_validate = literal[1:-1] if len(literal) > 2 else literal
        if is_valid_url(url_to_validate):
            return Token(TokenType.LIT_URL, literal, line, pos)
        else:
            return Token(TokenType.LIT_TEXT, literal, line, pos)

    def read_identifier_until_underscore(self) -> tuple[str, int, int]:
        """Read an identifier but stop at underscore (for underscore literals)."""
        start_pos = self.position
        start_line = self.line
        start_column = self.column
        while self.current_char and self.current_char.isalnum():
            self.advance()
        return self.source[start_pos : self.position], start_line, start_column

    def tokenize_identifier_or_boolean(self, line: int, pos: int) -> Token:
        """Tokenize an identifier or boolean literal."""
        literal, _, _ = self.read_identifier()

        # Check the token type (handles boolean literals, keywords, identifiers)
        token_type, canonical_literal = lookup_token_type(literal)
        return Token(token_type, canonical_literal, line, pos)

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

        # Check if there's another underscore immediately after (invalid pattern like __ or ___)
        if self.current_char == "_":
            # Multiple underscores at the start - invalid pattern
            self.position = start_pos
            self.line = start_line
            self.column = start_column
            self.current_char = self.source[self.position] if self.position < len(self.source) else None
            return None

        # Check what's inside the underscores
        if self.current_char is None:
            # Restore position if incomplete
            self.position = start_pos
            self.line = start_line
            self.column = start_column
            self.current_char = self.source[self.position] if self.position < len(self.source) else None
            return None

        # Handle numbers (including those starting with decimal point)
        peek_result = self.peek()
        if self.current_char and (
            self.current_char.isdigit()
            or (self.current_char == "." and peek_result is not None and peek_result.isdigit())
        ):
            # Use the helper function
            num_token = self.tokenize_number(self.line, self.column)

            # Check for closing underscore
            if self.current_char == "_":
                self.advance()  # Skip closing underscore
                # Check if there's another underscore (invalid pattern like _42__)
                if self.current_char == "_":
                    # Multiple underscores at the end - invalid pattern
                    self.position = start_pos
                    self.line = start_line
                    self.column = start_column
                    self.current_char = self.source[self.position] if self.position < len(self.source) else None
                    return None
                # Return the literal without underscores
                return num_token.literal, num_token.type, start_line, start_column

        # Handle strings
        elif self.current_char in ('"', "'"):
            # Use the helper function
            str_token = self.tokenize_string(self.line, self.column)

            # Check for closing underscore
            if self.current_char == "_":
                self.advance()  # Skip closing underscore
                # Check if there's another underscore (invalid pattern like _"hello"__)
                if self.current_char == "_":
                    # Multiple underscores at the end - invalid pattern
                    self.position = start_pos
                    self.line = start_line
                    self.column = start_column
                    self.current_char = self.source[self.position] if self.position < len(self.source) else None
                    return None
                # Return the literal without underscores
                return str_token.literal, str_token.type, start_line, start_column

        # Handle boolean literals (True/False) or identifiers
        elif self.current_char and self.current_char.isalpha():
            # Read identifier until underscore
            literal, _, _ = self.read_identifier_until_underscore()

            # Check the token type (handles boolean literals too)
            token_type, canonical_literal = lookup_token_type(literal)
            if token_type in (TokenType.LIT_TRUE, TokenType.LIT_FALSE):
                # Check for closing underscore
                if self.current_char == "_":
                    self.advance()  # Skip closing underscore
                    # Check if there's another underscore (invalid pattern like _true__)
                    if self.current_char == "_":
                        # Multiple underscores at the end - invalid pattern
                        self.position = start_pos
                        self.line = start_line
                        self.column = start_column
                        self.current_char = self.source[self.position] if self.position < len(self.source) else None
                        return None
                    # Return the canonical literal without underscores
                    return canonical_literal, token_type, start_line, start_column

        # Not a valid underscore literal, restore position
        self.position = start_pos
        self.line = start_line
        self.column = start_column
        self.current_char = self.source[self.position] if self.position < len(self.source) else None
        return None

    def read_double_asterisk_keyword(self) -> tuple[str, TokenType, int, int] | None:
        """Read a double-asterisk-wrapped keyword (e.g., **define**, **blueprint**).

        Returns:
            Tuple of (literal, token_type, line, column) if valid keyword found,
            None otherwise.
        """
        if not (self.current_char == "*" and self.peek() == "*"):
            return None

        start_pos = self.position
        start_line = self.line
        start_column = self.column

        self.advance()  # Skip first asterisk
        self.advance()  # Skip second asterisk

        # Check what's inside the asterisks
        if self.current_char is None or not self.current_char.isalpha():
            # Restore position if not a valid identifier start
            self.position = start_pos
            self.line = start_line
            self.column = start_column
            self.current_char = self.source[self.position] if self.position < len(self.source) else None
            return None

        # Read the identifier
        identifier_start = self.position
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            self.advance()

        identifier = self.source[identifier_start : self.position]

        # Check for multi-word keywords
        multi_word, _ = self.check_multi_word_keyword(identifier, self.line, self.column)
        if multi_word:
            identifier = multi_word

        # Check if it's followed by closing double asterisks
        if self.current_char == "*" and self.peek() == "*":
            self.advance()  # Skip first closing asterisk
            self.advance()  # Skip second closing asterisk

            # Check if the identifier is a keyword
            token_type, canonical_literal = lookup_token_type(identifier)
            if token_type.meta_type == TokenMetaType.KW:
                # It's a keyword, return without asterisks
                return canonical_literal, token_type, start_line, start_column

        # Not a valid keyword or missing closing asterisks, restore position
        self.position = start_pos
        self.line = start_line
        self.column = start_column
        self.current_char = self.source[self.position] if self.position < len(self.source) else None
        return None

    def tokenize(self) -> list[Token]:
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

                # Check if this is an incomplete underscore pattern (like _3.14 or _.25)
                next_char = self.peek()
                next_next_char = self.peek(2)
                if next_char and (
                    next_char.isdigit()
                    or (next_char == "." and next_next_char is not None and next_next_char.isdigit())
                ):
                    # This looks like an incomplete underscore literal
                    line, pos = self.line, self.column
                    # Read the entire pattern
                    start_pos = self.position
                    self.advance()  # Skip underscore

                    # Read the number part
                    peek_char = self.peek()
                    if self.current_char == "." and peek_char is not None and peek_char.isdigit():
                        self.tokenize_number(self.line, self.column)
                    elif self.current_char and self.current_char.isdigit():
                        self.tokenize_number(self.line, self.column)

                    # Also consume any trailing underscores
                    while self.current_char == "_":
                        self.advance()

                    # Create an illegal token for the entire pattern
                    illegal_literal = self.source[start_pos : self.position]
                    token = Token(TokenType.MISC_ILLEGAL, illegal_literal, line, pos)
                    tokens.append(token)
                    continue
                # If not a literal, fall through to identifier handling

            # Numbers (both wrapped and unwrapped are allowed)
            if self.current_char.isdigit():
                line, pos = self.line, self.column
                token = self.tokenize_number(line, pos)

                # Check if followed by underscore (invalid pattern like 3.14_)
                if self.current_char == "_":
                    # This is an invalid pattern - number followed by underscore
                    start_pos = self.position - len(token.literal)
                    self.advance()  # Skip underscore
                    illegal_literal = self.source[start_pos : self.position]

                    # Replace the valid number token with an illegal token
                    illegal_token = Token(TokenType.MISC_ILLEGAL, illegal_literal, line, pos)
                    tokens.append(illegal_token)
                else:
                    tokens.append(token)
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                line, pos = self.line, self.column

                # Special handling for multiple underscores followed by number
                if self.current_char == "_":
                    # Count consecutive underscores
                    underscore_count = 0
                    temp_pos = self.position
                    while temp_pos < len(self.source) and self.source[temp_pos] == "_":
                        underscore_count += 1
                        temp_pos += 1

                    # Check if followed by a number (digit or decimal point)
                    if temp_pos < len(self.source) and (
                        self.source[temp_pos].isdigit()
                        or (
                            self.source[temp_pos] == "."
                            and temp_pos + 1 < len(self.source)
                            and self.source[temp_pos + 1].isdigit()
                        )
                    ):
                        if underscore_count > 1:
                            # Multiple underscores followed by number - read entire pattern
                            start_pos = self.position

                            # Skip underscores
                            for _ in range(underscore_count):
                                self.advance()

                            # Read the number part
                            self.tokenize_number(self.line, self.column)

                            # Check for trailing underscores
                            trailing_underscores = 0
                            while self.current_char == "_":
                                trailing_underscores += 1
                                self.advance()

                            # Create illegal token for entire pattern
                            illegal_literal = self.source[start_pos : self.position]
                            token = Token(TokenType.MISC_ILLEGAL, illegal_literal, line, pos)
                            tokens.append(token)
                            continue

                # Check for multi-word keywords first
                literal, ident_line, ident_pos = self.read_identifier()
                multi_word, new_position = self.check_multi_word_keyword(literal, ident_line, ident_pos)

                if multi_word:
                    token_type, canonical_literal = lookup_token_type(multi_word)
                    tokens.append(Token(token_type, canonical_literal, ident_line, ident_pos))
                    # IMPORTANT: check_multi_word_keyword has already updated the lexer position
                    # so we just continue from where it left off
                else:
                    # Regular identifier, keyword, or boolean literal
                    token_type, canonical_literal = lookup_token_type(literal)
                    tokens.append(Token(token_type, canonical_literal, ident_line, ident_pos))
                    if token_type == TokenType.MISC_ILLEGAL:
                        # Illegal identifier pattern - error will be reported by parser
                        pass
                continue

            # Strings
            if self.current_char in ('"', "'"):
                line, pos = self.line, self.column
                token = self.tokenize_string(line, pos)
                tokens.append(token)
                continue

            # Backtick handling
            if self.current_char == "`":
                # Check for triple backticks
                if self.peek() == "`" and self.peek(2) == "`":
                    literal, line, pos = self.read_triple_backtick_string()
                    tokens.append(Token(TokenType.LIT_TRIPLE_BACKTICK, literal, line, pos))
                    continue

                # Single backtick - try to read identifier
                start_pos = self.position
                start_line = self.line
                start_column = self.column

                self.advance()  # Skip opening backtick

                # Read content until closing backtick
                identifier_start = self.position
                while self.current_char and self.current_char != "`":
                    self.advance()

                identifier = self.source[identifier_start : self.position]

                # Check if we have a closing backtick and valid identifier
                if self.current_char == "`" and identifier:
                    from machine_dialect.lexer.tokens import is_valid_identifier

                    if is_valid_identifier(identifier):
                        # Valid identifier - consume closing backtick and check token type
                        self.advance()
                        token_type, canonical_literal = lookup_token_type(identifier)
                        # For stopwords inside backticks, treat as identifiers
                        if token_type == TokenType.MISC_STOPWORD:
                            token_type = TokenType.MISC_IDENT
                            canonical_literal = identifier
                        # Only accept if it's not illegal
                        if token_type != TokenType.MISC_ILLEGAL:
                            tokens.append(Token(token_type, canonical_literal, start_line, start_column))
                            continue

                # Not a valid identifier - restore to just after the opening backtick
                # and treat the backtick as illegal
                self.position = start_pos
                self.line = start_line
                self.column = start_column
                self.current_char = self.source[self.position] if self.position < len(self.source) else None

                # Fall through to handle backtick as illegal character

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

            if self.current_char == "<" and self.peek() == "=":
                line, pos = self.line, self.column
                tokens.append(Token(TokenType.OP_LTE, "<=", line, pos))
                self.advance()
                self.advance()
                continue

            if self.current_char == ">" and self.peek() == "=":
                line, pos = self.line, self.column
                tokens.append(Token(TokenType.OP_GTE, ">=", line, pos))
                self.advance()
                self.advance()
                continue

            # Check for double-asterisk keywords before operator
            if self.current_char == "*" and self.peek() == "*":
                keyword_result = self.read_double_asterisk_keyword()
                if keyword_result:
                    literal, token_type, line, pos = keyword_result
                    tokens.append(Token(token_type, literal, line, pos))
                    continue
                # If not a keyword, it's the ** operator
                line, pos = self.line, self.column
                tokens.append(Token(TokenType.OP_TWO_STARS, "**", line, pos))
                self.advance()
                self.advance()
                continue

            # Check for floats starting with decimal point (e.g., .5, .25)
            peek_char = self.peek()
            if self.current_char == "." and peek_char is not None and peek_char.isdigit():
                line, pos = self.line, self.column
                token = self.tokenize_number(line, pos)

                # Check if followed by underscore (invalid pattern like .25_)
                if self.current_char == "_":
                    # This is an invalid pattern - number followed by underscore
                    # For numbers starting with ., we need to account for the original source
                    if token.literal.startswith("0.") and self.source[pos] == ".":
                        # Original started with . but token has 0. prefix
                        original_length = len(token.literal) - 1  # Remove the added 0
                    else:
                        original_length = len(token.literal)

                    start_pos = self.position - original_length
                    self.advance()  # Skip underscore
                    illegal_literal = self.source[start_pos : self.position]

                    # Replace the valid number token with an illegal token
                    illegal_token = Token(TokenType.MISC_ILLEGAL, illegal_literal, line, pos)
                    tokens.append(illegal_token)
                else:
                    tokens.append(token)
                continue

            if self.current_char in CHAR_TO_TOKEN_MAP:
                token_type = CHAR_TO_TOKEN_MAP[self.current_char]
                line, pos = self.line, self.column
                tokens.append(Token(token_type, self.current_char, line, pos))
                self.advance()
                continue

            # If we get here, it's an illegal character
            line, pos = self.line, self.column
            assert self.current_char is not None  # Loop invariant
            token = Token(TokenType.MISC_ILLEGAL, self.current_char, line, pos)
            tokens.append(token)
            self.advance()

        # Convert stopwords to identifiers in appropriate contexts
        tokens = self._convert_contextual_stopwords(tokens)

        # Apply post-processing to merge identifiers
        merged_tokens = self._merge_identifiers(tokens)
        return merged_tokens

    def _convert_contextual_stopwords(self, tokens: list[Token]) -> list[Token]:
        """Convert stopwords to identifiers after Set keyword in specific contexts."""
        if not tokens:
            return tokens

        result: list[Token] = []
        for i, token in enumerate(tokens):
            if token.type == TokenType.MISC_STOPWORD and i > 0 and tokens[i - 1].type == TokenType.KW_SET:
                # Check if this stopword should be converted
                # Only convert if there are no identifiers between this stopword and "to"/period/EOF
                should_convert = True
                j = i + 1
                while j < len(tokens):
                    if tokens[j].type == TokenType.KW_TO or tokens[j].type == TokenType.PUNCT_PERIOD:
                        # Found "to" or period, stop looking
                        break
                    elif tokens[j].type == TokenType.MISC_IDENT:
                        # Found an identifier before "to"/period, don't convert
                        should_convert = False
                        break
                    elif tokens[j].type == TokenType.MISC_STOPWORD:
                        # Another stopword, keep looking
                        j += 1
                    else:
                        # Some other token type, don't convert
                        should_convert = False
                        break

                if should_convert:
                    # Convert stopword to identifier
                    result.append(Token(TokenType.MISC_IDENT, token.literal, token.line, token.position))
                else:
                    result.append(token)
            else:
                result.append(token)

        return result

    def _merge_identifiers(self, tokens: list[Token]) -> list[Token]:
        """Merge consecutive identifiers with stopwords in between.

        This helper function merges sequences of identifiers and stopwords into single
        identifier tokens, following these rules:
        1. The sequence must start with an identifier
        2. The sequence must end with an identifier
        3. Stopwords in the middle are included
        4. Trailing stopwords are not included in the merge

        Examples:
        - "hello world" -> "hello world"
        - "info collected by the system" -> "info collected by the system"
        - "the username" -> "the" (stopword), "username" (identifier)
        - "username are" -> "username" (identifier), "are" (stopword)

        Args:
            tokens: List of tokens from the initial tokenization.

        Returns:
            List of tokens with identifiers merged where appropriate.
        """
        if not tokens:
            return tokens

        merged: list[Token] = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            # Check if this token starts an identifier sequence
            if token.type == TokenType.MISC_IDENT:
                # Find the extent of the sequence
                sequence_end = self._find_identifier_sequence_end(tokens, i)

                if sequence_end > i:
                    # We have a sequence to merge
                    merged_token = self._create_merged_identifier(tokens, i, sequence_end)
                    merged.append(merged_token)
                    i = sequence_end + 1
                else:
                    # No merging happened
                    merged.append(token)
                    i += 1
            else:
                # Not an identifier, keep as is
                merged.append(token)
                i += 1

        return merged

    def _find_identifier_sequence_end(self, tokens: list[Token], start: int) -> int:
        """Find the end index of an identifier sequence that can be merged.

        A mergeable sequence:
        - Starts with an identifier (at start index)
        - Can contain identifiers and stopwords
        - Must end with an identifier
        - Trailing stopwords are excluded

        Args:
            tokens: List of all tokens
            start: Starting index (must be an identifier)

        Returns:
            Index of the last token in the sequence (inclusive), or start if no merge
        """
        i = start
        last_identifier_index = start

        # Look ahead for identifiers and stopwords
        while i + 1 < len(tokens):
            next_token = tokens[i + 1]

            if next_token.type == TokenType.MISC_IDENT:
                # Continue the sequence and update last identifier position
                i += 1
                last_identifier_index = i
            elif next_token.type == TokenType.MISC_STOPWORD:
                # Tentatively include stopword, but only if followed by identifier
                temp_i = i + 1

                # Look ahead past consecutive stopwords
                while temp_i + 1 < len(tokens) and tokens[temp_i + 1].type == TokenType.MISC_STOPWORD:
                    temp_i += 1

                # Check if there's an identifier after the stopword(s)
                if temp_i + 1 < len(tokens) and tokens[temp_i + 1].type == TokenType.MISC_IDENT:
                    # There's an identifier after stopword(s), include them
                    i = temp_i
                else:
                    # No identifier after stopword(s), end sequence here
                    break
            else:
                # Any other token type ends the sequence
                break

        return last_identifier_index

    def _create_merged_identifier(self, tokens: list[Token], start: int, end: int) -> Token:
        """Create a merged identifier token from a sequence of tokens.

        Args:
            tokens: List of all tokens
            start: Starting index of the sequence
            end: Ending index of the sequence (inclusive)

        Returns:
            A new Token representing the merged identifier
        """
        parts = []

        for i in range(start, end + 1):
            if i > start:
                parts.append(" ")
            parts.append(tokens[i].literal)

        merged_literal = "".join(parts)
        return Token(TokenType.MISC_IDENT, merged_literal, tokens[start].line, tokens[start].position)
