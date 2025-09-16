"""Streaming lexer implementation for Machine Dialect™.

This module provides a Lexer class that generates tokens one at a time
instead of all at once, enabling memory-efficient parsing of large files.
"""

from machine_dialect.helpers.validators import is_valid_url
from machine_dialect.lexer.constants import CHAR_TO_TOKEN_MAP
from machine_dialect.lexer.tokens import Token, TokenType, lookup_tag_token, lookup_token_type


class Lexer:
    """Streaming lexer for Machine Dialect™ language.

    Generates tokens one at a time from the source code.
    """

    def __init__(self, source: str) -> None:
        """Initialize the lexer with source code.

        Args:
            source: The source code to tokenize.
        """
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.current_char: str | None = self.source[0] if source else None
        self.in_summary_comment = False

    @property
    def at_line_start(self) -> bool:
        """Check if we're at the start of a logical line.

        A logical line start means we're at column 1 or only have whitespace
        and block markers (>) before current position on this line.

        Returns:
            True if we're at the start of a logical line.
        """
        if self.column == 1:
            return True

        # Check if we only have whitespace or block markers before current position on this line
        # Find the start of the current line
        line_start = self.position - (self.column - 1)
        for i in range(line_start, self.position):
            if i < len(self.source):
                char = self.source[i]
                if not char.isspace() and char != ">":
                    return False
        return True

    def advance(self) -> None:
        """Move to the next character in the source."""
        if self.current_char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        self.position += 1
        if self.position >= len(self.source):
            self.current_char = None
        else:
            self.current_char = self.source[self.position]

    def _restore_position(self, pos: int) -> None:
        """Restore position and recalculate column.

        Args:
            pos: The position to restore to.
        """
        self.position = pos
        self.current_char = self.source[pos] if pos < len(self.source) else None

        # Recalculate column by counting from start of current line
        line_start = pos
        while line_start > 0 and self.source[line_start - 1] != "\n":
            line_start -= 1
        self.column = pos - line_start + 1

    def peek(self, offset: int = 1) -> str | None:
        """Look ahead at a character without consuming it.

        Args:
            offset: How many characters ahead to look.

        Returns:
            The character at the offset, or None if out of bounds.
        """
        peek_pos = self.position + offset
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]

    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.current_char and self.current_char.isspace():
            self.advance()

    def read_number(self) -> tuple[str, bool, int, int]:
        """Read a number literal.

        Returns:
            Tuple of (literal, is_float, line, column).
        """
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
        """Read an identifier.

        Returns:
            Tuple of (identifier, line, column).
        """
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

    def read_string(self) -> tuple[str, int, int]:
        """Read a string literal.

        Returns:
            Tuple of (string_literal, line, column).
        """
        start_pos = self.position
        start_line = self.line
        start_column = self.column
        quote_char = self.current_char
        self.advance()  # Skip opening quote

        while self.current_char and self.current_char != quote_char:
            if self.current_char == "\\":
                self.advance()  # Skip escape character
                if self.current_char:
                    self.advance()  # Skip escaped character
            else:
                self.advance()

        if self.current_char == quote_char:
            self.advance()  # Skip closing quote

        return self.source[start_pos : self.position], start_line, start_column

    def read_triple_backtick_string(self) -> tuple[str, int, int]:
        """Read a triple backtick string.

        Returns:
            Tuple of (string_content, line, column).
        """
        start_line = self.line
        start_column = self.column

        # Skip the three backticks
        self.advance()  # First backtick
        self.advance()  # Second backtick
        self.advance()  # Third backtick

        # Read until we find three closing backticks
        content_start = self.position
        while self.current_char:
            if self.current_char == "`" and self.peek() == "`" and self.peek(2) == "`":
                content = self.source[content_start : self.position]
                # Skip the closing backticks
                self.advance()
                self.advance()
                self.advance()
                return content, start_line, start_column
            self.advance()

        # Unclosed triple backtick string
        content = self.source[content_start : self.position]
        return content, start_line, start_column

    def check_multi_word_keyword(self, first_word: str, line: int, pos: int) -> tuple[str | None, int]:
        """Check if the identifier starts a multi-word keyword.

        Args:
            first_word: The first word that was read.
            line: Line number of the first word.
            pos: Column position of the first word.

        Returns:
            Tuple of (multi_word_keyword, end_position) if found, otherwise (None, current_position).
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
            self.skip_whitespace()

            # If no whitespace was skipped, we can't have a multi-word keyword
            if self.position == start_whitespace:
                break

            # Try to read the next word
            if not self.current_char or not self.current_char.isalpha():
                break

            next_word, _, _ = self.read_identifier()
            if not next_word:
                break

            words.append(next_word)
            potential_keyword = " ".join(words)

            # Check if this forms a valid multi-word keyword
            token_type, _ = lookup_token_type(potential_keyword)
            # Only accept actual keywords, not just any valid identifier
            if token_type not in (TokenType.MISC_ILLEGAL, TokenType.MISC_IDENT, TokenType.MISC_STOPWORD):
                # Found a valid multi-word keyword
                longest_match = potential_keyword
                longest_match_position = self.position
                longest_match_line = self.line
                longest_match_column = self.column
                longest_match_char = self.current_char

        if longest_match:
            # Use the longest matching multi-word keyword
            self.position = longest_match_position
            self.line = longest_match_line
            self.column = longest_match_column
            self.current_char = longest_match_char
            return longest_match, self.position
        else:
            # No multi-word keyword found, restore original position
            self.position = saved_position
            self.line = saved_line
            self.column = saved_column
            self.current_char = saved_char
            return None, self.position

    def read_double_asterisk_keyword(self) -> tuple[str, TokenType, int, int] | None:
        """Read a double-asterisk wrapped keyword.

        Returns:
            Tuple of (literal, token_type, line, column) or None if not a valid keyword.
        """
        start_pos = self.position
        start_line = self.line
        start_column = self.column

        # Skip first two asterisks
        self.advance()  # First *
        self.advance()  # Second *

        # Check what comes after the asterisks
        if not self.current_char or not self.current_char.isalpha():
            # Restore position
            self.position = start_pos
            self.line = start_line
            self.column = start_column
            self.current_char = self.source[self.position] if self.position < len(self.source) else None
            return None

        # Read the keyword (can be multi-word)
        words = []

        while True:
            # Read a word
            if not self.current_char or not self.current_char.isalpha():
                break

            word_start = self.position
            while self.current_char and self.current_char.isalpha():
                self.advance()
            words.append(self.source[word_start : self.position])

            # Check if there's a space and another word
            if self.current_char == " ":
                # Peek ahead to see if there's another word or closing **
                saved_pos = self.position
                saved_line = self.line
                saved_column = self.column
                saved_char = self.current_char

                self.advance()  # Skip space

                if self.current_char == "*" and self.peek() == "*":
                    # It's the closing **, restore and break
                    self.position = saved_pos
                    self.line = saved_line
                    self.column = saved_column
                    self.current_char = saved_char
                    break
                elif self.current_char and self.current_char.isalpha():
                    # Another word follows, continue
                    continue
                else:
                    # Not a word, restore and break
                    self.position = saved_pos
                    self.line = saved_line
                    self.column = saved_column
                    self.current_char = saved_char
                    break
            else:
                break

        keyword = " ".join(words) if words else ""

        # Check for closing double asterisk
        if self.current_char == "*" and self.peek() == "*":
            self.advance()  # First closing *
            self.advance()  # Second closing *

            # Check if it's a valid keyword
            from machine_dialect.lexer.tokens import lookup_token_type

            token_type, canonical = lookup_token_type(keyword)

            # Only accept actual keywords, not identifiers, stopwords, or boolean literals
            if token_type not in (
                TokenType.MISC_ILLEGAL,
                TokenType.MISC_IDENT,
                TokenType.MISC_STOPWORD,
                TokenType.LIT_YES,
                TokenType.LIT_NO,
            ):
                return canonical, token_type, start_line, start_column

        # Not a valid double-asterisk keyword, restore position
        self.position = start_pos
        self.line = start_line
        self.column = start_column
        self.current_char = self.source[self.position] if self.position < len(self.source) else None
        return None

    def read_tag_token(self) -> tuple[str, TokenType, int, int] | None:
        """Read a tag token like <summary>, </summary>, <details>, </details>.

        Returns:
            Tuple of (literal, token_type, line, column) or None if not a valid tag.
        """
        start_pos = self.position
        start_line = self.line
        start_column = self.column

        # Must start with '<'
        if self.current_char != "<":
            return None

        self.advance()  # Skip '<'

        # Check for closing tag
        is_closing = False
        if self.current_char == "/":
            is_closing = True
            self.advance()  # Skip '/'

        # Read the tag name
        tag_name_start = self.position
        while self.current_char and self.current_char.isalpha():
            self.advance()

        tag_name = self.source[tag_name_start : self.position]

        # Must end with '>'
        if self.current_char != ">":
            # Not a valid tag, restore position
            self.position = start_pos
            self.line = start_line
            self.column = start_column
            self.current_char = self.source[self.position] if self.position < len(self.source) else None
            return None

        self.advance()  # Skip '>'

        # Construct the full tag literal
        if is_closing:
            tag_literal = f"</{tag_name}>"
        else:
            tag_literal = f"<{tag_name}>"

        # Check if it's a valid tag token
        token_type, canonical_literal = lookup_tag_token(tag_literal)
        if token_type:
            return canonical_literal, token_type, start_line, start_column

        # Not a recognized tag, restore position
        self.position = start_pos
        self.line = start_line
        self.column = start_column
        self.current_char = self.source[self.position] if self.position < len(self.source) else None
        return None

    def read_comment_content(self) -> tuple[str, int, int]:
        """Read comment content until </summary> tag is found.

        Returns:
            Tuple of (comment_content, line, column).
        """
        start_line = self.line
        start_column = self.column
        content_start = self.position

        while self.current_char:
            # Look for potential closing tag
            if self.current_char == "<":
                # Save position before checking
                saved_pos = self.position
                saved_line = self.line
                saved_column = self.column
                saved_char = self.current_char

                # Check if it's </summary>
                self.advance()  # Skip '<'
                if self.current_char == "/":
                    self.advance()  # Skip '/'
                    # Check for "summary"
                    tag_start = self.position
                    while self.current_char and self.current_char.isalpha():
                        self.advance()
                    tag_name = self.source[tag_start : self.position]

                    if tag_name.lower() == "summary" and self.current_char == ">":
                        # Found closing tag, restore to before the tag
                        self.position = saved_pos
                        self.line = saved_line
                        self.column = saved_column
                        self.current_char = saved_char
                        # Return the content before the closing tag
                        content = self.source[content_start:saved_pos]
                        return content, start_line, start_column

                # Not a closing summary tag, restore and continue
                self.position = saved_pos
                self.line = saved_line
                self.column = saved_column
                self.current_char = saved_char

            self.advance()

        # No closing tag found, return content up to EOF
        content = self.source[content_start : self.position]
        return content, start_line, start_column

    def read_underscore_literal(self) -> tuple[str, TokenType, int, int] | None:
        """Read an underscore-wrapped literal.

        Returns:
            Tuple of (literal, token_type, line, column) or None if not a valid literal.
        """
        start_pos = self.position
        start_line = self.line
        start_column = self.column

        self.advance()  # Skip first underscore

        # For underscore literals, report the position after the underscore
        literal_column = start_column

        # Check what comes after the underscore
        if not self.current_char:
            # Restore position
            self.position = start_pos
            self.line = start_line
            self.column = start_column
            self.current_char = self.source[self.position] if self.position < len(self.source) else None
            return None

        # Check for negative sign before number
        has_minus = False
        if self.current_char == "-":
            has_minus = True
            self.advance()  # Skip minus sign

            # Check what comes after the minus
            if not self.current_char:
                # Restore position
                self.position = start_pos
                self.line = start_line
                self.column = start_column
                self.current_char = self.source[self.position] if self.position < len(self.source) else None
                return None

        # Try different literal types
        next_char = self.peek()
        if self.current_char.isdigit() or (self.current_char == "." and next_char and next_char.isdigit()):
            # Number literal
            literal, is_float, _, _ = self.read_number()

            # Normalize decimal-only floats (e.g., ".5" -> "0.5")
            if is_float and literal.startswith("."):
                literal = "0" + literal

            # Add minus sign if present
            if has_minus:
                literal = "-" + literal

            # Check for closing underscore
            if self.current_char == "_":
                self.advance()

                # Check for extra trailing underscores (invalid pattern)
                if self.current_char == "_":
                    # Multiple trailing underscores - this is invalid
                    # Don't restore position, let the caller handle the illegal token
                    return None

                # Return canonical form without underscores
                token_type = TokenType.LIT_FLOAT if is_float else TokenType.LIT_WHOLE_NUMBER
                return literal, token_type, start_line, literal_column
        elif self.current_char in ('"', "'"):
            # String literal - but minus sign is not valid before strings
            if has_minus:
                # Restore position
                self.position = start_pos
                self.line = start_line
                self.column = start_column
                self.current_char = self.source[self.position] if self.position < len(self.source) else None
                return None
            quote_char = self.current_char
            self.advance()  # Skip opening quote

            string_content_start = self.position
            while self.current_char and self.current_char != quote_char:
                if self.current_char == "\\":
                    self.advance()
                    if self.current_char:
                        self.advance()
                else:
                    self.advance()

            if self.current_char == quote_char:
                self.advance()  # Skip closing quote

                # Check for closing underscore
                if self.current_char == "_":
                    self.advance()
                    # Get string content without quotes
                    string_content = self.source[string_content_start : self.position - 2]
                    # Return canonical form with quotes but without underscores
                    full_literal = f"{quote_char}{string_content}{quote_char}"

                    # Check if it's a URL
                    url_to_check = string_content
                    token_type = TokenType.LIT_URL if is_valid_url(url_to_check) else TokenType.LIT_TEXT
                    return full_literal, token_type, start_line, literal_column
            else:
                # String is unclosed - this is a malformed underscore literal
                # Don't restore position, we've already consumed the content
                # Return None to indicate it's invalid, but keep the consumed position
                return None
        elif self.current_char.isalpha():
            # Read alphabetic characters only (no underscores) for potential boolean literal
            # Minus sign is not valid before boolean literals
            if has_minus:
                # Restore position
                self.position = start_pos
                self.line = start_line
                self.column = start_column
                self.current_char = self.source[self.position] if self.position < len(self.source) else None
                return None
            ident_start = self.position
            while self.current_char and self.current_char.isalpha():
                self.advance()

            literal = self.source[ident_start : self.position]

            # Check for closing underscore
            if self.current_char == "_":
                # Check if it's a boolean or empty literal
                if literal.lower() in ("true", "false", "yes", "no", "empty"):
                    self.advance()  # Consume the closing underscore
                    # Use canonical form for the literal (without underscores)
                    if literal.lower() == "empty":
                        return "empty", TokenType.KW_EMPTY, start_line, literal_column
                    else:
                        # Map Yes/No to True/False
                        is_true = literal.lower() in ("true", "yes")
                        canonical_literal = "Yes" if is_true else "No"
                        token_type = TokenType.LIT_YES if is_true else TokenType.LIT_NO
                        return canonical_literal, token_type, start_line, literal_column

        # Not a valid underscore-wrapped literal, restore position
        # (This also handles the case where we have a minus sign but no valid literal follows)
        self.position = start_pos
        self.line = start_line
        self.column = start_column
        self.current_char = self.source[self.position] if self.position < len(self.source) else None
        return None

    def next_token(self, in_block: bool = False, in_list_context: bool = False) -> Token:
        """Get the next token from the source.

        Args:
            in_block: Whether we're currently parsing inside a block (currently unused).
            in_list_context: Whether we're in a list definition context (after Set ... to:).

        Returns:
            The next token, or an EOF token if no more tokens are available.
        """
        # If we're in a summary comment, read the comment content
        if self.in_summary_comment:
            self.in_summary_comment = False
            # Don't skip whitespace - it's part of the comment
            # If we're at EOF, don't create a comment
            if self.current_char is None:
                return Token(TokenType.MISC_EOF, "", self.line, self.column)
            content, line, pos = self.read_comment_content()
            return Token(TokenType.MISC_COMMENT, content, line, pos)

        # Skip whitespace
        self.skip_whitespace()

        # Check if we've reached the end
        if self.current_char is None:
            return Token(TokenType.MISC_EOF, "", self.line, self.column)

        # Save position for token
        token_line = self.line
        token_column = self.column

        # Check for tag tokens (<summary>, </summary>, <details>, </details>)
        if self.current_char == "<":
            tag_result = self.read_tag_token()
            if tag_result:
                literal, token_type, line, pos = tag_result
                # If we just read a summary start tag, set flag for next token
                if token_type == TokenType.TAG_SUMMARY_START:
                    self.in_summary_comment = True
                return Token(token_type, literal, line, pos)

        # Check for underscore-wrapped literals
        if self.current_char == "_":
            start_pos = self.position
            literal_result = self.read_underscore_literal()
            if literal_result:
                literal, token_type, line, pos = literal_result
                return Token(token_type, literal, line, pos)

            # If read_underscore_literal returned None and consumed characters
            # we have an invalid pattern
            if self.position > start_pos:
                # We've consumed some characters - it's an invalid pattern
                # Continue consuming any remaining underscores
                while self.current_char == "_":
                    self.advance()
                illegal_literal = self.source[start_pos : self.position]
                return Token(TokenType.MISC_ILLEGAL, illegal_literal, token_line, token_column)

            # Check if this is an incomplete underscore pattern
            next_char = self.peek()
            next_next_char = self.peek(2)
            if next_char and (
                next_char.isdigit() or (next_char == "." and next_next_char is not None and next_next_char.isdigit())
            ):
                # Invalid underscore pattern
                self.advance()  # Skip underscore

                # Read the number part
                if self.current_char == "." or (self.current_char and self.current_char.isdigit()):
                    self.read_number()

                # Consume trailing underscores
                while self.current_char == "_":
                    self.advance()

                illegal_literal = self.source[start_pos : self.position]
                return Token(TokenType.MISC_ILLEGAL, illegal_literal, token_line, token_column)

        # Check for double-asterisk wrapped keywords or operator
        if self.current_char == "*" and self.peek() == "*":
            asterisk_result = self.read_double_asterisk_keyword()
            if asterisk_result:
                literal, token_type, line, pos = asterisk_result
                return Token(token_type, literal, line, pos)
            else:
                # Not a wrapped keyword, treat as ** operator
                self.advance()  # First *
                self.advance()  # Second *
                return Token(TokenType.OP_TWO_STARS, "**", token_line, token_column)

        # Numbers
        next_char = self.peek()
        if self.current_char.isdigit() or (self.current_char == "." and next_char and next_char.isdigit()):
            literal, is_float, _, _ = self.read_number()

            # Check for invalid trailing underscore
            if self.current_char == "_":
                start_pos = self.position - len(literal)
                self.advance()
                illegal_literal = self.source[start_pos : self.position]
                return Token(TokenType.MISC_ILLEGAL, illegal_literal, token_line, token_column)

            # Prepend "0" to literals starting with "."
            if literal.startswith("."):
                literal = "0" + literal

            token_type = TokenType.LIT_FLOAT if is_float else TokenType.LIT_WHOLE_NUMBER
            return Token(token_type, literal, token_line, token_column)

        # Identifiers and keywords
        if self.current_char.isalpha() or self.current_char == "_":
            # Handle multiple underscores followed by number
            if self.current_char == "_":
                underscore_count = 0
                temp_pos = self.position
                while temp_pos < len(self.source) and self.source[temp_pos] == "_":
                    underscore_count += 1
                    temp_pos += 1

                if temp_pos < len(self.source) and (
                    self.source[temp_pos].isdigit()
                    or (
                        self.source[temp_pos] == "."
                        and temp_pos + 1 < len(self.source)
                        and self.source[temp_pos + 1].isdigit()
                    )
                ):
                    if underscore_count > 1:
                        # Invalid pattern
                        start_pos = self.position
                        for _ in range(underscore_count):
                            self.advance()

                        self.read_number()

                        while self.current_char == "_":
                            self.advance()

                        illegal_literal = self.source[start_pos : self.position]
                        return Token(TokenType.MISC_ILLEGAL, illegal_literal, token_line, token_column)

            # Read identifier
            literal, _, _ = self.read_identifier()

            # Special check for "Yes/No" type keyword
            if (
                literal is not None
                and literal.lower() == "yes"
                and self.current_char == "/"
                and self.peek() is not None
                and self.peek().lower() == "n"  # type: ignore[union-attr]
                and self.peek(2) is not None
                and self.peek(2).lower() == "o"  # type: ignore[union-attr]
            ):
                # Consume "/No"
                self.advance()  # Skip '/'
                self.advance()  # Skip 'N' or 'n'
                self.advance()  # Skip 'o' or 'O'
                # Return the Yes/No keyword token
                return Token(TokenType.KW_YES_NO, "Yes/No", token_line, token_column)

            # Check for multi-word keywords
            multi_word, _ = self.check_multi_word_keyword(literal, token_line, token_column)
            if multi_word:
                token_type, canonical_literal = lookup_token_type(multi_word)
                return Token(token_type, canonical_literal, token_line, token_column)

            # Single word keyword or identifier
            token_type, canonical_literal = lookup_token_type(literal)
            return Token(token_type, canonical_literal, token_line, token_column)

        # Strings
        if self.current_char in ('"', "'"):
            literal, _, _ = self.read_string()

            # Check if it's a URL
            url_to_check = literal[1:-1] if len(literal) > 2 else literal
            token_type = TokenType.LIT_URL if is_valid_url(url_to_check) else TokenType.LIT_TEXT
            return Token(token_type, literal, token_line, token_column)

        # Backticks
        if self.current_char == "`":
            # Check for triple backticks
            if self.peek() == "`" and self.peek(2) == "`":
                literal, _, _ = self.read_triple_backtick_string()
                return Token(TokenType.LIT_TRIPLE_BACKTICK, literal, token_line, token_column)

            # Single backtick identifier
            start_pos = self.position
            self.advance()  # Skip opening backtick

            # For backtick identifiers:
            # - If backtick is at position 1, report position 1
            # - Otherwise, report position after the backtick
            identifier_column = token_column if token_column == 1 else self.column
            identifier_start = self.position
            while self.current_char and self.current_char != "`":
                self.advance()

            identifier = self.source[identifier_start : self.position]

            if self.current_char == "`" and identifier:
                from machine_dialect.lexer.tokens import is_valid_identifier

                if is_valid_identifier(identifier):
                    self.advance()  # Skip closing backtick
                    token_type, canonical_literal = lookup_token_type(identifier)

                    # Keywords, stopwords, and boolean literals in backticks become identifiers
                    # Backticks force the content to be treated as an identifier
                    from machine_dialect.lexer.tokens import TokenMetaType

                    if (
                        token_type == TokenType.MISC_STOPWORD
                        or token_type.meta_type == TokenMetaType.KW
                        or token_type in (TokenType.LIT_YES, TokenType.LIT_NO)
                    ):
                        token_type = TokenType.MISC_IDENT
                        canonical_literal = identifier

                    if token_type != TokenType.MISC_ILLEGAL:
                        # Check if this identifier is followed by 's for possessive
                        # This allows us to handle `person`'s name patterns
                        if self.current_char == "'" and self.peek() == "s":
                            # Skip the apostrophe and 's'
                            self.advance()  # Skip '
                            self.advance()  # Skip 's'
                            # Return a special token that indicates possessive access
                            # The literal includes the identifier for context
                            return Token(TokenType.PUNCT_APOSTROPHE_S, canonical_literal, token_line, identifier_column)
                        return Token(token_type, canonical_literal, token_line, identifier_column)

            # Invalid backtick usage
            self._restore_position(start_pos)

            # Single backtick is illegal
            self.advance()
            return Token(TokenType.MISC_ILLEGAL, "`", token_line, token_column)

        # Check for dash at line start in list context
        if self.current_char == "-" and self.at_line_start and in_list_context:
            # In list context, dash at line start is a list marker
            self.advance()
            return Token(TokenType.PUNCT_DASH, "-", token_line, token_column)

        # Single character tokens (operators, delimiters, punctuation)
        if self.current_char in CHAR_TO_TOKEN_MAP:
            char = self.current_char
            self.advance()

            # Check for multi-character operators
            if char == "<" and self.current_char == "=":
                self.advance()
                return Token(TokenType.OP_LTE, "<=", token_line, token_column)
            elif char == ">" and self.current_char == "=":
                self.advance()
                return Token(TokenType.OP_GTE, ">=", token_line, token_column)
            elif char == "#":
                # Check for ##, ###, or ####
                if self.current_char == "#":
                    self.advance()
                    if self.current_char == "#":
                        self.advance()
                        if self.current_char == "#":
                            self.advance()
                            return Token(TokenType.PUNCT_HASH_QUAD, "####", token_line, token_column)
                        return Token(TokenType.PUNCT_HASH_TRIPLE, "###", token_line, token_column)
                    return Token(TokenType.PUNCT_HASH_DOUBLE, "##", token_line, token_column)
            elif char == "-":
                # Check for --- (frontmatter delimiter)
                if self.current_char == "-" and self.peek() == "-":
                    self.advance()  # Second dash
                    self.advance()  # Third dash
                    return Token(TokenType.PUNCT_FRONTMATTER, "---", token_line, token_column)

            # Single character token
            token_type = CHAR_TO_TOKEN_MAP[char]
            return Token(token_type, char, token_line, token_column)

        # Unknown character - illegal token
        char = self.current_char
        self.advance()
        return Token(TokenType.MISC_ILLEGAL, char, token_line, token_column)
