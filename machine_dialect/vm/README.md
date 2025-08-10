# Virtual Machine (VM) Module

## Overview

The **Virtual Machine** module executes the **bytecode** produced by the *Codegen* phase of Machine Dialect.\
It is a **stack-based interpreter** that:

- Reads and decodes bytecode instructions
- Maintains execution state (stack, frames, program counter)
- Manages memory, variables, and function contexts
- Interacts with the host environment for I/O and native functions
- Supports both procedural and class-based modules (class support prepared for future)

> This README assumes you are already familiar with the bytecode structure (see Codegen README).

______________________________________________________________________

## Architecture

### Components

```text
vm/
├── __init__.py          # Public API
├── vm.py                # Main execution loop
├── instructions.py      # Opcode definitions and decoding
├── stack.py             # Stack implementation
├── frame.py             # Call frame and function management
├── objects.py           # Runtime object representations
├── natives.py           # Built-in native functions
├── errors.py            # VM-specific exceptions
└── tests/               # Test suite
```

______________________________________________________________________

## Execution Cycle

The VM's main loop follows the classic **fetch-decode-execute** pattern:

1. **Fetch** → Read the opcode at the program counter (`pc`).
1. **Decode** → Determine the instruction and its immediate operands.
1. **Execute** → Invoke the corresponding instruction handler (e.g., `op_add`, `op_load_const`).
1. **Update** → Advance `pc` or modify it for jumps.

Pseudo-code:

```python
while True:
    opcode = fetch_byte()
    if opcode == LOAD_CONST:
        idx = fetch_u16()
        push(const_pool[idx])
    elif opcode == ADD:
        b = pop()
        a = pop()
        push(a + b)
    elif opcode == RETURN:
        return pop()
```

______________________________________________________________________

## VM State

- **PC (Program Counter)** → Current bytecode position.
- **Stack** → Holds intermediate values and results.
- **Call Frames** → Execution contexts for functions:
  - Current chunk (bytecode)
  - Frame-specific `pc`
  - Local variables table
  - Stack segment
- **Constant Pool** → Shared immutable values (numbers, strings, etc.).
- **Globals** → Dictionary or symbol table for global variables.
- **Native Functions** → Mapping of names to host callables.

______________________________________________________________________

## Stack Model

This VM is **stack-based**, meaning:

- Arithmetic/logical ops pop operands from the top of the stack.
- Function calls push the callee and arguments before `CALL`.
- `RETURN` leaves the return value at the top of the stack.

Example for `2 + 3`:

```text
LOAD_CONST 0    ; 2
LOAD_CONST 1    ; 3
ADD
```

Stack state progression:

```text
[]           # start
[2]          # after LOAD_CONST 0
[2, 3]       # after LOAD_CONST 1
[5]          # after ADD
```

______________________________________________________________________

## Control Flow Execution

- **JUMP** → Adjusts `pc` by a relative offset.
- **JUMP_IF_FALSE** → Pops the stack and jumps if the value is falsy.
- **CALL** → Creates a new call frame for the target function.
- **RETURN** → Destroys the current frame and resumes the caller.

______________________________________________________________________

## Function Calls

### Bytecode Functions

- Stored as `Chunk` objects.
- Parameters are mapped to local variable slots in the frame.

### Native Functions

- Registered in `natives.py`.
- Resolved by name from the constant pool.

Example:

```python
def native_print(*args):
    print(*args)
```

______________________________________________________________________

## Error Handling

Common runtime errors include:

- **StackUnderflow** → Popping from an empty stack.
- **InvalidOpcode** → Encountering an unknown opcode.
- **IndexOutOfRange** → Accessing an invalid constant/variable index.
- **TypeError** → Performing an unsupported operation on given types.

______________________________________________________________________

## Execution Example

Bytecode (annotated):

```text
; consts: [2, 3]
LOAD_CONST 0    ; push 2
LOAD_CONST 1    ; push 3
ADD             ; pop 3, pop 2, push 5
RETURN          ; end with 5 on top of stack
```

Execution:

```python
from machine_dialect.vm import VM
from machine_dialect.codegen.serializer import deserialize_module

# Load compiled module
with open("program.mdc", "rb") as f:
    module = deserialize_module(f)  # Validates magic number

# Execute module
vm = VM()
result = vm.run(module)  # Checks module type (procedural/class)
print(result)  # 5
```

______________________________________________________________________

## Disassembly

The VM includes a **disassembler** utility to convert raw bytecode back into a
human-readable form for debugging.

Example:

```python
from machine_dialect.vm import disassemble

disassemble(chunk)
```

Output:

```text
0000  LOAD_CONST    0 (2)
0003  LOAD_CONST    1 (3)
0006  ADD
0007  RETURN
```

**Benefits of disassembly**:

- Easier debugging of compiler/codegen output
- Helps verify jump targets and operand encoding
- Useful for writing and maintaining tests

Recommended use:

- After compilation, before execution, to validate generated code
- As part of golden tests in the VM or Codegen test suites

______________________________________________________________________

## Testing

### Unit tests

- Arithmetic operations (ADD, SUB, etc.)
- Control flow (JUMP, JUMP_IF_FALSE)
- Function calls (bytecode and native)
- Error handling
- Full program execution
- Disassembler correctness

Run tests:

```bash
pytest vm/tests/ -v
```

______________________________________________________________________

## Extension Guide

- **New Instructions**: Add handler in `vm.py` and opcode in `instructions.py`.
- **New Native Functions**: Register in `natives.py`.
- **Disassembler**: Update formatting rules if new instructions or operand types are added.
- **Optimization**: Consider threaded code, JIT, or inline caching.

______________________________________________________________________

## Relationship with Other Modules

- **Codegen** → Produces the `Module` containing chunks that the VM executes.
- **Serializer** → Handles binary format with magic number validation.
- **AST / Parser** → Used only at compile time.
- **VM** → The final consumer of bytecode, executing the program.

______________________________________________________________________

## Disassembler Implementation

A small **disassembler** makes debugging way easier by turning raw bytecode into a
human‑readable listing with offsets, mnemonics, operands, and (optionally) source locations.

### Goals

- Show **byte offset** of each instruction.
- Decode **mnemonics** and **immediate operands** (u8/u16/i16).
- Resolve indices into **Constant Pool** (pretty‑print strings in quotes, numbers as literals).
- Optionally annotate **line/column** if line info is embedded in the `Chunk`.

### API

```python
from vm.disasm import disassemble_chunk, disassemble_bytes

# Pretty string output
print(disassemble_chunk(chunk))

# Or directly from raw bytes and an ISA table
print(disassemble_bytes(code=b"...", const_pool=[...], lineinfo=...))
```

### Output Format

```text
0000: LOAD_CONST  0         ; 2
0003: LOAD_CONST  1         ; 3
0006: ADD
0007: RETURN
```

If `lineinfo` is available, annotate on the right or above:

```text
# line 1
0000: LOAD_CONST  0         ; 2
# line 1
0003: LOAD_CONST  1         ; 3
# line 1
0006: ADD
# line 1
0007: RETURN
```

### Encoding Rules

- `u8` → read 1 byte (unsigned)
- `u16` → read 2 bytes **little‑endian** (unsigned)
- `i16` → read 2 bytes little‑endian and interpret as **signed** (relative jumps)

### Example Implementation Sketch

```python
# vm/disasm.py
from typing import Iterable, Optional

def read_u8(code: bytes, i: int) -> tuple[int, int]:
    return code[i], i + 1

def read_u16(code: bytes, i: int) -> tuple[int, int]:
    return int.from_bytes(code[i:i+2], "little", signed=False), i + 2

def read_i16(code: bytes, i: int) -> tuple[int, int]:
    return int.from_bytes(code[i:i+2], "little", signed=True), i + 2

def disassemble_bytes(code: bytes, const_pool: list, isa, lineinfo: Optional[dict[int, tuple[int,int]]] = None) -> str:
    """
    `isa` exposes: isa.name(op), isa.operand_kinds(op) -> e.g. ["u16"], ["i16"], []
    `lineinfo` maps byte offsets to (line, col).
    """
    out = []
    i = 0
    while i < len(code):
        if lineinfo and i in lineinfo:
            line, col = lineinfo[i]
            out.append(f"# line {line} col {col}")
        op = code[i]; i += 1
        name = isa.name(op)
        operands = []
        for kind in isa.operand_kinds(op):
            if kind == "u8":
                val, i = read_u8(code, i)
            elif kind == "u16":
                val, i = read_u16(code, i)
            elif kind == "i16":
                val, i = read_i16(code, i)
            else:
                raise ValueError(f"unknown operand kind: {kind}")
            operands.append(val)
        # Pretty-print constants
        suffix = ""
        if name in ("LOAD_CONST", "LOAD_GLOBAL", "STORE_GLOBAL") and operands:
            idx = operands[-1]
            try:
                k = const_pool[idx]
                if isinstance(k, str):
                    suffix = f'    ; "{k}"'
                else:
                    suffix = f"    ; {k}"
            except Exception:
                suffix = "    ; <const out of range>"
        # Emit line
        offset = f"{i - (1 + sum(1 if k=='u8' else 2 for k in isa.operand_kinds(op))):04d}"
        ops = " ".join(str(x) for x in operands)
        pad = " " * (12 - len(name)) if len(name) < 12 else " "
        out.append(f"{offset}: {name}{pad}{ops}{suffix}".rstrip())
    return "\n".join(out)

def disassemble_chunk(chunk) -> str:
    return disassemble_bytes(chunk.code, chunk.const_pool, chunk.isa, getattr(chunk, "lineinfo", None))
```

### CLI

Provide a tiny CLI to inspect compiled artifacts:

```bash
python -m vm.disasm path/to/program.mdkc
# or
python -m vm.disasm --hex 00 01 00 00 02 ...
```

### Tips

- Keep disassembly **pure** (no side effects). It should not need a running VM.
- If you change operand sizes or endianness in the ISA, update the disassembler table.
- For jump targets, you can **annotate** computed absolute destinations, e.g. `JUMP +8  ; -> 0019`.
- Consider adding a `--lines` flag to show/hide source line annotations.
