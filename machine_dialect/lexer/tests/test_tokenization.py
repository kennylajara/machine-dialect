import pytest

from machine_dialect.lexer.tokens import Token, TokenType


class TestLexer:
    @pytest.mark.parametrize(
        "input_text,expected_tokens",
        [
            # Numbers
            ("123", [Token(TokenType.LIT_INT, "123", line=1, position=0)]),
            ("3.14", [Token(TokenType.LIT_FLOAT, "3.14", line=1, position=0)]),
            ("0", [Token(TokenType.LIT_INT, "0", line=1, position=0)]),
            # Strings
            ('"hello"', [Token(TokenType.LIT_TEXT, '"hello"', line=1, position=0)]),
            ("'world'", [Token(TokenType.LIT_TEXT, "'world'", line=1, position=0)]),
            ('""', [Token(TokenType.LIT_TEXT, '""', line=1, position=0)]),
            # Backtick strings
            ("`code`", [Token(TokenType.LIT_BACKTICK, "`code`", line=1, position=0)]),
            ("`variable_name`", [Token(TokenType.LIT_BACKTICK, "`variable_name`", line=1, position=0)]),
            ("`42`", [Token(TokenType.LIT_BACKTICK, "`42`", line=1, position=0)]),
            ("``", [Token(TokenType.LIT_BACKTICK, "``", line=1, position=0)]),
            # Triple backtick strings
            ("```python```", [Token(TokenType.LIT_TRIPLE_BACKTICK, "```python```", line=1, position=0)]),
            (
                "```\ncode block\n```",
                [Token(TokenType.LIT_TRIPLE_BACKTICK, "```\ncode block\n```", line=1, position=0)],
            ),
            (
                "```js\nconst x = 42;\n```",
                [Token(TokenType.LIT_TRIPLE_BACKTICK, "```js\nconst x = 42;\n```", line=1, position=0)],
            ),
            ("``````", [Token(TokenType.LIT_TRIPLE_BACKTICK, "``````", line=1, position=0)]),
            # Identifiers
            ("variable", [Token(TokenType.MISC_IDENT, "variable", line=1, position=0)]),
            ("_underscore", [Token(TokenType.MISC_IDENT, "_underscore", line=1, position=0)]),
            ("camelCase", [Token(TokenType.MISC_IDENT, "camelCase", line=1, position=0)]),
            ("var123", [Token(TokenType.MISC_IDENT, "var123", line=1, position=0)]),
            # Keywords
            ("if", [Token(TokenType.KW_IF, "if", line=1, position=0)]),
            ("else", [Token(TokenType.KW_ELSE, "else", line=1, position=0)]),
            ("define", [Token(TokenType.KW_DEFINE, "define", line=1, position=0)]),
            ("give back", [Token(TokenType.KW_RETURN, "give back", line=1, position=0)]),
            ("gives back", [Token(TokenType.KW_RETURN, "gives back", line=1, position=0)]),
            ("true", [Token(TokenType.KW_TRUE, "true", line=1, position=0)]),
            ("false", [Token(TokenType.KW_FALSE, "false", line=1, position=0)]),
            ("and", [Token(TokenType.KW_AND, "and", line=1, position=0)]),
            ("or", [Token(TokenType.KW_OR, "or", line=1, position=0)]),
            ("is", [Token(TokenType.KW_IS, "is", line=1, position=0)]),
            ("as", [Token(TokenType.KW_AS, "as", line=1, position=0)]),
            ("with", [Token(TokenType.KW_WITH, "with", line=1, position=0)]),
            ("then", [Token(TokenType.KW_THEN, "then", line=1, position=0)]),
            # More keywords
            ("action", [Token(TokenType.KW_ACTION, "action", line=1, position=0)]),
            ("actions", [Token(TokenType.KW_ACTIONS, "actions", line=1, position=0)]),
            ("apply", [Token(TokenType.KW_CALL, "apply", line=1, position=0)]),
            ("assign", [Token(TokenType.KW_ASSIGN, "assign", line=1, position=0)]),
            ("Boolean", [Token(TokenType.KW_BOOL, "Boolean", line=1, position=0)]),
            ("class", [Token(TokenType.KW_CLASS, "class", line=1, position=0)]),
            ("Float", [Token(TokenType.KW_FLOAT, "Float", line=1, position=0)]),
            ("Floats", [Token(TokenType.KW_FLOATS, "Floats", line=1, position=0)]),
            ("from", [Token(TokenType.KW_FROM, "from", line=1, position=0)]),
            ("Integer", [Token(TokenType.KW_INT, "Integer", line=1, position=0)]),
            ("Integers", [Token(TokenType.KW_INTS, "Integers", line=1, position=0)]),
            ("not", [Token(TokenType.KW_NEGATION, "not", line=1, position=0)]),
            ("Nothing", [Token(TokenType.KW_NOTHING, "Nothing", line=1, position=0)]),
            ("Number", [Token(TokenType.KW_NUMBER, "Number", line=1, position=0)]),
            ("Numbers", [Token(TokenType.KW_NUMBERS, "Numbers", line=1, position=0)]),
            ("otherwise", [Token(TokenType.KW_ELSE, "otherwise", line=1, position=0)]),
            ("rule", [Token(TokenType.KW_RULE, "rule", line=1, position=0)]),
            ("Set", [Token(TokenType.KW_SET, "Set", line=1, position=0)]),
            ("take", [Token(TokenType.KW_TAKE, "take", line=1, position=0)]),
            ("takes", [Token(TokenType.KW_TAKES, "takes", line=1, position=0)]),
            ("Tell", [Token(TokenType.KW_TELL, "Tell", line=1, position=0)]),
            ("text", [Token(TokenType.KW_TEXT, "text", line=1, position=0)]),
            ("texts", [Token(TokenType.KW_TEXTS, "texts", line=1, position=0)]),
            ("to", [Token(TokenType.KW_TO, "to", line=1, position=0)]),
            ("trait", [Token(TokenType.KW_TRAIT, "trait", line=1, position=0)]),
            ("traits", [Token(TokenType.KW_TRAITS, "traits", line=1, position=0)]),
            ("URL", [Token(TokenType.KW_URL, "URL", line=1, position=0)]),
            ("URLs", [Token(TokenType.KW_URLS, "URLs", line=1, position=0)]),
            ("Date", [Token(TokenType.KW_DATE, "Date", line=1, position=0)]),
            ("Dates", [Token(TokenType.KW_DATES, "Dates", line=1, position=0)]),
            ("DateTime", [Token(TokenType.KW_DATETIME, "DateTime", line=1, position=0)]),
            ("DateTimes", [Token(TokenType.KW_DATETIMES, "DateTimes", line=1, position=0)]),
            ("Time", [Token(TokenType.KW_TIME, "Time", line=1, position=0)]),
            ("Times", [Token(TokenType.KW_TIMES, "Times", line=1, position=0)]),
            ("DataType", [Token(TokenType.KW_DATATYPE, "DataType", line=1, position=0)]),
            # Single character operators
            ("+", [Token(TokenType.OP_PLUS, "+", line=1, position=0)]),
            ("-", [Token(TokenType.OP_MINUS, "-", line=1, position=0)]),
            ("/", [Token(TokenType.OP_DIVISION, "/", line=1, position=0)]),
            ("=", [Token(TokenType.OP_ASSIGN, "=", line=1, position=0)]),
            ("<", [Token(TokenType.OP_LT, "<", line=1, position=0)]),
            (">", [Token(TokenType.OP_GT, ">", line=1, position=0)]),
            ("*", [Token(TokenType.OP_STAR, "*", line=1, position=0)]),
            # Multi-character operators
            ("==", [Token(TokenType.OP_EQ, "==", line=1, position=0)]),
            ("!=", [Token(TokenType.OP_NOT_EQ, "!=", line=1, position=0)]),
            ("**", [Token(TokenType.OP_TWO_STARS, "**", line=1, position=0)]),
            # Delimiters
            ("(", [Token(TokenType.DELIM_LPAREN, "(", line=1, position=0)]),
            (")", [Token(TokenType.DELIM_RPAREN, ")", line=1, position=0)]),
            ("{", [Token(TokenType.DELIM_LBRACE, "{", line=1, position=0)]),
            ("}", [Token(TokenType.DELIM_RBRACE, "}", line=1, position=0)]),
            # Punctuation
            (";", [Token(TokenType.PUNCT_SEMICOLON, ";", line=1, position=0)]),
            (",", [Token(TokenType.PUNCT_COMMA, ",", line=1, position=0)]),
            (".", [Token(TokenType.PUNCT_PERIOD, ".", line=1, position=0)]),
            (":", [Token(TokenType.PUNCT_COLON, ":", line=1, position=0)]),
            ("#", [Token(TokenType.PUNCT_HASH, "#", line=1, position=0)]),
            # Complex expressions
            (
                "x = 42",
                [
                    Token(TokenType.MISC_IDENT, "x", line=1, position=0),
                    Token(TokenType.OP_ASSIGN, "=", line=1, position=0),
                    Token(TokenType.LIT_INT, "42", line=1, position=0),
                ],
            ),
            (
                "if (x > 0)",
                [
                    Token(TokenType.KW_IF, "if", line=1, position=0),
                    Token(TokenType.DELIM_LPAREN, "(", line=1, position=0),
                    Token(TokenType.MISC_IDENT, "x", line=1, position=0),
                    Token(TokenType.OP_GT, ">", line=1, position=0),
                    Token(TokenType.LIT_INT, "0", line=1, position=0),
                    Token(TokenType.DELIM_RPAREN, ")", line=1, position=0),
                ],
            ),
            (
                "x # comment",
                [
                    Token(TokenType.MISC_IDENT, "x", line=1, position=0),
                    Token(TokenType.PUNCT_HASH, "#", line=1, position=0),
                    Token(TokenType.MISC_IDENT, "comment", line=1, position=0),
                ],
            ),
            (
                "Set `name` to `John`",
                [
                    Token(TokenType.KW_SET, "Set", line=1, position=0),
                    Token(TokenType.LIT_BACKTICK, "`name`", line=1, position=0),
                    Token(TokenType.KW_TO, "to", line=1, position=0),
                    Token(TokenType.LIT_BACKTICK, "`John`", line=1, position=0),
                ],
            ),
            (
                "if **x** is greater than 0, then return **true**",
                [
                    Token(TokenType.KW_IF, "if", line=1, position=0),
                    Token(TokenType.OP_TWO_STARS, "**", line=1, position=0),
                    Token(TokenType.MISC_IDENT, "x", line=1, position=0),
                    Token(TokenType.OP_TWO_STARS, "**", line=1, position=0),
                    Token(TokenType.KW_IS, "is", line=1, position=0),
                    Token(TokenType.MISC_IDENT, "greater", line=1, position=0),
                    Token(TokenType.MISC_IDENT, "than", line=1, position=0),
                    Token(TokenType.LIT_INT, "0", line=1, position=0),
                    Token(TokenType.PUNCT_COMMA, ",", line=1, position=0),
                    Token(TokenType.KW_THEN, "then", line=1, position=0),
                    Token(TokenType.MISC_IDENT, "return", line=1, position=0),
                    Token(TokenType.OP_TWO_STARS, "**", line=1, position=0),
                    Token(TokenType.KW_TRUE, "true", line=1, position=0),
                    Token(TokenType.OP_TWO_STARS, "**", line=1, position=0),
                ],
            ),
            (
                "if x > 0 then gives back true",
                [
                    Token(TokenType.KW_IF, "if", line=1, position=0),
                    Token(TokenType.MISC_IDENT, "x", line=1, position=0),
                    Token(TokenType.OP_GT, ">", line=1, position=0),
                    Token(TokenType.LIT_INT, "0", line=1, position=0),
                    Token(TokenType.KW_THEN, "then", line=1, position=0),
                    Token(TokenType.KW_RETURN, "gives back", line=1, position=0),
                    Token(TokenType.KW_TRUE, "true", line=1, position=0),
                ],
            ),
            (
                "define rule that give back 42",
                [
                    Token(TokenType.KW_DEFINE, "define", line=1, position=0),
                    Token(TokenType.KW_RULE, "rule", line=1, position=0),
                    Token(TokenType.MISC_IDENT, "that", line=1, position=0),
                    Token(TokenType.KW_RETURN, "give back", line=1, position=0),
                    Token(TokenType.LIT_INT, "42", line=1, position=0),
                ],
            ),
        ],
    )
    def test_lexer_tokenization(self, input_text: str, expected_tokens: list[Token]) -> None:
        from machine_dialect.lexer.lexer import Lexer

        lexer = Lexer(input_text)
        errors, tokens = lexer.tokenize()

        # For these tests, we expect no errors
        assert len(errors) == 0, f"Unexpected errors: {errors}"

        assert len(tokens) == len(expected_tokens), f"Expected {len(expected_tokens)} tokens, got {len(tokens)}"

        for i, (actual, expected) in enumerate(zip(tokens, expected_tokens, strict=True)):
            assert actual.type == expected.type, f"Token {i}: expected type {expected.type}, got {actual.type}"
            assert actual.literal == expected.literal, f"Token {i}: exp. '{expected.literal}' got '{actual.literal}'"
