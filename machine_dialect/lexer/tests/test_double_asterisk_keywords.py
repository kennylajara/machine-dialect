from machine_dialect.lexer import Lexer, TokenType
from machine_dialect.lexer.tests.helpers import collect_all_tokens


class TestDoubleAsteriskKeywords:
    def test_wrapped_keyword_define(self) -> None:
        """Test double-asterisk-wrapped keyword 'define'."""
        source = "**define**"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.KW_DEFINE
        assert tokens[0].literal == "define"

    def test_wrapped_keyword_rule(self) -> None:
        """Test double-asterisk-wrapped keyword 'rule'."""
        source = "**rule**"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.KW_RULE
        assert tokens[0].literal == "rule"

    def test_wrapped_keyword_set(self) -> None:
        """Test double-asterisk-wrapped keyword 'Set'."""
        source = "**Set**"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.KW_SET
        assert tokens[0].literal == "Set"

    def test_wrapped_multi_word_keyword(self) -> None:
        """Test double-asterisk-wrapped multi-word keyword."""
        source = "**give back**"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.KW_RETURN
        assert tokens[0].literal == "give back"

    def test_unwrapped_keyword(self) -> None:
        """Test unwrapped keyword (backward compatibility)."""
        source = "define"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.KW_DEFINE
        assert tokens[0].literal == "define"

    def test_incomplete_wrapped_keyword(self) -> None:
        """Test incomplete wrapped keyword (missing closing asterisks)."""
        source = "**define"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 2
        assert tokens[0].type == TokenType.OP_TWO_STARS
        assert tokens[0].literal == "**"
        assert tokens[1].type == TokenType.KW_DEFINE
        assert tokens[1].literal == "define"

    def test_non_keyword_wrapped(self) -> None:
        """Test non-keyword wrapped in double asterisks."""
        source = "**notakeyword**"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.OP_TWO_STARS
        assert tokens[0].literal == "**"
        assert tokens[1].type == TokenType.MISC_IDENT
        assert tokens[1].literal == "notakeyword"
        assert tokens[2].type == TokenType.OP_TWO_STARS
        assert tokens[2].literal == "**"

    def test_mixed_usage_in_expression(self) -> None:
        """Test both wrapped and unwrapped keywords in same expression."""
        source = "**define** a rule that takes"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 5
        assert tokens[0].type == TokenType.KW_DEFINE
        assert tokens[0].literal == "define"
        assert tokens[1].type == TokenType.MISC_STOPWORD  # "a"
        assert tokens[2].type == TokenType.KW_RULE
        assert tokens[2].literal == "rule"
        assert tokens[3].type == TokenType.MISC_STOPWORD  # "that"
        assert tokens[4].type == TokenType.KW_TAKE
        assert tokens[4].literal == "takes"

    def test_operator_usage(self) -> None:
        """Test that ** operator still works correctly."""
        source = "2 ** 3"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.LIT_WHOLE_NUMBER
        assert tokens[0].literal == "2"
        assert tokens[1].type == TokenType.OP_TWO_STARS
        assert tokens[1].literal == "**"
        assert tokens[2].type == TokenType.LIT_WHOLE_NUMBER
        assert tokens[2].literal == "3"

    def test_stopword_wrapped(self) -> None:
        """Test stopword wrapped in double asterisks (should not be recognized as keyword)."""
        source = "**the**"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.OP_TWO_STARS
        assert tokens[0].literal == "**"
        assert tokens[1].type == TokenType.MISC_STOPWORD
        assert tokens[1].literal == "the"
        assert tokens[2].type == TokenType.OP_TWO_STARS
        assert tokens[2].literal == "**"

    def test_boolean_literal_wrapped(self) -> None:
        """Test boolean literals wrapped in double asterisks (should not be recognized as keyword)."""
        source = "**Yes**"
        lexer = Lexer(source)
        tokens = collect_all_tokens(lexer)
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.OP_TWO_STARS
        assert tokens[0].literal == "**"
        assert tokens[1].type == TokenType.LIT_YES
        assert tokens[1].literal == "Yes"
        assert tokens[2].type == TokenType.OP_TWO_STARS
        assert tokens[2].literal == "**"
