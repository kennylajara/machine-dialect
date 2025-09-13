"""Comprehensive tests for HIR to MIR lowering with full AST coverage."""

from __future__ import annotations

from machine_dialect.ast import (
    ActionStatement,
    BlockStatement,
    ConditionalExpression,
    ErrorExpression,
    ErrorStatement,
    ExpressionStatement,
    Identifier,
    IfStatement,
    InfixExpression,
    InteractionStatement,
    Parameter,
    PrefixExpression,
    Program,
    ReturnStatement,
    SayStatement,
    SetStatement,
    StringLiteral,
    URLLiteral,
    UtilityStatement,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.lexer import Token, TokenType
from machine_dialect.mir.hir_to_mir import HIRToMIRLowering, lower_to_mir
from machine_dialect.mir.mir_instructions import (
    Assert,
    BinaryOp,
    ConditionalJump,
    LoadConst,
    MIRInstruction,
    Print,
    Scope,
    Select,
    UnaryOp,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant


class TestHIRToMIRComplete:
    """Test complete HIR to MIR lowering with all AST node types."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.lowerer = HIRToMIRLowering()

    def _dummy_token(self, literal: str = "", token_type: TokenType = TokenType.MISC_IDENT) -> Token:
        """Create a dummy token for testing."""
        return Token(token_type, literal, 0, 0)

    def test_error_statement_lowering(self) -> None:
        """Test lowering of ErrorStatement."""
        # Create error statement
        error_stmt = ErrorStatement(
            self._dummy_token("error"), skipped_tokens=[], message="Syntax error: unexpected token"
        )

        # Create program with error
        program = Program([error_stmt])

        # Lower to MIR
        mir = lower_to_mir(program)

        # Should have main function
        assert mir.get_function("__main__") is not None
        main = mir.get_function("__main__")

        # Should have entry block with Assert instruction
        assert main is not None
        entry = main.cfg.entry_block
        assert entry is not None

        # Find Assert instruction
        assert entry is not None
        asserts = [inst for inst in entry.instructions if isinstance(inst, Assert)]
        assert len(asserts) == 1
        assert asserts[0].message is not None
        assert "Parse error" in asserts[0].message

        # Should have entry block with Assert instruction
        entry2 = main.cfg.entry_block
        assert entry2 is not None

        # Find Assert instruction
        assert entry2 is not None
        asserts2 = [inst for inst in entry2.instructions if isinstance(inst, Assert)]
        assert len(asserts2) == 1
        assert asserts2[0].message is not None
        assert "Parse error" in asserts2[0].message

    def test_error_expression_lowering(self) -> None:
        """Test lowering of ErrorExpression."""
        # Create error expression in a statement
        error_expr = ErrorExpression(self._dummy_token("error"), message="Invalid expression")
        expr_stmt = ExpressionStatement(self._dummy_token(), error_expr)

        # Create program
        program = Program([expr_stmt])

        # Lower to MIR
        mir = lower_to_mir(program)

        # Should have Assert for error expression
        main = mir.get_function("__main__")
        assert main is not None
        entry = main.cfg.entry_block
        assert entry is not None
        asserts = [inst for inst in entry.instructions if isinstance(inst, Assert)]
        assert any(a.message and "Expression error" in a.message for a in asserts)

    def test_conditional_expression_lowering(self) -> None:
        """Test lowering of ConditionalExpression (ternary)."""
        # Create: x = true ? 1 : 2
        condition = YesNoLiteral(self._dummy_token("true"), True)
        true_val = WholeNumberLiteral(self._dummy_token("1"), 1)
        false_val = WholeNumberLiteral(self._dummy_token("2"), 2)

        cond_expr = ConditionalExpression(self._dummy_token(), true_val)
        cond_expr.condition = condition
        cond_expr.alternative = false_val

        set_stmt = SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("x"), "x"), cond_expr)

        program = Program([set_stmt])
        mir = lower_to_mir(program)

        # Should have Select instruction
        main = mir.get_function("__main__")
        assert main is not None
        entry = main.cfg.entry_block
        assert entry is not None
        selects = [inst for inst in entry.instructions if isinstance(inst, Select)]
        assert len(selects) == 1

    def test_say_statement_lowering(self) -> None:
        """Test lowering of SayStatement."""
        # Create: Say "Hello"
        say_stmt = SayStatement(self._dummy_token("say"), StringLiteral(self._dummy_token('"Hello"'), "Hello"))

        program = Program([say_stmt])
        mir = lower_to_mir(program)

        # Should have Print instruction
        main = mir.get_function("__main__")
        assert main is not None
        entry = main.cfg.entry_block
        assert entry is not None
        prints = [inst for inst in entry.instructions if isinstance(inst, Print)]
        assert len(prints) == 1

    def test_block_statement_with_scope(self) -> None:
        """Test that BlockStatement generates scope instructions."""
        # Create block with statements
        stmt1 = SetStatement(
            self._dummy_token("set"),
            Identifier(self._dummy_token("x"), "x"),
            WholeNumberLiteral(self._dummy_token("1"), 1),
        )

        block = BlockStatement(self._dummy_token(), depth=1)
        block.statements = [stmt1]

        program = Program([block])
        mir = lower_to_mir(program)

        # Should have Scope instructions
        main = mir.get_function("__main__")
        assert main is not None
        entry = main.cfg.entry_block
        assert entry is not None
        scopes = [inst for inst in entry.instructions if isinstance(inst, Scope)]

        # Should have begin and end scope
        assert len(scopes) == 2
        assert scopes[0].is_begin
        assert not scopes[1].is_begin

    def test_action_statement_lowering(self) -> None:
        """Test lowering of ActionStatement (private method)."""
        # Create action
        body_block = BlockStatement(self._dummy_token())
        body_block.statements = [ReturnStatement(self._dummy_token("return"), None)]
        action = ActionStatement(
            self._dummy_token("action"),
            name=Identifier(self._dummy_token("doWork"), "doWork"),
            inputs=[],
            outputs=None,
            body=body_block,
        )

        program = Program([action])
        mir = lower_to_mir(program)

        # Should have function with EMPTY return type
        func = mir.get_function("doWork")
        assert func is not None
        assert func is not None
        assert func.return_type == MIRType.EMPTY

    def test_interaction_statement_lowering(self) -> None:
        """Test lowering of InteractionStatement (public method)."""
        # Create interaction
        body_block = BlockStatement(self._dummy_token())
        body_block.statements = []
        interaction = InteractionStatement(
            self._dummy_token("interaction"),
            name=Identifier(self._dummy_token("handleRequest"), "handleRequest"),
            inputs=[
                Parameter(self._dummy_token("input"), Identifier(self._dummy_token("input"), "input"), "", True, None)
            ],
            outputs=None,
            body=body_block,
        )

        program = Program([interaction])
        mir = lower_to_mir(program)

        # Should have function with parameter
        func = mir.get_function("handleRequest")
        assert func is not None
        assert func is not None
        assert len(func.params) == 1
        assert func.params[0].name == "input"

    def test_utility_statement_lowering(self) -> None:
        """Test lowering of UtilityStatement (function with return)."""
        # Create utility that returns a value
        body_block = BlockStatement(self._dummy_token())
        body_block.statements = [
            ReturnStatement(self._dummy_token("return"), WholeNumberLiteral(self._dummy_token("42"), 42))
        ]
        utility = UtilityStatement(
            self._dummy_token("utility"),
            name=Identifier(self._dummy_token("calculate"), "calculate"),
            inputs=[],
            outputs=None,
            body=body_block,
        )

        program = Program([utility])
        mir = lower_to_mir(program)

        # Should have function with UNKNOWN return type (can return values)
        func = mir.get_function("calculate")
        assert func is not None
        assert func is not None
        assert func.return_type == MIRType.UNKNOWN

    def test_url_literal_lowering(self) -> None:
        """Test lowering of URLLiteral."""
        # Create: x = https://example.com
        url = URLLiteral(self._dummy_token("https://example.com"), "https://example.com")
        set_stmt = SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("x"), "x"), url)

        program = Program([set_stmt])
        mir = lower_to_mir(program)

        # Should create constant with URL type
        main = mir.get_function("__main__")
        assert main is not None

        # Check for LoadConst with URL
        main = mir.get_function("__main__")
        assert main is not None
        assert main is not None
        entry = main.cfg.entry_block
        assert entry is not None
        loads = [inst for inst in entry.instructions if isinstance(inst, LoadConst)]
        assert any(
            isinstance(inst.constant, Constant) and inst.constant.value == "https://example.com" for inst in loads
        )

    def test_complex_control_flow(self) -> None:
        """Test complex control flow with nested if statements."""
        # Create nested if: if (x > 0) { if (x < 10) { y = x } else { y = 10 } }
        x_ident = Identifier(self._dummy_token("x"), "x")
        y_ident = Identifier(self._dummy_token("y"), "y")

        # Outer condition: x > 0
        outer_cond = InfixExpression(self._dummy_token(">"), ">", x_ident)
        outer_cond.right = WholeNumberLiteral(self._dummy_token("0"), 0)

        # Inner condition: x < 10
        inner_cond = InfixExpression(self._dummy_token("<"), "<", x_ident)
        inner_cond.right = WholeNumberLiteral(self._dummy_token("10"), 10)

        # Inner then: y = x
        inner_then = BlockStatement(self._dummy_token())
        inner_then.statements = [SetStatement(self._dummy_token("set"), y_ident, x_ident)]

        # Inner else: y = 10
        inner_else = BlockStatement(self._dummy_token())
        inner_else.statements = [
            SetStatement(self._dummy_token("set"), y_ident, WholeNumberLiteral(self._dummy_token("10"), 10))
        ]

        # Inner if
        inner_if = IfStatement(self._dummy_token("if"), inner_cond)
        inner_if.consequence = inner_then
        inner_if.alternative = inner_else

        # Outer then contains inner if
        outer_then = BlockStatement(self._dummy_token())
        outer_then.statements = [inner_if]

        # Outer if
        outer_if = IfStatement(self._dummy_token("if"), outer_cond)
        outer_if.consequence = outer_then
        outer_if.alternative = None

        # Initialize x
        init_x = SetStatement(self._dummy_token("set"), x_ident, WholeNumberLiteral(self._dummy_token("5"), 5))

        program = Program([init_x, outer_if])
        mir = lower_to_mir(program)

        # Should have multiple basic blocks
        main = mir.get_function("__main__")
        assert main is not None
        assert len(main.cfg.blocks) > 3  # At least entry + branches

        # Should have conditional jumps
        all_instructions: list[MIRInstruction] = []
        for block in main.cfg.blocks.values():
            all_instructions.extend(block.instructions)

        cond_jumps = [inst for inst in all_instructions if isinstance(inst, ConditionalJump)]
        assert len(cond_jumps) >= 2  # At least 2 for nested ifs

    def test_all_binary_operators(self) -> None:
        """Test all binary operators are properly lowered."""
        operators = ["+", "-", "*", "/", "%", "^", "==", "!=", "<", ">", "<=", ">=", "and", "or"]

        for op in operators:
            # Create: result = 10 op 5
            expr = InfixExpression(self._dummy_token(op), op, WholeNumberLiteral(self._dummy_token("10"), 10))
            expr.right = WholeNumberLiteral(self._dummy_token("5"), 5)

            set_stmt = SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("result"), "result"), expr)

            program = Program([set_stmt])
            mir = lower_to_mir(program)

            # Should have BinaryOp with correct operator
            main = mir.get_function("__main__")
            assert main is not None, f"Failed for operator {op}"
            entry = main.cfg.entry_block
            assert entry is not None, f"Failed for operator {op}"
            binops = [inst for inst in entry.instructions if isinstance(inst, BinaryOp)]
            # ^ in AST becomes ** in MIR
            expected_op = "**" if op == "^" else op
            assert any(inst.op == expected_op for inst in binops), f"Failed for operator {op}"

    def test_unary_operators(self) -> None:
        """Test unary operators are properly lowered."""
        # Test negation: -5
        neg_expr = PrefixExpression(self._dummy_token("-"), "-")
        neg_expr.right = WholeNumberLiteral(self._dummy_token("5"), 5)

        # Test not: not true
        not_expr = PrefixExpression(self._dummy_token("not"), "not")
        not_expr.right = YesNoLiteral(self._dummy_token("true"), True)

        program = Program(
            [
                SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("x"), "x"), neg_expr),
                SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("y"), "y"), not_expr),
            ]
        )

        mir = lower_to_mir(program)
        main = mir.get_function("__main__")
        assert main is not None
        entry = main.cfg.entry_block
        assert entry is not None

        # Should have UnaryOp instructions
        unaryops = [inst for inst in entry.instructions if isinstance(inst, UnaryOp)]
        assert len(unaryops) == 2

        # Check operators
        ops = {inst.op for inst in unaryops}
        assert "-" in ops
        assert "not" in ops
