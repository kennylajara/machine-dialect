# Machine Dialect Rust VM

High-performance register-based virtual machine for executing Machine Dialect bytecode.

## Overview

This is the Phase 0 implementation of the Machine Dialect Rust VM, providing:

- 256 general-purpose registers
- Type-safe value system (Empty, Bool, Int, Float, String, Function, URL)
- Register-based instruction set
- MIR support (SSA phi nodes, assertions, scopes)
- Runtime operations (arithmetic, logic, comparisons, strings)
- PyO3 bindings for Python integration
- Reference counting memory management

## Building

```bash
cargo build --release
```

## Architecture

The VM uses a register-based architecture with:

- **Register File**: 256 registers with type tracking
- **Instruction Set**: ~40 register-based instructions
- **Value System**: Tagged union for efficient value representation
- **Runtime Operations**: Type-safe arithmetic and string operations
- **Memory Management**: Reference counting for strings and objects

## Integration

The VM integrates with the Python frontend via PyO3 bindings, allowing:

1. Python compiler generates MIR
1. MIR is optimized
1. Register-based bytecode is generated
1. Rust VM executes bytecode
1. Results returned to Python

## Performance

Target performance metrics:

- \< 2ns for basic arithmetic operations
- 5-10x speedup over Python interpreter
- Efficient register allocation from MIR

## Status

Phase 0 (MVP) implementation complete:

- ✅ Core VM engine
- ✅ Value and type system
- ✅ Register file management
- ✅ Instruction set
- ✅ Runtime operations
- ✅ Bytecode loader
- ✅ PyO3 bindings
- ✅ Python bytecode generator

## Next Steps

Phase 1 will add:

- Type-specialized instructions
- Advanced memory management
- Performance optimizations
- Collection types (arrays, maps, sets)
