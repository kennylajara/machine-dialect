"""Integration tests for the Rust VM.

Tests the full pipeline from Machine Dialect™ source to VM execution.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import machine_dialect_vm
from machine_dialect.codegen.bytecode_module import BytecodeModule, Chunk, ChunkType, ConstantTag
from machine_dialect.codegen.opcodes import Opcode
from machine_dialect.codegen.register_codegen import RegisterBytecodeGenerator
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    LoadConst,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant


def test_simple_arithmetic() -> None:
    """Test simple arithmetic operations in the VM."""
    # Create a simple MIR module with arithmetic
    module = MIRModule("test")
    func = MIRFunction("__main__")

    # Create a basic block
    from machine_dialect.mir import BasicBlock

    block = BasicBlock("entry")

    # Create temps for the computation (not global variables)
    a = func.new_temp(MIRType.INT)
    b = func.new_temp(MIRType.INT)
    result = func.new_temp(MIRType.INT)

    # Add instructions: result = 2 + 3
    block.add_instruction(LoadConst(a, Constant(2), (1, 1)))
    block.add_instruction(LoadConst(b, Constant(3), (1, 1)))
    block.add_instruction(BinaryOp(result, "+", a, b, (1, 1)))
    block.add_instruction(Return((1, 1), result))

    # Add block to function
    func.cfg.add_block(block)
    func.cfg.set_entry_block(block)

    module.functions["__main__"] = func

    # Generate bytecode
    generator = RegisterBytecodeGenerator()
    bytecode_module = generator.generate(module)

    # Serialize bytecode
    bytecode = bytecode_module.serialize()

    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
        f.write(bytecode)
        bytecode_path = f.name

    try:
        # Load and execute in VM
        vm = machine_dialect_vm.RustVM()
        vm.load_bytecode(bytecode_path)
        result = vm.execute()

        # Check result
        assert result == 5, f"Expected 5, got {result}"
        print("✓ Simple arithmetic test passed")

    finally:
        # Clean up
        Path(bytecode_path).unlink()


def test_manual_bytecode() -> None:
    """Test manually created bytecode in the VM."""
    # Create a simple bytecode module manually
    module = BytecodeModule("test")

    # Create main chunk with simple addition
    chunk = Chunk(
        name="main",
        chunk_type=ChunkType.MAIN,
        bytecode=bytearray(),
        constants=[(ConstantTag.INT, 10), (ConstantTag.INT, 20)],
        num_locals=3,
        num_params=0,
    )

    # Generate bytecode: r0 = 10, r1 = 20, r2 = r0 + r1, return r2
    bytecode = bytearray()

    # LoadConstR r0, 0
    bytecode.append(Opcode.LOAD_CONST_R)
    bytecode.append(0)  # dst: r0
    bytecode.extend(b"\x00\x00")  # const_idx: 0

    # LoadConstR r1, 1
    bytecode.append(Opcode.LOAD_CONST_R)
    bytecode.append(1)  # dst: r1
    bytecode.extend(b"\x01\x00")  # const_idx: 1

    # AddR r2, r0, r1
    bytecode.append(Opcode.ADD_R)
    bytecode.append(2)  # dst: r2
    bytecode.append(0)  # left: r0
    bytecode.append(1)  # right: r1

    # ReturnR r2
    bytecode.append(Opcode.RETURN_R)
    bytecode.append(1)  # has_value: true
    bytecode.append(2)  # src: r2

    chunk.bytecode = bytecode
    module.add_chunk(chunk)

    # Manually serialize in the format expected by the Rust VM
    import struct
    from io import BytesIO

    buffer = BytesIO()

    # Header
    buffer.write(b"MDBC")  # Magic
    buffer.write(struct.pack("<I", 1))  # Version
    buffer.write(struct.pack("<I", 0x0001))  # Flags

    # Calculate offsets
    header_size = 28
    name_offset = header_size
    const_offset = name_offset + 4 + 4  # length + "test"
    func_offset = const_offset + 4 + len(chunk.constants) * 9  # count + constants
    inst_offset = func_offset + 4  # empty function table

    # Write offsets
    buffer.write(struct.pack("<I", name_offset))
    buffer.write(struct.pack("<I", const_offset))
    buffer.write(struct.pack("<I", func_offset))
    buffer.write(struct.pack("<I", inst_offset))

    # Module name
    buffer.write(struct.pack("<I", 4))
    buffer.write(b"test")

    # Constants
    buffer.write(struct.pack("<I", len(chunk.constants)))
    for tag, value in chunk.constants:
        buffer.write(struct.pack("<B", tag))
        if tag == ConstantTag.INT:
            buffer.write(struct.pack("<q", value))

    # Function table (empty)
    buffer.write(struct.pack("<I", 0))

    # Instructions - parse and write individually
    inst_count = 0
    inst_buffer = BytesIO()
    i = 0
    while i < len(chunk.bytecode):
        opcode = chunk.bytecode[i]
        if opcode in [0, 2, 3]:  # LoadConstR, LoadGlobalR, StoreGlobalR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 4]))
            i += 4
        elif opcode in [1, 12, 13]:  # MoveR, NegR, NotR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 3]))
            i += 3
        elif opcode in [7, 8, 9, 10, 11]:  # Arithmetic
            inst_buffer.write(bytes(chunk.bytecode[i : i + 4]))
            i += 4
        elif opcode == 26:  # ReturnR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 3]))
            i += 3
        elif opcode in [34, 35]:  # ArrayGetR, ArraySetR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 4]))
            i += 4
        elif opcode in [33, 36]:  # NewArrayR, ArrayLenR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 3]))
            i += 3
        else:
            inst_buffer.write(bytes([chunk.bytecode[i]]))
            i += 1
        inst_count += 1

    buffer.write(struct.pack("<I", inst_count))
    buffer.write(inst_buffer.getvalue())

    bytecode_data = buffer.getvalue()

    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
        f.write(bytecode_data)
        bytecode_path = f.name

    try:
        # Load and execute in VM
        vm = machine_dialect_vm.RustVM()
        vm.set_debug(True)  # Enable debug mode
        vm.load_bytecode(bytecode_path)
        result = vm.execute()

        # Check result
        assert result == 30, f"Expected 30, got {result}"
        print("✓ Manual bytecode test passed")

    finally:
        # Clean up
        Path(bytecode_path).unlink()


def test_array_operations() -> None:
    """Test array operations in the VM."""
    # Create bytecode for array operations
    module = BytecodeModule("test")

    chunk = Chunk(
        name="main",
        chunk_type=ChunkType.MAIN,
        bytecode=bytearray(),
        constants=[(ConstantTag.INT, 3), (ConstantTag.INT, 0), (ConstantTag.INT, 42)],
        num_locals=5,
        num_params=0,
    )

    bytecode = bytearray()

    # r0 = 3 (array size)
    bytecode.append(Opcode.LOAD_CONST_R)
    bytecode.append(0)  # dst: r0
    bytecode.extend(b"\x00\x00")  # const_idx: 0 (value: 3)

    # r1 = new_array(r0)
    bytecode.append(Opcode.NEW_ARRAY_R)
    bytecode.append(1)  # dst: r1
    bytecode.append(0)  # size: r0

    # r2 = 0 (index)
    bytecode.append(Opcode.LOAD_CONST_R)
    bytecode.append(2)  # dst: r2
    bytecode.extend(b"\x01\x00")  # const_idx: 1 (value: 0)

    # r3 = 42 (value to store)
    bytecode.append(Opcode.LOAD_CONST_R)
    bytecode.append(3)  # dst: r3
    bytecode.extend(b"\x02\x00")  # const_idx: 2 (value: 42)

    # array[r2] = r3
    bytecode.append(Opcode.ARRAY_SET_R)
    bytecode.append(1)  # array: r1
    bytecode.append(2)  # index: r2
    bytecode.append(3)  # value: r3

    # r4 = array[r2]
    bytecode.append(Opcode.ARRAY_GET_R)
    bytecode.append(4)  # dst: r4
    bytecode.append(1)  # array: r1
    bytecode.append(2)  # index: r2

    # return r4
    bytecode.append(Opcode.RETURN_R)
    bytecode.append(1)  # has_value: true
    bytecode.append(4)  # src: r4

    chunk.bytecode = bytecode
    module.add_chunk(chunk)

    # Manually serialize in the format expected by the Rust VM
    import struct
    from io import BytesIO

    buffer = BytesIO()

    # Header
    buffer.write(b"MDBC")  # Magic
    buffer.write(struct.pack("<I", 1))  # Version
    buffer.write(struct.pack("<I", 0x0001))  # Flags

    # Calculate offsets
    header_size = 28
    name_offset = header_size
    const_offset = name_offset + 4 + 4  # length + "test"
    func_offset = const_offset + 4 + len(chunk.constants) * 9  # count + constants
    inst_offset = func_offset + 4  # empty function table

    # Write offsets
    buffer.write(struct.pack("<I", name_offset))
    buffer.write(struct.pack("<I", const_offset))
    buffer.write(struct.pack("<I", func_offset))
    buffer.write(struct.pack("<I", inst_offset))

    # Module name
    buffer.write(struct.pack("<I", 4))
    buffer.write(b"test")

    # Constants
    buffer.write(struct.pack("<I", len(chunk.constants)))
    for tag, value in chunk.constants:
        buffer.write(struct.pack("<B", tag))
        if tag == ConstantTag.INT:
            buffer.write(struct.pack("<q", value))

    # Function table (empty)
    buffer.write(struct.pack("<I", 0))

    # Instructions - parse and write individually
    inst_count = 0
    inst_buffer = BytesIO()
    i = 0
    while i < len(chunk.bytecode):
        opcode = chunk.bytecode[i]
        if opcode in [0, 2, 3]:  # LoadConstR, LoadGlobalR, StoreGlobalR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 4]))
            i += 4
        elif opcode in [1, 12, 13]:  # MoveR, NegR, NotR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 3]))
            i += 3
        elif opcode in [7, 8, 9, 10, 11]:  # Arithmetic
            inst_buffer.write(bytes(chunk.bytecode[i : i + 4]))
            i += 4
        elif opcode == 26:  # ReturnR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 3]))
            i += 3
        elif opcode in [34, 35]:  # ArrayGetR, ArraySetR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 4]))
            i += 4
        elif opcode in [33, 36]:  # NewArrayR, ArrayLenR
            inst_buffer.write(bytes(chunk.bytecode[i : i + 3]))
            i += 3
        else:
            inst_buffer.write(bytes([chunk.bytecode[i]]))
            i += 1
        inst_count += 1

    buffer.write(struct.pack("<I", inst_count))
    buffer.write(inst_buffer.getvalue())

    bytecode_data = buffer.getvalue()

    # Write to temporary file
    with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
        f.write(bytecode_data)
        bytecode_path = f.name

    try:
        # Load and execute in VM
        vm = machine_dialect_vm.RustVM()
        vm.load_bytecode(bytecode_path)
        result = vm.execute()

        # Check result
        assert result == 42, f"Expected 42, got {result}"
        print("✓ Array operations test passed")

    finally:
        # Clean up
        Path(bytecode_path).unlink()


if __name__ == "__main__":
    test_manual_bytecode()
    test_array_operations()
    # test_simple_arithmetic()  # This requires full MIR support
    print("\n✅ All VM integration tests passed!")
