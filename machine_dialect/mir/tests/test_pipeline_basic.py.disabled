"""Basic integration tests for the MIR compilation pipeline.

Tests basic functionality without requiring full AST construction.
"""

from __future__ import annotations

import unittest

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Jump,
    LoadConst,
    Return,
    StoreVar,
)
from machine_dialect.mir.mir_interpreter import MIRInterpreter
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_to_bytecode import generate_bytecode
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Variable
from machine_dialect.mir.optimizations import PeepholeOptimizer


class TestBasicPipeline(unittest.TestCase):
    """Test basic MIR pipeline functionality."""

    def test_simple_mir_execution(self) -> None:
        """Test simple MIR module execution."""
        # Create MIR module directly
        module = MIRModule("test")

        # Create main function
        main = MIRFunction("main", [], MIRType.INT)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Add instructions
        t1 = main.new_temp(MIRType.INT)
        entry.add_instruction(LoadConst(t1, 42))
        entry.add_instruction(Return(t1))

        module.add_function(main)

        # Test MIR interpreter
        interpreter = MIRInterpreter()
        result = interpreter.interpret_module(module)
        self.assertEqual(result, 42)

        # Test bytecode generation
        bytecode_module = generate_bytecode(module)
        self.assertIsNotNone(bytecode_module)
        self.assertGreater(len(bytecode_module.main_chunk.bytecode), 0)

    def test_arithmetic_mir(self) -> None:
        """Test arithmetic operations in MIR."""
        module = MIRModule("test")

        main = MIRFunction("main", [], MIRType.INT)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # 10 + 20
        t1 = main.new_temp(MIRType.INT)
        t2 = main.new_temp(MIRType.INT)
        t3 = main.new_temp(MIRType.INT)

        entry.add_instruction(LoadConst(t1, 10))
        entry.add_instruction(LoadConst(t2, 20))
        entry.add_instruction(BinaryOp(t3, "+", t1, t2))
        entry.add_instruction(Return(t3))

        module.add_function(main)

        # Execute
        interpreter = MIRInterpreter()
        result = interpreter.interpret_module(module)
        self.assertEqual(result, 30)

    def test_variable_operations(self) -> None:
        """Test variable operations in MIR."""
        module = MIRModule("test")

        main = MIRFunction("main", [], MIRType.INT)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Create variables
        x = Variable("x", MIRType.INT)
        main.add_local(x)

        t1 = main.new_temp(MIRType.INT)

        # x = 15
        entry.add_instruction(LoadConst(t1, 15))
        entry.add_instruction(StoreVar(x, t1))

        # return x
        entry.add_instruction(Return(x))

        module.add_function(main)

        # Execute
        interpreter = MIRInterpreter()
        result = interpreter.interpret_module(module)
        self.assertEqual(result, 15)

    def test_optimization(self) -> None:
        """Test bytecode optimization."""
        module = MIRModule("test")

        main = MIRFunction("main", [], MIRType.INT)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # Constant folding opportunity: 5 + 10
        t1 = main.new_temp(MIRType.INT)
        t2 = main.new_temp(MIRType.INT)
        t3 = main.new_temp(MIRType.INT)

        entry.add_instruction(LoadConst(t1, 5))
        entry.add_instruction(LoadConst(t2, 10))
        entry.add_instruction(BinaryOp(t3, "+", t1, t2))
        entry.add_instruction(Return(t3))

        module.add_function(main)

        # Generate bytecode
        bytecode_module = generate_bytecode(module)
        original_size = len(bytecode_module.main_chunk.bytecode)

        # Optimize
        optimizer = PeepholeOptimizer()
        optimized_chunk = optimizer.optimize_chunk(bytecode_module.main_chunk)
        optimized_size = len(optimized_chunk.bytecode)

        # Should be smaller after optimization
        self.assertLessEqual(optimized_size, original_size)

    def test_benchmarking_mir(self) -> None:
        """Test that benchmarking works with MIR modules."""
        # Create a simple MIR module directly
        module = MIRModule("benchmark_test")
        main = MIRFunction("main", [], MIRType.INT)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        t1 = main.new_temp(MIRType.INT)
        entry.add_instruction(LoadConst(t1, 100))
        entry.add_instruction(Return(t1))
        module.add_function(main)

        # Benchmark bytecode generation directly
        import time

        start = time.perf_counter()
        bytecode_module = generate_bytecode(module)
        end = time.perf_counter()

        # Check results
        self.assertIsNotNone(bytecode_module)
        self.assertGreater(end - start, 0)
        self.assertGreater(len(bytecode_module.main_chunk.bytecode), 0)

    def test_control_flow_mir(self) -> None:
        """Test control flow in MIR."""
        module = MIRModule("test")

        main = MIRFunction("main", [], MIRType.INT)

        # Create blocks
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        end_block = BasicBlock("end")

        main.cfg.add_block(entry)
        main.cfg.add_block(then_block)
        main.cfg.add_block(else_block)
        main.cfg.add_block(end_block)
        main.cfg.set_entry_block(entry)

        # Entry: always jump to then
        t1 = main.new_temp(MIRType.BOOL)
        entry.add_instruction(LoadConst(t1, True))
        entry.add_instruction(Jump("then"))

        # Then block
        t2 = main.new_temp(MIRType.INT)
        then_block.add_instruction(LoadConst(t2, 1))
        then_block.add_instruction(Return(t2))

        # Else block (unreachable)
        t3 = main.new_temp(MIRType.INT)
        else_block.add_instruction(LoadConst(t3, 0))
        else_block.add_instruction(Return(t3))

        module.add_function(main)

        # Execute
        interpreter = MIRInterpreter()
        result = interpreter.interpret_module(module)
        self.assertEqual(result, 1)

    def test_comparison_operations(self) -> None:
        """Test comparison operations in MIR."""
        module = MIRModule("test")

        main = MIRFunction("main", [], MIRType.BOOL)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)

        # 10 > 5
        t1 = main.new_temp(MIRType.INT)
        t2 = main.new_temp(MIRType.INT)
        t3 = main.new_temp(MIRType.BOOL)

        entry.add_instruction(LoadConst(t1, 10))
        entry.add_instruction(LoadConst(t2, 5))
        entry.add_instruction(BinaryOp(t3, ">", t1, t2))
        entry.add_instruction(Return(t3))

        module.add_function(main)

        # Execute
        interpreter = MIRInterpreter()
        result = interpreter.interpret_module(module)
        self.assertEqual(result, True)


if __name__ == "__main__":
    unittest.main()
