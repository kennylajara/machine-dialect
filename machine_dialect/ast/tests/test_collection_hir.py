"""Test HIR generation for collection operations."""

from machine_dialect.ast.expressions import CollectionAccessExpression, Identifier
from machine_dialect.ast.literals import UnorderedListLiteral, WholeNumberLiteral
from machine_dialect.ast.statements import CollectionMutationStatement
from machine_dialect.lexer import Token, TokenType


class TestCollectionHIR:
    """Test HIR generation for collection operations."""

    def test_list_literal_to_hir(self) -> None:
        """Test that list literals convert to HIR properly."""
        token = Token(TokenType.PUNCT_DASH, "-", 1, 1)
        from machine_dialect.ast.expressions import Expression

        elements: list[Expression] = [
            WholeNumberLiteral(token, 1),
            WholeNumberLiteral(token, 2),
            WholeNumberLiteral(token, 3),
        ]

        unordered = UnorderedListLiteral(token, elements)
        hir = unordered.to_hir()

        assert isinstance(hir, UnorderedListLiteral)
        assert len(hir.elements) == 3
        assert all(isinstance(elem, WholeNumberLiteral) for elem in hir.elements)

    def test_collection_access_ordinal_to_hir(self) -> None:
        """Test that ordinal access converts to zero-based index."""
        token = Token(TokenType.KW_FIRST, "first", 1, 1)
        collection = Identifier(token, "items")

        # Test "first" -> 0
        access = CollectionAccessExpression(token, collection, "first", "ordinal")
        hir = access.to_hir()

        assert hir.accessor == 0
        assert hir.access_type == "numeric"  # Changed from ordinal to numeric

        # Test "second" -> 1
        access = CollectionAccessExpression(token, collection, "second", "ordinal")
        hir = access.to_hir()

        assert hir.accessor == 1
        assert hir.access_type == "numeric"

        # Test "third" -> 2
        access = CollectionAccessExpression(token, collection, "third", "ordinal")
        hir = access.to_hir()

        assert hir.accessor == 2
        assert hir.access_type == "numeric"

    def test_collection_access_numeric_to_hir(self) -> None:
        """Test that numeric access converts from 1-based to 0-based."""
        token = Token(TokenType.KW_ITEM, "item", 1, 1)
        collection = Identifier(token, "items")

        # Test numeric index: 1 -> 0
        access = CollectionAccessExpression(token, collection, 1, "numeric")
        hir = access.to_hir()

        assert hir.accessor == 0  # 1-based to 0-based
        assert hir.access_type == "numeric"

        # Test larger index: 877 -> 876
        access = CollectionAccessExpression(token, collection, 877, "numeric")
        hir = access.to_hir()

        assert hir.accessor == 876
        assert hir.access_type == "numeric"

    def test_collection_access_last_to_hir(self) -> None:
        """Test that 'last' remains as special case."""
        token = Token(TokenType.KW_LAST, "last", 1, 1)
        collection = Identifier(token, "items")

        access = CollectionAccessExpression(token, collection, "last", "ordinal")
        hir = access.to_hir()

        # "last" should remain as "last" for special handling in MIR
        assert hir.accessor == "last"
        assert hir.access_type == "ordinal"  # Keeps ordinal type for "last"

    def test_collection_mutation_ordinal_to_hir(self) -> None:
        """Test that mutation statements convert ordinals properly."""
        token = Token(TokenType.KW_SET, "Set", 1, 1)
        collection = Identifier(token, "items")
        value = WholeNumberLiteral(token, 10)

        # Test "Set the first item" -> index 0
        mutation = CollectionMutationStatement(token, "set", collection, value, "first", "ordinal")
        hir = mutation.to_hir()

        assert hir.position == 0
        assert hir.position_type == "numeric"  # Changed from ordinal

        # Test "Set the second item" -> index 1
        mutation = CollectionMutationStatement(token, "set", collection, value, "second", "ordinal")
        hir = mutation.to_hir()

        assert hir.position == 1
        assert hir.position_type == "numeric"

    def test_collection_mutation_numeric_to_hir(self) -> None:
        """Test that mutation statements convert numeric indices."""
        token = Token(TokenType.KW_SET, "Set", 1, 1)
        collection = Identifier(token, "items")
        value = WholeNumberLiteral(token, 20)

        # Test "Set item 1" -> index 0
        mutation = CollectionMutationStatement(token, "set", collection, value, 1, "numeric")
        hir = mutation.to_hir()

        assert hir.position == 0  # 1-based to 0-based
        assert hir.position_type == "numeric"

        # Test "Set item 42" -> index 41
        mutation = CollectionMutationStatement(token, "set", collection, value, 42, "numeric")
        hir = mutation.to_hir()

        assert hir.position == 41
        assert hir.position_type == "numeric"

    def test_collection_mutation_insert_to_hir(self) -> None:
        """Test that insert operations convert positions properly."""
        token = Token(TokenType.KW_INSERT, "Insert", 1, 1)
        collection = Identifier(token, "items")
        value = WholeNumberLiteral(token, 15)

        # Test "Insert at position 2" -> index 1
        mutation = CollectionMutationStatement(token, "insert", collection, value, 2, "numeric")
        hir = mutation.to_hir()

        assert hir.position == 1  # 1-based to 0-based
        assert hir.position_type == "numeric"
