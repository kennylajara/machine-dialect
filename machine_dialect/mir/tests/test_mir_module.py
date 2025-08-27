"""Tests for MIR module and function containers."""

import unittest

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Jump,
    LoadConst,
    LoadVar,
    Return,
)
from machine_dialect.mir.mir_module import ConstantPool, MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp, Variable


class TestConstantPool(unittest.TestCase):
    """Test constant pool functionality."""

    def test_constant_pool_creation(self) -> None:
        """Test creating constant pool."""
        pool = ConstantPool()
        self.assertEqual(pool.constants, [])
        self.assertEqual(pool.size(), 0)

    def test_add_constants(self) -> None:
        """Test adding constants to pool."""
        pool = ConstantPool()

        c1 = Constant(42, MIRType.INT)
        c2 = Constant(3.14, MIRType.FLOAT)
        c3 = Constant("hello", MIRType.STRING)

        idx1 = pool.add(c1)
        idx2 = pool.add(c2)
        idx3 = pool.add(c3)

        self.assertEqual(idx1, 0)
        self.assertEqual(idx2, 1)
        self.assertEqual(idx3, 2)
        self.assertEqual(pool.size(), 3)

    def test_deduplication(self) -> None:
        """Test that identical constants are deduplicated."""
        pool = ConstantPool()

        c1 = Constant(42, MIRType.INT)
        c2 = Constant(42, MIRType.INT)  # Same value and type
        c3 = Constant(42, MIRType.FLOAT)  # Same value, different type

        idx1 = pool.add(c1)
        idx2 = pool.add(c2)
        idx3 = pool.add(c3)

        # c1 and c2 should map to same index
        self.assertEqual(idx1, idx2)
        # c3 should have different index
        self.assertNotEqual(idx1, idx3)
        self.assertEqual(pool.size(), 2)

    def test_get_constant(self) -> None:
        """Test retrieving constants from pool."""
        pool = ConstantPool()

        c1 = Constant(100)
        c2 = Constant("test")

        pool.add(c1)
        pool.add(c2)

        retrieved1 = pool.get(0)
        retrieved2 = pool.get(1)
        retrieved3 = pool.get(99)  # Out of bounds

        self.assertEqual(retrieved1, c1)
        self.assertEqual(retrieved2, c2)
        self.assertIsNone(retrieved3)

    def test_constant_pool_string_representation(self) -> None:
        """Test string representation of constant pool."""
        pool = ConstantPool()
        pool.add(Constant(42))
        pool.add(Constant("hello"))
        pool.add(Constant(True))

        result = str(pool)
        self.assertIn("Constants:", result)
        self.assertIn("[0] 42", result)
        self.assertIn('[1] "hello"', result)
        self.assertIn("[2] True", result)


class TestMIRFunction(unittest.TestCase):
    """Test MIR function functionality."""

    def test_function_creation(self) -> None:
        """Test creating MIR function."""
        func = MIRFunction("main", return_type=MIRType.INT)
        self.assertEqual(func.name, "main")
        self.assertEqual(func.return_type, MIRType.INT)
        self.assertEqual(func.params, [])
        self.assertIsNotNone(func.cfg)

    def test_function_with_parameters(self) -> None:
        """Test function with parameters."""
        params = [
            Variable("x", MIRType.INT),
            Variable("y", MIRType.FLOAT),
        ]
        func = MIRFunction("add", params, MIRType.FLOAT)

        self.assertEqual(func.params, params)
        self.assertEqual(len(func.params), 2)
        self.assertEqual(func.params[0].name, "x")
        self.assertEqual(func.params[1].type, MIRType.FLOAT)

    def test_add_local_variable(self) -> None:
        """Test adding local variables."""
        func = MIRFunction("compute")
        v1 = Variable("temp", MIRType.INT)
        v2 = Variable("result", MIRType.FLOAT)

        func.add_local(v1)
        func.add_local(v2)

        self.assertEqual(len(func.locals), 2)
        self.assertIn("temp", func.locals)
        self.assertIn("result", func.locals)
        self.assertEqual(func.locals["temp"], v1)

    def test_get_local_variable(self) -> None:
        """Test getting local variables."""
        func = MIRFunction("test")
        v = Variable("counter", MIRType.INT)
        func.add_local(v)

        retrieved = func.get_local("counter")
        self.assertEqual(retrieved, v)

        none_var = func.get_local("nonexistent")
        self.assertIsNone(none_var)

    def test_function_string_representation(self) -> None:
        """Test string representation of function."""
        func = MIRFunction(
            "factorial",
            [Variable("n", MIRType.INT)],
            MIRType.INT,
        )

        # Add some blocks
        entry = BasicBlock("entry")
        t0 = Temp(MIRType.INT, temp_id=0)
        entry.add_instruction(LoadConst(t0, 1))
        entry.add_instruction(Return(t0))

        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        result = str(func)
        self.assertIn("function factorial(n: int) -> int", result)
        self.assertIn("entry:", result)
        self.assertIn("t0 = 1", result)
        self.assertIn("return t0", result)

    def test_function_without_return_type(self) -> None:
        """Test function without return type (void)."""
        func = MIRFunction("print_message", [Variable("msg", MIRType.STRING)])
        result = str(func)
        self.assertIn("function print_message(msg: string)", result)
        self.assertNotIn("->", result)


class TestMIRModule(unittest.TestCase):
    """Test MIR module functionality."""

    def test_module_creation(self) -> None:
        """Test creating MIR module."""
        module = MIRModule("test_module")
        self.assertEqual(module.name, "test_module")
        self.assertEqual(module.functions, {})
        self.assertEqual(module.globals, {})
        self.assertIsNotNone(module.constants)
        self.assertIsNone(module.main_function)

    def test_add_function(self) -> None:
        """Test adding functions to module."""
        module = MIRModule("app")
        func1 = MIRFunction("main", return_type=MIRType.INT)
        func2 = MIRFunction("helper")

        module.add_function(func1)
        module.add_function(func2)

        self.assertEqual(len(module.functions), 2)
        self.assertIn("main", module.functions)
        self.assertIn("helper", module.functions)

    def test_get_function(self) -> None:
        """Test getting functions from module."""
        module = MIRModule("app")
        func = MIRFunction("compute", return_type=MIRType.FLOAT)
        module.add_function(func)

        retrieved = module.get_function("compute")
        self.assertEqual(retrieved, func)

        none_func = module.get_function("nonexistent")
        self.assertIsNone(none_func)

    def test_add_global_variable(self) -> None:
        """Test adding global variables."""
        module = MIRModule("app")
        v1 = Variable("global_count", MIRType.INT)
        v2 = Variable("pi", MIRType.FLOAT)

        module.add_global(v1)
        module.add_global(v2)

        self.assertEqual(len(module.globals), 2)
        self.assertIn("global_count", module.globals)
        self.assertIn("pi", module.globals)

    def test_get_global_variable(self) -> None:
        """Test getting global variables."""
        module = MIRModule("app")
        v = Variable("config", MIRType.STRING)
        module.add_global(v)

        retrieved = module.get_global("config")
        self.assertEqual(retrieved, v)

        none_var = module.get_global("nonexistent")
        self.assertIsNone(none_var)

    def test_main_function_handling(self) -> None:
        """Test main function setting and retrieval."""
        module = MIRModule("app")
        main_func = MIRFunction("main", return_type=MIRType.INT)
        module.add_function(main_func)

        # No main function by default
        self.assertIsNone(module.main_function)
        retrieved = module.get_main_function()
        self.assertIsNone(retrieved)

        # Set main function
        module.set_main_function("main")
        self.assertEqual(module.main_function, "main")
        retrieved = module.get_main_function()
        self.assertEqual(retrieved, main_func)

        # Change main function name
        module.set_main_function("start")
        self.assertEqual(module.main_function, "start")

        # Main function not found
        retrieved = module.get_main_function()
        self.assertIsNone(retrieved)

        # Add new main
        start_func = MIRFunction("start")
        module.add_function(start_func)
        retrieved = module.get_main_function()
        self.assertEqual(retrieved, start_func)

    def test_module_validation_success(self) -> None:
        """Test successful module validation."""
        module = MIRModule("app")

        # Create a valid function with proper CFG
        main = MIRFunction("main", return_type=MIRType.INT)
        entry = BasicBlock("entry")
        t0 = Temp(MIRType.INT, temp_id=0)
        entry.add_instruction(LoadConst(t0, 0))
        entry.add_instruction(Return(t0))

        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)
        module.add_function(main)

        errors = module.validate()
        self.assertEqual(errors, [])

    def test_module_validation_missing_main(self) -> None:
        """Test validation with missing main function."""
        module = MIRModule("app")
        module.main_function = "main"  # Main is expected but not present

        errors = module.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("Main function 'main' not found", errors[0])

    def test_module_validation_missing_entry_block(self) -> None:
        """Test validation with function missing entry block."""
        module = MIRModule("app")
        func = MIRFunction("broken")
        # Don't set entry block
        module.add_function(func)

        errors = module.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("Function 'broken' has no entry block", errors[0])

    def test_module_validation_unterminated_block(self) -> None:
        """Test validation with unterminated block."""
        module = MIRModule("app")
        func = MIRFunction("incomplete")

        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")
        t0 = Temp(MIRType.INT, temp_id=0)

        # Entry has terminator
        entry.add_instruction(Jump("bb1"))

        # bb1 has instructions but no terminator
        bb1.add_instruction(LoadConst(t0, 42))

        func.cfg.add_block(entry)
        func.cfg.add_block(bb1)
        func.cfg.set_entry_block(entry)
        module.add_function(func)

        errors = module.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("Block 'bb1' in function 'incomplete' is not terminated", errors[0])

    def test_module_validation_invalid_jump_target(self) -> None:
        """Test validation with jump to undefined label."""
        module = MIRModule("app")
        func = MIRFunction("bad_jump")

        entry = BasicBlock("entry")
        entry.add_instruction(Jump("nonexistent"))

        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        module.add_function(func)

        errors = module.validate()
        self.assertIn("Jump to undefined label 'nonexistent' in function 'bad_jump'", errors[0])

    def test_module_validation_invalid_conditional_jump(self) -> None:
        """Test validation with conditional jump to undefined labels."""
        module = MIRModule("app")
        func = MIRFunction("bad_cjump")

        entry = BasicBlock("entry")
        t0 = Temp(MIRType.BOOL, temp_id=0)
        entry.add_instruction(ConditionalJump(t0, "undefined1", "undefined2"))

        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        module.add_function(func)

        errors = module.validate()
        # Should have errors for both undefined labels
        self.assertTrue(any("undefined1" in err for err in errors))
        self.assertTrue(any("undefined2" in err for err in errors))

    def test_module_string_representation(self) -> None:
        """Test string representation of module."""
        module = MIRModule("example")

        # Add constants
        module.constants.add(Constant(42))
        module.constants.add(Constant("hello"))

        # Add global
        module.add_global(Variable("count", MIRType.INT))

        # Add function
        func = MIRFunction("main", return_type=MIRType.INT)
        entry = BasicBlock("entry")
        t0 = Temp(MIRType.INT, temp_id=0)
        entry.add_instruction(LoadConst(t0, 0))
        entry.add_instruction(Return(t0))
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        module.add_function(func)

        result = module.to_string()

        self.assertIn("module example {", result)
        self.assertIn("Constants:", result)
        self.assertIn("[0] 42", result)
        self.assertIn("globals:", result)
        self.assertIn("count: int", result)
        self.assertIn("functions:", result)
        self.assertIn("function main()", result)

    def test_module_string_representation_options(self) -> None:
        """Test module string representation with options."""
        module = MIRModule("test")
        module.constants.add(Constant(100))
        module.add_global(Variable("var", MIRType.STRING))

        # Without constants
        result = module.to_string(include_constants=False)
        self.assertNotIn("Constants:", result)

        # Without globals
        result = module.to_string(include_globals=False)
        self.assertNotIn("globals:", result)

        # With both
        result = module.to_string(include_constants=True, include_globals=True)
        self.assertIn("Constants:", result)
        self.assertIn("globals:", result)


class TestIntegration(unittest.TestCase):
    """Test integration of module, functions, and CFG."""

    def test_complete_module_example(self) -> None:
        """Test creating a complete module with multiple functions."""
        module = MIRModule("calculator")

        # Add global variable
        pi = Variable("pi", MIRType.FLOAT)
        module.add_global(pi)

        # Create add function
        add_func = MIRFunction(
            "add",
            [Variable("a", MIRType.INT), Variable("b", MIRType.INT)],
            MIRType.INT,
        )
        add_entry = BasicBlock("entry")
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)
        add_entry.add_instruction(LoadVar(t0, Variable("a", MIRType.INT)))
        add_entry.add_instruction(LoadVar(t1, Variable("b", MIRType.INT)))
        add_entry.add_instruction(BinaryOp(t2, "+", t0, t1))
        add_entry.add_instruction(Return(t2))
        add_func.cfg.add_block(add_entry)
        add_func.cfg.set_entry_block(add_entry)

        # Create main function
        main_func = MIRFunction("main", return_type=MIRType.INT)
        main_entry = BasicBlock("entry")
        t3 = Temp(MIRType.INT, temp_id=3)
        main_entry.add_instruction(LoadConst(t3, 0))
        main_entry.add_instruction(Return(t3))
        main_func.cfg.add_block(main_entry)
        main_func.cfg.set_entry_block(main_entry)

        # Add functions to module
        module.add_function(add_func)
        module.add_function(main_func)

        # Validate should pass
        errors = module.validate()
        self.assertEqual(errors, [])

        # Check string representation
        result = str(module)
        self.assertIn("module calculator", result)
        self.assertIn("function add(a: int, b: int) -> int", result)
        self.assertIn("function main() -> int", result)


if __name__ == "__main__":
    unittest.main()
