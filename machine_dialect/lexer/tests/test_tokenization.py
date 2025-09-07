import pytest

from machine_dialect.lexer import Lexer
from machine_dialect.lexer.tests.helpers import stream_and_assert_tokens
from machine_dialect.lexer.tokens import Token, TokenType


class TestLexer:
    @pytest.mark.parametrize(
        "input_text,expected_tokens",
        [
            # Boolean
            ("Yes", [Token(TokenType.LIT_YES, "Yes", line=1, position=1)]),
            ("No", [Token(TokenType.LIT_NO, "No", line=1, position=1)]),
            # Numbers
            ("123", [Token(TokenType.LIT_WHOLE_NUMBER, "123", line=1, position=1)]),
            ("3.14", [Token(TokenType.LIT_FLOAT, "3.14", line=1, position=1)]),
            ("0", [Token(TokenType.LIT_WHOLE_NUMBER, "0", line=1, position=1)]),
            # Strings
            ('"hello"', [Token(TokenType.LIT_TEXT, '"hello"', line=1, position=1)]),
            ("'world'", [Token(TokenType.LIT_TEXT, "'world'", line=1, position=1)]),
            ('""', [Token(TokenType.LIT_TEXT, '""', line=1, position=1)]),
            # Backtick identifiers (backticks consumed by lexer)
            ("`code`", [Token(TokenType.MISC_IDENT, "code", line=1, position=1)]),
            ("`variable_name`", [Token(TokenType.MISC_IDENT, "variable_name", line=1, position=1)]),
            # Numbers in backticks are not valid identifiers, so we get illegal tokens
            (
                "`42`",
                [
                    Token(TokenType.MISC_ILLEGAL, "`", line=1, position=1),
                    Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=2),
                    Token(TokenType.MISC_ILLEGAL, "`", line=1, position=4),
                ],
            ),
            # Empty backticks produce two illegal backtick tokens
            (
                "``",
                [
                    Token(TokenType.MISC_ILLEGAL, "`", line=1, position=1),
                    Token(TokenType.MISC_ILLEGAL, "`", line=1, position=2),
                ],
            ),
            # Triple backtick strings
            ("```python```", [Token(TokenType.LIT_TRIPLE_BACKTICK, "python", line=1, position=1)]),
            (
                "```\ncode block\n```",
                [Token(TokenType.LIT_TRIPLE_BACKTICK, "\ncode block\n", line=1, position=1)],
            ),
            (
                "```js\nconst x = 42;\n```",
                [Token(TokenType.LIT_TRIPLE_BACKTICK, "js\nconst x = 42;\n", line=1, position=1)],
            ),
            ("``````", [Token(TokenType.LIT_TRIPLE_BACKTICK, "", line=1, position=1)]),
            # Identifiers
            ("variable", [Token(TokenType.MISC_IDENT, "variable", line=1, position=1)]),
            ("_underscore", [Token(TokenType.MISC_IDENT, "_underscore", line=1, position=1)]),
            ("camelCase", [Token(TokenType.MISC_IDENT, "camelCase", line=1, position=1)]),
            ("var123", [Token(TokenType.MISC_IDENT, "var123", line=1, position=1)]),
            # Keywords
            ("if", [Token(TokenType.KW_IF, "if", line=1, position=1)]),
            ("else", [Token(TokenType.KW_ELSE, "else", line=1, position=1)]),
            ("define", [Token(TokenType.KW_DEFINE, "define", line=1, position=1)]),
            ("empty", [Token(TokenType.KW_EMPTY, "empty", line=1, position=1)]),
            ("entrypoint", [Token(TokenType.KW_ENTRYPOINT, "entrypoint", line=1, position=1)]),
            ("filter", [Token(TokenType.KW_FILTER, "filter", line=1, position=1)]),
            ("prompt", [Token(TokenType.KW_PROMPT, "prompt", line=1, position=1)]),
            ("template", [Token(TokenType.KW_TEMPLATE, "template", line=1, position=1)]),
            ("give back", [Token(TokenType.KW_RETURN, "give back", line=1, position=1)]),
            ("gives back", [Token(TokenType.KW_RETURN, "gives back", line=1, position=1)]),
            ("and", [Token(TokenType.KW_AND, "and", line=1, position=1)]),
            ("or", [Token(TokenType.KW_OR, "or", line=1, position=1)]),
            ("is", [Token(TokenType.KW_IS, "is", line=1, position=1)]),
            ("as", [Token(TokenType.KW_AS, "as", line=1, position=1)]),
            ("with", [Token(TokenType.KW_WITH, "with", line=1, position=1)]),
            ("then", [Token(TokenType.KW_THEN, "then", line=1, position=1)]),
            # More keywords
            ("action", [Token(TokenType.KW_ACTION, "action", line=1, position=1)]),
            ("actions", [Token(TokenType.KW_ACTION, "actions", line=1, position=1)]),
            # "apply" is reserved for future use, currently not mapped
            ("behavior", [Token(TokenType.KW_BEHAVIOR, "behavior", line=1, position=1)]),
            # Backslash
            ("\\", [Token(TokenType.PUNCT_BACKSLASH, "\\", line=1, position=1)]),
            (
                "x\\y",
                [
                    Token(TokenType.MISC_IDENT, "x", line=1, position=1),
                    Token(TokenType.PUNCT_BACKSLASH, "\\", line=1, position=2),
                    Token(TokenType.MISC_IDENT, "y", line=1, position=3),
                ],
            ),
            # Frontmatter delimiter
            ("---", [Token(TokenType.PUNCT_FRONTMATTER, "---", line=1, position=1)]),
            (
                "-- -",
                [
                    Token(TokenType.OP_MINUS, "-", line=1, position=1),
                    Token(TokenType.OP_MINUS, "-", line=1, position=2),
                    Token(TokenType.OP_MINUS, "-", line=1, position=4),
                ],
            ),
            (
                "--",
                [
                    Token(TokenType.OP_MINUS, "-", line=1, position=1),
                    Token(TokenType.OP_MINUS, "-", line=1, position=2),
                ],
            ),
            ("behaviors", [Token(TokenType.KW_BEHAVIOR, "behaviors", line=1, position=1)]),
            ("behaviour", [Token(TokenType.KW_BEHAVIOR, "behaviour", line=1, position=1)]),
            ("behaviours", [Token(TokenType.KW_BEHAVIOR, "behaviours", line=1, position=1)]),
            ("Yes/No", [Token(TokenType.KW_YES_NO, "Yes/No", line=1, position=1)]),
            ("Float", [Token(TokenType.KW_FLOAT, "Float", line=1, position=1)]),
            ("Floats", [Token(TokenType.KW_FLOAT, "Floats", line=1, position=1)]),
            ("from", [Token(TokenType.KW_FROM, "from", line=1, position=1)]),
            ("interaction", [Token(TokenType.KW_INTERACTION, "interaction", line=1, position=1)]),
            ("interactions", [Token(TokenType.KW_INTERACTION, "interactions", line=1, position=1)]),
            ("List", [Token(TokenType.KW_LIST, "List", line=1, position=1)]),
            ("not", [Token(TokenType.KW_NEGATION, "not", line=1, position=1)]),
            ("Number", [Token(TokenType.KW_NUMBER, "Number", line=1, position=1)]),
            ("Numbers", [Token(TokenType.KW_NUMBER, "Numbers", line=1, position=1)]),
            ("otherwise", [Token(TokenType.KW_ELSE, "otherwise", line=1, position=1)]),
            ("rule", [Token(TokenType.KW_RULE, "rule", line=1, position=1)]),
            ("Set", [Token(TokenType.KW_SET, "Set", line=1, position=1)]),
            ("Utility", [Token(TokenType.KW_UTILITY, "Utility", line=1, position=1)]),
            ("take", [Token(TokenType.KW_TAKE, "take", line=1, position=1)]),
            ("takes", [Token(TokenType.KW_TAKE, "takes", line=1, position=1)]),
            ("Tell", [Token(TokenType.KW_TELL, "Tell", line=1, position=1)]),
            ("text", [Token(TokenType.KW_TEXT, "text", line=1, position=1)]),
            ("texts", [Token(TokenType.KW_TEXT, "texts", line=1, position=1)]),
            ("to", [Token(TokenType.KW_TO, "to", line=1, position=1)]),
            ("trait", [Token(TokenType.KW_TRAIT, "trait", line=1, position=1)]),
            ("traits", [Token(TokenType.KW_TRAIT, "traits", line=1, position=1)]),
            ("Use", [Token(TokenType.KW_USE, "Use", line=1, position=1)]),
            ("URL", [Token(TokenType.KW_URL, "URL", line=1, position=1)]),
            ("URLs", [Token(TokenType.KW_URL, "URLs", line=1, position=1)]),
            ("Date", [Token(TokenType.KW_DATE, "Date", line=1, position=1)]),
            ("Dates", [Token(TokenType.KW_DATE, "Dates", line=1, position=1)]),
            ("DateTime", [Token(TokenType.KW_DATETIME, "DateTime", line=1, position=1)]),
            ("DateTimes", [Token(TokenType.KW_DATETIME, "DateTimes", line=1, position=1)]),
            ("Time", [Token(TokenType.KW_TIME, "Time", line=1, position=1)]),
            ("Times", [Token(TokenType.KW_TIME, "Times", line=1, position=1)]),
            ("DataType", [Token(TokenType.KW_DATATYPE, "DataType", line=1, position=1)]),
            # Single character operators
            ("+", [Token(TokenType.OP_PLUS, "+", line=1, position=1)]),
            ("-", [Token(TokenType.OP_MINUS, "-", line=1, position=1)]),
            ("/", [Token(TokenType.OP_DIVISION, "/", line=1, position=1)]),
            ("=", [Token(TokenType.OP_ASSIGN, "=", line=1, position=1)]),
            ("<", [Token(TokenType.OP_LT, "<", line=1, position=1)]),
            (">", [Token(TokenType.OP_GT, ">", line=1, position=1)]),
            ("*", [Token(TokenType.OP_STAR, "*", line=1, position=1)]),
            # Multi-character operators
            ("**", [Token(TokenType.OP_TWO_STARS, "**", line=1, position=1)]),
            # Delimiters
            ("(", [Token(TokenType.DELIM_LPAREN, "(", line=1, position=1)]),
            (")", [Token(TokenType.DELIM_RPAREN, ")", line=1, position=1)]),
            ("{", [Token(TokenType.DELIM_LBRACE, "{", line=1, position=1)]),
            ("}", [Token(TokenType.DELIM_RBRACE, "}", line=1, position=1)]),
            # Punctuation
            (";", [Token(TokenType.PUNCT_SEMICOLON, ";", line=1, position=1)]),
            (",", [Token(TokenType.PUNCT_COMMA, ",", line=1, position=1)]),
            (".", [Token(TokenType.PUNCT_PERIOD, ".", line=1, position=1)]),
            (":", [Token(TokenType.PUNCT_COLON, ":", line=1, position=1)]),
            ("#", [Token(TokenType.PUNCT_HASH, "#", line=1, position=1)]),
            # Complex expressions
            (
                "x = 42",
                [
                    Token(TokenType.MISC_IDENT, "x", line=1, position=1),
                    Token(TokenType.OP_ASSIGN, "=", line=1, position=3),
                    Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=5),
                ],
            ),
            (
                "if (x > 0)",
                [
                    Token(TokenType.KW_IF, "if", line=1, position=1),
                    Token(TokenType.DELIM_LPAREN, "(", line=1, position=4),
                    Token(TokenType.MISC_IDENT, "x", line=1, position=5),
                    Token(TokenType.OP_GT, ">", line=1, position=7),
                    Token(TokenType.LIT_WHOLE_NUMBER, "0", line=1, position=9),
                    Token(TokenType.DELIM_RPAREN, ")", line=1, position=10),
                ],
            ),
            (
                "x # comment",
                [
                    Token(TokenType.MISC_IDENT, "x", line=1, position=1),
                    Token(TokenType.PUNCT_HASH, "#", line=1, position=3),
                    Token(TokenType.MISC_IDENT, "comment", line=1, position=5),
                ],
            ),
            (
                'Set `name` to _"John"_',
                [
                    Token(TokenType.KW_SET, "Set", line=1, position=1),
                    Token(TokenType.MISC_IDENT, "name", line=1, position=6),
                    Token(TokenType.KW_TO, "to", line=1, position=12),
                    Token(TokenType.LIT_TEXT, '"John"', line=1, position=15),
                ],
            ),
            (
                "if **x** is greater than 0, then give back _Yes_",
                [
                    Token(TokenType.KW_IF, "if", line=1, position=1),
                    Token(TokenType.OP_TWO_STARS, "**", line=1, position=4),
                    Token(TokenType.MISC_IDENT, "x", line=1, position=6),
                    Token(TokenType.OP_TWO_STARS, "**", line=1, position=7),
                    Token(TokenType.OP_GT, "is greater than", line=1, position=10),
                    Token(TokenType.LIT_WHOLE_NUMBER, "0", line=1, position=26),
                    Token(TokenType.PUNCT_COMMA, ",", line=1, position=27),
                    Token(TokenType.KW_THEN, "then", line=1, position=29),
                    Token(TokenType.KW_RETURN, "give back", line=1, position=34),
                    Token(TokenType.LIT_YES, "Yes", line=1, position=44),
                ],
            ),
            (
                "if x > 0 then gives back Yes",
                [
                    Token(TokenType.KW_IF, "if", line=1, position=1),
                    Token(TokenType.MISC_IDENT, "x", line=1, position=4),
                    Token(TokenType.OP_GT, ">", line=1, position=6),
                    Token(TokenType.LIT_WHOLE_NUMBER, "0", line=1, position=8),
                    Token(TokenType.KW_THEN, "then", line=1, position=10),
                    Token(TokenType.KW_RETURN, "gives back", line=1, position=15),
                    Token(TokenType.LIT_YES, "Yes", line=1, position=26),
                ],
            ),
            (
                "define rule that give back 42",
                [
                    Token(TokenType.KW_DEFINE, "define", line=1, position=1),
                    Token(TokenType.KW_RULE, "rule", line=1, position=8),
                    Token(TokenType.MISC_STOPWORD, "that", line=1, position=13),
                    Token(TokenType.KW_RETURN, "give back", line=1, position=18),
                    Token(TokenType.LIT_WHOLE_NUMBER, "42", line=1, position=28),
                ],
            ),
        ],
    )
    def test_lexer_tokenization(self, input_text: str, expected_tokens: list[Token]) -> None:
        lexer = Lexer(input_text)
        stream_and_assert_tokens(lexer, expected_tokens)

    @pytest.mark.parametrize(
        "input_text, expected_tokens",
        [
            # Basic tag tokens
            ("<summary>", [Token(TokenType.TAG_SUMMARY_START, "<summary>", line=1, position=1)]),
            ("</summary>", [Token(TokenType.TAG_SUMMARY_END, "</summary>", line=1, position=1)]),
            ("<details>", [Token(TokenType.TAG_DETAILS_START, "<details>", line=1, position=1)]),
            ("</details>", [Token(TokenType.TAG_DETAILS_END, "</details>", line=1, position=1)]),
            # Case insensitive
            ("<SUMMARY>", [Token(TokenType.TAG_SUMMARY_START, "<summary>", line=1, position=1)]),
            ("</Summary>", [Token(TokenType.TAG_SUMMARY_END, "</summary>", line=1, position=1)]),
            ("<DETAILS>", [Token(TokenType.TAG_DETAILS_START, "<details>", line=1, position=1)]),
            ("</Details>", [Token(TokenType.TAG_DETAILS_END, "</details>", line=1, position=1)]),
            # Mixed case
            ("<SuMmArY>", [Token(TokenType.TAG_SUMMARY_START, "<summary>", line=1, position=1)]),
            ("</DeTaIlS>", [Token(TokenType.TAG_DETAILS_END, "</details>", line=1, position=1)]),
            # Tags with content
            (
                "<summary>This is a summary</summary>",
                [
                    Token(TokenType.TAG_SUMMARY_START, "<summary>", line=1, position=1),
                    Token(TokenType.MISC_COMMENT, "This is a summary", line=1, position=10),
                    Token(TokenType.TAG_SUMMARY_END, "</summary>", line=1, position=27),
                ],
            ),
            # Now "summary" and "details" as words should be identifiers
            ("summary", [Token(TokenType.MISC_IDENT, "summary", line=1, position=1)]),
            ("details", [Token(TokenType.MISC_IDENT, "details", line=1, position=1)]),
            # Invalid tags should not be recognized as tags
            (
                "<invalid>",
                [
                    Token(TokenType.OP_LT, "<", line=1, position=1),
                    Token(TokenType.MISC_IDENT, "invalid", line=1, position=2),
                    Token(TokenType.OP_GT, ">", line=1, position=9),
                ],
            ),
            # Less than operator should still work
            (
                "x < 5",
                [
                    Token(TokenType.MISC_IDENT, "x", line=1, position=1),
                    Token(TokenType.OP_LT, "<", line=1, position=3),
                    Token(TokenType.LIT_WHOLE_NUMBER, "5", line=1, position=5),
                ],
            ),
        ],
    )
    def test_tag_tokens(self, input_text: str, expected_tokens: list[Token]) -> None:
        lexer = Lexer(input_text)
        stream_and_assert_tokens(lexer, expected_tokens)
