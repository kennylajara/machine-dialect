"""Test collection mutation statements in Machine Dialect™."""

from machine_dialect.ast import (
    Identifier,
    SetStatement,
    UnorderedListLiteral,
    WholeNumberLiteral,
)
from machine_dialect.ast.statements import CollectionMutationStatement
from machine_dialect.parser import Parser


class TestCollectionMutations:
    """Test parsing of collection mutation operations."""

    def test_add_to_list(self) -> None:
        """Test Add operation on lists."""
        source = """
Define `items` as Unordered List.
Set `items` to blank.
Add _4_ to `items`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 3

        # Check Add statement
        add_stmt = program.statements[2]
        assert isinstance(add_stmt, CollectionMutationStatement)
        assert add_stmt.operation == "add"
        assert isinstance(add_stmt.collection, Identifier)
        assert add_stmt.collection.value == "items"
        assert isinstance(add_stmt.value, WholeNumberLiteral)
        assert add_stmt.value.value == 4

    def test_remove_from_list(self) -> None:
        """Test Remove operation on lists."""
        source = """
Define `items` as Unordered List.
Set `items` to:
- _2_.
Remove _2_ from `items`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 3

        # Check Remove statement
        remove_stmt = program.statements[2]
        assert isinstance(remove_stmt, CollectionMutationStatement)
        assert remove_stmt.operation == "remove"
        assert isinstance(remove_stmt.collection, Identifier)
        assert remove_stmt.collection.value == "items"
        assert isinstance(remove_stmt.value, WholeNumberLiteral)
        assert remove_stmt.value.value == 2

    def test_set_item_with_ordinal(self) -> None:
        """Test Set item using ordinal (first, second, third)."""
        source = """
Define `items` as Unordered List.
Set `items` to:
- _1_.
- _2_.
Set the first item of `items` to _10_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 3

        # Check Set item statement
        set_stmt = program.statements[2]
        assert isinstance(set_stmt, CollectionMutationStatement)
        assert set_stmt.operation == "set"
        assert isinstance(set_stmt.collection, Identifier)
        assert set_stmt.collection.value == "items"
        assert isinstance(set_stmt.value, WholeNumberLiteral)
        assert set_stmt.value.value == 10
        assert set_stmt.position == "first"
        assert set_stmt.position_type == "ordinal"

    def test_set_item_with_numeric_index(self) -> None:
        """Test Set item using numeric index."""
        source = """
Define `items` as Unordered List.
Set `items` to:
- _1_.
- _2_.
- _3_.
Set item _2_ of `items` to _20_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 3

        # Check Set item statement
        set_stmt = program.statements[2]
        assert isinstance(set_stmt, CollectionMutationStatement)
        assert set_stmt.operation == "set"
        assert isinstance(set_stmt.collection, Identifier)
        assert set_stmt.collection.value == "items"
        assert isinstance(set_stmt.value, WholeNumberLiteral)
        assert set_stmt.value.value == 20
        # Position should be the parsed expression
        assert isinstance(set_stmt.position, WholeNumberLiteral)
        assert set_stmt.position.value == 2
        assert set_stmt.position_type == "numeric"

    def test_insert_at_position(self) -> None:
        """Test Insert operation at specific position."""
        source = """
Define `items` as Unordered List.
Set `items` to:
- _1_.
- _3_.
Insert _15_ at position _2_ in `items`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 3

        # Check Insert statement
        insert_stmt = program.statements[2]
        assert isinstance(insert_stmt, CollectionMutationStatement)
        assert insert_stmt.operation == "insert"
        assert isinstance(insert_stmt.collection, Identifier)
        assert insert_stmt.collection.value == "items"
        assert isinstance(insert_stmt.value, WholeNumberLiteral)
        assert insert_stmt.value.value == 15
        assert isinstance(insert_stmt.position, WholeNumberLiteral)
        assert insert_stmt.position.value == 2
        assert insert_stmt.position_type == "numeric"

    def test_multiple_ordinals(self) -> None:
        """Test multiple ordinal Set operations."""
        source = """
Define `items` as Ordered List.
Set `items` to:
1. _1_.
2. _2_.
3. _3_.
4. _4_.
Set the first item of `items` to _100_.
Set the second item of `items` to _200_.
Set the third item of `items` to _300_.
Set the last item of `items` to _999_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 6

        # Check each Set statement
        ordinals = ["first", "second", "third", "last"]
        values = [100, 200, 300, 999]

        for i, (ordinal, value) in enumerate(zip(ordinals, values, strict=True), 2):
            set_stmt = program.statements[i]
            assert isinstance(set_stmt, CollectionMutationStatement)
            assert set_stmt.operation == "set"
            assert set_stmt.position == ordinal
            assert set_stmt.position_type == "ordinal"
            assert isinstance(set_stmt.value, WholeNumberLiteral)
            assert isinstance(set_stmt.value, WholeNumberLiteral)
            assert set_stmt.value.value == value

    def test_keywords_as_identifiers(self) -> None:
        """Test that keywords can be used as variable names in collection contexts."""
        source = """
Define `first` as Unordered List.
Set `first` to blank.
Add _1_ to `first`.
Define `items` as Unordered List.
Set `items` to blank.
Add _2_ to `items`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 6

        # Check that both 'first' (a keyword) and 'items' work as identifiers
        add_stmt1 = program.statements[2]
        assert isinstance(add_stmt1, CollectionMutationStatement)
        assert isinstance(add_stmt1.collection, Identifier)
        assert add_stmt1.collection.value == "first"

        add_stmt2 = program.statements[5]
        assert isinstance(add_stmt2, CollectionMutationStatement)
        assert isinstance(add_stmt2.collection, Identifier)
        assert add_stmt2.collection.value == "items"

    def test_set_without_the(self) -> None:
        """Test that 'Set first item of' works without 'the'."""
        source = """
Define `items` as Unordered List.
Set `items` to:
- _1_.
- _2_.
Set first item of `items` to _10_.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 3

        # Should parse the same as "Set the first item of"
        set_stmt = program.statements[2]
        assert isinstance(set_stmt, CollectionMutationStatement)
        assert set_stmt.operation == "set"
        assert set_stmt.position == "first"
        assert set_stmt.position_type == "ordinal"

    def test_complex_mutation_sequence(self) -> None:
        """Test a complex sequence of list mutations."""
        source = """
Define `shopping` as Unordered List.
Set `shopping` to:
- _"milk"_.
- _"bread"_.
- _"eggs"_.

Add _"butter"_ to `shopping`.
Remove _"bread"_ from `shopping`.
Set the first item of `shopping` to _"oat milk"_.
Insert _"cheese"_ at position _2_ in `shopping`.
"""
        parser = Parser()
        program = parser.parse(source)

        assert len(parser.errors) == 0, f"Parser errors: {parser.errors}"
        assert len(program.statements) == 6

        # Verify the initial list
        set_stmt = program.statements[1]
        assert isinstance(set_stmt, SetStatement)
        assert isinstance(set_stmt.value, UnorderedListLiteral)
        assert len(set_stmt.value.elements) == 3

        # Verify each mutation
        mutations = program.statements[2:]
        assert all(isinstance(stmt, CollectionMutationStatement) for stmt in mutations)

        # Check operations
        assert isinstance(mutations[0], CollectionMutationStatement)
        assert isinstance(mutations[1], CollectionMutationStatement)
        assert isinstance(mutations[2], CollectionMutationStatement)
        assert isinstance(mutations[3], CollectionMutationStatement)
        assert mutations[0].operation == "add"
        assert mutations[1].operation == "remove"
        assert mutations[2].operation == "set"
        assert mutations[3].operation == "insert"
