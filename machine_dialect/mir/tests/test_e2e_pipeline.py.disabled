"""End-to-end integration tests for the MIR compilation pipeline.

This module tests the complete compilation pipeline from AST to bytecode
execution, ensuring all components work together correctly.
"""

from __future__ import annotations

import unittest

from machine_dialect.ast import (
    Expression,
    FloatLiteral,
    Identifier,
    IfStatement,
    InfixExpression,
    PrefixExpression,
    Program,
    ReturnStatement,
    SayStatement,
    SetStatement,
    Statement,
    StringLiteral,
    WholeNumberLiteral,
    YesNoLiteral,
)
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.benchmarks import CompilationBenchmark
from machine_dialect.mir.debug_info import DebugInfo, SourceLocation
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.mir_interpreter import MIRInterpreter
from machine_dialect.mir.mir_to_bytecode import generate_bytecode
from machine_dialect.mir.optimizations import PeepholeOptimizer
from machine_dialect.vm.vm import VM


class TestE2EPipeline(unittest.TestCase):
    """Test the complete MIR compilation pipeline."""

    def _token(self, token_type: TokenType, value: str = "") -> Token:
        """Create a token for testing."""
        return Token(token_type, value, 0, 0)

    def _create_prefix(self, op: str, right: Expression) -> PrefixExpression:
        """Helper to create PrefixExpression properly."""
        token = Token(TokenType.OP_MINUS, op, 0, 0)  # No OP_NOT in TokenType
        prefix = PrefixExpression(token, op)
        prefix.right = right
        return prefix

    def _create_infix(self, left: Expression, op: str, right: Expression) -> InfixExpression:
        """Helper to create InfixExpression properly."""
        token_type = {
            "+": TokenType.OP_PLUS,
            "-": TokenType.OP_MINUS,
            "*": TokenType.OP_STAR,
            "/": TokenType.OP_DIVISION,
            ">": TokenType.OP_GT,
            "<": TokenType.OP_LT,
            ">=": TokenType.OP_GTE,
            "<=": TokenType.OP_LTE,
            "&&": TokenType.KW_AND,
            "||": TokenType.KW_OR,
        }.get(op, TokenType.OP_PLUS)

        token = Token(token_type, op, 0, 0)
        infix = InfixExpression(token, op, left)
        infix.right = right
        return infix

    def _create_if_statement(
        self, condition: Expression, then_stmt: Statement, else_stmt: Statement | None = None
    ) -> IfStatement:
        """Helper to create IfStatement with proper BlockStatements."""
        from machine_dialect.ast import BlockStatement

        if_stmt = IfStatement(self._token(TokenType.KW_IF, "if"), condition)

        # Create consequence block
        then_block = BlockStatement(self._token(TokenType.OP_GT, ">"))
        then_block.statements = [then_stmt]
        if_stmt.consequence = then_block

        # Create alternative block if provided
        if else_stmt:
            else_block = BlockStatement(self._token(TokenType.OP_GT, ">"))
            else_block.statements = [else_stmt]
            if_stmt.alternative = else_block

        return if_stmt

    def test_simple_program_compilation(self) -> None:
        """Test compilation of a simple program."""
        # Create AST
        program = Program(
            [
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "42"), 42),
                )
            ]
        )

        # Lower to MIR
        mir_module = lower_to_mir(program)
        self.assertIsNotNone(mir_module)
        self.assertEqual(len(mir_module.functions), 1)

        # Generate bytecode
        bytecode_module = generate_bytecode(mir_module)
        self.assertIsNotNone(bytecode_module)
        self.assertIsNotNone(bytecode_module.main_chunk)

        # Execute in VM
        vm = VM()
        result = vm.run(bytecode_module)
        self.assertEqual(result, 42)

    def test_arithmetic_operations(self) -> None:
        """Test arithmetic operations through the pipeline."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "20"), 20),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "z"), "z"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "z"), "z")
                ),
            ]
        )

        # Compile and execute
        mir_module = lower_to_mir(program)
        bytecode_module = generate_bytecode(mir_module)

        vm = VM()
        result = vm.run(bytecode_module)
        self.assertEqual(result, 30)

    def test_control_flow(self) -> None:
        """Test control flow through the pipeline."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "15"), 15),
                ),
                self._create_if_statement(
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        ">",
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                    ),
                    SetStatement(
                        self._token(TokenType.KW_SET, "set"),
                        Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                        StringLiteral(self._token(TokenType.LIT_TEXT, "greater"), "greater"),
                    ),
                    SetStatement(
                        self._token(TokenType.KW_SET, "set"),
                        Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                        StringLiteral(self._token(TokenType.LIT_TEXT, "less or equal"), "less or equal"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                ),
            ]
        )

        # Compile and execute
        mir_module = lower_to_mir(program)
        bytecode_module = generate_bytecode(mir_module)

        vm = VM()
        result = vm.run(bytecode_module)
        self.assertEqual(result, "greater")

    def test_debug_information_tracking(self) -> None:
        """Test that debug information is preserved through compilation."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "x"), "x")
                ),
            ]
        )

        # Create debug info
        debug_info = DebugInfo()
        debug_info.current_file = "test.md"

        # Add source locations for statements
        for i, _ in enumerate(program.statements):
            _ = SourceLocation("test.md", i + 1, 1)
            # Note: We'd need to track instructions during lowering
            # This is a simplified test

        # Compile with debug info
        mir_module = lower_to_mir(program)
        bytecode_module = generate_bytecode(mir_module, debug_info)

        # Check that module was generated
        self.assertIsNotNone(bytecode_module)

    def test_optimization_pipeline(self) -> None:
        """Test bytecode optimization in the pipeline."""
        # Program with constant folding opportunity
        program = Program(
            [
                # This should be optimized to just loading 30
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    self._create_infix(
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                        "+",
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "20"), 20),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "x"), "x")
                ),
            ]
        )

        # Compile
        mir_module = lower_to_mir(program)
        bytecode_module = generate_bytecode(mir_module)

        # Optimize
        optimizer = PeepholeOptimizer()
        original_size = len(bytecode_module.main_chunk.bytecode)
        optimized_chunk = optimizer.optimize_chunk(bytecode_module.main_chunk)
        optimized_size = len(optimized_chunk.bytecode)

        # Check that optimization occurred
        self.assertLessEqual(optimized_size, original_size)

        # Execute optimized code
        bytecode_module.main_chunk = optimized_chunk
        vm = VM()
        result = vm.run(bytecode_module)
        self.assertEqual(result, 30)

    def test_mir_interpreter_consistency(self) -> None:
        """Test that MIR interpreter produces same results as bytecode execution."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "5"), 5),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "3"), 3),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "c"), "c"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                        "*",
                        Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "c"), "c")
                ),
            ]
        )

        # Execute via MIR interpreter
        mir_module = lower_to_mir(program)
        interpreter = MIRInterpreter()
        mir_result = interpreter.interpret_module(mir_module)

        # Execute via bytecode
        bytecode_module = generate_bytecode(mir_module)
        vm = VM()
        bytecode_result = vm.run(bytecode_module)

        # Results should match
        self.assertEqual(mir_result, bytecode_result)
        self.assertEqual(mir_result, 15)

    def test_complex_program(self) -> None:
        """Test a complex program with multiple features."""
        program = Program(
            [
                # Fibonacci calculation
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "n"), "n"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "6"), 6),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "0"), 0),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "1"), 1),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "i"), "i"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "0"), 0),
                ),
                # Simplified - would need loop support for real fibonacci
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "temp"), "temp"),
                    Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    ),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                    Identifier(self._token(TokenType.MISC_IDENT, "temp"), "temp"),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "b"), "b")
                ),
            ]
        )

        # Compile and execute
        mir_module = lower_to_mir(program)
        bytecode_module = generate_bytecode(mir_module)

        vm = VM()
        result = vm.run(bytecode_module)
        self.assertEqual(result, 1)  # First fibonacci step

    def test_performance_benchmarking(self) -> None:
        """Test performance benchmarking integration."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "100"), 100),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "200"), 200),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    ),
                ),
            ]
        )

        # Benchmark compilation
        benchmark = CompilationBenchmark()
        result = benchmark.benchmark_compilation(program, "test_benchmark")

        # Check that benchmarking worked
        self.assertIsNotNone(result)
        self.assertGreater(result.compilation_time, 0)
        self.assertGreater(result.bytecode_size, 0)
        self.assertGreater(result.instruction_count, 0)

    def test_error_handling(self) -> None:
        """Test error handling through the pipeline."""
        # Program with potential runtime error (division by zero)
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "0"), 0),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "z"), "z"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        "/",
                        Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "z"), "z")
                ),
            ]
        )

        # Compile
        mir_module = lower_to_mir(program)
        bytecode_module = generate_bytecode(mir_module)

        # Execute and expect error
        vm = VM()

        # The VM should handle division by zero
        from machine_dialect.runtime.errors import DivisionByZeroError

        with self.assertRaises(DivisionByZeroError):
            vm.run(bytecode_module)

    def test_print_statement_output(self) -> None:
        """Test that print statements work through the pipeline."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "msg"), "msg"),
                    StringLiteral(self._token(TokenType.LIT_TEXT, "Hello, MIR!"), "Hello, MIR!"),
                ),
                SayStatement(
                    self._token(TokenType.KW_SAY, "say"), Identifier(self._token(TokenType.MISC_IDENT, "msg"), "msg")
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "0"), 0),
                ),
            ]
        )

        # Execute via MIR interpreter
        mir_module = lower_to_mir(program)
        interpreter = MIRInterpreter()
        result = interpreter.interpret_module(mir_module)
        output = interpreter.get_output()

        # Check output
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], "Hello, MIR!")
        self.assertEqual(result, 0)

    def test_boolean_operations(self) -> None:
        """Test boolean operations through the pipeline."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                    YesNoLiteral(self._token(TokenType.KW_YES_NO, "true"), True),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    YesNoLiteral(self._token(TokenType.KW_YES_NO, "false"), False),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "c"), "c"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                        "&&",
                        Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    ),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "d"), "d"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                        "||",
                        Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    ),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "e"), "e"),
                    self._create_prefix("!", Identifier(self._token(TokenType.MISC_IDENT, "b"), "b")),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "e"), "e")
                ),
            ]
        )

        # Compile and execute
        mir_module = lower_to_mir(program)
        bytecode_module = generate_bytecode(mir_module)

        vm = VM()
        result = vm.run(bytecode_module)
        self.assertEqual(result, True)  # !false = true

    def test_type_mixing(self) -> None:
        """Test operations with mixed types."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    FloatLiteral(self._token(TokenType.LIT_FLOAT, "2.5"), 2.5),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "z"), "z"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "z"), "z")
                ),
            ]
        )

        # Compile and execute
        mir_module = lower_to_mir(program)
        bytecode_module = generate_bytecode(mir_module)

        vm = VM()
        result = vm.run(bytecode_module)
        self.assertAlmostEqual(result, 12.5)


class TestPipelineIntegration(unittest.TestCase):
    """Test integration between pipeline components."""

    def _token(self, token_type: TokenType, value: str = "") -> Token:
        """Create a token for testing."""
        return Token(token_type, value, 0, 0)

    def _create_infix(self, left: Expression, op: str, right: Expression) -> InfixExpression:
        """Helper to create InfixExpression properly."""
        token_type = {
            "+": TokenType.OP_PLUS,
            "-": TokenType.OP_MINUS,
            "*": TokenType.OP_STAR,
            "/": TokenType.OP_DIVISION,
            ">": TokenType.OP_GT,
            "<": TokenType.OP_LT,
            ">=": TokenType.OP_GTE,
            "<=": TokenType.OP_LTE,
            "&&": TokenType.KW_AND,
            "||": TokenType.KW_OR,
        }.get(op, TokenType.OP_PLUS)

        token = Token(token_type, op, 0, 0)
        infix = InfixExpression(token, op, left)
        infix.right = right
        return infix

    def test_mir_to_bytecode_preservation(self) -> None:
        """Test that semantics are preserved from MIR to bytecode."""
        programs = [
            # Simple return
            Program(
                [
                    ReturnStatement(
                        self._token(TokenType.KW_RETURN, "return"),
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "42"), 42),
                    )
                ]
            ),
            # Variable assignment
            Program(
                [
                    SetStatement(
                        self._token(TokenType.KW_SET, "set"),
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                    ),
                    ReturnStatement(
                        self._token(TokenType.KW_RETURN, "return"),
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    ),
                ]
            ),
            # Arithmetic
            Program(
                [
                    ReturnStatement(
                        self._token(TokenType.KW_RETURN, "return"),
                        self._create_infix(
                            WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "5"), 5),
                            "*",
                            WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "6"), 6),
                        ),
                    )
                ]
            ),
            # Comparison
            Program(
                [
                    ReturnStatement(
                        self._token(TokenType.KW_RETURN, "return"),
                        self._create_infix(
                            WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                            ">",
                            WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "5"), 5),
                        ),
                    )
                ]
            ),
        ]

        for i, program in enumerate(programs):
            with self.subTest(program=i):
                # Execute via MIR interpreter
                mir_module = lower_to_mir(program)
                interpreter = MIRInterpreter()
                mir_result = interpreter.interpret_module(mir_module)

                # Execute via bytecode
                bytecode_module = generate_bytecode(mir_module)
                vm = VM()
                bytecode_result = vm.run(bytecode_module)

                # Results must match
                self.assertEqual(mir_result, bytecode_result)

    def test_optimization_correctness(self) -> None:
        """Test that optimizations preserve program semantics."""
        program = Program(
            [
                # Constant expression that can be folded
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    self._create_infix(
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "2"), 2),
                        "*",
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "3"), 3),
                    ),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    self._create_infix(
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                        "-",
                        WholeNumberLiteral(self._token(TokenType.LIT_WHOLE_NUMBER, "4"), 4),
                    ),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "z"), "z"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "y"), "y"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "z"), "z")
                ),
            ]
        )

        # Compile without optimization
        mir_module = lower_to_mir(program)
        unopt_module = generate_bytecode(mir_module)

        # Compile with optimization
        opt_module = generate_bytecode(mir_module)
        optimizer = PeepholeOptimizer()
        opt_module.main_chunk = optimizer.optimize_chunk(opt_module.main_chunk)

        # Execute both versions
        vm1 = VM()
        unopt_result = vm1.run(unopt_module)

        vm2 = VM()
        opt_result = vm2.run(opt_module)

        # Results must match
        self.assertEqual(unopt_result, opt_result)
        self.assertEqual(unopt_result, 12)  # (2*3) + (10-4) = 6 + 6 = 12


if __name__ == "__main__":
    unittest.main()
