from machine_dialect.ast import Identifier, IntegerLiteral, Program, ReturnStatement, SetStatement
from machine_dialect.lexer import Token, TokenType


class TestASTStringRepresentation:
    def test_set_statement_string(self) -> None:
        program: Program = Program(
            statements=[
                SetStatement(
                    token=Token(TokenType.KW_SET, "Set", 1, 0),
                    name=Identifier(token=Token(TokenType.LIT_BACKTICK, "`my_var`", 1, 4), value="my_var"),
                    value=Identifier(
                        token=Token(TokenType.LIT_BACKTICK, "`other_var`", 1, 15),
                        value="other_var",
                    ),
                )
            ]
        )

        program_str = str(program)

        assert program_str == "Set `my_var` to `other_var`.\n"

    def test_return_statement_string(self) -> None:
        program: Program = Program(
            statements=[
                ReturnStatement(
                    token=Token(TokenType.KW_RETURN, "Give back", 1, 0),
                    return_value=Identifier(token=Token(TokenType.LIT_BACKTICK, "`my_var`", 1, 7), value="my_var"),
                )
            ]
        )

        program_str = str(program)

        assert program_str == "\nGive back `my_var`.\n"

    def test_multiple_statements_string(self) -> None:
        program: Program = Program(
            statements=[
                SetStatement(
                    token=Token(TokenType.KW_SET, "Set", 1, 0),
                    name=Identifier(token=Token(TokenType.LIT_BACKTICK, "`x`", 1, 4), value="x"),
                    value=IntegerLiteral(token=Token(TokenType.LIT_INT, "_42_", 1, 11), value=42),
                ),
                SetStatement(
                    token=Token(TokenType.KW_SET, "Set", 2, 0),
                    name=Identifier(token=Token(TokenType.LIT_BACKTICK, "`y`", 2, 4), value="y"),
                    value=Identifier(token=Token(TokenType.LIT_BACKTICK, "`x`", 2, 11), value="x"),
                ),
                ReturnStatement(
                    token=Token(TokenType.KW_RETURN, "Give back", 3, 0),
                    return_value=Identifier(token=Token(TokenType.LIT_BACKTICK, "`y`", 3, 7), value="y"),
                ),
            ]
        )

        program_str = str(program)

        # The Program concatenates statements with ".\n" and adds final ".\n"
        expected = "Set `x` to _42_.\nSet `y` to `x`.\n\nGive back `y`.\n"
        assert program_str == expected
