"""Register-based code generation phase.

This module handles the register-based bytecode generation for the new Rust VM.
"""

from machine_dialect.codegen.bytecode_module import BytecodeModule
from machine_dialect.codegen.register_codegen import RegisterBytecodeGenerator
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.mir.mir_module import MIRModule


class CodeGenerationPhase:
    """Register-based bytecode generation phase."""

    def run(self, context: CompilationContext, mir_module: MIRModule) -> BytecodeModule | None:
        """Run code generation phase.

        Args:
            context: Compilation context.
            mir_module: MIR module to generate code from.

        Returns:
            Bytecode module or None if generation failed.
        """
        try:
            # Create bytecode generator with debug if verbose mode is on
            debug = context.config.verbose if context.config else False
            generator = RegisterBytecodeGenerator(debug=debug)

            # Generate bytecode from MIR
            bytecode_module = generator.generate(mir_module)

            # Store in context
            context.bytecode_module = bytecode_module

            return bytecode_module

        except Exception as e:
            context.add_error(f"Code generation failed: {e}")
            return None
