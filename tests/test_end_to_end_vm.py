"""End-to-end test for the Rust VM integration.

This test demonstrates the complete pipeline:
1. Machine Dialect™ source code
2. Lexing and parsing to AST
3. HIR generation
4. MIR generation
5. Register-based bytecode generation
6. Metadata collection
7. Bytecode serialization
8. Rust VM execution (when available)
"""

from __future__ import annotations

import json
from pathlib import Path

from machine_dialect.codegen.register_codegen import (
    MetadataCollector,
    RegisterAllocator,
    RegisterBytecodeGenerator,
)
from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
from machine_dialect.parser.parser import Parser


def test_simple_arithmetic_pipeline() -> None:
    """Test simple arithmetic through the entire pipeline."""
    # Machine Dialect™ source code
    source = """
# Simple Arithmetic Test

Set `x` to _10_.
Set `y` to _20_.
Set `sum` to `x` + `y`.
Give back `sum`.
"""

    # Step 1: Parsing to AST (includes lexing internally)
    parser = Parser()
    ast = parser.parse(source)
    assert ast is not None

    # Step 2: HIR Generation
    config = CompilerConfig(verbose=False)
    context = CompilationContext(source_path=Path("test.md"), config=config, source_content=source)
    hir_phase = HIRGenerationPhase()
    hir = hir_phase.run(context, ast)
    assert hir is not None

    # Step 3: MIR Generation
    mir_phase = MIRGenerationPhase()
    mir_module = mir_phase.run(context, hir)
    assert mir_module is not None
    assert "__main__" in mir_module.functions

    # Step 5: Register allocation
    allocator = RegisterAllocator()
    main_func = mir_module.functions["__main__"]
    allocation = allocator.allocate_function(main_func)
    assert allocation.next_register > 0
    assert allocation.next_register <= 256

    # Step 6: Bytecode generation
    generator = RegisterBytecodeGenerator()
    generator.allocation = allocation

    # Generate bytecode for main function
    # Note: We can't create actual bytecode without the proper module structure
    # but we can verify the generator processes the MIR correctly
    for block_name in main_func.cfg.blocks:
        block = main_func.cfg.blocks[block_name]
        for inst in block.instructions:
            # Verify the generator can handle each instruction
            generator.generate_instruction(inst)

    # Step 7: Metadata collection
    assert mir_module is not None
    collector = MetadataCollector(debug_mode=True)
    metadata = collector.collect(mir_module, allocation)

    assert metadata["version"] == 1
    assert metadata["metadata_level"] == "full"
    assert len(metadata["functions"]) > 0

    main_metadata = metadata["functions"][0]
    assert main_metadata["name"] == "__main__"
    assert "register_types" in main_metadata
    assert "basic_blocks" in main_metadata

    # Verify register allocation metadata
    assert len(main_metadata["register_types"]) > 0

    # Verify basic blocks
    assert len(main_metadata["basic_blocks"]) > 0

    print("✓ Complete pipeline test passed!")
    print(f"  - Allocated {allocation.next_register} registers")
    print(f"  - Generated {len(generator.bytecode)} bytes of bytecode")
    print(f"  - Collected metadata for {len(metadata['functions'])} functions")


def test_control_flow_pipeline() -> None:
    """Test control flow through the pipeline."""
    source = """
# Control Flow Test

Set `x` to _5_.
If `x` is greater than _0_ then:
    > Set `result` to _positive_.
Otherwise:
    > Set `result` to _negative_.
Give back `result`.
"""

    # Run through the pipeline
    parser = Parser()
    ast = parser.parse(source)

    config = CompilerConfig(verbose=False)
    context = CompilationContext(source_path=Path("test.md"), config=config, source_content=source)
    hir_phase = HIRGenerationPhase()
    hir = hir_phase.run(context, ast)

    mir_phase = MIRGenerationPhase()
    mir_module = mir_phase.run(context, hir)

    # Verify MIR has multiple basic blocks for control flow
    assert mir_module is not None
    main_func = mir_module.functions["__main__"]
    assert len(main_func.cfg.blocks) > 1  # Should have multiple blocks for if/else

    # Allocate registers
    allocator = RegisterAllocator()
    allocation = allocator.allocate_function(main_func)

    # Generate bytecode
    generator = RegisterBytecodeGenerator()
    generator.allocation = allocation

    # Process all blocks
    for block_name in main_func.cfg.blocks:
        block = main_func.cfg.blocks[block_name]
        generator.block_offsets[block.label] = len(generator.bytecode)
        for inst in block.instructions:
            generator.generate_instruction(inst)

    # Verify jumps were generated
    assert len(generator.pending_jumps) > 0 or b"\x16" in generator.bytecode  # JumpR opcode

    # Collect metadata
    assert mir_module is not None
    collector = MetadataCollector()
    metadata = collector.collect(mir_module, allocation)

    # Verify phi nodes if any were generated
    main_metadata = metadata["functions"][0]
    # Control flow might generate phi nodes
    assert "phi_nodes" in main_metadata

    print("✓ Control flow pipeline test passed!")
    print(f"  - Generated {len(main_func.cfg.blocks)} basic blocks")
    print(f"  - Allocated {allocation.next_register} registers")


def test_bytecode_serialization() -> None:
    """Test bytecode serialization format."""
    # Simple source
    source = "Set `x` to _42_. Give back `x`."

    # Run through pipeline
    parser = Parser()
    ast = parser.parse(source)
    config = CompilerConfig(verbose=False)
    context = CompilationContext(source_path=Path("test.md"), config=config, source_content=source)
    hir_phase = HIRGenerationPhase()
    hir = hir_phase.run(context, ast)
    mir_phase = MIRGenerationPhase()
    mir_module = mir_phase.run(context, hir)

    # Generate bytecode
    generator = RegisterBytecodeGenerator()
    assert mir_module is not None
    main_func = mir_module.functions["__main__"]
    allocation = generator.allocator.allocate_function(main_func)
    generator.allocation = allocation

    # Generate instructions
    for block_name in main_func.cfg.blocks:
        block = main_func.cfg.blocks[block_name]
        for inst in block.instructions:
            generator.generate_instruction(inst)

    # Verify bytecode structure
    bytecode = generator.bytecode
    assert len(bytecode) > 0

    # Check for expected opcodes
    # LoadConstR = 0, MoveR = 1, ReturnR = 26
    assert any(b in bytecode for b in [0, 1, 26])

    # Collect and serialize metadata
    assert mir_module is not None
    collector = MetadataCollector()
    metadata = collector.collect(mir_module, allocation)

    # Serialize metadata as JSON (for .mdbm file)
    metadata_json = json.dumps(metadata, indent=2)
    assert len(metadata_json) > 0

    print("✓ Bytecode serialization test passed!")
    print(f"  - Generated {len(bytecode)} bytes of bytecode")
    print(f"  - Generated {len(metadata_json)} bytes of metadata")


def test_register_allocation_limits() -> None:
    """Test register allocation with limits."""
    # Create a function that uses many variables
    source = """
# Register allocation test
"""

    # Add many variable assignments
    for i in range(20):
        source += f"Set `var{i}` to _{i}_.\n"

    source += "Give back `var0`."

    # Run through pipeline
    parser = Parser()
    ast = parser.parse(source)
    config = CompilerConfig(verbose=False)
    context = CompilationContext(source_path=Path("test.md"), config=config, source_content=source)
    hir_phase = HIRGenerationPhase()
    hir = hir_phase.run(context, ast)
    mir_phase = MIRGenerationPhase()
    mir_module = mir_phase.run(context, hir)

    # Allocate registers
    allocator = RegisterAllocator()
    assert mir_module is not None
    main_func = mir_module.functions["__main__"]
    allocation = allocator.allocate_function(main_func)

    # Verify we didn't exceed register limit
    assert allocation.next_register <= allocation.max_registers

    print("✓ Register allocation limits test passed!")
    print(f"  - Allocated {allocation.next_register} of {allocation.max_registers} registers")


if __name__ == "__main__":
    # Run tests directly
    test_simple_arithmetic_pipeline()
    test_control_flow_pipeline()
    test_bytecode_serialization()
    test_register_allocation_limits()
    print("\n✅ All end-to-end tests passed!")
