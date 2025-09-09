"""Tests for MIR module and function containers."""

import json
from typing import Any

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


class TestConstantPool:
    """Test constant pool functionality."""

    def test_constant_pool_creation(self) -> None:
        """Test creating constant pool."""
        pool = ConstantPool()
        assert pool.constants == []
        assert pool.size() == 0

    def test_add_constants(self) -> None:
        """Test adding constants to pool."""
        pool = ConstantPool()

        c1 = Constant(42, MIRType.INT)
        c2 = Constant(3.14, MIRType.FLOAT)
        c3 = Constant("hello", MIRType.STRING)

        idx1 = pool.add(c1)
        idx2 = pool.add(c2)
        idx3 = pool.add(c3)

        assert idx1 == 0
        assert idx2 == 1
        assert idx3 == 2
        assert pool.size() == 3

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
        assert idx1 == idx2
        # c3 should have different index
        assert idx1 != idx3
        assert pool.size() == 2

    def test_deduplication_complex_types(self) -> None:
        """Test deduplication with complex constants."""
        pool = ConstantPool()

        # Test string deduplication
        s1 = Constant("hello world", MIRType.STRING)
        s2 = Constant("hello world", MIRType.STRING)
        s3 = Constant("hello", MIRType.STRING)

        idx1 = pool.add(s1)
        idx2 = pool.add(s2)
        idx3 = pool.add(s3)

        assert idx1 == idx2  # Same strings deduplicated
        assert idx1 != idx3  # Different strings

        # Test boolean deduplication
        b1 = Constant(True, MIRType.BOOL)
        b2 = Constant(True, MIRType.BOOL)
        b3 = Constant(False, MIRType.BOOL)

        idx4 = pool.add(b1)
        idx5 = pool.add(b2)
        idx6 = pool.add(b3)

        assert idx4 == idx5  # Same booleans deduplicated
        assert idx4 != idx6  # Different booleans

        # Should have 4 unique constants total (2 strings, 2 booleans)
        assert pool.size() == 4

    def test_deduplication_preserves_insertion_order(self) -> None:
        """Test that deduplication preserves the first insertion."""
        pool = ConstantPool()

        c1 = Constant(100, MIRType.INT)
        c2 = Constant(200, MIRType.INT)
        c3 = Constant(100, MIRType.INT)  # Duplicate of c1

        idx1 = pool.add(c1)
        idx2 = pool.add(c2)
        idx3 = pool.add(c3)

        assert idx1 == 0
        assert idx2 == 1
        assert idx3 == 0  # Should reuse c1's index

        # Check that the original constant is preserved
        retrieved = pool.get(0)
        assert retrieved == c1
        assert retrieved is not None
        if retrieved:  # Type guard for mypy
            assert retrieved.value == 100

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

        assert retrieved1 == c1
        assert retrieved2 == c2
        assert retrieved3 is None

    def test_constant_pool_string_representation(self) -> None:
        """Test string representation of constant pool."""
        pool = ConstantPool()
        pool.add(Constant(42))
        pool.add(Constant("hello"))
        pool.add(Constant(True))

        result = str(pool)
        assert "Constants:" in result
        assert "[0] 42" in result
        assert '[1] "hello"' in result
        assert "[2] True" in result


class TestMIRFunction:
    """Test MIR function functionality."""

    def test_function_creation(self) -> None:
        """Test creating MIR function."""
        func = MIRFunction("main", return_type=MIRType.INT)
        assert func.name == "main"
        assert func.return_type == MIRType.INT
        assert func.params == []
        assert func.cfg is not None

    def test_function_with_parameters(self) -> None:
        """Test function with parameters."""
        params = [
            Variable("x", MIRType.INT),
            Variable("y", MIRType.FLOAT),
        ]
        func = MIRFunction("add", params, MIRType.FLOAT)

        assert func.params == params
        assert len(func.params) == 2
        assert func.params[0].name == "x"
        assert func.params[1].type == MIRType.FLOAT

    def test_add_local_variable(self) -> None:
        """Test adding local variables."""
        func = MIRFunction("compute")
        v1 = Variable("temp", MIRType.INT)
        v2 = Variable("result", MIRType.FLOAT)

        func.add_local(v1)
        func.add_local(v2)

        assert len(func.locals) == 2
        assert "temp" in func.locals
        assert "result" in func.locals
        assert func.locals["temp"] == v1

    def test_get_local_variable(self) -> None:
        """Test getting local variables."""
        func = MIRFunction("test")
        v = Variable("counter", MIRType.INT)
        func.add_local(v)

        retrieved = func.get_local("counter")
        assert retrieved == v

        none_var = func.get_local("nonexistent")
        assert none_var is None

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
        entry.add_instruction(LoadConst(t0, 1, (1, 1)))
        entry.add_instruction(Return((1, 1), t0))

        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        result = str(func)
        assert "function factorial(n: int) -> int" in result
        assert "entry:" in result
        assert "t0 = 1" in result
        assert "return t0" in result

    def test_function_without_return_type(self) -> None:
        """Test function without return type (void)."""
        func = MIRFunction("print_message", [Variable("msg", MIRType.STRING)])
        result = str(func)
        assert "function print_message(msg: string)" in result
        assert "->" not in result


class TestModuleSerialization:
    """Test module serialization/deserialization."""

    def test_module_to_dict(self) -> None:
        """Test converting module to dictionary representation."""
        module = MIRModule("test_module")

        # Add constants
        module.constants.add(Constant(42, MIRType.INT))
        module.constants.add(Constant("hello", MIRType.STRING))

        # Add global
        module.add_global(Variable("count", MIRType.INT))

        # Add function
        func = MIRFunction("main", return_type=MIRType.INT)
        entry = BasicBlock("entry")
        t0 = Temp(MIRType.INT, temp_id=0)
        entry.add_instruction(LoadConst(t0, 0, (1, 1)))
        entry.add_instruction(Return((1, 1), t0))
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        module.add_function(func)
        module.set_main_function("main")

        # Convert to dict
        module_dict: dict[str, Any] = {
            "name": module.name,
            "main_function": module.main_function,
            "constants": [{"value": c.value, "type": str(c.type)} for c in module.constants.constants],
            "globals": {name: str(var.type) for name, var in module.globals.items()},
            "functions": list(module.functions.keys()),
        }

        assert module_dict["name"] == "test_module"
        assert module_dict["main_function"] == "main"
        constants = module_dict["constants"]
        assert isinstance(constants, list)
        assert len(constants) == 2
        assert constants[0]["value"] == 42
        globals_dict = module_dict["globals"]
        assert isinstance(globals_dict, dict)
        assert globals_dict["count"] == "int"
        functions = module_dict["functions"]
        assert isinstance(functions, list)
        assert "main" in functions

    def test_module_from_dict(self) -> None:
        """Test reconstructing module from dictionary representation."""
        module_data: dict[str, Any] = {
            "name": "restored_module",
            "main_function": "start",
            "globals": {
                "version": "string",
                "debug": "bool",
            },
        }

        # Reconstruct module
        module_name: str = module_data["name"]
        module = MIRModule(module_name)

        globals_dict: dict[str, str] = module_data["globals"]
        for var_name, type_str in globals_dict.items():
            # Map string to MIRType
            type_map = {
                "int": MIRType.INT,
                "float": MIRType.FLOAT,
                "string": MIRType.STRING,
                "bool": MIRType.BOOL,
            }
            mir_type = type_map[type_str]
            module.add_global(Variable(var_name, mir_type))

        main_func: str | None = module_data.get("main_function")
        if main_func:
            module.set_main_function(main_func)

        # Verify reconstruction
        assert module.name == "restored_module"
        assert module.main_function == "start"
        assert len(module.globals) == 2
        version_var = module.get_global("version")
        debug_var = module.get_global("debug")
        assert version_var is not None
        assert debug_var is not None
        assert version_var is not None  # Type guard for mypy
        assert debug_var is not None  # Type guard for mypy
        assert version_var.type == MIRType.STRING
        assert debug_var.type == MIRType.BOOL

    def test_module_json_roundtrip(self) -> None:
        """Test serializing module to JSON and back."""
        # Create module
        module = MIRModule("json_test")
        module.constants.add(Constant(100, MIRType.INT))
        module.constants.add(Constant(3.14, MIRType.FLOAT))
        module.add_global(Variable("MAX", MIRType.INT))

        # Serialize to JSON-compatible dict
        module_dict = {
            "name": module.name,
            "constants_count": module.constants.size(),
            "globals_count": len(module.globals),
            "functions_count": len(module.functions),
        }

        # Convert to JSON and back
        json_str = json.dumps(module_dict)
        restored_dict = json.loads(json_str)

        # Verify
        assert restored_dict["name"] == "json_test"
        assert restored_dict["constants_count"] == 2
        assert restored_dict["globals_count"] == 1
        assert restored_dict["functions_count"] == 0


class TestMIRModule:
    """Test MIR module functionality."""

    def test_module_creation(self) -> None:
        """Test creating MIR module."""
        module = MIRModule("test_module")
        assert module.name == "test_module"
        assert module.functions == {}
        assert module.globals == {}
        assert module.constants is not None
        assert module.main_function is None

    def test_add_function(self) -> None:
        """Test adding functions to module."""
        module = MIRModule("app")
        func1 = MIRFunction("main", return_type=MIRType.INT)
        func2 = MIRFunction("helper")

        module.add_function(func1)
        module.add_function(func2)

        assert len(module.functions) == 2
        assert "main" in module.functions
        assert "helper" in module.functions

    def test_get_function(self) -> None:
        """Test getting functions from module."""
        module = MIRModule("app")
        func = MIRFunction("compute", return_type=MIRType.FLOAT)
        module.add_function(func)

        retrieved = module.get_function("compute")
        assert retrieved == func

        none_func = module.get_function("nonexistent")
        assert none_func is None

    def test_function_overwrite(self) -> None:
        """Test that adding a function with same name overwrites the previous one."""
        module = MIRModule("app")

        func1 = MIRFunction("process", return_type=MIRType.INT)
        func2 = MIRFunction("process", return_type=MIRType.STRING)  # Same name, different signature

        module.add_function(func1)
        assert module.get_function("process") == func1

        module.add_function(func2)  # Should overwrite
        retrieved_func = module.get_function("process")
        assert retrieved_func == func2
        assert retrieved_func is not None
        assert retrieved_func is not None  # Type guard for mypy
        assert retrieved_func.return_type == MIRType.STRING
        assert len(module.functions) == 1

    def test_multiple_functions(self) -> None:
        """Test managing multiple functions."""
        module = MIRModule("app")

        functions = [
            MIRFunction("init"),
            MIRFunction("compute", [Variable("x", MIRType.FLOAT)], MIRType.FLOAT),
            MIRFunction("validate", [Variable("s", MIRType.STRING)], MIRType.BOOL),
            MIRFunction("main", return_type=MIRType.INT),
            MIRFunction("cleanup"),
        ]

        for func in functions:
            module.add_function(func)

        assert len(module.functions) == 5

        # Verify each function
        for func in functions:
            retrieved = module.get_function(func.name)
            assert retrieved == func
            assert retrieved is not None
            assert retrieved is not None  # Type guard for mypy
            assert retrieved.return_type == func.return_type

    def test_function_lookup_case_sensitive(self) -> None:
        """Test that function lookup is case-sensitive."""
        module = MIRModule("app")

        func_lower = MIRFunction("process")
        func_upper = MIRFunction("PROCESS")
        func_mixed = MIRFunction("Process")

        module.add_function(func_lower)
        module.add_function(func_upper)
        module.add_function(func_mixed)

        assert len(module.functions) == 3
        assert module.get_function("process") == func_lower
        assert module.get_function("PROCESS") == func_upper
        assert module.get_function("Process") == func_mixed
        assert module.get_function("pRoCeSs") is None

    def test_add_global_variable(self) -> None:
        """Test adding global variables."""
        module = MIRModule("app")
        v1 = Variable("global_count", MIRType.INT)
        v2 = Variable("pi", MIRType.FLOAT)

        module.add_global(v1)
        module.add_global(v2)

        assert len(module.globals) == 2
        assert "global_count" in module.globals
        assert "pi" in module.globals

    def test_get_global_variable(self) -> None:
        """Test getting global variables."""
        module = MIRModule("app")
        v = Variable("config", MIRType.STRING)
        module.add_global(v)

        retrieved = module.get_global("config")
        assert retrieved == v

        none_var = module.get_global("nonexistent")
        assert none_var is None

    def test_global_variable_overwrite(self) -> None:
        """Test that adding a global with same name overwrites the previous one."""
        module = MIRModule("app")

        v1 = Variable("config", MIRType.STRING)
        v2 = Variable("config", MIRType.INT)  # Same name, different type

        module.add_global(v1)
        assert module.get_global("config") == v1

        module.add_global(v2)  # Should overwrite
        retrieved_var = module.get_global("config")
        assert retrieved_var == v2
        assert retrieved_var is not None
        assert retrieved_var is not None  # Type guard for mypy
        assert retrieved_var.type == MIRType.INT
        assert len(module.globals) == 1

    def test_multiple_global_variables(self) -> None:
        """Test managing multiple global variables."""
        module = MIRModule("app")

        globals_to_add = [
            Variable("MAX_SIZE", MIRType.INT),
            Variable("VERSION", MIRType.STRING),
            Variable("DEBUG", MIRType.BOOL),
            Variable("EPSILON", MIRType.FLOAT),
        ]

        for var in globals_to_add:
            module.add_global(var)

        assert len(module.globals) == 4

        # Verify each global
        for var in globals_to_add:
            retrieved = module.get_global(var.name)
            assert retrieved == var
            assert retrieved is not None
            assert retrieved is not None  # Type guard for mypy
            assert retrieved.type == var.type

    def test_main_function_handling(self) -> None:
        """Test main function setting and retrieval."""
        module = MIRModule("app")
        main_func = MIRFunction("main", return_type=MIRType.INT)
        module.add_function(main_func)

        # No main function by default
        assert module.main_function is None
        retrieved = module.get_main_function()
        assert retrieved is None

        # Set main function
        module.set_main_function("main")
        assert module.main_function == "main"
        retrieved = module.get_main_function()
        assert retrieved == main_func

        # Change main function name
        module.set_main_function("start")
        assert module.main_function == "start"

        # Main function not found
        retrieved = module.get_main_function()
        assert retrieved is None

        # Add new main
        start_func = MIRFunction("start")
        module.add_function(start_func)
        retrieved = module.get_main_function()
        assert retrieved == start_func

    def test_main_function_validation_scenarios(self) -> None:
        """Test various main function validation scenarios."""
        module = MIRModule("app")

        # Scenario 1: Set main to non-existent function
        module.set_main_function("nonexistent_main")
        errors = module.validate()
        assert any("Main function 'nonexistent_main' not found" in err for err in errors)

        # Scenario 2: Add the main function after setting
        main_func = MIRFunction("nonexistent_main", return_type=MIRType.INT)
        entry = BasicBlock("entry")
        t0 = Temp(MIRType.INT, temp_id=0)
        entry.add_instruction(LoadConst(t0, 0, (1, 1)))
        entry.add_instruction(Return((1, 1), t0))
        main_func.cfg.add_block(entry)
        main_func.cfg.set_entry_block(entry)
        module.add_function(main_func)

        errors = module.validate()
        assert errors == []  # Should now be valid

        # Scenario 3: Change main to another function
        other_func = MIRFunction("other")
        other_entry = BasicBlock("entry")
        t1 = Temp(MIRType.INT, temp_id=1)
        other_entry.add_instruction(LoadConst(t1, 0, (1, 1)))
        other_entry.add_instruction(Return((1, 1), t1))
        other_func.cfg.add_block(other_entry)
        other_func.cfg.set_entry_block(other_entry)
        module.add_function(other_func)

        module.set_main_function("other")
        assert module.get_main_function() == other_func
        errors = module.validate()
        assert errors == []

    def test_main_function_with_empty_name(self) -> None:
        """Test setting main function with empty name."""
        module = MIRModule("app")

        # Setting empty string as main function
        module.set_main_function("")
        assert module.main_function == ""
        assert module.get_main_function() is None

        # Validation passes because empty string is falsy and won't trigger the check
        errors = module.validate()
        assert errors == []

    def test_main_function_clear(self) -> None:
        """Test clearing main function."""
        module = MIRModule("app")

        # Add and set main function
        main_func = MIRFunction("main", return_type=MIRType.INT)
        entry = BasicBlock("entry")
        entry.add_instruction(Return((1, 1), Temp(MIRType.INT, temp_id=0)))
        main_func.cfg.add_block(entry)
        main_func.cfg.set_entry_block(entry)
        module.add_function(main_func)
        module.set_main_function("main")

        assert module.get_main_function() == main_func

        # Clear main function by setting to None
        module.main_function = None
        assert module.main_function is None
        assert module.get_main_function() is None

        # Module should still validate without main function
        errors = module.validate()
        assert errors == []

    def test_module_validation_success(self) -> None:
        """Test successful module validation."""
        module = MIRModule("app")

        # Create a valid function with proper CFG
        main = MIRFunction("main", return_type=MIRType.INT)
        entry = BasicBlock("entry")
        t0 = Temp(MIRType.INT, temp_id=0)
        entry.add_instruction(LoadConst(t0, 0, (1, 1)))
        entry.add_instruction(Return((1, 1), t0))

        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)
        module.add_function(main)

        errors = module.validate()
        assert errors == []

    def test_module_validation_missing_main(self) -> None:
        """Test validation with missing main function."""
        module = MIRModule("app")
        module.main_function = "main"  # Main is expected but not present

        errors = module.validate()
        assert len(errors) == 1
        assert "Main function 'main' not found" in errors[0]

    def test_module_validation_missing_entry_block(self) -> None:
        """Test validation with function missing entry block."""
        module = MIRModule("app")
        func = MIRFunction("broken")
        # Don't set entry block
        module.add_function(func)

        errors = module.validate()
        assert len(errors) == 1
        assert "Function 'broken' has no entry block" in errors[0]

    def test_module_validation_unterminated_block(self) -> None:
        """Test validation with unterminated block."""
        module = MIRModule("app")
        func = MIRFunction("incomplete")

        entry = BasicBlock("entry")
        bb1 = BasicBlock("bb1")
        t0 = Temp(MIRType.INT, temp_id=0)

        # Entry has terminator
        entry.add_instruction(Jump("bb1", (1, 1)))

        # bb1 has instructions but no terminator
        bb1.add_instruction(LoadConst(t0, 42, (1, 1)))

        func.cfg.add_block(entry)
        func.cfg.add_block(bb1)
        func.cfg.set_entry_block(entry)
        module.add_function(func)

        errors = module.validate()
        assert len(errors) == 1
        assert "Block 'bb1' in function 'incomplete' is not terminated" in errors[0]

    def test_module_validation_invalid_jump_target(self) -> None:
        """Test validation with jump to undefined label."""
        module = MIRModule("app")
        func = MIRFunction("bad_jump")

        entry = BasicBlock("entry")
        entry.add_instruction(Jump("nonexistent", (1, 1)))

        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        module.add_function(func)

        errors = module.validate()
        assert "Jump to undefined label 'nonexistent' in function 'bad_jump'" in errors[0]

    def test_module_validation_invalid_conditional_jump(self) -> None:
        """Test validation with conditional jump to undefined labels."""
        module = MIRModule("app")
        func = MIRFunction("bad_cjump")

        entry = BasicBlock("entry")
        t0 = Temp(MIRType.BOOL, temp_id=0)
        entry.add_instruction(ConditionalJump(t0, "undefined1", (1, 1), "undefined2"))

        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        module.add_function(func)

        errors = module.validate()
        # Should have errors for both undefined labels
        assert any("undefined1" in err for err in errors)
        assert any("undefined2" in err for err in errors)

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
        entry.add_instruction(LoadConst(t0, 0, (1, 1)))
        entry.add_instruction(Return((1, 1), t0))
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        module.add_function(func)

        result = module.to_string()

        assert "module example {" in result
        assert "Constants:" in result
        assert "[0] 42" in result
        assert "globals:" in result
        assert "count: int" in result
        assert "functions:" in result
        assert "function main()" in result

    def test_module_string_representation_options(self) -> None:
        """Test module string representation with options."""
        module = MIRModule("test")
        module.constants.add(Constant(100))
        module.add_global(Variable("var", MIRType.STRING))

        # Without constants
        result = module.to_string(include_constants=False)
        assert "Constants:" not in result

        # Without globals
        result = module.to_string(include_globals=False)
        assert "globals:" not in result

        # With both
        result = module.to_string(include_constants=True, include_globals=True)
        assert "Constants:" in result
        assert "globals:" in result

    def test_module_repr(self) -> None:
        """Test module __repr__ method."""
        module = MIRModule("debug_module")

        # Empty module
        repr_str = repr(module)
        assert "MIRModule(debug_module" in repr_str
        assert "functions=0" in repr_str
        assert "globals=0" in repr_str

        # Add functions and globals
        module.add_function(MIRFunction("func1"))
        module.add_function(MIRFunction("func2"))
        module.add_global(Variable("var1", MIRType.INT))

        repr_str = repr(module)
        assert "functions=2" in repr_str
        assert "globals=1" in repr_str

    def test_empty_module_validation(self) -> None:
        """Test validation of completely empty module."""
        module = MIRModule("empty")
        errors = module.validate()
        assert errors == []  # Empty module should be valid

    def test_constant_pool_boundary_cases(self) -> None:
        """Test constant pool with boundary cases."""
        pool = ConstantPool()

        # Test negative index
        assert pool.get(-1) is None

        # Test very large index
        assert pool.get(999999) is None

        # Test empty pool size
        assert pool.size() == 0

        # Test adding and getting at boundary
        c = Constant(42, MIRType.INT)
        idx = pool.add(c)
        assert idx == 0
        assert pool.get(0) is not None
        assert pool.get(1) is None


class TestIntegration:
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
        add_entry.add_instruction(LoadVar(t0, Variable("a", MIRType.INT), (1, 1)))
        add_entry.add_instruction(LoadVar(t1, Variable("b", MIRType.INT), (1, 1)))
        add_entry.add_instruction(BinaryOp(t2, "+", t0, t1, (1, 1)))
        add_entry.add_instruction(Return((1, 1), t2))
        add_func.cfg.add_block(add_entry)
        add_func.cfg.set_entry_block(add_entry)

        # Create main function
        main_func = MIRFunction("main", return_type=MIRType.INT)
        main_entry = BasicBlock("entry")
        t3 = Temp(MIRType.INT, temp_id=3)
        main_entry.add_instruction(LoadConst(t3, Constant(0, MIRType.INT), (1, 1)))
        main_entry.add_instruction(Return((1, 1), t3))
        main_func.cfg.add_block(main_entry)
        main_func.cfg.set_entry_block(main_entry)

        # Add functions to module
        module.add_function(add_func)
        module.add_function(main_func)

        # Validate should pass
        errors = module.validate()
        assert errors == []

        # Check string representation
        result = str(module)
        assert "module calculator" in result
        assert "function add(a: int, b: int) -> int" in result
        assert "function main() -> int" in result
