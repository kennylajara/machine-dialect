"""Simple VM test to verify basic functionality."""

import struct
import tempfile
from pathlib import Path

import machine_dialect_vm

# Create minimal bytecode that just returns 42
bytecode = bytearray()

# Magic number "MDBC"
bytecode.extend(b"MDBC")

# Version (1)
bytecode.extend(struct.pack("<I", 1))

# Flags (little-endian)
bytecode.extend(struct.pack("<I", 0x0001))

# Calculate offsets
header_size = 28  # magic(4) + version(4) + flags(4) + 4 offsets(16)
name_offset = header_size
const_offset = name_offset + 8  # 4 (length) + 4 ("main")
func_offset = const_offset + 13  # 4 (count) + 1 (tag) + 8 (value for int 42)
inst_offset = func_offset + 4  # 4 (count=0, no functions)

# Offsets
bytecode.extend(struct.pack("<I", name_offset))  # Name offset
bytecode.extend(struct.pack("<I", const_offset))  # Constant offset
bytecode.extend(struct.pack("<I", func_offset))  # Function offset
bytecode.extend(struct.pack("<I", inst_offset))  # Instruction offset

# Module name section
bytecode.extend(struct.pack("<I", 4))  # Name length
bytecode.extend(b"main")

# Constants section (1 constant: int 42)
bytecode.extend(struct.pack("<I", 1))  # 1 constant
bytecode.extend(struct.pack("<B", 0x01))  # Tag: INT
bytecode.extend(struct.pack("<q", 42))  # Value: 42

# Function table section (empty)
bytecode.extend(struct.pack("<I", 0))  # 0 functions

# Instructions section
bytecode.extend(struct.pack("<I", 2))  # 2 instructions

# LoadConstR r0, 0
bytecode.append(0)  # LOAD_CONST_R
bytecode.append(0)  # dst: r0
bytecode.extend(struct.pack("<H", 0))  # const_idx: 0

# ReturnR r0
bytecode.append(26)  # RETURN_R
bytecode.append(1)  # has_value: true
bytecode.append(0)  # src: r0

# Write to file
with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
    f.write(bytecode)
    bytecode_path = f.name

print(f"Bytecode file: {bytecode_path}")
print(f"Bytecode size: {len(bytecode)} bytes")

# Hex dump for debugging
print("\nBytecode hex dump:")
for i in range(0, len(bytecode), 16):
    hex_str = " ".join(f"{b:02x}" for b in bytecode[i : i + 16])
    ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in bytecode[i : i + 16])
    print(f"{i:04x}: {hex_str:<48} {ascii_str}")

try:
    # Load and execute
    vm = machine_dialect_vm.RustVM()
    vm.set_debug(True)
    print("\nLoading bytecode...")
    vm.load_bytecode(bytecode_path)
    print("Executing...")
    result = vm.execute()
    print(f"Result: {result}")

    if result == 42:
        print("✓ Test passed!")
    else:
        print(f"✗ Test failed: expected 42, got {result}")

finally:
    Path(bytecode_path).unlink()
