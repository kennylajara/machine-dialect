"""Tests for the Pop instruction and expression statement handling."""

import unittest
from pathlib import Path

import pytest

from machine_dialect.ast import (
    ExpressionStatement,
    Identifier,
    InfixExpression,
    Program,
    SetStatement,
    WholeNumberLiteral,
)
from machine_dialect.codegen.isa import Opcode
from machine_dialect.compiler.config import CompilerConfig, OptimizationLevel
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.phases.codegen import CodeGenerationPhase
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
from machine_dialect.lexer import Token, TokenType
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.hir_to_mir import HIRToMIRLowering
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, Pop
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_to_bytecode import generate_bytecode
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp


def count_opcode(bytecode: bytearray, opcode: Opcode) -> int:
    """Count occurrences of an opcode in bytecode, skipping operands.

    TODO: This is a temporary workaround. The proper fix is to implement
    a method on the bytecode or Opcode class that correctly counts opcodes
    while understanding the bytecode structure (skipping operands).
    See: bytecode.count(Opcode.POP) incorrectly counts operand bytes.

    Args:
        bytecode: The bytecode to search.
        opcode: The opcode to count.

    Returns:
        Number of times the opcode appears as an instruction (not as an operand).
    """
    count = 0
    i = 0
    while i < len(bytecode):
        if bytecode[i] == opcode:
            count += 1

        # Skip operands based on current opcode
        current_op = Opcode(bytecode[i])
        if current_op in [
            Opcode.LOAD_CONST,
            Opcode.LOAD_LOCAL,
            Opcode.STORE_LOCAL,
            Opcode.LOAD_GLOBAL,
            Opcode.STORE_GLOBAL,
            Opcode.JUMP,
            Opcode.JUMP_IF_FALSE,
            Opcode.LOAD_FUNCTION,
        ]:
            i += 3  # These have 2-byte operands
        elif current_op == Opcode.CALL:
            i += 2  # This has a 1-byte operand
        else:
            i += 1  # No operand

    return count


class TestPopInstruction(unittest.TestCase):
    """Test the Pop MIR instruction."""

    def test_pop_creation(self) -> None:
        """Test creating a Pop instruction."""
        t0 = Temp(MIRType.INT, temp_id=0)
        pop_inst = Pop(t0)

        self.assertEqual(str(pop_inst), "pop t0")
        self.assertEqual(pop_inst.value, t0)

    def test_pop_uses_and_defs(self) -> None:
        """Test uses and defs for Pop instruction."""
        t0 = Temp(MIRType.INT, temp_id=0)
        pop_inst = Pop(t0)

        # Pop uses the value but doesn't define anything
        self.assertEqual(pop_inst.get_uses(), [t0])
        self.assertEqual(pop_inst.get_defs(), [])

    def test_pop_replace_use(self) -> None:
        """Test replacing uses in Pop instruction."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)

        pop_inst = Pop(t0)
        pop_inst.replace_use(t0, t1)

        self.assertEqual(pop_inst.value, t1)
        self.assertEqual(str(pop_inst), "pop t1")


class TestExpressionStatementMIR(unittest.TestCase):
    """Test MIR generation for expression statements."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.converter = HIRToMIRLowering()
        # Initialize with a function and block
        self.converter.current_function = MIRFunction("test", [], MIRType.EMPTY)
        self.converter.current_block = BasicBlock("entry")
        self.converter.current_function.cfg.add_block(self.converter.current_block)

    def test_expression_statement_generates_pop(self) -> None:
        """Test that expression statements generate Pop instructions."""
        # Create an expression statement: 2 + 3
        left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 0), 2)
        right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 4), 3)
        expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 1, 2), "+", left)
        expr.right = right
        expr_stmt = ExpressionStatement(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 0), expr)

        # Convert to MIR
        self.converter.lower_expression_statement(expr_stmt)

        # Check that the last instruction is a Pop
        current_block = self.converter.current_block
        assert current_block is not None
        instructions = list(current_block.instructions)
        self.assertTrue(len(instructions) > 0)
        self.assertIsInstance(instructions[-1], Pop)

    def test_multiple_expression_statements(self) -> None:
        """Test multiple expression statements each generate Pop."""
        # Create two expression statements
        expr1 = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 0), 42)
        stmt1 = ExpressionStatement(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 0), expr1)

        expr2 = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "100", 2, 0), 100)
        stmt2 = ExpressionStatement(Token(TokenType.LIT_WHOLE_NUMBER, "100", 2, 0), expr2)

        # Convert both
        self.converter.lower_expression_statement(stmt1)
        self.converter.lower_expression_statement(stmt2)

        # Count Pop instructions
        current_block = self.converter.current_block
        assert current_block is not None
        instructions = list(current_block.instructions)
        pop_count = sum(1 for inst in instructions if isinstance(inst, Pop))
        self.assertEqual(pop_count, 2)


class TestPopBytecodeGeneration(unittest.TestCase):
    """Test bytecode generation for Pop instruction."""

    def test_pop_generates_bytecode(self) -> None:
        """Test that Pop instruction generates POP opcode."""
        # Create a simple MIR module with a Pop instruction
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Add a constant and pop it
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, "+", Constant(2, MIRType.INT), Constant(3, MIRType.INT)))
        entry.add_instruction(Pop(t0))

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        # Generate bytecode
        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        # Check that POP opcode is present
        self.assertIn(Opcode.POP, bytecode)

    @pytest.mark.skip(reason="Bytecode generation not yet implemented for Rust VM")
    def test_expression_statement_full_pipeline(self) -> None:
        """Test full pipeline from AST expression statement to bytecode with POP."""
        # Create an expression statement in AST
        left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 0), 5)
        right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "7", 1, 4), 7)
        expr = InfixExpression(Token(TokenType.OP_STAR, "*", 1, 2), "*", left)
        expr.right = right
        expr_stmt = ExpressionStatement(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 0), expr)

        program = Program([expr_stmt])

        # Run through the compilation pipeline with NO optimization to ensure MUL is generated
        config = CompilerConfig(optimization_level=OptimizationLevel.NONE)
        context = CompilationContext(source_path=Path("test.md"), config=config)
        context.ast = program

        # Generate HIR -> MIR -> Bytecode
        hir_phase = HIRGenerationPhase()
        mir_phase = MIRGenerationPhase()
        codegen_phase = CodeGenerationPhase()

        hir = hir_phase.run(context, program)
        mir_module = mir_phase.run(context, hir)
        self.assertIsNotNone(mir_module)
        assert mir_module is not None
        context.mir_module = mir_module
        bytecode_module = codegen_phase.run(context, mir_module)

        self.assertIsNotNone(bytecode_module)
        assert bytecode_module is not None

        # Verify bytecode contains multiplication and POP
        bytecode = bytecode_module.main_chunk.bytecode
        self.assertIn(Opcode.MUL, bytecode)
        self.assertIn(Opcode.POP, bytecode)

        # The sequence should be: load 5, load 7, multiply, pop
        pop_index = bytecode.index(Opcode.POP)
        self.assertGreater(pop_index, 0)  # POP should not be first

    @pytest.mark.skip(reason="Bytecode generation not yet implemented for Rust VM")
    def test_mixed_statements_with_expression(self) -> None:
        """Test that only expression statements generate Pop, not assignments."""
        # Create a program with both assignment and expression statement
        # Set x to 10
        set_stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 1, 0),
            Identifier(Token(TokenType.MISC_IDENT, "x", 1, 4), "x"),
            WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "10", 1, 9), 10),
        )

        # Expression statement: 5 + 3 (result discarded)
        left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 2, 0), 5)
        right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 2, 4), 3)
        expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 2, 2), "+", left)
        expr.right = right
        expr_stmt = ExpressionStatement(Token(TokenType.LIT_WHOLE_NUMBER, "5", 2, 0), expr)

        program = Program([set_stmt, expr_stmt])

        # Run through the pipeline with NO optimization to test actual ADD instruction
        config = CompilerConfig(optimization_level=OptimizationLevel.NONE)
        context = CompilationContext(source_path=Path("test.md"), config=config)
        context.ast = program

        hir_phase = HIRGenerationPhase()
        mir_phase = MIRGenerationPhase()
        codegen_phase = CodeGenerationPhase()

        hir = hir_phase.run(context, program)
        mir_module = mir_phase.run(context, hir)
        self.assertIsNotNone(mir_module)
        assert mir_module is not None
        context.mir_module = mir_module
        bytecode_module = codegen_phase.run(context, mir_module)

        self.assertIsNotNone(bytecode_module)
        assert bytecode_module is not None

        # Verify bytecode
        bytecode = bytecode_module.main_chunk.bytecode

        # Should have exactly one POP (for the expression statement)
        pop_count = count_opcode(bytecode, Opcode.POP)
        self.assertEqual(pop_count, 1, "Should have exactly one POP for the expression statement")

        # Should have STORE_GLOBAL for the assignment
        self.assertIn(Opcode.STORE_GLOBAL, bytecode)

        # Should have ADD for the expression
        self.assertIn(Opcode.ADD, bytecode)


class TestComplexExpressionStatements(unittest.TestCase):
    """Test complex cases with expression statements."""

    def test_nested_expression_statement(self) -> None:
        """Test nested expressions in expression statements generate correct Pop."""
        # Create: (2 + 3) * 4 as an expression statement
        add_left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 0), 2)
        add_right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 4), 3)
        add_expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 1, 2), "+", add_left)
        add_expr.right = add_right

        mul_right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "4", 1, 8), 4)
        mul_expr = InfixExpression(Token(TokenType.OP_STAR, "*", 1, 6), "*", add_expr)
        mul_expr.right = mul_right

        expr_stmt = ExpressionStatement(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 0), mul_expr)
        program = Program([expr_stmt])

        # Compile
        config = CompilerConfig()
        context = CompilationContext(source_path=Path("test.md"), config=config)
        context.ast = program

        hir_phase = HIRGenerationPhase()
        mir_phase = MIRGenerationPhase()

        hir = hir_phase.run(context, program)
        mir_module = mir_phase.run(context, hir)

        self.assertIsNotNone(mir_module)
        assert mir_module is not None

        # Check MIR has Pop instruction
        main_func = mir_module.get_function("main")
        self.assertIsNotNone(main_func)
        assert main_func is not None

        # Collect all instructions from all blocks
        all_instructions: list[object] = []
        for block in main_func.cfg.blocks.values():
            all_instructions.extend(block.instructions)

        # Should have at least one Pop instruction
        pop_instructions = [inst for inst in all_instructions if isinstance(inst, Pop)]
        self.assertGreaterEqual(len(pop_instructions), 1)

    @pytest.mark.skip(reason="Bytecode generation not yet implemented for Rust VM")
    def test_identifier_expression_statement(self) -> None:
        """Test that identifier as expression statement generates Pop."""
        # First set a variable, then use it in an expression statement
        set_stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 1, 0),
            Identifier(Token(TokenType.MISC_IDENT, "x", 1, 4), "x"),
            WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 9), 42),
        )

        # Use x as an expression statement (just evaluate and discard)
        x_ref = Identifier(Token(TokenType.MISC_IDENT, "x", 2, 0), "x")
        expr_stmt = ExpressionStatement(Token(TokenType.MISC_IDENT, "x", 2, 0), x_ref)

        program = Program([set_stmt, expr_stmt])

        # Compile to bytecode
        config = CompilerConfig()
        context = CompilationContext(source_path=Path("test.md"), config=config)
        context.ast = program

        hir_phase = HIRGenerationPhase()
        mir_phase = MIRGenerationPhase()
        codegen_phase = CodeGenerationPhase()

        hir = hir_phase.run(context, program)
        mir_module = mir_phase.run(context, hir)
        self.assertIsNotNone(mir_module)
        assert mir_module is not None
        context.mir_module = mir_module
        bytecode_module = codegen_phase.run(context, mir_module)

        self.assertIsNotNone(bytecode_module)
        assert bytecode_module is not None

        # Should have LOAD_GLOBAL followed by POP for the identifier expression
        bytecode = bytecode_module.main_chunk.bytecode

        # Find LOAD_GLOBAL instructions
        load_indices = [i for i, b in enumerate(bytecode) if b == Opcode.LOAD_GLOBAL]

        # At least one should be followed by POP (for the expression statement)
        found_load_pop = False
        for load_idx in load_indices:
            # Check if there's a POP after this LOAD_GLOBAL (might have operand bytes in between)
            for j in range(load_idx + 1, min(load_idx + 10, len(bytecode))):
                if bytecode[j] == Opcode.POP:
                    found_load_pop = True
                    break

        self.assertTrue(found_load_pop, "Should have LOAD_GLOBAL followed by POP for identifier expression statement")


if __name__ == "__main__":
    unittest.main()
