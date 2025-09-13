"""Tests for dictionary operations in HIR to MIR lowering."""

import unittest

from machine_dialect.ast import (
    DefineStatement,
    Identifier,
    NamedListLiteral,
    Program,
    SetStatement,
    StringLiteral,
    WholeNumberLiteral,
)
from machine_dialect.ast.expressions import CollectionAccessExpression
from machine_dialect.lexer import Token, TokenType
from machine_dialect.mir.hir_to_mir import HIRToMIRLowering
from machine_dialect.mir.mir_instructions import (
    DictCreate,
    DictGet,
    DictSet,
    LoadConst,
)


class TestDictionaryLowering(unittest.TestCase):
    """Test dictionary operations are properly lowered to MIR."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.lowerer = HIRToMIRLowering()

    def test_empty_dictionary_creation(self) -> None:
        """Test creating an empty dictionary."""
        # Define `config` as named list.
        # Set `config` to named list.
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        config_id = Identifier(Token(TokenType.MISC_IDENT, "config", 1, 8), "config")
        define = DefineStatement(token, config_id, ["named", "list"])

        # Create empty named list literal
        named_list = NamedListLiteral(token, [])

        set_stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 2, 1),
            Identifier(Token(TokenType.MISC_IDENT, "config", 2, 5), "config"),
            named_list,
        )

        # Create program and lower to MIR
        program = Program([define, set_stmt])
        mir_module = self.lowerer.lower_program(program)

        # Check that DictCreate instruction was generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None
        # Collect all instructions from all basic blocks
        instructions = []
        for block in main_func.cfg.blocks.values():
            instructions.extend(block.instructions)

        # Should have DictCreate and assignment
        dict_creates = [inst for inst in instructions if isinstance(inst, DictCreate)]
        self.assertEqual(len(dict_creates), 1, "Should have one DictCreate instruction")

    def test_dictionary_with_values(self) -> None:
        """Test creating a dictionary with initial key-value pairs."""
        # Define `settings` as named list.
        # Set `settings` to named list with:
        # - `port`: _8080_
        # - `host`: _"localhost"_
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        settings_id = Identifier(Token(TokenType.MISC_IDENT, "settings", 1, 8), "settings")
        define = DefineStatement(token, settings_id, ["named", "list"])

        # Create named list with items
        named_list = NamedListLiteral(token, [])
        named_list.entries = [
            (
                "port",
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "8080", 3, 11), 8080),
            ),
            (
                "host",
                StringLiteral(Token(TokenType.LIT_TEXT, "localhost", 4, 11), "localhost"),
            ),
        ]

        set_stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 2, 1),
            Identifier(Token(TokenType.MISC_IDENT, "settings", 2, 5), "settings"),
            named_list,
        )

        # Create program and lower to MIR
        program = Program([define, set_stmt])
        mir_module = self.lowerer.lower_program(program)

        # Check instructions
        main_func = mir_module.get_function("__main__")
        assert main_func is not None
        # Collect all instructions from all basic blocks
        instructions = []
        for block in main_func.cfg.blocks.values():
            instructions.extend(block.instructions)

        # Should have DictCreate followed by DictSet operations
        dict_creates = [inst for inst in instructions if isinstance(inst, DictCreate)]
        dict_sets = [inst for inst in instructions if isinstance(inst, DictSet)]

        self.assertEqual(len(dict_creates), 1, "Should have one DictCreate instruction")
        self.assertEqual(len(dict_sets), 2, "Should have two DictSet instructions for two key-value pairs")

    def test_dictionary_property_access(self) -> None:
        """Test accessing dictionary values using property syntax."""
        # Define `config` as named list.
        # Define `port` as whole number.
        # Set `port` to `config`'s port.
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        config_id = Identifier(Token(TokenType.MISC_IDENT, "config", 1, 8), "config")
        define1 = DefineStatement(token, config_id, ["named", "list"])
        port_id = Identifier(Token(TokenType.MISC_IDENT, "port", 2, 8), "port")
        define2 = DefineStatement(token, port_id, ["whole", "number"])

        # Create property access: config's port
        config_id = Identifier(Token(TokenType.MISC_IDENT, "config", 3, 15), "config")
        access = CollectionAccessExpression(token, config_id, "port", "property")

        set_stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 3, 1),
            Identifier(Token(TokenType.MISC_IDENT, "port", 3, 5), "port"),
            access,
        )

        # Create program and lower to MIR
        program = Program([define1, define2, set_stmt])
        mir_module = self.lowerer.lower_program(program)

        # Check instructions
        main_func = mir_module.get_function("__main__")
        assert main_func is not None
        # Collect all instructions from all basic blocks
        instructions = []
        for block in main_func.cfg.blocks.values():
            instructions.extend(block.instructions)

        # Should have DictGet instruction
        dict_gets = [inst for inst in instructions if isinstance(inst, DictGet)]
        self.assertEqual(len(dict_gets), 1, "Should have one DictGet instruction for property access")

    def test_dictionary_name_access(self) -> None:
        """Test accessing dictionary values using name syntax."""
        # Define `data` as named list.
        # Define `value` as text.
        # Set `value` to the "key" item of `data`.
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        data_id = Identifier(Token(TokenType.MISC_IDENT, "data", 1, 8), "data")
        define1 = DefineStatement(token, data_id, ["named", "list"])
        value_id = Identifier(Token(TokenType.MISC_IDENT, "value", 2, 8), "value")
        define2 = DefineStatement(token, value_id, ["text"])

        # Create name access: data["key"]
        data_id = Identifier(Token(TokenType.MISC_IDENT, "data", 3, 31), "data")
        access = CollectionAccessExpression(token, data_id, "key", "name")

        set_stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 3, 1),
            Identifier(Token(TokenType.MISC_IDENT, "value", 3, 5), "value"),
            access,
        )

        # Create program and lower to MIR
        program = Program([define1, define2, set_stmt])
        mir_module = self.lowerer.lower_program(program)

        # Check instructions
        main_func = mir_module.get_function("__main__")
        assert main_func is not None
        # Collect all instructions from all basic blocks
        instructions = []
        for block in main_func.cfg.blocks.values():
            instructions.extend(block.instructions)

        # Should have DictGet instruction
        dict_gets = [inst for inst in instructions if isinstance(inst, DictGet)]
        self.assertEqual(len(dict_gets), 1, "Should have one DictGet instruction for name access")

    def test_nested_dictionary_creation(self) -> None:
        """Test creating nested dictionaries."""
        # Define `config` as named list.
        # Set `config` to named list with:
        # - `database`: named list with:
        #   - `host`: _"db.example.com"_
        #   - `port`: _5432_
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        config_id = Identifier(Token(TokenType.MISC_IDENT, "config", 1, 8), "config")
        define = DefineStatement(token, config_id, ["named", "list"])

        # Create inner dictionary
        inner_dict = NamedListLiteral(token, [])
        inner_dict.entries = [
            (
                "host",
                StringLiteral(Token(TokenType.LIT_TEXT, "db.example.com", 4, 13), "db.example.com"),
            ),
            (
                "port",
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5432", 5, 13), 5432),
            ),
        ]

        # Create outer dictionary with nested dictionary
        outer_dict = NamedListLiteral(token, [])
        outer_dict.entries = [
            ("database", inner_dict),
        ]

        set_stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 2, 1),
            Identifier(Token(TokenType.MISC_IDENT, "config", 2, 5), "config"),
            outer_dict,
        )

        # Create program and lower to MIR
        program = Program([define, set_stmt])
        mir_module = self.lowerer.lower_program(program)

        # Check instructions
        main_func = mir_module.get_function("__main__")
        assert main_func is not None
        # Collect all instructions from all basic blocks
        instructions = []
        for block in main_func.cfg.blocks.values():
            instructions.extend(block.instructions)

        # Should have multiple DictCreate instructions for nested structure
        dict_creates = [inst for inst in instructions if isinstance(inst, DictCreate)]
        dict_sets = [inst for inst in instructions if isinstance(inst, DictSet)]

        self.assertGreaterEqual(len(dict_creates), 2, "Should have at least two DictCreate instructions")
        self.assertGreaterEqual(len(dict_sets), 3, "Should have at least three DictSet instructions")

    def test_dictionary_with_expression_keys(self) -> None:
        """Test dictionary with identifier expressions as keys."""
        # Define `lookup` as named list.
        # Define `key1` as text.
        # Set `key1` to _"first"_.
        # Set `lookup` to named list with:
        # - `key1`: _100_
        token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        lookup_id = Identifier(Token(TokenType.MISC_IDENT, "lookup", 1, 8), "lookup")
        define1 = DefineStatement(token, lookup_id, ["named", "list"])
        key1_id = Identifier(Token(TokenType.MISC_IDENT, "key1", 2, 8), "key1")
        define2 = DefineStatement(token, key1_id, ["text"])

        set_key = SetStatement(
            Token(TokenType.KW_SET, "Set", 3, 1),
            Identifier(Token(TokenType.MISC_IDENT, "key1", 3, 5), "key1"),
            StringLiteral(Token(TokenType.LIT_TEXT, "first", 3, 14), "first"),
        )

        # Create dictionary with string key (not identifier)
        named_list = NamedListLiteral(token, [])
        named_list.entries = [
            (
                "key1",
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "100", 5, 11), 100),
            ),
        ]

        set_dict = SetStatement(
            Token(TokenType.KW_SET, "Set", 4, 1),
            Identifier(Token(TokenType.MISC_IDENT, "lookup", 4, 5), "lookup"),
            named_list,
        )

        # Create program and lower to MIR
        program = Program([define1, define2, set_key, set_dict])
        mir_module = self.lowerer.lower_program(program)

        # Check instructions
        main_func = mir_module.get_function("__main__")
        assert main_func is not None
        # Collect all instructions from all basic blocks
        instructions = []
        for block in main_func.cfg.blocks.values():
            instructions.extend(block.instructions)

        # Should properly handle identifier keys
        dict_creates = [inst for inst in instructions if isinstance(inst, DictCreate)]
        dict_sets = [inst for inst in instructions if isinstance(inst, DictSet)]
        load_consts = [inst for inst in instructions if isinstance(inst, LoadConst)]

        self.assertEqual(len(dict_creates), 1, "Should have one DictCreate instruction")
        self.assertGreaterEqual(len(dict_sets), 1, "Should have at least one DictSet instruction")
        self.assertGreaterEqual(len(load_consts), 2, "Should have LoadConst for keys and values")


if __name__ == "__main__":
    unittest.main()
