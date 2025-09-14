"""Tests for one-based index translation in MIR generation."""

from machine_dialect.ast import Program
from machine_dialect.ast.expressions import CollectionAccessExpression, Identifier
from machine_dialect.ast.literals import UnorderedListLiteral, WholeNumberLiteral
from machine_dialect.ast.statements import CollectionMutationStatement, SetStatement
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.mir_instructions import ArrayGet, BinaryOp, LoadConst


class TestOneBasedIndexing:
    """Test that one-based indexing is correctly translated to zero-based."""

    def test_numeric_access_literal_index(self) -> None:
        """Test that item _1_ of list accesses index 0."""
        # Create a list access: item _1_ of `mylist`
        token = Token(TokenType.KW_ITEM, "item", 1, 1)
        collection = Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist")

        # Create access with literal index 1 (should become 0 after HIR conversion)
        access = CollectionAccessExpression(token, collection, 1, "numeric")

        # Convert to HIR - this should subtract 1
        hir_access = access.to_hir()
        assert isinstance(hir_access, CollectionAccessExpression)
        assert hir_access.accessor == 0  # 1-based becomes 0-based

        # Lower to MIR
        program = Program(
            [
                SetStatement(
                    Token(TokenType.KW_SET, "Set", 1, 1),
                    Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist"),
                    UnorderedListLiteral(
                        Token(TokenType.PUNCT_DASH, "-", 1, 1),
                        [WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "10", 1, 1), 10)],
                    ),
                ),
                SetStatement(
                    Token(TokenType.KW_SET, "Set", 1, 1),
                    Identifier(Token(TokenType.MISC_IDENT, "result", 1, 1), "result"),
                    hir_access,
                ),
            ]
        )
        mir_module = lower_to_mir(program)

        # Find the ArrayGet instruction
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Look for ArrayGet instruction
        array_gets = [
            inst for block in main_func.cfg.blocks.values() for inst in block.instructions if isinstance(inst, ArrayGet)
        ]
        assert len(array_gets) == 1

        # The index should be loaded as constant 0
        load_consts = [
            inst
            for block in main_func.cfg.blocks.values()
            for inst in block.instructions
            if isinstance(inst, LoadConst)
        ]
        # Find the LoadConst that loads 0 (the converted index)
        index_loads = [inst for inst in load_consts if hasattr(inst.constant, "value") and inst.constant.value == 0]
        assert len(index_loads) > 0, "Should have loaded index 0"

    def test_numeric_access_expression_index(self) -> None:
        """Test that expression-based indices get 1 subtracted at runtime."""
        # Create a list access: item `idx` of `mylist` where idx is an expression
        token = Token(TokenType.KW_ITEM, "item", 1, 1)
        collection = Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist")
        index_expr = Identifier(Token(TokenType.MISC_IDENT, "idx", 1, 1), "idx")

        # Create access with expression index
        access = CollectionAccessExpression(token, collection, index_expr, "numeric")

        # Convert to HIR - expression indices should NOT be modified
        hir_access = access.to_hir()
        assert isinstance(hir_access, CollectionAccessExpression)
        # The accessor should still be an expression
        assert isinstance(hir_access.accessor, Identifier)

        # Lower to MIR
        program = Program(
            [
                SetStatement(
                    Token(TokenType.KW_SET, "Set", 1, 1),
                    Identifier(Token(TokenType.MISC_IDENT, "idx", 1, 1), "idx"),
                    WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "1", 1, 1), 1),
                ),
                SetStatement(
                    Token(TokenType.KW_SET, "Set", 1, 1),
                    Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist"),
                    UnorderedListLiteral(
                        Token(TokenType.PUNCT_DASH, "-", 1, 1),
                        [WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "10", 1, 1), 10)],
                    ),
                ),
                SetStatement(
                    Token(TokenType.KW_SET, "Set", 1, 1),
                    Identifier(Token(TokenType.MISC_IDENT, "result", 1, 1), "result"),
                    hir_access,
                ),
            ]
        )
        mir_module = lower_to_mir(program)

        # Find the BinaryOp that subtracts 1
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Look for BinaryOp instruction with subtraction
        binary_ops = [
            inst for block in main_func.cfg.blocks.values() for inst in block.instructions if isinstance(inst, BinaryOp)
        ]
        subtract_ops = [inst for inst in binary_ops if inst.op == "-"]
        assert len(subtract_ops) > 0, "Should have a subtraction operation for index adjustment"

    def test_ordinal_access_first(self) -> None:
        """Test that 'the first item of' accesses index 0."""
        token = Token(TokenType.KW_FIRST, "first", 1, 1)
        collection = Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist")

        # Create ordinal access
        access = CollectionAccessExpression(token, collection, "first", "ordinal")

        # Convert to HIR - should convert to numeric with index 0
        hir_access = access.to_hir()
        assert isinstance(hir_access, CollectionAccessExpression)
        assert hir_access.access_type == "numeric"
        assert hir_access.accessor == 0

    def test_ordinal_access_second(self) -> None:
        """Test that 'the second item of' accesses index 1."""
        token = Token(TokenType.KW_SECOND, "second", 1, 1)
        collection = Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist")

        # Create ordinal access
        access = CollectionAccessExpression(token, collection, "second", "ordinal")

        # Convert to HIR - should convert to numeric with index 1
        hir_access = access.to_hir()
        assert isinstance(hir_access, CollectionAccessExpression)
        assert hir_access.access_type == "numeric"
        assert hir_access.accessor == 1

    def test_mutation_set_literal_index(self) -> None:
        """Test that 'Set item _1_ of list' sets index 0."""
        token = Token(TokenType.KW_SET, "set", 1, 1)
        collection = Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist")
        value = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 1), 42)

        # Create mutation with literal index 1
        mutation = CollectionMutationStatement(token, "set", collection, value, 1, "numeric")

        # Convert to HIR - should subtract 1
        hir_mutation = mutation.to_hir()
        assert isinstance(hir_mutation, CollectionMutationStatement)
        assert hir_mutation.position == 0  # 1-based becomes 0-based

    def test_mutation_insert_literal_index(self) -> None:
        """Test that 'Insert at position _1_' inserts at index 0."""
        token = Token(TokenType.KW_INSERT, "insert", 1, 1)
        collection = Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist")
        value = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 1), 42)

        # Create mutation with literal index 1
        mutation = CollectionMutationStatement(token, "insert", collection, value, 1, "numeric")

        # Convert to HIR - should subtract 1
        hir_mutation = mutation.to_hir()
        assert isinstance(hir_mutation, CollectionMutationStatement)
        assert hir_mutation.position == 0  # 1-based becomes 0-based

    def test_mutation_remove_literal_index(self) -> None:
        """Test that 'Remove item _1_' removes index 0."""
        token = Token(TokenType.KW_REMOVE, "remove", 1, 1)
        collection = Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist")

        # Create mutation with literal index 1
        mutation = CollectionMutationStatement(token, "remove", collection, None, 1, "numeric")

        # Convert to HIR - should subtract 1
        hir_mutation = mutation.to_hir()
        assert isinstance(hir_mutation, CollectionMutationStatement)
        assert hir_mutation.position == 0  # 1-based becomes 0-based

    def test_large_index(self) -> None:
        """Test that item _877_ of list accesses index 876."""
        token = Token(TokenType.KW_ITEM, "item", 1, 1)
        collection = Identifier(Token(TokenType.MISC_IDENT, "mylist", 1, 1), "mylist")

        # Create access with large index
        access = CollectionAccessExpression(token, collection, 877, "numeric")

        # Convert to HIR - should subtract 1
        hir_access = access.to_hir()
        assert isinstance(hir_access, CollectionAccessExpression)
        assert hir_access.accessor == 876  # 877-based becomes 876-based
