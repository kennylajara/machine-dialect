"""Tests for comment token recognition."""

from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tokens import TokenType


class TestComments:
    """Test comment token recognition."""

    def test_simple_comment(self) -> None:
        """Test simple comment within summary tags."""
        source = "<summary>This is a comment</summary>"
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        assert len(tokens) == 4
        assert tokens[0].type == TokenType.TAG_SUMMARY_START
        assert tokens[0].literal == "<summary>"
        assert tokens[1].type == TokenType.MISC_COMMENT
        assert tokens[1].literal == "This is a comment"
        assert tokens[2].type == TokenType.TAG_SUMMARY_END
        assert tokens[2].literal == "</summary>"
        assert tokens[3].type == TokenType.MISC_EOF

    def test_multiline_comment(self) -> None:
        """Test multiline comment within summary tags."""
        source = """<summary>
This is a comment
that spans multiple lines
</summary>"""
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        assert len(tokens) == 4
        assert tokens[0].type == TokenType.TAG_SUMMARY_START
        assert tokens[1].type == TokenType.MISC_COMMENT
        assert tokens[1].literal == "\nThis is a comment\nthat spans multiple lines\n"
        assert tokens[2].type == TokenType.TAG_SUMMARY_END
        assert tokens[3].type == TokenType.MISC_EOF

    def test_empty_comment(self) -> None:
        """Test empty comment within summary tags."""
        source = "<summary></summary>"
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        assert len(tokens) == 4
        assert tokens[0].type == TokenType.TAG_SUMMARY_START
        assert tokens[1].type == TokenType.MISC_COMMENT
        assert tokens[1].literal == ""
        assert tokens[2].type == TokenType.TAG_SUMMARY_END
        assert tokens[3].type == TokenType.MISC_EOF

    def test_comment_with_code_before_and_after(self) -> None:
        """Test comment with code before and after."""
        source = "set x to 10. <summary>This is a comment</summary> set y to 20."
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        # Check first part: set x to 10.
        assert tokens[0].type == TokenType.KW_SET
        assert tokens[1].type == TokenType.MISC_IDENT
        assert tokens[1].literal == "x"
        assert tokens[2].type == TokenType.KW_TO
        assert tokens[3].type == TokenType.LIT_WHOLE_NUMBER
        assert tokens[3].literal == "10"
        assert tokens[4].type == TokenType.PUNCT_PERIOD

        # Check comment part
        assert tokens[5].type == TokenType.TAG_SUMMARY_START
        assert tokens[6].type == TokenType.MISC_COMMENT
        assert tokens[6].literal == "This is a comment"
        assert tokens[7].type == TokenType.TAG_SUMMARY_END

        # Check second part: set y to 20.
        assert tokens[8].type == TokenType.KW_SET
        assert tokens[9].type == TokenType.MISC_IDENT
        assert tokens[9].literal == "y"
        assert tokens[10].type == TokenType.KW_TO
        assert tokens[11].type == TokenType.LIT_WHOLE_NUMBER
        assert tokens[11].literal == "20"
        assert tokens[12].type == TokenType.PUNCT_PERIOD
        assert tokens[13].type == TokenType.MISC_EOF

    def test_comment_case_insensitive_tags(self) -> None:
        """Test that summary tags are case-insensitive."""
        source = "<SUMMARY>This is a comment</SUMMARY>"
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        assert len(tokens) == 4
        assert tokens[0].type == TokenType.TAG_SUMMARY_START
        assert tokens[0].literal == "<summary>"  # Canonical form
        assert tokens[1].type == TokenType.MISC_COMMENT
        assert tokens[1].literal == "This is a comment"
        assert tokens[2].type == TokenType.TAG_SUMMARY_END
        assert tokens[2].literal == "</summary>"

    def test_mixed_case_tags(self) -> None:
        """Test mixed case summary tags."""
        source = "<SuMmArY>Mixed case comment</sUmMaRy>"
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        assert len(tokens) == 4
        assert tokens[0].type == TokenType.TAG_SUMMARY_START
        assert tokens[1].type == TokenType.MISC_COMMENT
        assert tokens[1].literal == "Mixed case comment"
        assert tokens[2].type == TokenType.TAG_SUMMARY_END

    def test_comment_with_special_characters(self) -> None:
        """Test comment containing special characters."""
        source = "<summary>Comment with special chars: !@#$%^&*()_+-=[]{}|;:'\",.<>?/`~</summary>"
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        assert len(tokens) == 4
        assert tokens[0].type == TokenType.TAG_SUMMARY_START
        assert tokens[1].type == TokenType.MISC_COMMENT
        assert tokens[1].literal == "Comment with special chars: !@#$%^&*()_+-=[]{}|;:'\",.<>?/`~"
        assert tokens[2].type == TokenType.TAG_SUMMARY_END

    def test_unclosed_summary_tag(self) -> None:
        """Test that unclosed summary tag creates a comment up to EOF."""
        source = "<summary>This is a comment without closing tag"
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        # Should tokenize as summary tag followed by comment content up to EOF
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.TAG_SUMMARY_START
        assert tokens[1].type == TokenType.MISC_COMMENT
        assert tokens[1].literal == "This is a comment without closing tag"
        assert tokens[2].type == TokenType.MISC_EOF

    def test_nested_tags_in_comment(self) -> None:
        """Test comment containing nested tags."""
        source = "<summary>Comment with <tag> and </tag> inside</summary>"
        lexer = Lexer(source)

        tokens = []
        while True:
            token = lexer.next_token()
            tokens.append(token)
            if token.type == TokenType.MISC_EOF:
                break

        assert len(tokens) == 4
        assert tokens[0].type == TokenType.TAG_SUMMARY_START
        assert tokens[1].type == TokenType.MISC_COMMENT
        assert tokens[1].literal == "Comment with <tag> and </tag> inside"
        assert tokens[2].type == TokenType.TAG_SUMMARY_END
