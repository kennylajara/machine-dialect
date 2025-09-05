from machine_dialect.lexer import Lexer, TokenType
from machine_dialect.lexer.tests.helpers import collect_all_tokens


class TestBacktickIdentifiers:
    def test_backtick_wrapped_identifier(self) -> None:
        """Test backtick-wrapped identifier."""
        source = "`identifier`"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "identifier"

    def test_backtick_wrapped_keyword(self) -> None:
        """Test that backtick-wrapped keywords become identifiers."""
        source = "`define`"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "define"

    def test_backtick_wrapped_number(self) -> None:
        """Test that backtick-wrapped numbers are not valid identifiers."""
        source = "`42`"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        # `42` is not a valid identifier, so backtick is illegal, then 42, then backtick
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.MISC_ILLEGAL
        assert tokens[0].literal == "`"
        assert tokens[1].type == TokenType.LIT_WHOLE_NUMBER
        assert tokens[1].literal == "42"
        assert tokens[2].type == TokenType.MISC_ILLEGAL
        assert tokens[2].literal == "`"

    def test_empty_backticks(self) -> None:
        """Test that empty backticks are treated as illegal."""
        source = "``"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        # Empty content is not a valid identifier, so both backticks are illegal
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.MISC_ILLEGAL
        assert tokens[0].literal == "`"
        assert tokens[1].type == TokenType.MISC_ILLEGAL
        assert tokens[1].literal == "`"

    def test_unwrapped_identifier(self) -> None:
        """Test unwrapped identifier (backward compatibility)."""
        source = "identifier"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "identifier"

    def test_mixed_usage_in_expression(self) -> None:
        """Test both wrapped and unwrapped identifiers in same expression."""
        source = "Set `x` to y"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 4
        assert tokens[0].type == TokenType.KW_SET
        assert tokens[0].literal == "Set"
        assert tokens[1].type == TokenType.MISC_IDENT
        assert tokens[1].literal == "x"
        assert tokens[2].type == TokenType.KW_TO
        assert tokens[2].literal == "to"
        assert tokens[3].type == TokenType.MISC_IDENT
        assert tokens[3].literal == "y"

    def test_unclosed_backtick(self) -> None:
        """Test unclosed backtick without closing backtick is treated as illegal."""
        source = "`unclosed"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        # Without closing backtick, the opening backtick is illegal
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.MISC_ILLEGAL
        assert tokens[0].literal == "`"
        assert tokens[1].type == TokenType.MISC_IDENT
        assert tokens[1].literal == "unclosed"

    def test_backtick_with_spaces(self) -> None:
        """Test backtick with spaces inside."""
        source = "`with spaces`"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "with spaces"

    def test_triple_backticks_still_work(self) -> None:
        """Test that triple backticks still work as string literals."""
        source = "```code block```"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.LIT_TRIPLE_BACKTICK
        assert tokens[0].literal == "code block"

    def test_backtick_with_hyphens(self) -> None:
        """Test backtick with hyphens inside."""
        source = "`my-identifier`"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "my-identifier"

    def test_backtick_with_spaces_and_hyphens(self) -> None:
        """Test backtick with both spaces and hyphens."""
        source = "`my-complex identifier`"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "my-complex identifier"

    def test_backtick_wrapped_type_keyword(self) -> None:
        """Test that type keywords like 'number' become identifiers in backticks."""
        source = "`number`"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.MISC_IDENT
        assert tokens[0].literal == "number"
