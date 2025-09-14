"""Tests for collection operation lowering from HIR to MIR."""

from machine_dialect.ast import (
    CollectionAccessExpression,
    CollectionMutationStatement,
    DefineStatement,
    Expression,
    Identifier,
    OrderedListLiteral,
    Program,
    SetStatement,
    StringLiteral,
    UnorderedListLiteral,
    WholeNumberLiteral,
)
from machine_dialect.lexer import Token, TokenType
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.mir_instructions import (
    ArrayAppend,
    ArrayClear,
    ArrayCreate,
    ArrayFindIndex,
    ArrayGet,
    ArrayInsert,
    ArrayLength,
    ArrayRemove,
    ArraySet,
    BinaryOp,
    LoadConst,
)


class TestCollectionMutationLowering:
    """Test lowering of CollectionMutationStatement to MIR."""

    def test_add_to_list(self) -> None:
        """Test Add operation generates ArrayAppend."""
        # Create AST for: Add _"cherry"_ to `fruits`
        token = Token(TokenType.KW_ADD, "Add", 1, 1)
        collection = Identifier(token, "fruits")
        value = StringLiteral(token, "cherry")

        stmt = CollectionMutationStatement(
            token=token,
            operation="add",
            collection=collection,
            value=value,
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "fruits"),
            type_spec=["unordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayAppend was generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Find ArrayAppend instruction
        found_append = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayAppend):
                    found_append = True
                    break

        assert found_append, "ArrayAppend instruction not found"

    def test_set_list_item_numeric(self) -> None:
        """Test Set operation with numeric index generates ArraySet."""
        # Create AST for: Set item _2_ of `numbers` to _99_
        token = Token(TokenType.KW_SET, "Set", 1, 1)
        collection = Identifier(token, "numbers")
        value = WholeNumberLiteral(token, 99)

        # Position is already 0-based after HIR transformation
        stmt = CollectionMutationStatement(
            token=token,
            operation="set",
            collection=collection,
            value=value,
            position=1,  # Index 1 (second item, 0-based)
            position_type="numeric",
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "numbers"),
            type_spec=["ordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArraySet was generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Find ArraySet instruction
        found_set = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArraySet):
                    found_set = True
                    break

        assert found_set, "ArraySet instruction not found"

    def test_set_last_item(self) -> None:
        """Test Set operation with 'last' position."""
        # Create AST for: Set the last item of `numbers` to _999_
        token = Token(TokenType.KW_SET, "Set", 1, 1)
        collection = Identifier(token, "numbers")
        value = WholeNumberLiteral(token, 999)

        stmt = CollectionMutationStatement(
            token=token,
            operation="set",
            collection=collection,
            value=value,
            position="last",
            position_type="ordinal",
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "numbers"),
            type_spec=["ordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayLength and BinaryOp (subtract) were generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Find ArrayLength and BinaryOp instructions
        found_length = False
        found_subtract = False
        found_set = False

        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayLength):
                    found_length = True
                elif isinstance(inst, BinaryOp) and inst.op == "-":
                    found_subtract = True
                elif isinstance(inst, ArraySet):
                    found_set = True

        assert found_length, "ArrayLength instruction not found"
        assert found_subtract, "BinaryOp subtract instruction not found"
        assert found_set, "ArraySet instruction not found"

    def test_remove_from_list(self) -> None:
        """Test Remove operation generates ArrayRemove."""
        # Create AST for: Remove the second item from `numbers`
        token = Token(TokenType.KW_REMOVE, "Remove", 1, 1)
        collection = Identifier(token, "numbers")

        stmt = CollectionMutationStatement(
            token=token,
            operation="remove",
            collection=collection,
            position=1,  # Index 1 (second item, 0-based)
            position_type="numeric",
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "numbers"),
            type_spec=["ordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayRemove was generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Find ArrayRemove instruction
        found_remove = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayRemove):
                    found_remove = True
                    break

        assert found_remove, "ArrayRemove instruction not found"

    def test_remove_by_value_from_list(self) -> None:
        """Test Remove by value generates ArrayFindIndex and ArrayRemove."""
        # Create AST for: Remove _"banana"_ from `fruits`
        token = Token(TokenType.KW_REMOVE, "Remove", 1, 1)
        collection = Identifier(token, "fruits")
        value = StringLiteral(token, "banana")

        stmt = CollectionMutationStatement(
            token=token,
            operation="remove",
            collection=collection,
            value=value,
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "fruits"),
            type_spec=["unordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayFindIndex and ArrayRemove were generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Find ArrayFindIndex and ArrayRemove instructions
        found_find = False
        found_remove = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayFindIndex):
                    found_find = True
                elif isinstance(inst, ArrayRemove):
                    found_remove = True

        assert found_find, "ArrayFindIndex instruction not found"
        assert found_remove, "ArrayRemove instruction not found"

    def test_insert_into_list(self) -> None:
        """Test Insert operation generates ArrayInsert."""
        # Create AST for: Insert _50_ at position 2 in `numbers`
        token = Token(TokenType.KW_INSERT, "Insert", 1, 1)
        collection = Identifier(token, "numbers")
        value = WholeNumberLiteral(token, 50)

        stmt = CollectionMutationStatement(
            token=token,
            operation="insert",
            collection=collection,
            value=value,
            position=2,  # Index 2 (third position, 0-based)
            position_type="numeric",
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "numbers"),
            type_spec=["ordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayInsert was generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Find ArrayInsert instruction
        found_insert = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayInsert):
                    found_insert = True
                    break

        assert found_insert, "ArrayInsert instruction not found"

    def test_empty_list_operation(self) -> None:
        """Test Clear operation generates ArrayClear."""
        # Create AST for: Clear `numbers`
        token = Token(TokenType.KW_CLEAR, "Clear", 1, 1)
        collection = Identifier(token, "numbers")

        stmt = CollectionMutationStatement(
            token=token,
            operation="clear",
            collection=collection,
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "numbers"),
            type_spec=["ordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayClear was generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Find ArrayClear instruction
        found_clear = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayClear):
                    found_clear = True
                    break

        assert found_clear, "ArrayClear instruction not found"


class TestCollectionAccessLowering:
    """Test lowering of CollectionAccessExpression to MIR."""

    def test_numeric_access(self) -> None:
        """Test numeric array access generates ArrayGet."""
        # Create AST for: item _1_ of `numbers` (0-based after HIR)
        token = Token(TokenType.KW_ITEM, "item", 1, 1)
        collection = Identifier(token, "numbers")

        expr = CollectionAccessExpression(
            token=token,
            collection=collection,
            accessor=0,  # Already 0-based after HIR
            access_type="numeric",
        )

        # Create a SetStatement using this expression
        set_token = Token(TokenType.KW_SET, "Set", 1, 1)
        stmt = SetStatement(
            token=set_token,
            name=Identifier(token, "value"),
            value=expr,
        )

        # Create a program with variable definitions
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_numbers = DefineStatement(
            token=define_token,
            name=Identifier(token, "numbers"),
            type_spec=["ordered", "list"],
        )
        define_value = DefineStatement(
            token=define_token,
            name=Identifier(token, "value"),
            type_spec=["whole", "number"],
        )

        program = Program([define_numbers, define_value, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayGet was generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Find ArrayGet instruction
        found_get = False
        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayGet):
                    found_get = True
                    break

        assert found_get, "ArrayGet instruction not found"

    def test_last_item_access(self) -> None:
        """Test 'last' item access generates proper MIR."""
        # Create AST for: the last item of `numbers`
        token = Token(TokenType.KW_LAST, "last", 1, 1)
        collection = Identifier(token, "numbers")

        expr = CollectionAccessExpression(
            token=token,
            collection=collection,
            accessor="last",
            access_type="ordinal",
        )

        # Create a SetStatement using this expression
        set_token = Token(TokenType.KW_SET, "Set", 1, 1)
        stmt = SetStatement(
            token=set_token,
            name=Identifier(token, "value"),
            value=expr,
        )

        # Create a program with variable definitions
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_numbers = DefineStatement(
            token=define_token,
            name=Identifier(token, "numbers"),
            type_spec=["ordered", "list"],
        )
        define_value = DefineStatement(
            token=define_token,
            name=Identifier(token, "value"),
            type_spec=["whole", "number"],
        )

        program = Program([define_numbers, define_value, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayLength, BinaryOp (subtract), and ArrayGet were generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        found_length = False
        found_subtract = False
        found_get = False

        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayLength):
                    found_length = True
                elif isinstance(inst, BinaryOp) and inst.op == "-":
                    found_subtract = True
                elif isinstance(inst, ArrayGet):
                    found_get = True

        assert found_length, "ArrayLength instruction not found"
        assert found_subtract, "BinaryOp subtract instruction not found"
        assert found_get, "ArrayGet instruction not found"


class TestListLiteralLowering:
    """Test lowering of list literals to MIR."""

    def test_ordered_list_literal(self) -> None:
        """Test ordered list literal generates ArrayCreate and ArraySet."""
        # Create AST for ordered list with elements
        token = Token(TokenType.LIT_WHOLE_NUMBER, "1", 1, 1)
        elements: list[Expression] = [
            WholeNumberLiteral(token, 10),
            WholeNumberLiteral(token, 20),
            WholeNumberLiteral(token, 30),
        ]

        list_literal = OrderedListLiteral(token, elements)

        # Create a SetStatement with this list
        set_token = Token(TokenType.KW_SET, "Set", 1, 1)
        stmt = SetStatement(
            token=set_token,
            name=Identifier(token, "numbers"),
            value=list_literal,
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "numbers"),
            type_spec=["ordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayCreate and ArraySet were generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        found_create = False
        set_count = 0

        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayCreate):
                    found_create = True
                elif isinstance(inst, ArraySet):
                    set_count += 1

        assert found_create, "ArrayCreate instruction not found"
        assert set_count == 3, f"Expected 3 ArraySet instructions, found {set_count}"

    def test_unordered_list_literal(self) -> None:
        """Test unordered list literal generates ArrayCreate and ArraySet."""
        # Create AST for unordered list with elements
        token = Token(TokenType.PUNCT_DASH, "-", 1, 1)
        elements: list[Expression] = [
            StringLiteral(token, "apple"),
            StringLiteral(token, "banana"),
            StringLiteral(token, "cherry"),
        ]

        list_literal = UnorderedListLiteral(token, elements)

        # Create a SetStatement with this list
        set_token = Token(TokenType.KW_SET, "Set", 1, 1)
        stmt = SetStatement(
            token=set_token,
            name=Identifier(token, "fruits"),
            value=list_literal,
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "fruits"),
            type_spec=["unordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayCreate and ArraySet were generated
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        found_create = False
        set_count = 0

        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayCreate):
                    found_create = True
                elif isinstance(inst, ArraySet):
                    set_count += 1

        assert found_create, "ArrayCreate instruction not found"
        assert set_count == 3, f"Expected 3 ArraySet instructions, found {set_count}"

    def test_empty_list(self) -> None:
        """Test empty list generates ArrayCreate with size 0."""
        # Create AST for empty ordered list
        token = Token(TokenType.LIT_WHOLE_NUMBER, "1", 1, 1)
        list_literal = OrderedListLiteral(token, [])

        # Create a SetStatement with this list
        set_token = Token(TokenType.KW_SET, "Set", 1, 1)
        stmt = SetStatement(
            token=set_token,
            name=Identifier(token, "empty"),
            value=list_literal,
        )

        # Create a program with variable definition
        define_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)
        define_stmt = DefineStatement(
            token=define_token,
            name=Identifier(token, "empty"),
            type_spec=["ordered", "list"],
        )

        program = Program([define_stmt, stmt])

        # Lower to MIR
        mir_module = lower_to_mir(program)

        # Check that ArrayCreate was generated with size 0
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        found_create = False
        found_zero_const = False

        for block in main_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ArrayCreate):
                    found_create = True
                elif isinstance(inst, LoadConst):
                    # Check if we're loading a constant 0
                    if hasattr(inst.constant, "value") and inst.constant.value == 0:
                        found_zero_const = True

        assert found_create, "ArrayCreate instruction not found"
        assert found_zero_const, "LoadConst with value 0 not found"
