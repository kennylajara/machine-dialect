"""Code generation phase of compilation.

This module handles the bytecode generation phase of compilation.
"""

from machine_dialect.codegen.objects import Module as BytecodeModule
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_to_bytecode import generate_bytecode
from machine_dialect.mir.optimizations.peephole_optimizer import PeepholeOptimizer


class CodeGenerationPhase:
    """Bytecode generation phase."""

    def run(self, context: CompilationContext, mir_module: MIRModule) -> BytecodeModule | None:
        """Run code generation phase.

        Args:
            context: Compilation context.
            mir_module: MIR module to generate code from.

        Returns:
            Bytecode module or None if generation failed.
        """
        if context.config.verbose:
            print("Generating bytecode from MIR...")

        try:
            # Generate bytecode from MIR
            bytecode_module = generate_bytecode(mir_module)

            if context.config.verbose:
                chunk_count = 1 + len(bytecode_module.functions)
                print(f"Generated {chunk_count} bytecode chunks")

            # Apply peephole optimization to bytecode if enabled
            if context.should_optimize():
                self._apply_peephole_optimization(bytecode_module, context)

            return bytecode_module

        except Exception as e:
            context.add_error(f"Bytecode generation error: {e}")
            return None

    def _apply_peephole_optimization(
        self,
        module: BytecodeModule,
        context: CompilationContext,
    ) -> None:
        """Apply peephole optimization to bytecode.

        Args:
            module: Bytecode module.
            context: Compilation context.
        """
        if context.config.verbose:
            print("Applying peephole optimization to bytecode...")

        optimizer = PeepholeOptimizer()

        # Optimize main chunk
        module.main_chunk = optimizer.optimize_chunk(module.main_chunk)

        # Optimize function chunks
        for name, chunk in module.functions.items():
            module.functions[name] = optimizer.optimize_chunk(chunk)

        stats = optimizer.get_statistics()
        if context.config.verbose and stats["patterns_applied"] > 0:
            print(
                f"Peephole optimization: {stats['patterns_applied']} patterns applied, "
                f"{stats['bytes_saved']} bytes saved"
            )
