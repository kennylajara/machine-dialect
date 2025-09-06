"""Debug bytecode generation."""

from machine_dialect.codegen.register_codegen import RegisterBytecodeGenerator
from machine_dialect.mir import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import BinaryOp, LoadConst, Return
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_values import Constant, Variable

# Create a simple MIR module with arithmetic
module = MIRModule("test")
func = MIRFunction("main")

# Create a basic block
block = BasicBlock("entry")

# Create variables for the computation
a = Variable("a", "int")
b = Variable("b", "int")
result = Variable("result", "int")

# Add instructions: result = 2 + 3
block.add_instruction(LoadConst(a, Constant(2)))
block.add_instruction(LoadConst(b, Constant(3)))
block.add_instruction(BinaryOp(result, "+", a, b))
block.add_instruction(Return(result))

# Add block to function
func.cfg.add_block(block)
func.cfg.set_entry_block(block)

module.functions["main"] = func

# Generate bytecode
generator = RegisterBytecodeGenerator()

# Debug: show MIR first
print("MIR Instructions:")
for inst in block.instructions:
    print(f"  {inst}")

print("\nGenerating bytecode...")
bytecode_module = generator.generate(module)

print("\nGenerated chunk:")
chunk = bytecode_module.chunks[0]
print(f"  Bytecode ({len(chunk.bytecode)} bytes): {chunk.bytecode.hex()}")

# Parse bytecode manually
print("\nParsed instructions:")
i = 0
inst_num = 0
while i < len(chunk.bytecode):
    opcode = chunk.bytecode[i]
    print(f"  [{inst_num}] @{i:02x}: opcode={opcode:02x}", end=" ")

    if opcode == 0:  # LoadConstR
        dst = chunk.bytecode[i + 1]
        const_idx = chunk.bytecode[i + 2] | (chunk.bytecode[i + 3] << 8)
        print(f"LoadConstR r{dst}, #{const_idx}")
        i += 4
    elif opcode == 1:  # MoveR
        dst = chunk.bytecode[i + 1]
        src = chunk.bytecode[i + 2]
        print(f"MoveR r{dst}, r{src}")
        i += 3
    elif opcode == 7:  # AddR
        dst = chunk.bytecode[i + 1]
        left = chunk.bytecode[i + 2]
        right = chunk.bytecode[i + 3]
        print(f"AddR r{dst}, r{left}, r{right}")
        i += 4
    elif opcode == 26:  # ReturnR
        has_value = chunk.bytecode[i + 1]
        if has_value:
            src = chunk.bytecode[i + 2]
            print(f"ReturnR r{src}")
            i += 3
        else:
            print("ReturnR (no value)")
            i += 2
    else:
        print(f"Unknown opcode {opcode:02x}")
        i += 1
    inst_num += 1

print(f"\nTotal: {inst_num} instructions")
