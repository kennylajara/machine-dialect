"""Integration tests for complete AST → MIR → Bytecode pipeline."""

from __future__ import annotations

import unittest

from machine_dialect.ast import (
    Arguments,
    BlockStatement,
    CallExpression,
    CallStatement,
    ConditionalExpression,
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
    UtilityStatement,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.codegen.isa import Opcode
from machine_dialect.lexer import Token, TokenType
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.mir_to_bytecode import generate_bytecode
from machine_dialect.mir.mir_validation import validate_module
from machine_dialect.mir.ssa_construction import construct_ssa


class TestIntegrationPipeline(unittest.TestCase):
    """Test complete compilation pipeline from AST to bytecode."""

    def _dummy_token(self, literal: str = "", token_type: TokenType = TokenType.MISC_IDENT) -> Token:
        """Create a dummy token for testing."""
        return Token(token_type, literal, 0, 0)

    def _create_infix(self, op: str, left: Expression, right: Expression) -> InfixExpression:
        """Create an InfixExpression with proper initialization."""
        expr = InfixExpression(self._dummy_token(op), op, left)
        expr.right = right
        return expr

    def _create_block_with_statements(self, statements: list[Statement]) -> BlockStatement:
        """Create a BlockStatement with statements."""
        block = BlockStatement(self._dummy_token())
        block.statements = statements
        return block

    def _create_if_statement(
        self, condition: Expression, consequence: BlockStatement, alternative: BlockStatement | None = None
    ) -> IfStatement:
        """Create an IfStatement with proper initialization."""
        if_stmt = IfStatement(self._dummy_token("if"), condition)
        if_stmt.consequence = consequence
        if_stmt.alternative = alternative
        return if_stmt

    def _create_call_expression(self, func_name: str, args_list: list[Expression]) -> CallExpression:
        """Create a CallExpression with proper Arguments."""
        args = Arguments(self._dummy_token("with"))
        args.positional = args_list
        call_expr = CallExpression(self._dummy_token("call"), Identifier(self._dummy_token(func_name), func_name))
        call_expr.arguments = args
        return call_expr

    def test_simple_program_pipeline(self) -> None:
        """Test simple program through complete pipeline."""
        # Create AST: Set x to 42
        set_stmt = SetStatement(
            self._dummy_token("set"),
            Identifier(self._dummy_token("x"), "x"),
            WholeNumberLiteral(self._dummy_token("42"), 42),
        )

        program = Program([set_stmt])

        # Lower to MIR
        mir = lower_to_mir(program)

        # Validate MIR
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        # Convert to SSA
        for func in mir.functions.values():
            construct_ssa(func)

        # Generate bytecode
        module = generate_bytecode(mir)

        # Verify bytecode was generated
        self.assertIsNotNone(module)
        self.assertIsNotNone(module.main_chunk)
        self.assertGreater(len(module.main_chunk.bytecode), 0)

    def test_function_call_pipeline(self) -> None:
        """Test function definition and call through pipeline."""
        # Create utility function
        param = Parameter(self._dummy_token("x"), Identifier(self._dummy_token("x"), "x"), "int", True, None)

        utility = UtilityStatement(
            self._dummy_token("utility"),
            name=Identifier(self._dummy_token("double"), "double"),
            inputs=[param],
            outputs=None,
            body=self._create_block_with_statements(
                [
                    ReturnStatement(
                        self._dummy_token("return"),
                        self._create_infix(
                            "*", Identifier(self._dummy_token("x"), "x"), WholeNumberLiteral(self._dummy_token("2"), 2)
                        ),
                    )
                ]
            ),
        )

        # Call the function
        args = Arguments(self._dummy_token("with"))
        args.positional = [WholeNumberLiteral(self._dummy_token("21"), 21)]
        call = CallStatement(self._dummy_token("call"), Identifier(self._dummy_token("double"), "double"), args)

        program = Program([utility, call])

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Verify both main and double functions exist
        self.assertIsNotNone(module)
        self.assertIn("double", module.functions)
        self.assertGreater(len(module.functions["double"].bytecode), 0)

    def test_control_flow_pipeline(self) -> None:
        """Test if statement control flow through pipeline."""
        # Create: if (x > 10) { y = 100 } else { y = 200 }
        condition = self._create_infix(
            ">", Identifier(self._dummy_token("x"), "x"), WholeNumberLiteral(self._dummy_token("10"), 10)
        )

        then_branch = self._create_block_with_statements(
            [
                SetStatement(
                    self._dummy_token("set"),
                    Identifier(self._dummy_token("y"), "y"),
                    WholeNumberLiteral(self._dummy_token("100"), 100),
                )
            ]
        )

        else_branch = self._create_block_with_statements(
            [
                SetStatement(
                    self._dummy_token("set"),
                    Identifier(self._dummy_token("y"), "y"),
                    WholeNumberLiteral(self._dummy_token("200"), 200),
                )
            ]
        )

        if_stmt = IfStatement(self._dummy_token("if"), condition)
        if_stmt.consequence = then_branch
        if_stmt.alternative = else_branch

        # Initialize x
        init_x = SetStatement(
            self._dummy_token("set"),
            Identifier(self._dummy_token("x"), "x"),
            WholeNumberLiteral(self._dummy_token("15"), 15),
        )

        program = Program([init_x, if_stmt])

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Verify jump instructions exist in bytecode
        self.assertIsNotNone(module)
        bytecode = module.main_chunk.bytecode

        # Should contain jump opcodes
        jump_opcodes = {Opcode.JUMP, Opcode.JUMP_IF_FALSE}
        found_jumps = any(byte in jump_opcodes for byte in bytecode[::2])  # Check opcodes
        self.assertTrue(found_jumps, "No jump instructions found in bytecode")

    def test_expression_evaluation_pipeline(self) -> None:
        """Test complex expression evaluation through pipeline."""
        # Create: result = (10 + 20) * (30 - 15)
        add_expr = self._create_infix(
            "+", WholeNumberLiteral(self._dummy_token("10"), 10), WholeNumberLiteral(self._dummy_token("20"), 20)
        )

        sub_expr = self._create_infix(
            "-", WholeNumberLiteral(self._dummy_token("30"), 30), WholeNumberLiteral(self._dummy_token("15"), 15)
        )

        mul_expr = self._create_infix("*", add_expr, sub_expr)

        set_stmt = SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("result"), "result"), mul_expr)

        program = Program([set_stmt])

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Verify arithmetic opcodes exist
        self.assertIsNotNone(module)
        bytecode = module.main_chunk.bytecode

        arithmetic_opcodes = {Opcode.ADD, Opcode.SUB, Opcode.MUL}
        found_arithmetic = any(byte in arithmetic_opcodes for byte in bytecode[::2])
        self.assertTrue(found_arithmetic, "No arithmetic instructions found in bytecode")

    def test_all_literal_types_pipeline(self) -> None:
        """Test all literal types through pipeline."""
        statements = [
            SetStatement(
                self._dummy_token("set"),
                Identifier(self._dummy_token("int_var"), "int_var"),
                WholeNumberLiteral(self._dummy_token("42"), 42),
            ),
            SetStatement(
                self._dummy_token("set"),
                Identifier(self._dummy_token("float_var"), "float_var"),
                FloatLiteral(self._dummy_token("3.14"), 3.14),
            ),
            SetStatement(
                self._dummy_token("set"),
                Identifier(self._dummy_token("str_var"), "str_var"),
                StringLiteral(self._dummy_token('"hello"'), "hello"),
            ),
            SetStatement(
                self._dummy_token("set"),
                Identifier(self._dummy_token("bool_var"), "bool_var"),
                YesNoLiteral(self._dummy_token("true"), True),
            ),
        ]

        from typing import cast

        from machine_dialect.ast import Statement

        program = Program(cast(list[Statement], statements))

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Verify constants were added
        self.assertIsNotNone(module)
        self.assertGreater(module.main_chunk.constants.size(), 0)

        # Check that various types are in constants
        constant_values = module.main_chunk.constants.constants()
        self.assertIn(42, constant_values)
        self.assertIn(3.14, constant_values)
        self.assertIn("hello", constant_values)
        self.assertIn(True, constant_values)

    def test_nested_blocks_pipeline(self) -> None:
        """Test nested block statements with scoping through pipeline."""
        # Create nested blocks
        inner_stmt = SetStatement(
            self._dummy_token("set"),
            Identifier(self._dummy_token("inner"), "inner"),
            WholeNumberLiteral(self._dummy_token("1"), 1),
        )

        inner_block = BlockStatement(self._dummy_token(), depth=2)
        inner_block.statements = [inner_stmt]

        outer_stmt = SetStatement(
            self._dummy_token("set"),
            Identifier(self._dummy_token("outer"), "outer"),
            WholeNumberLiteral(self._dummy_token("2"), 2),
        )

        outer_block = BlockStatement(self._dummy_token(), depth=1)
        outer_block.statements = [outer_stmt, inner_block]

        program = Program([outer_block])

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Should compile without errors
        self.assertIsNotNone(module)
        self.assertGreater(len(module.main_chunk.bytecode), 0)

    def test_conditional_expression_pipeline(self) -> None:
        """Test conditional expression (ternary) through pipeline."""
        # Create: x = true ? 10 : 20
        cond_expr = ConditionalExpression(self._dummy_token(), WholeNumberLiteral(self._dummy_token("10"), 10))
        cond_expr.condition = YesNoLiteral(self._dummy_token("true"), True)
        cond_expr.alternative = WholeNumberLiteral(self._dummy_token("20"), 20)

        set_stmt = SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("x"), "x"), cond_expr)

        program = Program([set_stmt])

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Should generate bytecode with conditional logic
        self.assertIsNotNone(module)
        self.assertGreater(len(module.main_chunk.bytecode), 0)

    def test_unary_operations_pipeline(self) -> None:
        """Test unary operations through pipeline."""
        # Create: x = -5; y = not true
        neg_expr = PrefixExpression(self._dummy_token("-"), "-")
        neg_expr.right = WholeNumberLiteral(self._dummy_token("5"), 5)
        neg_stmt = SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("x"), "x"), neg_expr)

        not_expr = PrefixExpression(self._dummy_token("not"), "not")
        not_expr.right = YesNoLiteral(self._dummy_token("true"), True)
        not_stmt = SetStatement(self._dummy_token("set"), Identifier(self._dummy_token("y"), "y"), not_expr)

        program = Program([neg_stmt, not_stmt])

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Verify unary opcodes
        self.assertIsNotNone(module)
        bytecode = module.main_chunk.bytecode

        unary_opcodes = {Opcode.NEG, Opcode.NOT}
        found_unary = any(byte in unary_opcodes for byte in bytecode[::2])
        self.assertTrue(found_unary, "No unary instructions found in bytecode")

    def test_multiple_functions_pipeline(self) -> None:
        """Test multiple function definitions through pipeline."""
        # Create helper functions
        add_func = UtilityStatement(
            self._dummy_token("utility"),
            name=Identifier(self._dummy_token("add"), "add"),
            inputs=[
                Parameter(self._dummy_token("a"), Identifier(self._dummy_token("a"), "a"), "int", True, None),
                Parameter(self._dummy_token("b"), Identifier(self._dummy_token("b"), "b"), "int", True, None),
            ],
            outputs=None,
            body=self._create_block_with_statements(
                [
                    ReturnStatement(
                        self._dummy_token("return"),
                        self._create_infix(
                            "+", Identifier(self._dummy_token("a"), "a"), Identifier(self._dummy_token("b"), "b")
                        ),
                    )
                ]
            ),
        )

        mul_func = UtilityStatement(
            self._dummy_token("utility"),
            name=Identifier(self._dummy_token("multiply"), "multiply"),
            inputs=[
                Parameter(self._dummy_token("x"), Identifier(self._dummy_token("x"), "x"), "int", True, None),
                Parameter(self._dummy_token("y"), Identifier(self._dummy_token("y"), "y"), "int", True, None),
            ],
            outputs=None,
            body=self._create_block_with_statements(
                [
                    ReturnStatement(
                        self._dummy_token("return"),
                        self._create_infix(
                            "*", Identifier(self._dummy_token("x"), "x"), Identifier(self._dummy_token("y"), "y")
                        ),
                    )
                ]
            ),
        )

        # Call both functions
        args1 = Arguments(self._dummy_token("with"))
        args1.positional = [
            WholeNumberLiteral(self._dummy_token("10"), 10),
            WholeNumberLiteral(self._dummy_token("20"), 20),
        ]
        call1 = CallStatement(self._dummy_token("call"), Identifier(self._dummy_token("add"), "add"), args1)

        args2 = Arguments(self._dummy_token("with"))
        args2.positional = [
            WholeNumberLiteral(self._dummy_token("3"), 3),
            WholeNumberLiteral(self._dummy_token("4"), 4),
        ]
        call2 = CallStatement(self._dummy_token("call"), Identifier(self._dummy_token("multiply"), "multiply"), args2)

        program = Program([add_func, mul_func, call1, call2])

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Verify all functions exist
        self.assertIsNotNone(module)
        self.assertIn("add", module.functions)
        self.assertIn("multiply", module.functions)
        self.assertGreater(len(module.functions["add"].bytecode), 0)
        self.assertGreater(len(module.functions["multiply"].bytecode), 0)

    def test_complex_program_pipeline(self) -> None:
        """Test complex program with multiple features through pipeline."""
        # Create a factorial function
        factorial = FunctionStatement(
            self._dummy_token("function"),
            visibility=FunctionVisibility.PUBLIC,
            name=Identifier(self._dummy_token("factorial"), "factorial"),
            inputs=[Parameter(self._dummy_token("n"), Identifier(self._dummy_token("n"), "n"), "int", True, None)],
            outputs=None,
            body=self._create_block_with_statements(
                [
                    # if (n <= 1) { return 1 }
                    self._create_if_statement(
                        self._create_infix(
                            "<=", Identifier(self._dummy_token("n"), "n"), WholeNumberLiteral(self._dummy_token("1"), 1)
                        ),
                        self._create_block_with_statements(
                            [
                                ReturnStatement(
                                    self._dummy_token("return"), WholeNumberLiteral(self._dummy_token("1"), 1)
                                )
                            ]
                        ),
                        None,
                    ),
                    # return n * factorial(n - 1)
                    ReturnStatement(
                        self._dummy_token("return"),
                        self._create_infix(
                            "*",
                            Identifier(self._dummy_token("n"), "n"),
                            self._create_call_expression(
                                "factorial",
                                [
                                    self._create_infix(
                                        "-",
                                        Identifier(self._dummy_token("n"), "n"),
                                        WholeNumberLiteral(self._dummy_token("1"), 1),
                                    )
                                ],
                            ),
                        ),
                    ),
                ]
            ),
        )

        # Call factorial(5)
        args = Arguments(self._dummy_token("with"))
        args.positional = [WholeNumberLiteral(self._dummy_token("5"), 5)]
        call = CallStatement(self._dummy_token("call"), Identifier(self._dummy_token("factorial"), "factorial"), args)

        program = Program([factorial, call])

        # Complete pipeline
        mir = lower_to_mir(program)
        success, errors, warnings = validate_module(mir)
        self.assertTrue(success, f"MIR validation failed: {errors}")

        for func in mir.functions.values():
            construct_ssa(func)

        module = generate_bytecode(mir)

        # Verify factorial function with recursion
        self.assertIsNotNone(module)
        self.assertIn("factorial", module.functions)

        # Should have significant bytecode for recursive function
        factorial_chunk = module.functions["factorial"]
        self.assertGreater(len(factorial_chunk.bytecode), 10)  # Non-trivial function

        # Should have CALL opcode for recursion
        self.assertIn(Opcode.CALL.value, factorial_chunk.bytecode)


if __name__ == "__main__":
    unittest.main()
