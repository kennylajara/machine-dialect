"""Test for-each statement desugaring to while loops."""

from machine_dialect.ast import Identifier
from machine_dialect.ast.call_expression import CallExpression
from machine_dialect.ast.literals import OrderedListLiteral, StringLiteral, WholeNumberLiteral
from machine_dialect.ast.statements import BlockStatement, ForEachStatement, SetStatement
from machine_dialect.lexer import Token, TokenType


class TestForEachDesugaring:
    """Test that for-each statements correctly desugar to while loops."""

    def test_basic_foreach_desugaring(self) -> None:
        """Test basic for-each loop desugaring."""
        # Create tokens
        for_token = Token(TokenType.KW_FOR, "for", 1, 1)
        item_token = Token(TokenType.MISC_IDENT, "item", 1, 10)
        collection_token = Token(TokenType.MISC_IDENT, "items", 1, 20)

        # Create the for-each statement:
        # For each `item` in `items`:
        #     body
        item_id = Identifier(item_token, "item")
        collection_id = Identifier(collection_token, "items")

        # Create a simple body
        body = BlockStatement(for_token)
        body.statements = [
            SetStatement(
                Token(TokenType.KW_SET, "Set", 2, 1),
                Identifier(Token(TokenType.MISC_IDENT, "result", 2, 5), "result"),
                item_id,
            )
        ]

        foreach_stmt = ForEachStatement(for_token, item=item_id, collection=collection_id, body=body)

        # Desugar the for-each statement
        desugared = foreach_stmt.desugar()

        # Should return a BlockStatement containing initialization and while loop
        assert isinstance(desugared, BlockStatement)
        assert len(desugared.statements) == 3  # init_index, init_length, while_stmt

        # Check initialization statements
        init_index = desugared.statements[0]
        assert isinstance(init_index, SetStatement)
        assert isinstance(init_index.name, Identifier)
        assert init_index.name.value.startswith("$foreach_idx_")  # Synthetic variable
        assert isinstance(init_index.value, WholeNumberLiteral)
        assert init_index.value.value == 0

        init_length = desugared.statements[1]
        assert isinstance(init_length, SetStatement)
        assert isinstance(init_length.name, Identifier)
        assert init_length.name.value.startswith("$foreach_len_")  # Synthetic variable
        assert init_length.value is not None
        assert isinstance(init_length.value, CallExpression)
        assert init_length.value.function_name is not None
        assert isinstance(init_length.value.function_name, Identifier)
        assert init_length.value.function_name.value == "len"

        # The desugared ForEachStatement returns a BlockStatement containing:
        # [0] Set $foreach_idx_N to 0
        # [1] Set $foreach_len_N to len(collection)
        # [2] WhileStatement with the loop logic
        while_stmt = desugared.statements[2]

        # Verify the while statement structure
        from machine_dialect.ast.expressions import CollectionAccessExpression, InfixExpression
        from machine_dialect.ast.statements import WhileStatement

        assert isinstance(while_stmt, WhileStatement)

        # Check condition: index < length
        assert isinstance(while_stmt.condition, InfixExpression)
        assert while_stmt.condition.operator == "<"
        assert isinstance(while_stmt.condition.left, Identifier)
        assert while_stmt.condition.left.value.startswith("$foreach_idx_")
        assert isinstance(while_stmt.condition.right, Identifier)
        assert while_stmt.condition.right.value.startswith("$foreach_len_")

        # Check while body
        assert isinstance(while_stmt.body, BlockStatement)
        assert len(while_stmt.body.statements) >= 3  # set item, original body, increment

        # First statement should set item = collection[index]
        first_stmt = while_stmt.body.statements[0]
        assert isinstance(first_stmt, SetStatement)
        assert first_stmt.name is not None
        assert first_stmt.name.value == "item"  # The original loop variable
        assert isinstance(first_stmt.value, CollectionAccessExpression)

        # Last statement should increment index
        last_stmt = while_stmt.body.statements[-1]
        assert isinstance(last_stmt, SetStatement)
        assert last_stmt.name is not None
        assert last_stmt.name.value.startswith("$foreach_idx_")
        assert isinstance(last_stmt.value, InfixExpression)
        assert last_stmt.value.operator == "+"

    def test_foreach_with_literal_collection(self) -> None:
        """Test for-each with a literal list as collection."""
        # Create tokens
        for_token = Token(TokenType.KW_FOR, "for", 1, 1)
        item_token = Token(TokenType.MISC_IDENT, "fruit", 1, 10)

        # Create a literal list
        list_token = Token(TokenType.MISC_IDENT, "[", 1, 20)
        str1_token = Token(TokenType.LIT_TEXT, "apple", 1, 22)
        str2_token = Token(TokenType.LIT_TEXT, "banana", 1, 30)

        collection = OrderedListLiteral(
            list_token, [StringLiteral(str1_token, "apple"), StringLiteral(str2_token, "banana")]
        )

        # Create for-each with literal collection
        foreach_stmt = ForEachStatement(
            for_token,
            item=Identifier(item_token, "fruit"),
            collection=collection,
            body=BlockStatement(for_token),  # Empty body
        )

        # Desugar
        desugared = foreach_stmt.desugar()

        # Should still produce valid desugared form
        assert isinstance(desugared, BlockStatement)
        assert len(desugared.statements) == 3

    def test_foreach_empty_body(self) -> None:
        """Test for-each with empty body."""
        for_token = Token(TokenType.KW_FOR, "for", 1, 1)

        foreach_stmt = ForEachStatement(
            for_token,
            item=Identifier(Token(TokenType.MISC_IDENT, "x", 1, 10), "x"),
            collection=Identifier(Token(TokenType.MISC_IDENT, "xs", 1, 15), "xs"),
            body=None,
        )

        desugared = foreach_stmt.desugar()

        # Should still produce valid structure
        assert isinstance(desugared, BlockStatement)
        assert len(desugared.statements) == 3

    def test_foreach_malformed_missing_parts(self) -> None:
        """Test for-each with missing item or collection."""
        for_token = Token(TokenType.KW_FOR, "for", 1, 1)

        # Missing collection
        foreach_stmt = ForEachStatement(
            for_token,
            item=Identifier(Token(TokenType.MISC_IDENT, "x", 1, 10), "x"),
            collection=None,
            body=BlockStatement(for_token),
        )

        desugared = foreach_stmt.desugar()

        # Should return an empty while statement for malformed input
        from machine_dialect.ast.statements import WhileStatement

        assert isinstance(desugared, WhileStatement)
        assert desugared.condition is None
        assert desugared.body is None

    def test_gensym_uniqueness(self) -> None:
        """Test that gensym generates unique variable names."""
        # Reset counter for predictable testing
        original_counter = ForEachStatement._gensym_counter
        ForEachStatement._gensym_counter = 0

        try:
            # Generate multiple synthetic variables
            var1 = ForEachStatement._gensym("test")
            var2 = ForEachStatement._gensym("test")
            var3 = ForEachStatement._gensym("other")

            # All should be unique
            assert var1.value == "$test_1"
            assert var2.value == "$test_2"
            assert var3.value == "$other_3"

            # All should have $ prefix (invalid for user variables)
            assert all(v.value.startswith("$") for v in [var1, var2, var3])
        finally:
            # Restore original counter
            ForEachStatement._gensym_counter = original_counter

    def test_nested_foreach_unique_variables(self) -> None:
        """Test that nested for-each loops get unique synthetic variables."""
        # Create outer for-each
        outer_foreach = ForEachStatement(
            Token(TokenType.KW_FOR, "for", 1, 1),
            item=Identifier(Token(TokenType.MISC_IDENT, "x", 1, 10), "x"),
            collection=Identifier(Token(TokenType.MISC_IDENT, "xs", 1, 15), "xs"),
            body=BlockStatement(Token(TokenType.KW_FOR, "for", 1, 1)),
        )

        # Create inner for-each
        inner_foreach = ForEachStatement(
            Token(TokenType.KW_FOR, "for", 2, 1),
            item=Identifier(Token(TokenType.MISC_IDENT, "y", 2, 10), "y"),
            collection=Identifier(Token(TokenType.MISC_IDENT, "ys", 2, 15), "ys"),
            body=BlockStatement(Token(TokenType.KW_FOR, "for", 2, 1)),
        )

        # Desugar both
        outer_desugared = outer_foreach.desugar()
        inner_desugared = inner_foreach.desugar()

        # Extract synthetic variable names from both
        assert isinstance(outer_desugared, BlockStatement)
        assert isinstance(inner_desugared, BlockStatement)

        # Cast to SetStatement and check name existence
        outer_set0 = outer_desugared.statements[0]
        outer_set1 = outer_desugared.statements[1]
        inner_set0 = inner_desugared.statements[0]
        inner_set1 = inner_desugared.statements[1]

        assert isinstance(outer_set0, SetStatement)
        assert isinstance(outer_set1, SetStatement)
        assert isinstance(inner_set0, SetStatement)
        assert isinstance(inner_set1, SetStatement)

        assert outer_set0.name is not None
        assert outer_set1.name is not None
        assert inner_set0.name is not None
        assert inner_set1.name is not None

        outer_index_var = outer_set0.name.value
        outer_length_var = outer_set1.name.value
        inner_index_var = inner_set0.name.value
        inner_length_var = inner_set1.name.value

        # All should be unique
        all_vars = {outer_index_var, outer_length_var, inner_index_var, inner_length_var}
        assert len(all_vars) == 4, "All synthetic variables should be unique"

        # All should start with $
        assert all(v.startswith("$") for v in all_vars)
