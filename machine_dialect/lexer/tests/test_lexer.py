import pytest

from machine_dialect.lexer.tokens import Token, TokenType


class TestLexer:
    @pytest.mark.parametrize(  # type: ignore[misc]
        "input_text,expected_tokens",
        [
            # Numbers
            ("123", [Token(TokenType.LIT_INT, "123")]),
            ("3.14", [Token(TokenType.LIT_FLOAT, "3.14")]),
            ("0", [Token(TokenType.LIT_INT, "0")]),
            # Strings
            ('"hello"', [Token(TokenType.LIT_TEXT, '"hello"')]),
            ("'world'", [Token(TokenType.LIT_TEXT, "'world'")]),
            ('""', [Token(TokenType.LIT_TEXT, '""')]),
            # Backtick strings
            ("`code`", [Token(TokenType.LIT_BACKTICK, "`code`")]),
            ("`variable_name`", [Token(TokenType.LIT_BACKTICK, "`variable_name`")]),
            ("`42`", [Token(TokenType.LIT_BACKTICK, "`42`")]),
            ("``", [Token(TokenType.LIT_BACKTICK, "``")]),
            # Triple backtick strings
            ("```python```", [Token(TokenType.LIT_TRIPLE_BACKTICK, "```python```")]),
            (
                "```\ncode block\n```",
                [Token(TokenType.LIT_TRIPLE_BACKTICK, "```\ncode block\n```")],
            ),
            (
                "```js\nconst x = 42;\n```",
                [Token(TokenType.LIT_TRIPLE_BACKTICK, "```js\nconst x = 42;\n```")],
            ),
            ("``````", [Token(TokenType.LIT_TRIPLE_BACKTICK, "``````")]),
            # Identifiers
            ("variable", [Token(TokenType.MISC_IDENT, "variable")]),
            ("_underscore", [Token(TokenType.MISC_IDENT, "_underscore")]),
            ("camelCase", [Token(TokenType.MISC_IDENT, "camelCase")]),
            ("var123", [Token(TokenType.MISC_IDENT, "var123")]),
            # Keywords
            ("if", [Token(TokenType.KW_IF, "if")]),
            ("else", [Token(TokenType.KW_ELSE, "else")]),
            ("define", [Token(TokenType.KW_DEFINE, "define")]),
            ("returns", [Token(TokenType.KW_RETURN, "returns")]),
            ("true", [Token(TokenType.KW_TRUE, "true")]),
            ("false", [Token(TokenType.KW_FALSE, "false")]),
            ("and", [Token(TokenType.KW_AND, "and")]),
            ("or", [Token(TokenType.KW_OR, "or")]),
            ("is", [Token(TokenType.KW_IS, "is")]),
            ("as", [Token(TokenType.KW_AS, "as")]),
            ("with", [Token(TokenType.KW_WITH, "with")]),
            ("then", [Token(TokenType.KW_THEN, "then")]),
            # More keywords
            ("action", [Token(TokenType.KW_ACTION, "action")]),
            ("actions", [Token(TokenType.KW_ACTIONS, "actions")]),
            ("apply", [Token(TokenType.KW_CALL, "apply")]),
            ("assign", [Token(TokenType.KW_ASSIGN, "assign")]),
            ("Boolean", [Token(TokenType.KW_BOOL, "Boolean")]),
            ("class", [Token(TokenType.KW_CLASS, "class")]),
            ("Float", [Token(TokenType.KW_FLOAT, "Float")]),
            ("Floats", [Token(TokenType.KW_FLOATS, "Floats")]),
            ("from", [Token(TokenType.KW_FROM, "from")]),
            ("Integer", [Token(TokenType.KW_INT, "Integer")]),
            ("Integers", [Token(TokenType.KW_INTS, "Integers")]),
            ("not", [Token(TokenType.KW_NEGATION, "not")]),
            ("Nothing", [Token(TokenType.KW_NOTHING, "Nothing")]),
            ("Number", [Token(TokenType.KW_NUMBER, "Number")]),
            ("Numbers", [Token(TokenType.KW_NUMBERS, "Numbers")]),
            ("otherwise", [Token(TokenType.KW_ELSE, "otherwise")]),
            ("rule", [Token(TokenType.KW_RULE, "rule")]),
            ("Set", [Token(TokenType.KW_SET, "Set")]),
            ("take", [Token(TokenType.KW_TAKE, "take")]),
            ("takes", [Token(TokenType.KW_TAKES, "takes")]),
            ("Tell", [Token(TokenType.KW_TELL, "Tell")]),
            ("text", [Token(TokenType.KW_TEXT, "text")]),
            ("texts", [Token(TokenType.KW_TEXTS, "texts")]),
            ("to", [Token(TokenType.KW_TO, "to")]),
            ("trait", [Token(TokenType.KW_TRAIT, "trait")]),
            ("traits", [Token(TokenType.KW_TRAITS, "traits")]),
            ("URL", [Token(TokenType.KW_URL, "URL")]),
            ("URLs", [Token(TokenType.KW_URLS, "URLs")]),
            ("Date", [Token(TokenType.KW_DATE, "Date")]),
            ("Dates", [Token(TokenType.KW_DATES, "Dates")]),
            ("DateTime", [Token(TokenType.KW_DATETIME, "DateTime")]),
            ("DateTimes", [Token(TokenType.KW_DATETIMES, "DateTimes")]),
            ("Time", [Token(TokenType.KW_TIME, "Time")]),
            ("Times", [Token(TokenType.KW_TIMES, "Times")]),
            ("DataType", [Token(TokenType.KW_DATATYPE, "DataType")]),
            # Single character operators
            ("+", [Token(TokenType.OP_PLUS, "+")]),
            ("-", [Token(TokenType.OP_MINUS, "-")]),
            ("/", [Token(TokenType.OP_DIVISION, "/")]),
            ("=", [Token(TokenType.OP_ASSIGN, "=")]),
            ("<", [Token(TokenType.OP_LT, "<")]),
            (">", [Token(TokenType.OP_GT, ">")]),
            ("*", [Token(TokenType.OP_STAR, "*")]),
            # Multi-character operators
            ("==", [Token(TokenType.OP_EQ, "==")]),
            ("!=", [Token(TokenType.OP_NOT_EQ, "!=")]),
            ("**", [Token(TokenType.OP_TWO_STARS, "**")]),
            # Delimiters
            ("(", [Token(TokenType.DELIM_LPAREN, "(")]),
            (")", [Token(TokenType.DELIM_RPAREN, ")")]),
            ("{", [Token(TokenType.DELIM_LBRACE, "{")]),
            ("}", [Token(TokenType.DELIM_RBRACE, "}")]),
            # Punctuation
            (";", [Token(TokenType.PUNCT_SEMICOLON, ";")]),
            (",", [Token(TokenType.PUNCT_COMMA, ",")]),
            (".", [Token(TokenType.PUNCT_PERIOD, ".")]),
            (":", [Token(TokenType.PUNCT_COLON, ":")]),
            ("#", [Token(TokenType.PUNCT_HASH, "#")]),
            # Complex expressions
            (
                "x = 42",
                [
                    Token(TokenType.MISC_IDENT, "x"),
                    Token(TokenType.OP_ASSIGN, "="),
                    Token(TokenType.LIT_INT, "42"),
                ],
            ),
            (
                "if (x > 0)",
                [
                    Token(TokenType.KW_IF, "if"),
                    Token(TokenType.DELIM_LPAREN, "("),
                    Token(TokenType.MISC_IDENT, "x"),
                    Token(TokenType.OP_GT, ">"),
                    Token(TokenType.LIT_INT, "0"),
                    Token(TokenType.DELIM_RPAREN, ")"),
                ],
            ),
            (
                "x # comment",
                [
                    Token(TokenType.MISC_IDENT, "x"),
                    Token(TokenType.PUNCT_HASH, "#"),
                    Token(TokenType.MISC_IDENT, "comment"),
                ],
            ),
            (
                "Set `name` to `John`",
                [
                    Token(TokenType.KW_SET, "Set"),
                    Token(TokenType.LIT_BACKTICK, "`name`"),
                    Token(TokenType.KW_TO, "to"),
                    Token(TokenType.LIT_BACKTICK, "`John`"),
                ],
            ),
            (
                "if **x** is greater than 0, then return **true**",
                [
                    Token(TokenType.KW_IF, "if"),
                    Token(TokenType.OP_TWO_STARS, "**"),
                    Token(TokenType.MISC_IDENT, "x"),
                    Token(TokenType.OP_TWO_STARS, "**"),
                    Token(TokenType.KW_IS, "is"),
                    Token(TokenType.MISC_IDENT, "greater"),
                    Token(TokenType.MISC_IDENT, "than"),
                    Token(TokenType.LIT_INT, "0"),
                    Token(TokenType.PUNCT_COMMA, ","),
                    Token(TokenType.KW_THEN, "then"),
                    Token(TokenType.MISC_IDENT, "return"),
                    Token(TokenType.OP_TWO_STARS, "**"),
                    Token(TokenType.KW_TRUE, "true"),
                    Token(TokenType.OP_TWO_STARS, "**"),
                ],
            ),
        ],
    )
    def test_lexer_tokenization(self, input_text: str, expected_tokens: list[Token]) -> None:
        from machine_dialect.lexer.lexer import Lexer

        lexer = Lexer(input_text)
        tokens = list(lexer.tokenize())

        assert len(tokens) == len(expected_tokens), f"Expected {len(expected_tokens)} tokens, got {len(tokens)}"

        for i, (actual, expected) in enumerate(zip(tokens, expected_tokens, strict=True)):
            assert actual.type == expected.type, f"Token {i}: expected type {expected.type}, got {actual.type}"
            assert actual.literal == expected.literal, f"Token {i}: exp. '{expected.literal}' got '{actual.literal}'"
