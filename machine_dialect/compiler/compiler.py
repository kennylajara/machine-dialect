"""Main compiler module.

This module provides the main Compiler class that manages the entire
compilation process.
"""

from pathlib import Path

from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.pipeline import CompilationPipeline


class Compiler:
    """Main compiler class for Machine Dialect™.

    Manages the entire compilation process from source files to bytecode,
    including lexing, parsing, HIR/MIR generation, optimization, and
    bytecode generation.

    Attributes:
        config: Compiler configuration settings.
        pipeline: Compilation pipeline instance.
    """

    def __init__(self, config: CompilerConfig | None = None) -> None:
        """Initialize the compiler.

        Args:
            config: Compiler configuration.
        """
        self.config = config or CompilerConfig()
        self.pipeline = CompilationPipeline(self.config)

    def compile_file(
        self,
        source_path: str | Path,
        output_path: str | Path | None = None,
    ) -> bool:
        """Compile a Machine Dialect™ source file to bytecode.

        Args:
            source_path: Path to the .md source file to compile.
            output_path: Optional output path for compiled bytecode.
                If not provided, uses config default or derives from source.

        Returns:
            True if compilation succeeded without errors.

        Raises:
            FileNotFoundError: If source file doesn't exist.
            PermissionError: If unable to write output file.
        """
        source_path = Path(source_path)

        # Update output path in config if provided
        if output_path:
            self.config.output_path = Path(output_path)

        # Run compilation pipeline
        context = self.pipeline.compile_file(source_path)

        # Print errors and warnings
        context.print_errors_and_warnings()

        # Check for errors
        if context.has_errors():
            return False

        # Save compiled module if bytecode was generated
        if context.bytecode_module and not self.config.mir_phase_only:
            success = self._save_module(context)
            if not success:
                return False

        # Show disassembly if requested
        if self.config.verbose and context.bytecode_module:
            self._show_disassembly(context)

        # Print success message (but not for MIR-only mode)
        if not self.config.mir_phase_only:
            if self.config.verbose:
                self._print_success(context)
            else:
                # Always print basic success message
                output_path = context.get_output_path()
                print(f"Successfully compiled to '{output_path}'")

        return True

    def compile_string(self, source: str, module_name: str = "__main__") -> CompilationContext:
        """Compile a string of source code.

        Args:
            source: Source code string.
            module_name: Name for the module.

        Returns:
            Compilation context with results.
        """
        # Create a context with dummy source path
        context = CompilationContext(
            source_path=Path("<string>"),
            config=self.config,
            source_content=source,
        )

        # Set module name
        self.config.module_name = module_name

        # Run compilation pipeline
        return self.pipeline.compile(context)

    def _save_module(self, context: CompilationContext) -> bool:
        """Save compiled bytecode module to disk.

        Args:
            context: Compilation context containing bytecode module.

        Returns:
            True if save succeeded, False otherwise.

        Note:
            Errors during save are added to the compilation context.
        """
        if not context.bytecode_module:
            return False

        output_path = context.get_output_path()

        try:
            # Set module name
            context.bytecode_module.name = context.get_module_name()

            # Serialize and save using VM serializer
            bytecode_data = context.bytecode_module.serialize()
            with open(output_path, "wb") as f:
                f.write(bytecode_data)

            if self.config.verbose:
                print(f"Wrote compiled module to {output_path}")

            return True

        except Exception as e:
            context.add_error(f"Failed to save module: {e}")
            return False

    def _show_disassembly(self, context: CompilationContext) -> None:
        """Display human-readable disassembly of compiled bytecode.

        Args:
            context: Compilation context containing bytecode module.

        Note:
            Currently placeholder - disassembly for register-based
            bytecode is not yet implemented.
        """
        if not context.bytecode_module:
            return

        print("\n=== Disassembly ===")
        # TODO: Implement disassembly for new register-based bytecode
        print("Disassembly not yet implemented for register-based bytecode")

    def _print_success(self, context: CompilationContext) -> None:
        """Print detailed compilation success summary.

        Args:
            context: Compilation context containing statistics and results.

        Note:
            Only called when verbose mode is enabled in config.
        """
        stats = context.get_statistics()

        print("\n=== Compilation Summary ===")
        print(f"Source: {stats['source_file']}")
        print(f"Module: {stats['module_name']}")

        if "mir_functions" in stats:
            print(f"Functions: {stats['mir_functions']}")

        if "optimizations" in stats:
            opt_stats = stats["optimizations"]
            if opt_stats:
                # opt_stats is a string summary, not a dict
                if isinstance(opt_stats, str):
                    # Just show that optimizations were applied
                    print("Optimizations applied")
                elif isinstance(opt_stats, dict):
                    print(f"Optimizations applied: {opt_stats.get('total_transformations', 0)}")

        if "bytecode_chunks" in stats:
            print(f"Bytecode chunks: {stats['bytecode_chunks']}")

        print("Compilation successful!")
