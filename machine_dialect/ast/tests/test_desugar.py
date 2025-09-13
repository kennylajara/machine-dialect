"""Tests for AST desugaring functionality."""

from machine_dialect.ast import (
    ActionStatement,
    Arguments,
    BlockStatement,
    CallStatement,
    ConditionalExpression,
    EmptyLiteral,
    ExpressionStatement,
    FloatLiteral,
    FunctionStatement,
    FunctionVisibility,
    Identifier,
    IfStatement,
    InfixExpression,
    InteractionStatement,
    PrefixExpression,
    ReturnStatement,
    SetStatement,
    StringLiteral,
    UtilityStatement,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.lexer import Token, TokenType


class TestExpressionDesugaring:
    """Test desugaring of expression nodes."""

    def test_literal_desugaring(self) -> None:
        """Test that literals remain unchanged during desugaring."""
        # Whole Number literal
        int_lit = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 1), 42)
        assert int_lit.desugar() is int_lit

        # Float literal
        float_lit = FloatLiteral(Token(TokenType.LIT_FLOAT, "3.14", 1, 1), 3.14)
        assert float_lit.desugar() is float_lit

        # String literal
        str_lit = StringLiteral(Token(TokenType.LIT_TEXT, '"hello"', 1, 1), '"hello"')
        assert str_lit.desugar() is str_lit

        # Boolean literal
        bool_lit = YesNoLiteral(Token(TokenType.LIT_YES, "True", 1, 1), True)
        assert bool_lit.desugar() is bool_lit

        # Empty literal
        empty_lit = EmptyLiteral(Token(TokenType.KW_EMPTY, "empty", 1, 1))
        assert empty_lit.desugar() is empty_lit

    def test_identifier_desugaring(self) -> None:
        """Test that identifiers remain unchanged during desugaring."""
        ident = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 1), "x")
        assert ident.desugar() is ident

    def test_prefix_expression_desugaring(self) -> None:
        """Test desugaring of prefix expressions."""
        # Create a prefix expression: -42
        token = Token(TokenType.OP_MINUS, "-", 1, 1)
        prefix = PrefixExpression(token, "-")
        prefix.right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 2), 42)

        desugared = prefix.desugar()

        # Should be a new PrefixExpression
        assert isinstance(desugared, PrefixExpression)
        assert desugared is not prefix
        assert desugared.operator == "-"
        # Right should be the same literal (literals don't change)
        assert desugared.right is prefix.right

    def test_infix_expression_operator_normalization(self) -> None:
        """Test that natural language operators are normalized during desugaring."""
        left = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 1), "x")
        right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 10), 5)

        # Test equality operators - include correct token types
        test_cases = [
            (TokenType.OP_EQ, "equals", "=="),
            (TokenType.OP_EQ, "is equal to", "=="),
            (TokenType.OP_EQ, "is the same as", "=="),
            (TokenType.OP_NOT_EQ, "is not equal to", "!="),
            (TokenType.OP_NOT_EQ, "does not equal", "!="),
            (TokenType.OP_NOT_EQ, "is different from", "!="),
            (TokenType.OP_STRICT_EQ, "is strictly equal to", "==="),
            (TokenType.OP_STRICT_EQ, "is exactly equal to", "==="),
            (TokenType.OP_STRICT_EQ, "is identical to", "==="),
            (TokenType.OP_STRICT_NOT_EQ, "is not strictly equal to", "!=="),
            (TokenType.OP_STRICT_NOT_EQ, "is not exactly equal to", "!=="),
            (TokenType.OP_STRICT_NOT_EQ, "is not identical to", "!=="),
            (TokenType.OP_GT, "is greater than", ">"),
            (TokenType.OP_LT, "is less than", "<"),
            (TokenType.OP_GTE, "is greater than or equal to", ">="),
            (TokenType.OP_LTE, "is less than or equal to", "<="),
        ]

        for token_type, natural, normalized in test_cases:
            token = Token(token_type, natural, 1, 5)
            infix = InfixExpression(token, natural, left)
            infix.right = right

            desugared = infix.desugar()

            assert isinstance(desugared, InfixExpression)
            assert desugared.operator == normalized, f"Failed to normalize '{natural}' to '{normalized}'"
            # Check that operands are also desugared
            assert desugared.left is left  # Identifiers return self
            assert desugared.right is right  # Literals return self

    def test_infix_expression_already_normalized(self) -> None:
        """Test that already normalized operators remain unchanged."""
        left = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 1), "x")
        right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 5), 5)

        # Use correct token types for each operator
        operators = [
            (TokenType.OP_PLUS, "+"),
            (TokenType.OP_MINUS, "-"),
            (TokenType.OP_STAR, "*"),
            (TokenType.OP_DIVISION, "/"),
            (TokenType.OP_EQ, "=="),
            (TokenType.OP_NOT_EQ, "!="),
            (TokenType.OP_STRICT_EQ, "==="),
            (TokenType.OP_STRICT_NOT_EQ, "!=="),
            (TokenType.OP_GT, ">"),
            (TokenType.OP_LT, "<"),
            (TokenType.OP_GTE, ">="),
            (TokenType.OP_LTE, "<="),
            (TokenType.OP_CARET, "^"),
        ]

        for token_type, op in operators:
            token = Token(token_type, op, 1, 3)
            infix = InfixExpression(token, op, left)
            infix.right = right

            desugared = infix.desugar()

            assert isinstance(desugared, InfixExpression)
            assert desugared.operator == op, f"Operator '{op}' should remain unchanged"

    def test_conditional_expression_desugaring(self) -> None:
        """Test desugaring of conditional expressions."""
        consequence = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "1", 1, 1), 1)
        condition = YesNoLiteral(Token(TokenType.LIT_YES, "True", 1, 5), True)
        alternative = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 15), 2)

        token = Token(TokenType.KW_IF, "if", 1, 3)
        cond_expr = ConditionalExpression(token, consequence)
        cond_expr.condition = condition
        cond_expr.alternative = alternative

        desugared = cond_expr.desugar()

        assert isinstance(desugared, ConditionalExpression)
        assert desugared is not cond_expr
        # Literals should return self
        assert desugared.consequence is consequence
        assert desugared.condition is condition
        assert desugared.alternative is alternative

    def test_arguments_desugaring(self) -> None:
        """Test desugaring of arguments."""
        token = Token(TokenType.KW_WITH, "with", 1, 10)
        args = Arguments(token)

        # Add positional arguments
        args.positional.append(WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "1", 1, 15), 1))
        args.positional.append(StringLiteral(Token(TokenType.LIT_TEXT, '"test"', 1, 18), '"test"'))

        # Add named arguments
        name = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 25), "x")
        value = YesNoLiteral(Token(TokenType.LIT_YES, "True", 1, 28), True)
        args.named.append((name, value))

        desugared = args.desugar()

        assert isinstance(desugared, Arguments)
        assert desugared is not args
        assert len(desugared.positional) == 2
        assert len(desugared.named) == 1
        # Literals should be the same
        assert desugared.positional[0] is args.positional[0]
        assert desugared.positional[1] is args.positional[1]


class TestStatementDesugaring:
    """Test desugaring of statement nodes."""

    def test_return_statement_normalization(self) -> None:
        """Test that return statements normalize 'give back' and 'gives back' to 'return'."""
        return_value = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 11), 42)

        # Test "give back"
        token1 = Token(TokenType.KW_RETURN, "give back", 1, 1)
        ret1 = ReturnStatement(token1, return_value)
        desugared1 = ret1.desugar()

        assert isinstance(desugared1, ReturnStatement)
        assert desugared1.token.literal == "return"
        assert desugared1.return_value is return_value

        # Test "gives back"
        token2 = Token(TokenType.KW_RETURN, "gives back", 1, 1)
        ret2 = ReturnStatement(token2, return_value)
        desugared2 = ret2.desugar()

        assert isinstance(desugared2, ReturnStatement)
        assert desugared2.token.literal == "return"
        assert desugared2.return_value is return_value

    def test_set_statement_desugaring(self) -> None:
        """Test desugaring of set statements."""
        token = Token(TokenType.KW_SET, "Set", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 5), "x")
        value = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 10), 42)

        set_stmt = SetStatement(token, name, value)
        desugared = set_stmt.desugar()

        assert isinstance(desugared, SetStatement)
        assert desugared is not set_stmt
        assert desugared.name is name  # Identifiers return self
        assert desugared.value is value  # Literals return self

    def test_call_statement_desugaring(self) -> None:
        """Test desugaring of call statements."""
        token = Token(TokenType.KW_USE, "use", 1, 1)
        func_name = StringLiteral(Token(TokenType.LIT_TEXT, '"print"', 1, 6), '"print"')

        args = Arguments(Token(TokenType.KW_WITH, "with", 1, 14))
        args.positional.append(StringLiteral(Token(TokenType.LIT_TEXT, '"hello"', 1, 20), '"hello"'))

        call_stmt = CallStatement(token, func_name, args)
        desugared = call_stmt.desugar()

        assert isinstance(desugared, CallStatement)
        assert desugared is not call_stmt
        assert desugared.function_name is func_name  # Literals return self
        assert isinstance(desugared.arguments, Arguments)
        assert desugared.arguments is not args

    def test_block_statement_flattening(self) -> None:
        """Test that blocks preserve scope (no longer flatten)."""
        token = Token(TokenType.PUNCT_COLON, ":", 1, 10)

        # Test single statement block - now preserves block for scope
        block1 = BlockStatement(token, depth=1)
        single_stmt = ReturnStatement(
            Token(TokenType.KW_RETURN, "return", 2, 3),
            WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 2, 10), 42),
        )
        block1.statements = [single_stmt]

        desugared1 = block1.desugar()
        assert isinstance(desugared1, BlockStatement)  # Block is preserved
        assert len(desugared1.statements) == 1

        # Test multi-statement block - should remain a block
        block2 = BlockStatement(token, depth=1)
        stmt1 = SetStatement(
            Token(TokenType.KW_SET, "Set", 2, 3),
            Identifier(Token(TokenType.MISC_IDENT, "x", 2, 7), "x"),
            WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "1", 2, 12), 1),
        )
        stmt2 = ReturnStatement(
            Token(TokenType.KW_RETURN, "return", 3, 3), Identifier(Token(TokenType.MISC_IDENT, "x", 3, 10), "x")
        )
        block2.statements = [stmt1, stmt2]

        desugared2 = block2.desugar()
        assert isinstance(desugared2, BlockStatement)
        assert len(desugared2.statements) == 2

        # Test nested block with single statement - blocks are preserved
        block3 = BlockStatement(token, depth=1)
        inner_block = BlockStatement(token, depth=2)
        inner_block.statements = [single_stmt]
        block3.statements = [inner_block]

        desugared3 = block3.desugar()
        assert isinstance(desugared3, BlockStatement)  # Outer block preserved
        assert len(desugared3.statements) == 1
        assert isinstance(desugared3.statements[0], BlockStatement)  # Inner block preserved

    def test_if_statement_desugaring(self) -> None:
        """Test desugaring of if statements."""
        token = Token(TokenType.KW_IF, "if", 1, 1)
        condition = YesNoLiteral(Token(TokenType.LIT_YES, "True", 1, 4), True)

        # Create consequence block
        consequence = BlockStatement(Token(TokenType.PUNCT_COLON, ":", 1, 9), depth=1)
        consequence.statements = [
            ReturnStatement(
                Token(TokenType.KW_RETURN, "give back", 2, 3),
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "1", 2, 13), 1),
            )
        ]

        # Create alternative block
        alternative = BlockStatement(Token(TokenType.PUNCT_COLON, ":", 3, 5), depth=1)
        alternative.statements = [
            ReturnStatement(
                Token(TokenType.KW_RETURN, "gives back", 4, 3),
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "2", 4, 14), 2),
            )
        ]

        if_stmt = IfStatement(token, condition)
        if_stmt.consequence = consequence
        if_stmt.alternative = alternative

        desugared = if_stmt.desugar()

        assert isinstance(desugared, IfStatement)
        assert desugared.condition is condition  # Literals return self

        # Even though blocks have single statements, IfStatement keeps them as blocks
        assert isinstance(desugared.consequence, BlockStatement)
        assert isinstance(desugared.alternative, BlockStatement)

        # Check that the return statements inside were normalized
        assert desugared.consequence is not None  # Type guard
        cons_stmt = desugared.consequence.statements[0]
        assert isinstance(cons_stmt, ReturnStatement)
        assert cons_stmt.token.literal == "return"

        assert desugared.alternative is not None  # Type guard
        alt_stmt = desugared.alternative.statements[0]
        assert isinstance(alt_stmt, ReturnStatement)
        assert alt_stmt.token.literal == "return"

    def test_expression_statement_desugaring(self) -> None:
        """Test desugaring of expression statements."""
        # Create an infix expression that needs normalization
        left = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 1), "x")
        right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 15), 5)

        infix = InfixExpression(Token(TokenType.OP_EQ, "is equal to", 1, 3), "is equal to", left)
        infix.right = right

        expr_stmt = ExpressionStatement(Token(TokenType.MISC_IDENT, "x", 1, 1), infix)
        desugared = expr_stmt.desugar()

        assert isinstance(desugared, ExpressionStatement)
        assert desugared is not expr_stmt
        assert isinstance(desugared.expression, InfixExpression)
        assert desugared.expression.operator == "=="  # Should be normalized


class TestFunctionStatementDesugaring:
    """Test desugaring of function-like statements."""

    def test_action_statement_desugaring(self) -> None:
        """Test that ActionStatement desugars to FunctionStatement with PRIVATE visibility."""
        token = Token(TokenType.KW_ACTION, "action", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "doSomething", 1, 8), "doSomething")

        body = BlockStatement(Token(TokenType.PUNCT_COLON, ":", 1, 20), depth=1)
        body.statements = [
            ReturnStatement(
                Token(TokenType.KW_RETURN, "give back", 2, 3),
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 2, 13), 42),
            )
        ]

        action = ActionStatement(token, name, body=body)
        desugared = action.desugar()

        assert isinstance(desugared, FunctionStatement)
        assert desugared.visibility == FunctionVisibility.PRIVATE
        assert desugared.name is name
        # Body might be flattened if it has single statement
        if isinstance(desugared.body, BlockStatement):
            # Check that body was desugared (return statement normalized)
            ret_stmt = desugared.body.statements[0]
        else:
            # Single statement was flattened
            ret_stmt = desugared.body
        assert isinstance(ret_stmt, ReturnStatement)
        assert ret_stmt.token.literal == "return"

    def test_interaction_statement_desugaring(self) -> None:
        """Test that InteractionStatement desugars to FunctionStatement with PUBLIC visibility."""
        token = Token(TokenType.KW_INTERACTION, "interaction", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "handleRequest", 1, 13), "handleRequest")

        body = BlockStatement(Token(TokenType.PUNCT_COLON, ":", 1, 27), depth=1)
        body.statements = [
            SetStatement(
                Token(TokenType.KW_SET, "Set", 2, 3),
                Identifier(Token(TokenType.MISC_IDENT, "x", 2, 7), "x"),
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "10", 2, 12), 10),
            )
        ]

        interaction = InteractionStatement(token, name, body=body)
        desugared = interaction.desugar()

        assert isinstance(desugared, FunctionStatement)
        assert desugared.visibility == FunctionVisibility.PUBLIC
        assert desugared.name is name

    def test_utility_statement_desugaring(self) -> None:
        """Test that UtilityStatement desugars to FunctionStatement with FUNCTION visibility."""
        token = Token(TokenType.KW_UTILITY, "utility", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "calculate", 1, 9), "calculate")

        body = BlockStatement(Token(TokenType.PUNCT_COLON, ":", 1, 19), depth=1)
        body.statements = [
            ReturnStatement(
                Token(TokenType.KW_RETURN, "gives back", 2, 3),
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "100", 2, 14), 100),
            )
        ]

        utility = UtilityStatement(token, name, body=body)
        desugared = utility.desugar()

        assert isinstance(desugared, FunctionStatement)
        assert desugared.visibility == FunctionVisibility.FUNCTION
        assert desugared.name is name
        # Check return normalization
        if isinstance(desugared.body, BlockStatement):
            ret_stmt = desugared.body.statements[0]
        else:
            # Single statement was flattened
            ret_stmt = desugared.body
        assert isinstance(ret_stmt, ReturnStatement)
        assert ret_stmt.token.literal == "return"

    def test_function_statement_str_representation(self) -> None:
        """Test string representation of FunctionStatement."""
        token = Token(TokenType.KW_ACTION, "action", 1, 1)
        name = Identifier(Token(TokenType.MISC_IDENT, "test", 1, 8), "test")
        body = BlockStatement(Token(TokenType.PUNCT_COLON, ":", 1, 13), depth=1)

        # Test PRIVATE (action)
        func1 = FunctionStatement(token, FunctionVisibility.PRIVATE, name, body=body)
        func1_str = str(func1)
        assert "action" in func1_str
        assert "`test`" in func1_str  # Identifier is wrapped in backticks

        # Test PUBLIC (interaction)
        func2 = FunctionStatement(token, FunctionVisibility.PUBLIC, name, body=body)
        func2_str = str(func2)
        assert "interaction" in func2_str
        assert "`test`" in func2_str

        # Test FUNCTION (utility)
        func3 = FunctionStatement(token, FunctionVisibility.FUNCTION, name, body=body)
        func3_str = str(func3)
        assert "utility" in func3_str
        assert "`test`" in func3_str


class TestComplexDesugaring:
    """Test desugaring of complex nested structures."""

    def test_nested_expression_desugaring(self) -> None:
        """Test desugaring of deeply nested expressions."""
        # Create: (x is equal to 5) and (y is greater than 10)
        x = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 1), "x")
        five = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 15), 5)

        left_expr = InfixExpression(Token(TokenType.OP_EQ, "is equal to", 1, 3), "is equal to", x)
        left_expr.right = five

        y = Identifier(Token(TokenType.MISC_IDENT, "y", 1, 20), "y")
        ten = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "10", 1, 38), 10)

        right_expr = InfixExpression(Token(TokenType.OP_GT, "is greater than", 1, 22), "is greater than", y)
        right_expr.right = ten

        and_expr = InfixExpression(Token(TokenType.KW_AND, "and", 1, 17), "and", left_expr)
        and_expr.right = right_expr

        desugared = and_expr.desugar()

        assert isinstance(desugared, InfixExpression)
        assert desugared.operator == "and"

        # Check left side normalization
        assert isinstance(desugared.left, InfixExpression)
        assert desugared.left.operator == "=="

        # Check right side normalization
        assert desugared.right is not None  # Type guard
        assert isinstance(desugared.right, InfixExpression)
        assert desugared.right.operator == ">"

    def test_complex_statement_desugaring(self) -> None:
        """Test desugaring of complex statement structures."""
        # Create an if statement with nested blocks and expressions
        token = Token(TokenType.KW_IF, "if", 1, 1)

        # Condition: x is strictly equal to 5
        x = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 4), "x")
        five = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 27), 5)
        condition = InfixExpression(
            Token(TokenType.OP_STRICT_EQ, "is strictly equal to", 1, 6), "is strictly equal to", x
        )
        condition.right = five

        # Consequence: nested block with give back
        consequence = BlockStatement(Token(TokenType.PUNCT_COLON, ":", 1, 32), depth=1)
        inner_block = BlockStatement(Token(TokenType.PUNCT_COLON, ":", 2, 5), depth=2)
        inner_block.statements = [
            ReturnStatement(
                Token(TokenType.KW_RETURN, "give back", 3, 7),
                WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "100", 3, 17), 100),
            )
        ]
        consequence.statements = [inner_block]

        if_stmt = IfStatement(token, condition)
        if_stmt.consequence = consequence

        desugared = if_stmt.desugar()

        assert isinstance(desugared, IfStatement)

        # Check condition normalization
        assert desugared.condition is not None  # Type guard
        assert isinstance(desugared.condition, InfixExpression)
        assert desugared.condition.operator == "==="

        # Check that nested single-statement blocks are preserved in if statement
        assert desugared.consequence is not None  # Type guard
        assert isinstance(desugared.consequence, BlockStatement)
        # Blocks are now preserved for scope
        assert len(desugared.consequence.statements) == 1
        inner_block2 = desugared.consequence.statements[0]
        assert isinstance(inner_block2, BlockStatement)  # Block is preserved
        assert len(inner_block2.statements) == 1
        ret_stmt = inner_block2.statements[0]
        assert isinstance(ret_stmt, ReturnStatement)
        assert ret_stmt.token.literal == "return"
