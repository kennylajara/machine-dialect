"""Simplified tests for HIR to MIR lowering without token dependencies."""

import unittest

from machine_dialect.mir.hir_to_mir import HIRToMIRLowering
from machine_dialect.mir.mir_types import MIRType


class TestHIRToMIRSimple(unittest.TestCase):
    """Simplified tests for HIR to MIR lowering."""

    def test_lowering_initialization(self) -> None:
        """Test that the lowering class can be initialized."""
        lowerer = HIRToMIRLowering()
        self.assertIsNone(lowerer.module)
        self.assertIsNone(lowerer.current_function)
        self.assertIsNone(lowerer.current_block)
        self.assertEqual(lowerer.variable_map, {})
        self.assertEqual(lowerer.label_counter, 0)

    def test_generate_label(self) -> None:
        """Test label generation."""
        lowerer = HIRToMIRLowering()

        label1 = lowerer.generate_label("test")
        self.assertEqual(label1, "test_0")

        label2 = lowerer.generate_label("test")
        self.assertEqual(label2, "test_1")

        label3 = lowerer.generate_label("loop")
        self.assertEqual(label3, "loop_2")

    def test_mir_module_creation(self) -> None:
        """Test that a MIR module can be created."""
        from machine_dialect.mir.mir_module import MIRModule

        module = MIRModule("test_module")
        self.assertEqual(module.name, "test_module")
        self.assertEqual(len(module.functions), 0)
        self.assertIsNone(module.main_function)

    def test_mir_function_creation(self) -> None:
        """Test that a MIR function can be created."""
        from machine_dialect.mir.mir_function import MIRFunction
        from machine_dialect.mir.mir_values import Variable

        params = [Variable("x", MIRType.INT), Variable("y", MIRType.INT)]
        func = MIRFunction("add", params, MIRType.INT)

        self.assertEqual(func.name, "add")
        self.assertEqual(len(func.params), 2)
        self.assertEqual(func.return_type, MIRType.INT)
        self.assertIsNotNone(func.cfg)

    def test_basic_lowering_flow(self) -> None:
        """Test the basic flow of lowering without actual AST nodes."""
        from machine_dialect.mir.basic_block import BasicBlock
        from machine_dialect.mir.mir_function import MIRFunction
        from machine_dialect.mir.mir_instructions import LoadConst, Return
        from machine_dialect.mir.mir_module import MIRModule

        # Create a simple module with one function manually
        module = MIRModule("test")

        # Create a simple function
        func = MIRFunction("main", [], MIRType.INT)

        # Create entry block
        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Add some instructions
        t0 = func.new_temp(MIRType.INT)
        entry.add_instruction(LoadConst(t0, 42))
        entry.add_instruction(Return(t0))

        # Add function to module
        module.add_function(func)
        module.set_main_function("main")

        # Verify structure
        self.assertEqual(module.name, "test")
        self.assertEqual(len(module.functions), 1)
        self.assertEqual(module.main_function, "main")

        main_func = module.get_function("main")
        assert main_func is not None
        assert main_func.cfg.entry_block is not None

        self.assertEqual(len(main_func.cfg.entry_block.instructions), 2)
        self.assertIsInstance(main_func.cfg.entry_block.instructions[0], LoadConst)
        self.assertIsInstance(main_func.cfg.entry_block.instructions[1], Return)

    def test_control_flow_structure(self) -> None:
        """Test creating control flow structures in MIR."""
        from machine_dialect.mir.basic_block import BasicBlock
        from machine_dialect.mir.mir_function import MIRFunction
        from machine_dialect.mir.mir_instructions import ConditionalJump, LoadConst
        from machine_dialect.mir.mir_types import MIRType

        func = MIRFunction("test_cf", [], MIRType.INT)

        # Create blocks
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge_block = BasicBlock("merge")

        # Add blocks to CFG
        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge_block)
        func.cfg.set_entry_block(entry)

        # Create condition
        cond = func.new_temp(MIRType.BOOL)
        entry.add_instruction(LoadConst(cond, True))
        entry.add_instruction(ConditionalJump(cond, "then", "else"))

        # Connect blocks
        func.cfg.connect(entry, then_block)
        func.cfg.connect(entry, else_block)
        func.cfg.connect(then_block, merge_block)
        func.cfg.connect(else_block, merge_block)

        # Verify structure
        self.assertEqual(len(func.cfg.blocks), 4)
        self.assertEqual(len(entry.successors), 2)
        self.assertEqual(len(merge_block.predecessors), 2)


if __name__ == "__main__":
    unittest.main()
