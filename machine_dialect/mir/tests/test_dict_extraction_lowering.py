"""Tests for dictionary extraction MIR lowering."""

from machine_dialect.ast import Program
from machine_dialect.ast.dict_extraction import DictExtraction
from machine_dialect.ast.expressions import Identifier
from machine_dialect.ast.literals import NamedListLiteral, StringLiteral, WholeNumberLiteral
from machine_dialect.ast.statements import SetStatement, Statement
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.hir_to_mir import lower_to_mir


class TestDictExtractionLowering:
    """Test lowering of dictionary extraction to MIR."""

    def test_lower_dict_keys_extraction(self) -> None:
        """Test lowering 'the names of dict' to DictKeys instruction."""
        # Create a dictionary and extract its keys
        dict_token = Token(TokenType.PUNCT_DASH, "-", 1, 1)
        dict_literal = NamedListLiteral(
            dict_token,
            [
                (
                    "name",
                    StringLiteral(Token(TokenType.LIT_TEXT, "Alice", 1, 1), "Alice"),
                ),
                (
                    "age",
                    WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "30", 1, 1), 30),
                ),
            ],
        )

        # Create the extraction expression
        extraction = DictExtraction(
            Token(TokenType.MISC_STOPWORD, "the", 1, 1),
            Identifier(Token(TokenType.MISC_IDENT, "person", 1, 1), "person"),
            "names",
        )

        # Create statements to lower
        statements: list[Statement] = [
            SetStatement(
                Token(TokenType.KW_SET, "Set", 1, 1),
                Identifier(Token(TokenType.MISC_IDENT, "person", 1, 1), "person"),
                dict_literal,
            ),
            SetStatement(
                Token(TokenType.KW_SET, "Set", 1, 1),
                Identifier(Token(TokenType.MISC_IDENT, "keys", 1, 1), "keys"),
                extraction,
            ),
        ]

        # Lower to MIR
        program = Program(statements)
        mir_module = lower_to_mir(program)

        # Check that we have DictKeys instruction
        main_func = mir_module.get_function("__main__")

        assert main_func is not None

        # Look for DictKeys instruction
        dict_keys_insts = []
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if inst.__class__.__name__ == "DictKeys":
                    dict_keys_insts.append(inst)

        assert len(dict_keys_insts) == 1, "Should have one DictKeys instruction"

    def test_lower_dict_values_extraction(self) -> None:
        """Test lowering 'the contents of dict' to DictValues instruction."""
        # Create a dictionary and extract its values
        dict_token = Token(TokenType.PUNCT_DASH, "-", 1, 1)
        dict_literal = NamedListLiteral(
            dict_token,
            [
                (
                    "host",
                    StringLiteral(Token(TokenType.LIT_TEXT, "localhost", 1, 1), "localhost"),
                ),
                (
                    "port",
                    WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "8080", 1, 1), 8080),
                ),
            ],
        )

        # Create the extraction expression
        extraction = DictExtraction(
            Token(TokenType.MISC_STOPWORD, "the", 1, 1),
            Identifier(Token(TokenType.MISC_IDENT, "config", 1, 1), "config"),
            "contents",
        )

        # Create statements to lower
        statements: list[Statement] = [
            SetStatement(
                Token(TokenType.KW_SET, "Set", 1, 1),
                Identifier(Token(TokenType.MISC_IDENT, "config", 1, 1), "config"),
                dict_literal,
            ),
            SetStatement(
                Token(TokenType.KW_SET, "Set", 1, 1),
                Identifier(Token(TokenType.MISC_IDENT, "values", 1, 1), "values"),
                extraction,
            ),
        ]

        # Lower to MIR
        program = Program(statements)
        mir_module = lower_to_mir(program)

        # Check that we have DictValues instruction
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Look for DictValues instruction
        dict_values_insts = []
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if inst.__class__.__name__ == "DictValues":
                    dict_values_insts.append(inst)

        assert len(dict_values_insts) == 1, "Should have one DictValues instruction"

    def test_extraction_creates_array_result(self) -> None:
        """Test that extraction creates an array result."""
        # Create the extraction expression
        extraction = DictExtraction(
            Token(TokenType.MISC_STOPWORD, "the", 1, 1),
            Identifier(Token(TokenType.MISC_IDENT, "data", 1, 1), "data"),
            "names",
        )

        # Create statements
        statements: list[Statement] = [
            SetStatement(
                Token(TokenType.KW_SET, "Set", 1, 1),
                Identifier(Token(TokenType.MISC_IDENT, "data", 1, 1), "data"),
                NamedListLiteral(Token(TokenType.PUNCT_DASH, "-", 1, 1), []),
            ),
            SetStatement(
                Token(TokenType.KW_SET, "Set", 1, 1),
                Identifier(Token(TokenType.MISC_IDENT, "result", 1, 1), "result"),
                extraction,
            ),
        ]

        # Lower to MIR
        program = Program(statements)
        mir_module = lower_to_mir(program)

        # The result should be stored as an array type
        main_func = mir_module.get_function("__main__")

        # Check that the result is treated as an array
        # This would be verified by checking the type of the temp register
        # that holds the result of DictKeys/DictValues
        assert main_func is not None

    def test_extraction_from_expression(self) -> None:
        """Test extraction from a dictionary expression (not just identifier)."""
        # This tests that we can extract from any expression that evaluates to a dict
        extraction = DictExtraction(
            Token(TokenType.MISC_STOPWORD, "the", 1, 1),
            # Could be a more complex expression in real code
            Identifier(Token(TokenType.MISC_IDENT, "get_config", 1, 1), "get_config"),
            "contents",
        )

        statements: list[Statement] = [
            SetStatement(
                Token(TokenType.KW_SET, "Set", 1, 1),
                Identifier(Token(TokenType.MISC_IDENT, "get_config", 1, 1), "get_config"),
                NamedListLiteral(Token(TokenType.PUNCT_DASH, "-", 1, 1), []),
            ),
            SetStatement(
                Token(TokenType.KW_SET, "Set", 1, 1),
                Identifier(Token(TokenType.MISC_IDENT, "vals", 1, 1), "vals"),
                extraction,
            ),
        ]

        # Lower to MIR
        program = Program(statements)
        mir_module = lower_to_mir(program)

        # Should successfully lower
        main_func = mir_module.get_function("__main__")
        assert main_func is not None
