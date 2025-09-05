"""Tests for bitwise operations in MIR and bytecode generation."""

import unittest
from pathlib import Path

from machine_dialect.ast import (
    Identifier,
    InfixExpression,
    Program,
    SetStatement,
    WholeNumberLiteral,
)
from machine_dialect.codegen.isa import Opcode
from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.phases.codegen import CodeGenerationPhase
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
from machine_dialect.lexer import Token, TokenType
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, Return, StoreVar, UnaryOp
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_to_bytecode import generate_bytecode
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp, Variable
from machine_dialect.vm.vm import VM


class TestBitwiseMIRInstructions(unittest.TestCase):
    """Test bitwise operations in MIR instructions."""

    def test_bitwise_and_instruction(self) -> None:
        """Test bitwise AND instruction creation."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        and_op = BinaryOp(t0, "&", t1, t2)
        self.assertEqual(str(and_op), "t0 = t1 & t2")
        self.assertEqual(and_op.op, "&")

    def test_bitwise_or_instruction(self) -> None:
        """Test bitwise OR instruction creation."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        or_op = BinaryOp(t0, "|", t1, t2)
        self.assertEqual(str(or_op), "t0 = t1 | t2")
        self.assertEqual(or_op.op, "|")

    def test_bitwise_xor_instruction(self) -> None:
        """Test bitwise XOR instruction creation."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        xor_op = BinaryOp(t0, "^", t1, t2)
        self.assertEqual(str(xor_op), "t0 = t1 ^ t2")
        self.assertEqual(xor_op.op, "^")

    def test_bitwise_not_instruction(self) -> None:
        """Test bitwise NOT instruction creation."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)

        not_op = UnaryOp(t0, "~", t1)
        self.assertEqual(str(not_op), "t0 = ~ t1")
        self.assertEqual(not_op.op, "~")

    def test_shift_left_instruction(self) -> None:
        """Test shift left instruction creation."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        shl_op = BinaryOp(t0, "<<", t1, t2)
        self.assertEqual(str(shl_op), "t0 = t1 << t2")
        self.assertEqual(shl_op.op, "<<")

    def test_shift_right_instruction(self) -> None:
        """Test shift right instruction creation."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        shr_op = BinaryOp(t0, ">>", t1, t2)
        self.assertEqual(str(shr_op), "t0 = t1 >> t2")
        self.assertEqual(shr_op.op, ">>")


class TestBitwiseBytecodeGeneration(unittest.TestCase):
    """Test bytecode generation for bitwise operations."""

    def test_bitwise_and_generates_bytecode(self) -> None:
        """Test that bitwise AND generates BIT_AND opcode."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # 5 & 3
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, "&", Constant(5, MIRType.INT), Constant(3, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t0))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        self.assertIn(Opcode.BIT_AND, bytecode)

    def test_bitwise_or_generates_bytecode(self) -> None:
        """Test that bitwise OR generates BIT_OR opcode."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # 5 | 3
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, "|", Constant(5, MIRType.INT), Constant(3, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t0))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        self.assertIn(Opcode.BIT_OR, bytecode)

    def test_bitwise_xor_generates_bytecode(self) -> None:
        """Test that bitwise XOR generates XOR opcode."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # 5 ^ 3
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, "^", Constant(5, MIRType.INT), Constant(3, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t0))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        self.assertIn(Opcode.XOR, bytecode)

    def test_bitwise_not_generates_bytecode(self) -> None:
        """Test that bitwise NOT generates BIT_NOT opcode."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # ~5
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(UnaryOp(t0, "~", Constant(5, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t0))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        self.assertIn(Opcode.BIT_NOT, bytecode)

    def test_shift_left_generates_bytecode(self) -> None:
        """Test that shift left generates SHL opcode."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # 5 << 2
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, "<<", Constant(5, MIRType.INT), Constant(2, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t0))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        self.assertIn(Opcode.SHL, bytecode)

    def test_shift_right_generates_bytecode(self) -> None:
        """Test that shift right generates SHR opcode."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # 20 >> 2
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, ">>", Constant(20, MIRType.INT), Constant(2, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t0))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        self.assertIn(Opcode.SHR, bytecode)


class TestBitwiseVMExecution(unittest.TestCase):
    """Test VM execution of bitwise operations."""

    def compile_and_run(self, program: Program) -> dict[str, object]:
        """Helper to compile and run a program, returning globals."""
        config = CompilerConfig()
        context = CompilationContext(source_path=Path("test.md"), config=config)
        context.ast = program

        hir_phase = HIRGenerationPhase()
        mir_phase = MIRGenerationPhase()
        codegen_phase = CodeGenerationPhase()

        hir = hir_phase.run(context, program)
        mir_module = mir_phase.run(context, hir)
        if mir_module is None:
            raise RuntimeError("Failed to generate MIR module")
        context.mir_module = mir_module
        module = codegen_phase.run(context, mir_module)
        if module is None:
            raise RuntimeError("Failed to generate bytecode module")

        vm = VM()
        vm.run(module)
        return vm.globals

    @unittest.skip("Bitwise operators not yet implemented in frontend (lexer/parser/AST)")
    def test_bitwise_and_execution(self) -> None:
        """Test bitwise AND execution in VM."""
        # Create: Set result to 12 & 7
        # 12 = 1100 in binary
        # 7  = 0111 in binary
        # Result should be 0100 = 4
        left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "12", 1, 0), 12)
        right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "7", 1, 4), 7)

        # Note: We need to check if "&" is recognized as an operator token
        # For now, let's create the expression using the caret operator which is mapped to XOR
        # We'll need to verify what token type is used for bitwise AND
        expr = InfixExpression(Token(TokenType.OP_CARET, "&", 1, 2), "&", left)
        expr.right = right

        stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 1, 0),
            Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"),
            expr,
        )
        program = Program([stmt])

        # Since we don't have VM implementation for bitwise ops yet,
        # we'll just test that the bytecode is generated correctly
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
        module = codegen_phase.run(context, mir_module)
        self.assertIsNotNone(module)
        assert module is not None

        # Check that bytecode contains BIT_AND
        bytecode = module.main_chunk.bytecode
        self.assertIn(Opcode.BIT_AND, bytecode)

    @unittest.skip("Bitwise operators not yet implemented in frontend (lexer/parser/AST)")
    def test_bitwise_xor_with_caret(self) -> None:
        """Test that ^ operator generates XOR in bytecode."""
        # Create: Set result to 12 ^ 7
        # 12 = 1100 in binary
        # 7  = 0111 in binary
        # Result should be 1011 = 11
        left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "12", 1, 0), 12)
        right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "7", 1, 4), 7)

        # The caret operator should be recognized
        expr = InfixExpression(Token(TokenType.OP_CARET, "^", 1, 2), "^", left)
        expr.right = right

        stmt = SetStatement(
            Token(TokenType.KW_SET, "Set", 1, 0),
            Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"),
            expr,
        )
        program = Program([stmt])

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
        module = codegen_phase.run(context, mir_module)
        self.assertIsNotNone(module)
        assert module is not None

        # Check that bytecode contains XOR
        bytecode = module.main_chunk.bytecode
        self.assertIn(Opcode.XOR, bytecode)


class TestComplexBitwiseOperations(unittest.TestCase):
    """Test complex bitwise operation scenarios."""

    def test_nested_bitwise_operations(self) -> None:
        """Test nested bitwise operations in MIR."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # (5 & 3) | (8 ^ 2)
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, "&", Constant(5, MIRType.INT), Constant(3, MIRType.INT)))

        t1 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t1, "^", Constant(8, MIRType.INT), Constant(2, MIRType.INT)))

        t2 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t2, "|", t0, t1))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t2))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        # Should contain all three bitwise operations
        self.assertIn(Opcode.BIT_AND, bytecode)
        self.assertIn(Opcode.XOR, bytecode)
        self.assertIn(Opcode.BIT_OR, bytecode)

    def test_bitwise_with_shifts(self) -> None:
        """Test combination of bitwise operations with shifts."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # (5 << 2) & 255
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, "<<", Constant(5, MIRType.INT), Constant(2, MIRType.INT)))

        t1 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t1, "&", t0, Constant(255, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t1))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        # Should contain shift and bitwise AND
        self.assertIn(Opcode.SHL, bytecode)
        self.assertIn(Opcode.BIT_AND, bytecode)

    def test_bitwise_not_with_and(self) -> None:
        """Test bitwise NOT combined with AND."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # ~5 & 255 (mask to 8 bits)
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(UnaryOp(t0, "~", Constant(5, MIRType.INT)))

        t1 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t1, "&", t0, Constant(255, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t1))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        # Should contain NOT and AND
        self.assertIn(Opcode.BIT_NOT, bytecode)
        self.assertIn(Opcode.BIT_AND, bytecode)


class TestBitwiseOperatorPrecedence(unittest.TestCase):
    """Test operator precedence with bitwise operations."""

    def test_bitwise_with_arithmetic(self) -> None:
        """Test that arithmetic has higher precedence than bitwise."""
        mir_module = MIRModule("test")
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # 5 + 3 & 7 should be (5 + 3) & 7 = 8 & 7 = 0
        # First do addition
        t0 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t0, "+", Constant(5, MIRType.INT), Constant(3, MIRType.INT)))

        # Then bitwise AND
        t1 = main.new_temp(MIRType.INT)
        entry.add_instruction(BinaryOp(t1, "&", t0, Constant(7, MIRType.INT)))

        # Store result
        result = Variable("result", MIRType.INT)
        entry.add_instruction(StoreVar(result, t1))
        entry.add_instruction(Return())

        mir_module.add_function(main)
        mir_module.set_main_function("main")

        bytecode_module = generate_bytecode(mir_module)
        bytecode = bytecode_module.main_chunk.bytecode

        # Check order: ADD should come before BIT_AND
        add_idx = bytecode.index(Opcode.ADD)
        and_idx = bytecode.index(Opcode.BIT_AND)
        self.assertLess(add_idx, and_idx, "ADD should come before BIT_AND")


if __name__ == "__main__":
    unittest.main()
