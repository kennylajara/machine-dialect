"""Differential testing suite for MIR pipeline vs old codegen.

This module tests that the new MIR-based compilation pipeline produces
semantically equivalent results to the old AST-to-bytecode code generator.
"""

from __future__ import annotations

import unittest

from machine_dialect.ast import (
    BlockStatement,
    BooleanLiteral,
    EmptyLiteral,
    Expression,
    FloatLiteral,
    Identifier,
    IfStatement,
    InfixExpression,
    IntegerLiteral,
    PrefixExpression,
    Program,
    ReturnStatement,
    SetStatement,
    Statement,
    StringLiteral,
)
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.differential_validator import DifferentialValidator, ValidationResult


class TestDifferentialCodegen(unittest.TestCase):
    """Test suite for differential validation between old and new pipelines."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.validator = DifferentialValidator(verbose=False)

    def _token(self, token_type: TokenType, value: str = "") -> Token:
        """Create a token for testing."""
        return Token(token_type, value, 0, 0)

    def _create_infix(self, left: Expression, op: str, right: Expression) -> InfixExpression:
        """Helper to create InfixExpression."""
        token_type = {
            "+": TokenType.OP_PLUS,
            "-": TokenType.OP_MINUS,
            "*": TokenType.OP_STAR,
            "/": TokenType.OP_DIVISION,
            ">": TokenType.OP_GT,
            "<": TokenType.OP_LT,
            ">=": TokenType.OP_GTE,
            "<=": TokenType.OP_LTE,
            "==": TokenType.OP_EQ,
            "!=": TokenType.OP_NOT_EQ,
            "and": TokenType.KW_AND,
            "or": TokenType.KW_OR,
        }.get(op, TokenType.OP_PLUS)

        token = Token(token_type, op, 0, 0)
        infix = InfixExpression(token, op, left)
        infix.right = right
        return infix

    def _create_prefix(self, op: str, right: Expression) -> PrefixExpression:
        """Helper to create PrefixExpression."""
        token_type = TokenType.OP_MINUS if op == "-" else TokenType.KW_NEGATION
        token = Token(token_type, op, 0, 0)
        prefix = PrefixExpression(token, op)
        prefix.right = right
        return prefix

    def test_simple_return(self) -> None:
        """Test simple return statement."""
        program = Program(
            [
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), IntegerLiteral(self._token(TokenType.LIT_INT, "42"), 42)
                )
            ]
        )

        result = self.validator.validate_program(program, "simple_return")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertEqual(result.old_output, 42)
        self.assertEqual(result.new_output, 42)

    def test_variable_assignment(self) -> None:
        """Test variable assignment and retrieval."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    IntegerLiteral(self._token(TokenType.LIT_INT, "100"), 100),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"), Identifier(self._token(TokenType.MISC_IDENT, "x"), "x")
                ),
            ]
        )

        result = self.validator.validate_program(program, "variable_assignment")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertEqual(result.old_output, 100)
        self.assertEqual(result.new_output, 100)

    def test_arithmetic_operations(self) -> None:
        """Test all arithmetic operations."""
        test_cases = [
            ("addition", "+", 10, 5, 15),
            ("subtraction", "-", 10, 5, 5),
            ("multiplication", "*", 10, 5, 50),
            ("division", "/", 10, 5, 2.0),
        ]

        for name, op, left_val, right_val, expected in test_cases:
            with self.subTest(operation=name):
                program = Program(
                    [
                        ReturnStatement(
                            self._token(TokenType.KW_RETURN, "return"),
                            self._create_infix(
                                IntegerLiteral(self._token(TokenType.LIT_INT, str(left_val)), left_val),
                                op,
                                IntegerLiteral(self._token(TokenType.LIT_INT, str(right_val)), right_val),
                            ),
                        )
                    ]
                )

                result = self.validator.validate_program(program, f"arithmetic_{name}")
                self.assertEqual(result.result, ValidationResult.PASS)
                self.assertEqual(result.old_output, expected)
                self.assertEqual(result.new_output, expected)

    def test_comparison_operations(self) -> None:
        """Test comparison operations."""
        test_cases = [
            ("greater_true", ">", 10, 5, True),
            ("greater_false", ">", 5, 10, False),
            ("less_true", "<", 5, 10, True),
            ("less_false", "<", 10, 5, False),
            ("gte_true", ">=", 10, 10, True),
            ("gte_false", ">=", 9, 10, False),
            ("lte_true", "<=", 10, 10, True),
            ("lte_false", "<=", 11, 10, False),
        ]

        for name, op, left_val, right_val, expected in test_cases:
            with self.subTest(operation=name):
                program = Program(
                    [
                        ReturnStatement(
                            self._token(TokenType.KW_RETURN, "return"),
                            self._create_infix(
                                IntegerLiteral(self._token(TokenType.LIT_INT, str(left_val)), left_val),
                                op,
                                IntegerLiteral(self._token(TokenType.LIT_INT, str(right_val)), right_val),
                            ),
                        )
                    ]
                )

                result = self.validator.validate_program(program, f"comparison_{name}")
                self.assertEqual(result.result, ValidationResult.PASS)
                self.assertEqual(result.old_output, expected)
                self.assertEqual(result.new_output, expected)

    def test_logical_operations(self) -> None:
        """Test logical AND and OR operations."""
        test_cases = [
            ("and_true_true", "and", True, True, True),
            ("and_true_false", "and", True, False, False),
            ("and_false_true", "and", False, True, False),
            ("and_false_false", "and", False, False, False),
            ("or_true_true", "or", True, True, True),
            ("or_true_false", "or", True, False, True),
            ("or_false_true", "or", False, True, True),
            ("or_false_false", "or", False, False, False),
        ]

        for name, op, left_val, right_val, expected in test_cases:
            with self.subTest(operation=name):
                program = Program(
                    [
                        ReturnStatement(
                            self._token(TokenType.KW_RETURN, "return"),
                            self._create_infix(
                                BooleanLiteral(
                                    self._token(
                                        TokenType.LIT_TRUE if left_val else TokenType.LIT_FALSE,
                                        str(left_val),
                                    ),
                                    left_val,
                                ),
                                op,
                                BooleanLiteral(
                                    self._token(
                                        TokenType.LIT_TRUE if right_val else TokenType.LIT_FALSE, str(right_val)
                                    ),
                                    right_val,
                                ),
                            ),
                        )
                    ]
                )

                result = self.validator.validate_program(program, f"logical_{name}")
                self.assertEqual(result.result, ValidationResult.PASS)
                self.assertEqual(result.old_output, expected)
                self.assertEqual(result.new_output, expected)

    def test_string_operations(self) -> None:
        """Test string literals and concatenation."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "msg"), "msg"),
                    StringLiteral(self._token(TokenType.LIT_TEXT, "Hello"), "Hello"),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    Identifier(self._token(TokenType.MISC_IDENT, "msg"), "msg"),
                ),
            ]
        )

        result = self.validator.validate_program(program, "string_operations")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertEqual(result.old_output, "Hello")
        self.assertEqual(result.new_output, "Hello")

    def test_float_operations(self) -> None:
        """Test floating point operations."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "pi"), "pi"),
                    FloatLiteral(self._token(TokenType.LIT_FLOAT, "3.14"), 3.14),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "radius"), "radius"),
                    FloatLiteral(self._token(TokenType.LIT_FLOAT, "2.0"), 2.0),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "pi"), "pi"),
                        "*",
                        Identifier(self._token(TokenType.MISC_IDENT, "radius"), "radius"),
                    ),
                ),
            ]
        )

        result = self.validator.validate_program(program, "float_operations")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertAlmostEqual(result.old_output, 6.28, places=5)
        self.assertAlmostEqual(result.new_output, 6.28, places=5)

    def test_if_statement(self) -> None:
        """Test if-else control flow."""
        # Test true branch
        program_true = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    IntegerLiteral(self._token(TokenType.LIT_INT, "10"), 10),
                ),
                self._create_if_statement(
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        ">",
                        IntegerLiteral(self._token(TokenType.LIT_INT, "5"), 5),
                    ),
                    SetStatement(
                        self._token(TokenType.KW_SET, "set"),
                        Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                        IntegerLiteral(self._token(TokenType.LIT_INT, "1"), 1),
                    ),
                    SetStatement(
                        self._token(TokenType.KW_SET, "set"),
                        Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                        IntegerLiteral(self._token(TokenType.LIT_INT, "0"), 0),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                ),
            ]
        )

        result = self.validator.validate_program(program_true, "if_true_branch")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertEqual(result.old_output, 1)
        self.assertEqual(result.new_output, 1)

        # Test false branch
        program_false = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    IntegerLiteral(self._token(TokenType.LIT_INT, "3"), 3),
                ),
                self._create_if_statement(
                    self._create_infix(
                        Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                        ">",
                        IntegerLiteral(self._token(TokenType.LIT_INT, "5"), 5),
                    ),
                    SetStatement(
                        self._token(TokenType.KW_SET, "set"),
                        Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                        IntegerLiteral(self._token(TokenType.LIT_INT, "1"), 1),
                    ),
                    SetStatement(
                        self._token(TokenType.KW_SET, "set"),
                        Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                        IntegerLiteral(self._token(TokenType.LIT_INT, "0"), 0),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    Identifier(self._token(TokenType.MISC_IDENT, "result"), "result"),
                ),
            ]
        )

        result = self.validator.validate_program(program_false, "if_false_branch")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertEqual(result.old_output, 0)
        self.assertEqual(result.new_output, 0)

    def _create_if_statement(
        self, condition: Expression, then_stmt: Statement, else_stmt: Statement | None = None
    ) -> IfStatement:
        """Helper to create IfStatement with proper BlockStatements."""
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

    def test_complex_expression(self) -> None:
        """Test complex nested expressions."""
        # (10 + 5) * (20 - 10) / 3 = 15 * 10 / 3 = 50
        program = Program(
            [
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    self._create_infix(
                        self._create_infix(
                            self._create_infix(
                                IntegerLiteral(self._token(TokenType.LIT_INT, "10"), 10),
                                "+",
                                IntegerLiteral(self._token(TokenType.LIT_INT, "5"), 5),
                            ),
                            "*",
                            self._create_infix(
                                IntegerLiteral(self._token(TokenType.LIT_INT, "20"), 20),
                                "-",
                                IntegerLiteral(self._token(TokenType.LIT_INT, "10"), 10),
                            ),
                        ),
                        "/",
                        IntegerLiteral(self._token(TokenType.LIT_INT, "3"), 3),
                    ),
                )
            ]
        )

        result = self.validator.validate_program(program, "complex_expression")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertAlmostEqual(result.old_output, 50.0, places=5)
        self.assertAlmostEqual(result.new_output, 50.0, places=5)

    def test_multiple_variables(self) -> None:
        """Test programs with multiple variable assignments."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                    IntegerLiteral(self._token(TokenType.LIT_INT, "10"), 10),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                    IntegerLiteral(self._token(TokenType.LIT_INT, "20"), 20),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "c"), "c"),
                    IntegerLiteral(self._token(TokenType.LIT_INT, "30"), 30),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "sum"), "sum"),
                    self._create_infix(
                        self._create_infix(
                            Identifier(self._token(TokenType.MISC_IDENT, "a"), "a"),
                            "+",
                            Identifier(self._token(TokenType.MISC_IDENT, "b"), "b"),
                        ),
                        "+",
                        Identifier(self._token(TokenType.MISC_IDENT, "c"), "c"),
                    ),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    Identifier(self._token(TokenType.MISC_IDENT, "sum"), "sum"),
                ),
            ]
        )

        result = self.validator.validate_program(program, "multiple_variables")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertEqual(result.old_output, 60)
        self.assertEqual(result.new_output, 60)

    def test_prefix_operations(self) -> None:
        """Test prefix operations like negation."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    IntegerLiteral(self._token(TokenType.LIT_INT, "10"), 10),
                ),
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "neg_x"), "neg_x"),
                    self._create_prefix("-", Identifier(self._token(TokenType.MISC_IDENT, "x"), "x")),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    Identifier(self._token(TokenType.MISC_IDENT, "neg_x"), "neg_x"),
                ),
            ]
        )

        result = self.validator.validate_program(program, "prefix_negation")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertEqual(result.old_output, -10)
        self.assertEqual(result.new_output, -10)

    def test_empty_literal(self) -> None:
        """Test empty/null literal handling."""
        program = Program(
            [
                SetStatement(
                    self._token(TokenType.KW_SET, "set"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                    EmptyLiteral(self._token(TokenType.KW_EMPTY, "empty")),
                ),
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    Identifier(self._token(TokenType.MISC_IDENT, "x"), "x"),
                ),
            ]
        )

        result = self.validator.validate_program(program, "empty_literal")
        self.assertEqual(result.result, ValidationResult.PASS)
        self.assertIsNone(result.old_output)
        self.assertIsNone(result.new_output)

    def test_error_handling(self) -> None:
        """Test that both pipelines handle errors consistently."""
        # Division by zero
        program = Program(
            [
                ReturnStatement(
                    self._token(TokenType.KW_RETURN, "return"),
                    self._create_infix(
                        IntegerLiteral(self._token(TokenType.LIT_INT, "10"), 10),
                        "/",
                        IntegerLiteral(self._token(TokenType.LIT_INT, "0"), 0),
                    ),
                )
            ]
        )

        result = self.validator.validate_program(program, "division_by_zero")
        # Both should error with DivisionByZeroError
        self.assertIn(result.result, [ValidationResult.PASS, ValidationResult.BOTH_ERROR])

    def test_summary_report(self) -> None:
        """Test that summary report is generated correctly."""
        # Run a few simple tests
        programs = [
            Program(
                [
                    ReturnStatement(
                        self._token(TokenType.KW_RETURN),
                        IntegerLiteral(self._token(TokenType.LIT_INT), i),
                    )
                ]
            )
            for i in range(5)
        ]

        for i, program in enumerate(programs):
            self.validator.validate_program(program, f"test_{i}")

        summary = self.validator.get_summary()
        self.assertIn("Differential Validation Summary", summary)
        self.assertIn("Total Tests:", summary)
        self.assertIn("Passed:", summary)


if __name__ == "__main__":
    unittest.main()
