"""Bytecode optimization phase.

This module handles bytecode-level optimizations after code generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from machine_dialect.codegen.bytecode_module import BytecodeModule
from machine_dialect.mir.optimizations.jump_threading import JumpThreadingOptimizer

if TYPE_CHECKING:
    from machine_dialect.compiler.context import CompilationContext


class BytecodeOptimizationPhase:
    """Bytecode optimization phase.

    Applies bytecode-level optimizations like jump threading,
    peephole optimization, etc.
    """

    def __init__(self) -> None:
        """Initialize the bytecode optimization phase."""
        self.jump_threading = JumpThreadingOptimizer()

    def run(self, context: CompilationContext, bytecode_module: BytecodeModule) -> BytecodeModule:
        """Run bytecode optimizations.

        Args:
            context: Compilation context.
            bytecode_module: Bytecode module to optimize.

        Returns:
            Optimized bytecode module.
        """
        if not context.should_optimize():
            return bytecode_module

        if context.config.verbose:
            print("Running bytecode optimizations...")

        # Apply jump threading to each chunk
        optimized_chunks = []
        total_stats = {
            "jumps_threaded": 0,
            "blocks_eliminated": 0,
            "jumps_simplified": 0,
            "blocks_merged": 0,
        }

        for chunk in bytecode_module.chunks:
            # Reset optimizer for each chunk
            self.jump_threading = JumpThreadingOptimizer()

            # Optimize the chunk
            optimized_chunk = self.jump_threading.optimize(chunk)
            optimized_chunks.append(optimized_chunk)

            # Accumulate statistics
            stats = self.jump_threading.get_stats()
            for key, value in stats.items():
                total_stats[key] += value

        # Create new module with optimized chunks
        optimized_module = BytecodeModule(bytecode_module.name)
        optimized_module.chunks = optimized_chunks
        optimized_module.function_table = bytecode_module.function_table.copy()
        optimized_module.global_names = bytecode_module.global_names.copy()
        optimized_module.metadata = bytecode_module.metadata.copy()

        # Report optimization results
        if context.config.verbose and any(total_stats.values()):
            print("\n=== Bytecode Optimization Results ===")
            if total_stats["jumps_threaded"] > 0:
                print(f"  Jumps threaded: {total_stats['jumps_threaded']}")
            if total_stats["blocks_eliminated"] > 0:
                print(f"  Dead blocks eliminated: {total_stats['blocks_eliminated']}")
            if total_stats["jumps_simplified"] > 0:
                print(f"  Conditional jumps simplified: {total_stats['jumps_simplified']}")
            if total_stats["blocks_merged"] > 0:
                print(f"  Blocks merged: {total_stats['blocks_merged']}")
            print()

        # Store stats in context for reporting
        if context.optimization_reporter:
            context.optimization_reporter.add_custom_stats("bytecode_optimization", total_stats)

        return optimized_module
