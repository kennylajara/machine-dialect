# Machine Dialect™ Rust VM

High-performance register-based virtual machine for executing Machine Dialect™ bytecode.

## Overview

This is the Phase 0 implementation of the Machine Dialect™ Rust VM, providing:

- 256 general-purpose registers
- Type-safe value system (Empty, Bool, Int, Float, String, Function, URL)
- Register-based instruction set
- MIR support (SSA phi nodes, assertions, scopes)
- Runtime operations (arithmetic, logic, comparisons, strings)
- PyO3 bindings for Python integration
- Reference counting memory management

## Building

### Prerequisites

- Rust 1.70+
- Python 3.9+
- maturin (install via `uv sync --all-groups`)

### Build Instructions

From project root:

```bash
./build_vm.sh
```

Or manually:

```bash
cd machine_dialect_vm
maturin develop --features pyo3
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

Measured performance (via Criterion benchmarks):

- Simple addition: ~1.02 µs per operation
- VM creation: ~3.49 µs
- Target: 5-10x speedup over Python interpreter

Run benchmarks:

```bash
cargo bench --bench basic_benchmark
```

## Status

Phase 0 (MVP) implementation **92% complete**:

### Completed ✅

- Core VM engine with 256 registers
- Full value and type system (including arrays)
- Complete instruction set (38 opcodes)
- All runtime operations (arithmetic, logic, string, array)
- Binary bytecode loader (.mdbc format)
- PyO3 bindings with Python integration
- Python bytecode generator and serializer
- Performance benchmarks
- REPL integration (with fallback)

### Remaining Work

- End-to-end execution validation
- Expanded test coverage
- Production hardening

## Next Steps

Phase 1 will add:

- Type-specialized instructions
- Advanced memory management
- Performance optimizations
- Collection types (arrays, maps, sets)
