# Codegen Support Module

## Overview

The **Codegen** module provides supporting structures for bytecode generation in Machine Dialect™.
The actual code generation is now handled by the MIR (Mid-level Intermediate Representation) pipeline.

This module contains:

- Bytecode format definitions (ISA)
- Auxiliary data structures (constants, symbols)
- Serialization/deserialization for compiled modules
- VM object definitions

> **Note**: The AST-to-bytecode compiler has been replaced with a modern MIR-based compilation pipeline:
> AST → HIR → MIR → Optimization → Bytecode

______________________________________________________________________

## Architecture

### Components

```text
codegen/
├── __init__.py           # Module exports
├── isa.py                # Instruction set architecture definition
├── symtab.py             # Symbol table for scope management
├── constpool.py          # Constant pool (deduplication)
├── objects.py            # Compiled artifacts (Chunk, Module)
├── serializer.py         # Binary serialization with magic number validation
└── tests/                # Test suite
```

### Current Usage

These components are used by the MIR-to-bytecode generator located in:

- `machine_dialect/compiler/phases/codegen.py` - Uses MIR to generate bytecode
- `machine_dialect/mir/mir_to_bytecode.py` - Core MIR-to-bytecode transformation

______________________________________________________________________

## ISA (Instruction Set Architecture)

The VM is **stack-based**. Each instruction may have immediate operands (little-endian integers).

### Core Instructions

```text
# Load/store
LOAD_CONST   <u16 idx>        ; Push constant[idx] to stack
LOAD_LOCAL   <u16 slot>       ; Push local[slot]
STORE_LOCAL  <u16 slot>       ; local[slot] = pop()
LOAD_GLOBAL  <u16 idx>        ; Push global with name in const[idx]
STORE_GLOBAL <u16 idx>        ; Assign to global with name in const[idx]

# Arithmetic / logic
ADD, SUB, MUL, DIV, MOD, POW
EQ, NEQ, LT, GT, LTE, GTE
NOT, AND, OR

# Control flow
JUMP        <i16 rel>         ; PC += rel
JUMP_IF_FALSE <i16 rel>       ; jump if pop() is falsy
POP                          ; discard top of stack

# Functions
CALL       <u8 nargs>         ; call target with nargs arguments
RETURN                        ; return (top of stack, or empty)

# Misc
DUP, SWAP, NOP, PRINT, HALT
```

______________________________________________________________________

## Auxiliary Structures

### ConstantPool

- Deduplicates: `int`, `float`, `string`, identifiers, and function refs
- Indexed by insertion order, uses string interning

```python
pool.add(42)         # -> idx 0
pool.add("hello")    # -> idx 1
pool.add("hello")    # -> idx 1 (reused)
```

### SymbolTable and Scopes

- Manages nested scopes (blocks, functions)
- Local variables get consecutive slots (u16)
- Unresolved identifiers are treated as globals

```text
Scope(root)
└── Scope(function foo)
    ├── param x -> slot 0
    └── local y -> slot 1
```

______________________________________________________________________

## Compiled Artifact Format

### Module Structure

```text
Module:
- magic: u32            ; "¾¾Êþ" (BE BE CA FE)
- version: u16          ; format version (0x0001)
- flags: u16            ; endianness flags
- module_type: u8       ; 0=PROCEDURAL, 1=CLASS
- name: string          ; module name
- main_chunk: Chunk     ; main execution chunk
- functions: [Chunk]    ; function definitions
- metadata: dict        ; additional metadata
```

### Chunk Structure

```text
Chunk:
- chunk_type: u8        ; MAIN, FUNCTION, METHOD, etc.
- name: string          ; chunk name
- const_pool: [Const]   ; constants
- code: [u8]            ; bytecode
- num_locals: u16       ; local variable count
- num_params: u8        ; parameter count
```

______________________________________________________________________

## Serialization

The serializer provides binary format support for compiled modules:

```python
from machine_dialect.codegen.serializer import serialize_module, deserialize_module

# Serialize to binary format
with open("output.mdc", "wb") as f:
    serialize_module(module, f)

# Deserialize from binary format
with open("output.mdc", "rb") as f:
    module = deserialize_module(f)
```

______________________________________________________________________

## MIR-Based Compilation Pipeline

The modern compilation pipeline uses MIR (Mid-level Intermediate Representation):

1. **Parsing**: Source code → AST
1. **HIR Generation**: AST → HIR (desugaring)
1. **MIR Generation**: HIR → MIR (SSA form)
1. **Optimization**: Multiple optimization passes on MIR
1. **Bytecode Generation**: MIR → Bytecode using structures from this module

For details on the MIR pipeline, see:

- `machine_dialect/compiler/` - Compilation pipeline orchestration
- `machine_dialect/mir/` - MIR generation and optimization

______________________________________________________________________

## Testing

### Unit tests

```bash
pytest machine_dialect/codegen/tests/ -v
```

Tests cover:

- Constant pool deduplication
- Symbol table management
- Serialization/deserialization
- ISA encoding/decoding

______________________________________________________________________

## Relationship with Other Modules

- **MIR**: Uses these structures for final bytecode generation
- **VM**: Consumes the bytecode and executes it
- **Compiler**: Orchestrates the full compilation pipeline

______________________________________________________________________

## Migration Notice

The direct AST-to-bytecode compiler (`CodeGenerator`) has been removed in favor of the MIR
pipeline. This provides:

- Better optimization opportunities
- Clearer separation of concerns
- More maintainable architecture
- Foundation for future JIT compilation
