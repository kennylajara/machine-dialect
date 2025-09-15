"""Test opcode compatibility between Python bytecode emitter and Rust VM.

This test ensures that the opcodes defined in Python match exactly what
the Rust VM expects, providing a safety net against opcode mismatches.
"""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

import pytest

import machine_dialect_vm
from machine_dialect.codegen.bytecode_module import BytecodeModule, Chunk, ChunkType, ConstantTag
from machine_dialect.codegen.opcodes import Opcode
from machine_dialect.codegen.register_codegen import RegisterBytecodeGenerator
from machine_dialect.mir import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    LoadConst,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_values import Constant, Variable


class TestOpcodeCompatibility:
    """Test that Python opcodes match Rust VM expectations."""

    def test_opcode_values(self) -> None:
        """Verify all opcode values match expected values."""
        # These values MUST match the Rust VM's instruction decoder
        expected_opcodes = {
            "LOAD_CONST_R": 0,
            "MOVE_R": 1,
            "LOAD_GLOBAL_R": 2,
            "STORE_GLOBAL_R": 3,
            "DEFINE_R": 4,
            "CHECK_TYPE_R": 5,
            "CAST_R": 6,
            "ADD_R": 7,
            "SUB_R": 8,
            "MUL_R": 9,
            "DIV_R": 10,
            "MOD_R": 11,
            "NEG_R": 12,
            "NOT_R": 13,
            "AND_R": 14,
            "OR_R": 15,
            "EQ_R": 16,
            "NEQ_R": 17,
            "LT_R": 18,
            "GT_R": 19,
            "LTE_R": 20,
            "GTE_R": 21,
            "JUMP_R": 22,
            "JUMP_IF_R": 23,
            "JUMP_IF_NOT_R": 24,
            "CALL_R": 25,
            "RETURN_R": 26,
            "PHI_R": 27,
            "ASSERT_R": 28,
            "SCOPE_ENTER_R": 29,
            "SCOPE_EXIT_R": 30,
            "CONCAT_STR_R": 31,
            "STR_LEN_R": 32,
            "NEW_ARRAY_R": 33,
            "ARRAY_GET_R": 34,
            "ARRAY_SET_R": 35,
            "ARRAY_LEN_R": 36,
            "DEBUG_PRINT": 37,
            "BREAKPOINT": 38,
            "HALT": 39,
            "NOP": 40,
            "DICT_NEW_R": 41,
            "DICT_GET_R": 42,
            "DICT_SET_R": 43,
            "DICT_REMOVE_R": 44,
            "DICT_CONTAINS_R": 45,
            "DICT_KEYS_R": 46,
            "DICT_VALUES_R": 47,
            "DICT_CLEAR_R": 48,
            "DICT_LEN_R": 49,
        }

        # First, verify the count matches
        python_opcodes = [
            name for name in dir(Opcode) if not name.startswith("_") and isinstance(getattr(Opcode, name), int)
        ]
        assert len(python_opcodes) == len(expected_opcodes), (
            f"Python has {len(python_opcodes)} opcodes, expected {len(expected_opcodes)}. "
            f"Python opcodes: {sorted(python_opcodes)}"
        )

        # Then verify each opcode value
        for name, expected_value in expected_opcodes.items():
            actual_value = getattr(Opcode, name)
            assert actual_value == expected_value, f"Opcode.{name} = {actual_value}, expected {expected_value}"

        # Also verify no unexpected opcodes exist
        for name in python_opcodes:
            assert name in expected_opcodes, f"Unexpected opcode in Python: {name} = {getattr(Opcode, name)}"

    def test_instruction_encoding_load_const(self) -> None:
        """Test LoadConstR instruction encoding."""
        bytecode = bytearray()

        # LoadConstR r0, #0
        bytecode.append(Opcode.LOAD_CONST_R)
        bytecode.append(0)  # dst: r0
        bytecode.extend(struct.pack("<H", 0))  # const_idx: 0

        assert len(bytecode) == 4
        assert bytecode[0] == 0  # LOAD_CONST_R opcode
        assert bytecode[1] == 0  # dst register
        assert struct.unpack("<H", bytecode[2:4])[0] == 0  # const index

    def test_instruction_encoding_arithmetic(self) -> None:
        """Test arithmetic instruction encoding."""
        bytecode = bytearray()

        # AddR r2, r0, r1
        bytecode.append(Opcode.ADD_R)
        bytecode.append(2)  # dst: r2
        bytecode.append(0)  # left: r0
        bytecode.append(1)  # right: r1

        assert len(bytecode) == 4
        assert bytecode[0] == 7  # ADD_R opcode
        assert bytecode[1] == 2  # dst register
        assert bytecode[2] == 0  # left register
        assert bytecode[3] == 1  # right register

    def test_instruction_encoding_array_ops(self) -> None:
        """Test array operation instruction encoding."""
        # NewArrayR - 3 bytes
        new_array = bytearray()
        new_array.append(Opcode.NEW_ARRAY_R)
        new_array.append(1)  # dst: r1
        new_array.append(0)  # size: r0

        assert len(new_array) == 3
        assert new_array[0] == 33  # NEW_ARRAY_R opcode

        # ArrayGetR - 4 bytes
        array_get = bytearray()
        array_get.append(Opcode.ARRAY_GET_R)
        array_get.append(2)  # dst: r2
        array_get.append(0)  # array: r0
        array_get.append(1)  # index: r1

        assert len(array_get) == 4
        assert array_get[0] == 34  # ARRAY_GET_R opcode

        # ArraySetR - 4 bytes
        array_set = bytearray()
        array_set.append(Opcode.ARRAY_SET_R)
        array_set.append(0)  # array: r0
        array_set.append(1)  # index: r1
        array_set.append(2)  # value: r2

        assert len(array_set) == 4
        assert array_set[0] == 35  # ARRAY_SET_R opcode

    def test_instruction_encoding_control_flow(self) -> None:
        """Test control flow instruction encoding."""
        # JumpR - 5 bytes
        jump = bytearray()
        jump.append(Opcode.JUMP_R)
        jump.extend(struct.pack("<i", 10))  # offset: 10

        assert len(jump) == 5
        assert jump[0] == 22  # JUMP_R opcode

        # JumpIfR - 6 bytes
        jump_if = bytearray()
        jump_if.append(Opcode.JUMP_IF_R)
        jump_if.append(0)  # cond: r0
        jump_if.extend(struct.pack("<i", 10))  # offset: 10

        assert len(jump_if) == 6
        assert jump_if[0] == 23  # JUMP_IF_R opcode

        # ReturnR with value - 3 bytes
        ret_val = bytearray()
        ret_val.append(Opcode.RETURN_R)
        ret_val.append(1)  # has_value: true
        ret_val.append(0)  # src: r0

        assert len(ret_val) == 3
        assert ret_val[0] == 26  # RETURN_R opcode

        # ReturnR without value - 2 bytes
        ret_void = bytearray()
        ret_void.append(Opcode.RETURN_R)
        ret_void.append(0)  # has_value: false

        assert len(ret_void) == 2
        assert ret_void[0] == 26  # RETURN_R opcode

    def test_vm_can_decode_all_instructions(self) -> None:
        """Test that the Rust VM can decode all instruction types we emit."""
        module = BytecodeModule("opcode_test")

        chunk = Chunk(
            name="main",
            chunk_type=ChunkType.MAIN,
            bytecode=bytearray(),
            constants=[
                (ConstantTag.INT, 42),
                (ConstantTag.FLOAT, 3.14),
                (ConstantTag.STRING, "hello"),
                (ConstantTag.BOOL, True),
                (ConstantTag.EMPTY, None),
            ],
            num_locals=10,
            num_params=0,
        )

        bytecode = bytearray()

        # Test various instruction types
        # LoadConstR
        bytecode.append(Opcode.LOAD_CONST_R)
        bytecode.append(0)
        bytecode.extend(b"\x00\x00")

        # MoveR
        bytecode.append(Opcode.MOVE_R)
        bytecode.append(1)
        bytecode.append(0)

        # Arithmetic
        bytecode.append(Opcode.ADD_R)
        bytecode.append(2)
        bytecode.append(0)
        bytecode.append(1)

        bytecode.append(Opcode.SUB_R)
        bytecode.append(3)
        bytecode.append(2)
        bytecode.append(1)

        # Comparison
        bytecode.append(Opcode.LT_R)
        bytecode.append(4)
        bytecode.append(0)
        bytecode.append(1)

        # Array operations
        bytecode.append(Opcode.NEW_ARRAY_R)
        bytecode.append(5)
        bytecode.append(0)

        bytecode.append(Opcode.ARRAY_GET_R)
        bytecode.append(6)
        bytecode.append(5)
        bytecode.append(0)

        # Return
        bytecode.append(Opcode.RETURN_R)
        bytecode.append(1)
        bytecode.append(6)

        chunk.bytecode = bytecode
        module.add_chunk(chunk)

        # Serialize and attempt to load in VM
        serialized = module.serialize()

        with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
            f.write(serialized)
            bytecode_path = f.name

        try:
            vm = machine_dialect_vm.RustVM()
            vm.load_bytecode(bytecode_path)
            # If we get here without error, the VM successfully decoded all instructions
            assert True
        finally:
            Path(bytecode_path).unlink()

    def test_mir_to_bytecode_opcode_mapping(self) -> None:
        """Test that MIR instructions map to correct opcodes."""
        module = MIRModule("test")
        func = MIRFunction("__main__")
        block = BasicBlock("entry")

        # Create various MIR instructions
        from machine_dialect.mir.mir_types import MIRType

        v1 = Variable("v1", MIRType.INT)
        v2 = Variable("v2", MIRType.INT)
        v3 = Variable("v3", MIRType.INT)

        block.add_instruction(LoadConst(v1, Constant(10), (1, 1)))
        block.add_instruction(LoadConst(v2, Constant(20), (1, 1)))
        block.add_instruction(BinaryOp(v3, "+", v1, v2, (1, 1)))
        block.add_instruction(Return((1, 1), v3))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)
        module.functions["__main__"] = func

        # Generate bytecode
        generator = RegisterBytecodeGenerator()
        bytecode_module = generator.generate(module)

        # Check the generated bytecode contains expected opcodes
        chunk = bytecode_module.chunks[0]
        bytecode = chunk.bytecode

        # Parse opcodes
        opcodes_found = []
        i = 0
        while i < len(bytecode):
            opcodes_found.append(bytecode[i])

            # Skip instruction bytes based on opcode
            if bytecode[i] == Opcode.LOAD_CONST_R:
                i += 4
            elif bytecode[i] == Opcode.ADD_R:
                i += 4
            elif bytecode[i] == Opcode.RETURN_R:
                i += 3
            else:
                i += 1

        # Verify we have the expected opcodes
        assert Opcode.LOAD_CONST_R in opcodes_found
        assert Opcode.ADD_R in opcodes_found
        assert Opcode.RETURN_R in opcodes_found

    def test_constant_tag_compatibility(self) -> None:
        """Test that constant tags match between Python and Rust."""
        expected_tags = {
            "INT": 0x01,
            "FLOAT": 0x02,
            "STRING": 0x03,
            "BOOL": 0x04,
            "EMPTY": 0x05,
        }

        for name, expected_value in expected_tags.items():
            actual_value = getattr(ConstantTag, name)
            assert actual_value == expected_value, (
                f"ConstantTag.{name} = {actual_value:#x}, expected {expected_value:#x}"
            )

    def test_rust_vm_recognizes_all_opcodes(self) -> None:
        """Test that the Rust VM's decoder handles all opcodes we define."""
        # This test creates a bytecode file with every single opcode
        # to ensure the Rust VM's loader can handle them all
        module = BytecodeModule("opcode_coverage_test")

        chunk = Chunk(
            name="main",
            chunk_type=ChunkType.MAIN,
            bytecode=bytearray(),
            constants=[
                (ConstantTag.INT, 1),
                (ConstantTag.FLOAT, 1.0),
                (ConstantTag.STRING, "test"),
                (ConstantTag.BOOL, True),
            ],
            num_locals=10,
            num_params=0,
        )

        bytecode = bytearray()

        # Test all opcodes systematically
        # Note: Some opcodes are not yet implemented in the Rust loader,
        # so we only test the ones that are
        implemented_opcodes = {
            Opcode.LOAD_CONST_R: lambda: bytecode.extend([Opcode.LOAD_CONST_R, 0, 0, 0]),
            Opcode.MOVE_R: lambda: bytecode.extend([Opcode.MOVE_R, 1, 0]),
            Opcode.LOAD_GLOBAL_R: lambda: bytecode.extend([Opcode.LOAD_GLOBAL_R, 0, 0, 0]),
            Opcode.STORE_GLOBAL_R: lambda: bytecode.extend([Opcode.STORE_GLOBAL_R, 0, 0, 0]),
            # Arithmetic
            Opcode.ADD_R: lambda: bytecode.extend([Opcode.ADD_R, 2, 0, 1]),
            Opcode.SUB_R: lambda: bytecode.extend([Opcode.SUB_R, 2, 0, 1]),
            Opcode.MUL_R: lambda: bytecode.extend([Opcode.MUL_R, 2, 0, 1]),
            Opcode.DIV_R: lambda: bytecode.extend([Opcode.DIV_R, 2, 0, 1]),
            Opcode.MOD_R: lambda: bytecode.extend([Opcode.MOD_R, 2, 0, 1]),
            Opcode.NEG_R: lambda: bytecode.extend([Opcode.NEG_R, 1, 0]),
            Opcode.NOT_R: lambda: bytecode.extend([Opcode.NOT_R, 1, 0]),
            # Logical
            Opcode.AND_R: lambda: bytecode.extend([Opcode.AND_R, 2, 0, 1]),
            Opcode.OR_R: lambda: bytecode.extend([Opcode.OR_R, 2, 0, 1]),
            # Comparison
            Opcode.EQ_R: lambda: bytecode.extend([Opcode.EQ_R, 2, 0, 1]),
            Opcode.NEQ_R: lambda: bytecode.extend([Opcode.NEQ_R, 2, 0, 1]),
            Opcode.LT_R: lambda: bytecode.extend([Opcode.LT_R, 2, 0, 1]),
            Opcode.GT_R: lambda: bytecode.extend([Opcode.GT_R, 2, 0, 1]),
            Opcode.LTE_R: lambda: bytecode.extend([Opcode.LTE_R, 2, 0, 1]),
            Opcode.GTE_R: lambda: bytecode.extend([Opcode.GTE_R, 2, 0, 1]),
            # Control flow
            Opcode.JUMP_R: lambda: bytecode.extend([Opcode.JUMP_R, *list(struct.pack("<i", 0))]),
            Opcode.JUMP_IF_R: lambda: bytecode.extend([Opcode.JUMP_IF_R, 0, *list(struct.pack("<i", 0))]),
            Opcode.JUMP_IF_NOT_R: lambda: bytecode.extend([Opcode.JUMP_IF_NOT_R, 0, *list(struct.pack("<i", 0))]),
            Opcode.CALL_R: lambda: bytecode.extend([Opcode.CALL_R, 0, 0, 0]),  # func, dst, 0 args
            # String ops
            Opcode.CONCAT_STR_R: lambda: bytecode.extend([Opcode.CONCAT_STR_R, 2, 0, 1]),
            Opcode.STR_LEN_R: lambda: bytecode.extend([Opcode.STR_LEN_R, 1, 0]),
            # Array ops
            Opcode.NEW_ARRAY_R: lambda: bytecode.extend([Opcode.NEW_ARRAY_R, 1, 0]),
            Opcode.ARRAY_GET_R: lambda: bytecode.extend([Opcode.ARRAY_GET_R, 2, 0, 1]),
            Opcode.ARRAY_SET_R: lambda: bytecode.extend([Opcode.ARRAY_SET_R, 0, 1, 2]),
            Opcode.ARRAY_LEN_R: lambda: bytecode.extend([Opcode.ARRAY_LEN_R, 1, 0]),
            # Dictionary ops
            Opcode.DICT_NEW_R: lambda: bytecode.extend([Opcode.DICT_NEW_R, 0]),
            Opcode.DICT_GET_R: lambda: bytecode.extend([Opcode.DICT_GET_R, 2, 0, 1]),
            Opcode.DICT_SET_R: lambda: bytecode.extend([Opcode.DICT_SET_R, 0, 1, 2]),
            Opcode.DICT_CONTAINS_R: lambda: bytecode.extend([Opcode.DICT_CONTAINS_R, 2, 0, 1]),
            Opcode.DICT_REMOVE_R: lambda: bytecode.extend([Opcode.DICT_REMOVE_R, 0, 1]),
            Opcode.DICT_KEYS_R: lambda: bytecode.extend([Opcode.DICT_KEYS_R, 1, 0]),
            Opcode.DICT_VALUES_R: lambda: bytecode.extend([Opcode.DICT_VALUES_R, 1, 0]),
            Opcode.DICT_CLEAR_R: lambda: bytecode.extend([Opcode.DICT_CLEAR_R, 0]),
            Opcode.DICT_LEN_R: lambda: bytecode.extend([Opcode.DICT_LEN_R, 1, 0]),
            # Debug
            Opcode.DEBUG_PRINT: lambda: bytecode.extend([Opcode.DEBUG_PRINT, 0]),
            Opcode.BREAKPOINT: lambda: bytecode.extend([Opcode.BREAKPOINT]),
            # System
            Opcode.HALT: lambda: bytecode.extend([Opcode.HALT]),
            Opcode.NOP: lambda: bytecode.extend([Opcode.NOP]),
        }

        # Add instructions for implemented opcodes
        for _opcode, add_instruction in implemented_opcodes.items():
            add_instruction()  # type: ignore[no-untyped-call]

        # End with return
        bytecode.extend([Opcode.RETURN_R, 0])  # no value

        chunk.bytecode = bytecode
        module.add_chunk(chunk)

        # Try to load in VM
        serialized = module.serialize()
        with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
            f.write(serialized)
            bytecode_path = f.name

        try:
            vm = machine_dialect_vm.RustVM()
            vm.load_bytecode(bytecode_path)
            # Success means all opcodes were recognized
            assert True
        finally:
            Path(bytecode_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
