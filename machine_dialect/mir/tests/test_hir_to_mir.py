"""Tests for HIR to MIR lowering."""

from __future__ import annotations

from machine_dialect.ast import (
    Arguments,
    BlockStatement,
    CallStatement,
    EmptyLiteral,
    Expression,
    FloatLiteral,
    FunctionStatement,
    FunctionVisibility,
    Identifier,
    IfStatement,
    InfixExpression,
    Parameter,
    PrefixExpression,
    Program,
    ReturnStatement,
    SetStatement,
    Statement,
    StringLiteral,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.lexer import Token, TokenType
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    LoadConst,
    Return,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_types import MIRType


class TestHIRToMIRLowering:
    """Test HIR to MIR lowering."""

    def _dummy_token(self, literal: str = "", token_type: TokenType = TokenType.MISC_IDENT) -> Token:
        """Create a dummy token for testing."""
        return Token(token_type, literal, 0, 0)

    def _create_infix_expr(self, operator: str, left: Expression, right: Expression) -> InfixExpression:
        """Create an infix expression with proper initialization."""
        token_map = {
            "+": TokenType.OP_PLUS,
            "-": TokenType.OP_MINUS,
            "*": TokenType.OP_STAR,
            "/": TokenType.OP_DIVISION,
        }
        token_type = token_map.get(operator, TokenType.MISC_ILLEGAL)
        expr = InfixExpression(token=self._dummy_token(operator, token_type), operator=operator, left=left)
        expr.right = right
        return expr

    def test_lower_empty_program(self) -> None:
        """Test lowering an empty program."""
        program = Program(statements=[])
        module = lower_to_mir(program)

        assert module.name == "__main__"
        assert len(module.functions) == 0
        assert module.main_function is None

    def test_lower_simple_function(self) -> None:
        """Test lowering a simple function."""
        # Create function: function main() { return 42; }
        body = BlockStatement(token=self._dummy_token())
        body.statements = [
            ReturnStatement(
                token=self._dummy_token("return", TokenType.KW_RETURN),
                return_value=WholeNumberLiteral(token=self._dummy_token("42", TokenType.LIT_WHOLE_NUMBER), value=42),
            )
        ]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("__main__"), "__main__"),
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        # Check module has main function
        assert len(module.functions) == 1
        assert "__main__" in module.functions
        assert module.main_function == "__main__"

        # Check function structure
        main_func = module.get_function("__main__")
        assert main_func is not None
        assert main_func.name == "__main__"
        assert len(main_func.params) == 0

        # Check CFG
        assert main_func.cfg.entry_block is not None
        entry = main_func.cfg.entry_block
        # With Load-Then-Store approach, we generate LoadConst + Return
        assert len(entry.instructions) == 2
        assert isinstance(entry.instructions[0], LoadConst)
        assert isinstance(entry.instructions[1], Return)

    def test_lower_function_with_parameters(self) -> None:
        """Test lowering a function with parameters."""
        # Create function: function add(a, b) { return a + b; }
        inputs = [
            Parameter(token=self._dummy_token("a"), name=Identifier(self._dummy_token("a"), "a")),
            Parameter(token=self._dummy_token("b"), name=Identifier(self._dummy_token("b"), "b")),
        ]
        body = BlockStatement(token=self._dummy_token())
        body.statements = [
            ReturnStatement(
                token=self._dummy_token("return", TokenType.KW_RETURN),
                return_value=self._create_infix_expr(
                    "+", Identifier(self._dummy_token("a"), "a"), Identifier(self._dummy_token("b"), "b")
                ),
            )
        ]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("add"), "add"),
            inputs=inputs,
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        # Check function has parameters
        add_func = module.get_function("add")
        assert add_func is not None
        assert len(add_func.params) == 2
        assert add_func.params[0].name == "a"
        assert add_func.params[1].name == "b"

    def test_lower_set_statement(self) -> None:
        """Test lowering a set statement."""
        # Create: function main() { set x to 10; }
        body = BlockStatement(token=self._dummy_token())
        body.statements = [
            SetStatement(
                token=self._dummy_token("set", TokenType.KW_SET),
                name=Identifier(self._dummy_token("x"), "x"),
                value=WholeNumberLiteral(token=self._dummy_token("10", TokenType.LIT_WHOLE_NUMBER), value=10),
            )
        ]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("__main__"), "__main__"),
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        main_func = module.get_function("__main__")
        assert main_func is not None
        assert main_func.cfg.entry_block is not None

        # Should have StoreVar instruction
        instructions = main_func.cfg.entry_block.instructions
        assert any(isinstance(inst, StoreVar) for inst in instructions)

    def test_lower_if_statement(self) -> None:
        """Test lowering an if statement."""
        # Create: if (true) { return 1; } else { return 2; }
        consequence_block = BlockStatement(token=self._dummy_token())
        consequence_block.statements = [
            ReturnStatement(
                token=self._dummy_token("return", TokenType.KW_RETURN),
                return_value=WholeNumberLiteral(token=self._dummy_token("1", TokenType.LIT_WHOLE_NUMBER), value=1),
            )
        ]

        alternative_block = BlockStatement(token=self._dummy_token())
        alternative_block.statements = [
            ReturnStatement(
                token=self._dummy_token("return", TokenType.KW_RETURN),
                return_value=WholeNumberLiteral(token=self._dummy_token("2", TokenType.LIT_WHOLE_NUMBER), value=2),
            )
        ]

        if_stmt = IfStatement(
            token=self._dummy_token("if", TokenType.KW_IF),
            condition=YesNoLiteral(token=self._dummy_token("true", TokenType.LIT_YES), value=True),
        )
        if_stmt.consequence = consequence_block
        if_stmt.alternative = alternative_block
        body = BlockStatement(token=self._dummy_token())
        body.statements = [if_stmt]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("test"), "test"),
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        test_func = module.get_function("test")
        assert test_func is not None

        # Should have multiple blocks
        assert len(test_func.cfg.blocks) > 1

        # Should have conditional jump in entry block
        assert test_func.cfg.entry_block is not None
        entry = test_func.cfg.entry_block
        assert any(isinstance(inst, ConditionalJump) for inst in entry.instructions)

    def test_lower_call_statement(self) -> None:
        """Test lowering a call statement."""
        # Create: call print with "hello";
        args = Arguments(token=self._dummy_token())
        args.positional = [StringLiteral(token=self._dummy_token('"hello"', TokenType.LIT_TEXT), value='"hello"')]
        call_stmt = CallStatement(
            token=self._dummy_token("use", TokenType.KW_USE),
            function_name=StringLiteral(token=self._dummy_token('"print"', TokenType.LIT_TEXT), value='"print"'),
            arguments=args,
        )
        body = BlockStatement(token=self._dummy_token())
        body.statements = [call_stmt]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("__main__"), "__main__"),
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        main_func = module.get_function("__main__")
        assert main_func is not None
        assert main_func.cfg.entry_block is not None

        # Should have Call instruction
        instructions = main_func.cfg.entry_block.instructions
        assert any(isinstance(inst, Call) for inst in instructions)

    def test_lower_infix_expression(self) -> None:
        """Test lowering infix expressions."""
        # Create: return 2 + 3 * 4;
        expr = self._create_infix_expr(
            "+",
            WholeNumberLiteral(token=self._dummy_token("2", TokenType.LIT_WHOLE_NUMBER), value=2),
            self._create_infix_expr(
                "*",
                WholeNumberLiteral(token=self._dummy_token("3", TokenType.LIT_WHOLE_NUMBER), value=3),
                WholeNumberLiteral(token=self._dummy_token("4", TokenType.LIT_WHOLE_NUMBER), value=4),
            ),
        )
        body = BlockStatement(token=self._dummy_token())
        body.statements = [ReturnStatement(token=self._dummy_token("return", TokenType.KW_RETURN), return_value=expr)]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("calc"), "calc"),
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        calc_func = module.get_function("calc")
        assert calc_func is not None
        assert calc_func.cfg.entry_block is not None

        # Should have BinaryOp instructions
        instructions = calc_func.cfg.entry_block.instructions
        binary_ops = [inst for inst in instructions if isinstance(inst, BinaryOp)]
        assert len(binary_ops) == 2  # One for *, one for +

    def test_lower_prefix_expression(self) -> None:
        """Test lowering prefix expressions."""
        # Create: return -42;
        expr = PrefixExpression(token=self._dummy_token("-", TokenType.OP_MINUS), operator="-")
        expr.right = WholeNumberLiteral(token=self._dummy_token("42", TokenType.LIT_WHOLE_NUMBER), value=42)
        body = BlockStatement(token=self._dummy_token())
        body.statements = [ReturnStatement(token=self._dummy_token("return", TokenType.KW_RETURN), return_value=expr)]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("neg"), "neg"),
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        neg_func = module.get_function("neg")
        assert neg_func is not None
        assert neg_func.cfg.entry_block is not None

        # Should have UnaryOp instruction
        instructions = neg_func.cfg.entry_block.instructions
        assert any(isinstance(inst, UnaryOp) for inst in instructions)

    # def test_lower_call_expression(self) -> None:
    #     """Test lowering call expressions."""
    #     # Note: CallExpression doesn't exist in the current AST
    #     # This test would need to be implemented differently
    #     pass

    def test_lower_literals(self) -> None:
        """Test lowering various literal types."""
        # Create function with various literals
        stmts: list[Statement] = [
            SetStatement(
                token=self._dummy_token("set", TokenType.KW_SET),
                name=Identifier(self._dummy_token("i"), "i"),
                value=WholeNumberLiteral(token=self._dummy_token("42", TokenType.LIT_WHOLE_NUMBER), value=42),
            ),
            SetStatement(
                token=self._dummy_token("set", TokenType.KW_SET),
                name=Identifier(self._dummy_token("f"), "f"),
                value=FloatLiteral(token=self._dummy_token("3.14", TokenType.LIT_FLOAT), value=3.14),
            ),
            SetStatement(
                token=self._dummy_token("set", TokenType.KW_SET),
                name=Identifier(self._dummy_token("s"), "s"),
                value=StringLiteral(token=self._dummy_token('"hello"', TokenType.LIT_TEXT), value='"hello"'),
            ),
            SetStatement(
                token=self._dummy_token("set", TokenType.KW_SET),
                name=Identifier(self._dummy_token("b"), "b"),
                value=YesNoLiteral(token=self._dummy_token("true", TokenType.LIT_YES), value=True),
            ),
            SetStatement(
                token=self._dummy_token("set", TokenType.KW_SET),
                name=Identifier(self._dummy_token("e"), "e"),
                value=EmptyLiteral(token=self._dummy_token("empty", TokenType.KW_EMPTY)),
            ),
        ]
        body = BlockStatement(token=self._dummy_token())
        body.statements = stmts
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("literals"), "literals"),
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        lit_func = module.get_function("literals")
        assert lit_func is not None

        # Check that we have 5 local variables
        assert len(lit_func.locals) == 5
        assert "i" in lit_func.locals
        assert "f" in lit_func.locals
        assert "s" in lit_func.locals
        assert "b" in lit_func.locals
        assert "e" in lit_func.locals

    def test_lower_action_and_interaction(self) -> None:
        """Test lowering action and interaction functions."""
        # Create action (private method)
        action = FunctionStatement(
            token=self._dummy_token("action", TokenType.KW_ACTION),
            visibility=FunctionVisibility.PRIVATE,
            name=Identifier(self._dummy_token("helper"), "helper"),
            body=BlockStatement(token=self._dummy_token()),
        )

        # Create interaction (public method)
        body = BlockStatement(token=self._dummy_token())
        interaction = FunctionStatement(
            token=self._dummy_token("interaction", TokenType.KW_INTERACTION),
            visibility=FunctionVisibility.PUBLIC,
            name=Identifier(self._dummy_token("process"), "process"),
            inputs=[Parameter(token=self._dummy_token("input"), name=Identifier(self._dummy_token("input"), "input"))],
            body=body,
        )

        program = Program(statements=[action, interaction])
        module = lower_to_mir(program)

        # Both should be in module
        assert len(module.functions) == 2
        assert "helper" in module.functions
        assert "process" in module.functions

        # Check return types (both should be void/empty)
        helper = module.get_function("helper")
        process = module.get_function("process")
        assert helper is not None
        assert process is not None
        assert helper.return_type == MIRType.EMPTY
        assert process.return_type == MIRType.EMPTY

    def test_implicit_return(self) -> None:
        """Test that implicit return is added when needed."""
        # Function without explicit return
        body = BlockStatement(token=self._dummy_token())
        body.statements = [
            SetStatement(
                token=self._dummy_token("set", TokenType.KW_SET),
                name=Identifier(self._dummy_token("x"), "x"),
                value=WholeNumberLiteral(token=self._dummy_token("10", TokenType.LIT_WHOLE_NUMBER), value=10),
            )
        ]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("no_return"), "no_return"),
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        no_return = module.get_function("no_return")
        assert no_return is not None
        assert no_return.cfg.entry_block is not None

        # Should have added implicit return
        instructions = no_return.cfg.entry_block.instructions
        assert any(isinstance(inst, Return) for inst in instructions)

    def test_nested_if_statements(self) -> None:
        """Test lowering nested if statements."""
        # Create: if (a) { if (b) { return 1; } }
        inner_consequence = BlockStatement(token=self._dummy_token())
        inner_consequence.statements = [
            ReturnStatement(
                token=self._dummy_token("return", TokenType.KW_RETURN),
                return_value=WholeNumberLiteral(token=self._dummy_token("1", TokenType.LIT_WHOLE_NUMBER), value=1),
            )
        ]

        inner_if = IfStatement(
            token=self._dummy_token("if", TokenType.KW_IF), condition=Identifier(self._dummy_token("b"), "b")
        )
        inner_if.consequence = inner_consequence

        outer_consequence = BlockStatement(token=self._dummy_token())
        outer_consequence.statements = [inner_if]

        outer_if = IfStatement(
            token=self._dummy_token("if", TokenType.KW_IF), condition=Identifier(self._dummy_token("a"), "a")
        )
        outer_if.consequence = outer_consequence
        body = BlockStatement(token=self._dummy_token())
        body.statements = [outer_if]
        func = FunctionStatement(
            token=self._dummy_token("utility", TokenType.KW_UTILITY),
            visibility=FunctionVisibility.FUNCTION,
            name=Identifier(self._dummy_token("nested"), "nested"),
            inputs=[
                Parameter(token=self._dummy_token("a"), name=Identifier(self._dummy_token("a"), "a")),
                Parameter(token=self._dummy_token("b"), name=Identifier(self._dummy_token("b"), "b")),
            ],
            body=body,
        )
        program = Program(statements=[func])
        module = lower_to_mir(program)

        nested = module.get_function("nested")
        assert nested is not None

        # Should have multiple blocks for nested control flow
        assert len(nested.cfg.blocks) > 3
