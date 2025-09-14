"""Test list-related token recognition in the lexer."""

from machine_dialect.lexer import Lexer, TokenType


class TestListMarkers:
    """Test recognition of list markers (dash vs minus)."""

    def test_dash_at_line_start(self) -> None:
        """Test that dash at line start is recognized as PUNCT_DASH in list context."""
        lexer = Lexer('- _"apple"_')

        # Without list context, it's OP_MINUS
        token = lexer.next_token(in_list_context=False)
        assert token.type == TokenType.OP_MINUS
        assert token.literal == "-"

        # Reset lexer
        lexer = Lexer('- _"apple"_')

        # With list context, it's PUNCT_DASH
        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_DASH
        assert token.literal == "-"

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.LIT_TEXT
        assert token.literal == '"apple"'

    def test_dash_after_whitespace(self) -> None:
        """Test that dash after whitespace at line start is PUNCT_DASH in list context."""
        lexer = Lexer('  - _"apple"_')

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_DASH
        assert token.literal == "-"

    def test_dash_after_block_marker(self) -> None:
        """Test that dash after block marker (>) is PUNCT_DASH in list context."""
        lexer = Lexer('> - _"apple"_')

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.OP_GT

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_DASH
        assert token.literal == "-"

    def test_dash_in_expression(self) -> None:
        """Test that dash in expression context is OP_MINUS."""
        lexer = Lexer("_5_ - _3_")

        # First number
        token = lexer.next_token()
        assert token.type == TokenType.LIT_WHOLE_NUMBER

        # Minus operator
        token = lexer.next_token()
        assert token.type == TokenType.OP_MINUS
        assert token.literal == "-"

        # Second number
        token = lexer.next_token()
        assert token.type == TokenType.LIT_WHOLE_NUMBER

    def test_multiple_dashes_at_line_start(self) -> None:
        """Test that --- at line start is PUNCT_FRONTMATTER."""
        lexer = Lexer("---")

        token = lexer.next_token()
        assert token.type == TokenType.PUNCT_FRONTMATTER
        assert token.literal == "---"

    def test_dash_on_new_line(self) -> None:
        """Test dash recognition across multiple lines in list context."""
        source = """Set `x` to _5_.
- _"apple"_
- _"banana"_"""

        lexer = Lexer(source)

        # First line: Set `x` to _5_ (not in list context)
        token = lexer.next_token()
        assert token.type == TokenType.KW_SET

        token = lexer.next_token()
        assert token.type == TokenType.MISC_IDENT

        token = lexer.next_token()
        assert token.type == TokenType.KW_TO

        token = lexer.next_token()
        assert token.type == TokenType.LIT_WHOLE_NUMBER

        token = lexer.next_token()
        assert token.type == TokenType.PUNCT_PERIOD

        # Second line: - _"apple"_ (in list context)
        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_DASH
        assert token.literal == "-"

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.LIT_TEXT

        # Third line: - _"banana"_ (in list context)
        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_DASH
        assert token.literal == "-"

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.LIT_TEXT


class TestListKeywords:
    """Test new keywords for list operations."""

    def test_list_operation_keywords(self) -> None:
        """Test recognition of list operation keywords."""
        keywords = [
            ("add", TokenType.KW_ADD),
            ("remove", TokenType.KW_REMOVE),
            ("insert", TokenType.KW_INSERT),
            ("has", TokenType.KW_HAS),
        ]

        for literal, expected_type in keywords:
            lexer = Lexer(literal)
            token = lexer.next_token()
            assert token.type == expected_type
            assert token.literal == literal

    def test_list_type_keywords(self) -> None:
        """Test recognition of list type keywords."""
        keywords = [
            ("Ordered List", TokenType.KW_ORDERED_LIST),
            ("Unordered List", TokenType.KW_UNORDERED_LIST),
            ("Named List", TokenType.KW_NAMED_LIST),
        ]

        for literal, expected_type in keywords:
            lexer = Lexer(literal)
            token = lexer.next_token()
            assert token.type == expected_type
            assert token.literal == literal

    def test_list_access_keywords(self) -> None:
        """Test recognition of list access keywords."""
        keywords = [
            ("first", TokenType.KW_FIRST),
            ("second", TokenType.KW_SECOND),
            ("third", TokenType.KW_THIRD),
            ("last", TokenType.KW_LAST),
            ("item", TokenType.KW_ITEM),
            ("of", TokenType.KW_OF),
        ]

        for literal, expected_type in keywords:
            lexer = Lexer(literal)
            token = lexer.next_token()
            assert token.type == expected_type
            assert token.literal == literal

    def test_iteration_keywords(self) -> None:
        """Test recognition of iteration keywords."""
        keywords = [
            ("for", TokenType.KW_FOR),
            ("each", TokenType.KW_EACH),
            ("in", TokenType.KW_IN),
        ]

        for literal, expected_type in keywords:
            lexer = Lexer(literal)
            token = lexer.next_token()
            assert token.type == expected_type
            assert token.literal == literal

    def test_named_list_keywords(self) -> None:
        """Test recognition of named list keywords."""
        keywords = [
            ("name", TokenType.KW_NAME),
            ("names", TokenType.KW_NAME),  # Plural maps to same token type
            ("content", TokenType.KW_CONTENT),
            ("contents", TokenType.KW_CONTENT),  # Plural maps to same token type
        ]

        for literal, expected_type in keywords:
            lexer = Lexer(literal)
            token = lexer.next_token()
            assert token.type == expected_type
            # Literals are preserved as-is in the token
            assert token.literal == literal


class TestComplexListScenarios:
    """Test complex scenarios involving list tokens."""

    def test_list_with_colon(self) -> None:
        """Test dash followed by identifier and colon (named list syntax)."""
        lexer = Lexer("- name: `value`")

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_DASH

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.KW_NAME

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_COLON

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.MISC_IDENT
        assert token.literal == "value"

    def test_numbered_list_marker(self) -> None:
        """Test numbered list markers (1., 2., etc)."""
        lexer = Lexer("1. first\n2. second")

        # 1.
        token = lexer.next_token()
        assert token.type == TokenType.LIT_WHOLE_NUMBER
        assert token.literal == "1"

        token = lexer.next_token()
        assert token.type == TokenType.PUNCT_PERIOD

        # first
        token = lexer.next_token()
        assert token.type == TokenType.KW_FIRST

        # 2.
        token = lexer.next_token()
        assert token.type == TokenType.LIT_WHOLE_NUMBER
        assert token.literal == "2"

        token = lexer.next_token()
        assert token.type == TokenType.PUNCT_PERIOD

        # second
        token = lexer.next_token()
        assert token.type == TokenType.KW_SECOND

    def test_expression_with_negative_number(self) -> None:
        """Test that negative numbers still work correctly."""
        lexer = Lexer("_-42_")

        token = lexer.next_token()
        assert token.type == TokenType.LIT_WHOLE_NUMBER
        assert token.literal == "-42"

    def test_subtraction_vs_list_marker(self) -> None:
        """Test differentiating subtraction from list markers."""
        # Subtraction (not in list context)
        lexer = Lexer("`x` - `y`")

        token = lexer.next_token()
        assert token.type == TokenType.MISC_IDENT

        token = lexer.next_token()
        assert token.type == TokenType.OP_MINUS

        token = lexer.next_token()
        assert token.type == TokenType.MISC_IDENT

        # List marker on new line (in list context)
        lexer = Lexer('\n- _"apple"_')

        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_DASH

    def test_list_with_negative_number(self) -> None:
        """Test list items that include negative numbers."""
        lexer = Lexer("- _-42_")

        # First dash is list marker in list context
        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.PUNCT_DASH

        # The literal with negative number
        token = lexer.next_token(in_list_context=True)
        assert token.type == TokenType.LIT_WHOLE_NUMBER
        assert token.literal == "-42"
