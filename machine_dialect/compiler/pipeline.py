"""Compilation pipeline module.

This module orchestrates the entire compilation process through its phases.
"""

from pathlib import Path

from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.phases.bytecode_optimization import BytecodeOptimizationPhase
from machine_dialect.compiler.phases.codegen import CodeGenerationPhase
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
from machine_dialect.compiler.phases.optimization import OptimizationPhase
from machine_dialect.compiler.phases.parsing import ParsingPhase
from machine_dialect.mir.mir_dumper import DumpVerbosity, MIRDumper


class CompilationPipeline:
    """Manages the compilation pipeline."""

    def __init__(self, config: CompilerConfig | None = None) -> None:
        """Initialize the compilation pipeline.

        Args:
            config: Compiler configuration.
        """
        self.config = config or CompilerConfig()

        # Initialize phases
        self.parsing_phase = ParsingPhase()
        self.hir_phase = HIRGenerationPhase()
        self.mir_phase = MIRGenerationPhase()
        self.optimization_phase = OptimizationPhase()
        self.codegen_phase = CodeGenerationPhase()
        self.bytecode_optimization_phase = BytecodeOptimizationPhase()

    def compile_file(self, source_path: Path) -> CompilationContext:
        """Compile a source file.

        Args:
            source_path: Path to source file.

        Returns:
            Compilation context with results.
        """
        # Create compilation context
        context = CompilationContext(source_path=source_path, config=self.config)

        # Read source file
        try:
            context.source_content = source_path.read_text()
        except OSError as e:
            context.add_error(f"Failed to read source file: {e}")
            return context

        # Run compilation pipeline
        return self.compile(context)

    def compile(self, context: CompilationContext) -> CompilationContext:
        """Run the compilation pipeline.

        Args:
            context: Compilation context.

        Returns:
            Updated compilation context.
        """
        # Print "Compiling" message if verbose
        if context.config.verbose:
            print(f"Compiling {context.source_path}...")

        # Phase 1: Syntactic Analysis (includes lexical analysis)
        if not context.has_errors():
            ast = self.parsing_phase.run(context)
            if ast:
                context.ast = ast
            else:
                return context
        else:
            return context

        # Phase 2: HIR Generation (Desugaring)
        if not context.has_errors():
            hir = self.hir_phase.run(context, context.ast)
        else:
            return context

        # Phase 3: MIR Generation
        if not context.has_errors():
            mir_module = self.mir_phase.run(context, hir)
            if mir_module:
                context.mir_module = mir_module
            else:
                return context
        else:
            return context

        # Check if we should stop after MIR
        if context.config.mir_phase_only:
            self._dump_final_mir(context)
            print("Stopping after MIR generation (--mir-phase flag)")
            return context

        # Phase 4: Optimization
        if not context.has_errors() and context.should_optimize():
            optimized_mir = self.optimization_phase.run(context, context.mir_module)
            context.mir_module = optimized_mir
        else:
            if context.has_errors():
                return context

        # Phase 5: Code Generation
        if not context.has_errors() and context.should_generate_bytecode():
            bytecode_module = self.codegen_phase.run(context, context.mir_module)
            if bytecode_module:
                context.bytecode_module = bytecode_module
            else:
                return context
        else:
            return context

        # Phase 6: Bytecode Optimization (after code generation)
        if not context.has_errors() and context.bytecode_module and context.should_optimize():
            optimized_bytecode = self.bytecode_optimization_phase.run(context, context.bytecode_module)
            context.bytecode_module = optimized_bytecode

        return context

    def _dump_final_mir(self, context: CompilationContext) -> None:
        """Dump final MIR when stopping at MIR phase.

        Args:
            context: Compilation context.
        """
        if not context.mir_module:
            return

        verbosity = DumpVerbosity.from_string(context.config.mir_dump_verbosity)
        dumper = MIRDumper(verbosity=verbosity, use_color=True)

        print("\n=== Final MIR ===")
        dumper.dump_module(context.mir_module)
