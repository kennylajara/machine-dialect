"""Compilation context module.

This module manages the state and context throughout the compilation process.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from machine_dialect.ast.ast_node import ASTNode
from machine_dialect.codegen.bytecode_module import BytecodeModule
from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.profiling.profile_data import ProfileData
from machine_dialect.mir.reporting.optimization_reporter import OptimizationReporter


@dataclass
class CompilationContext:
    """Context for a single compilation session.

    Attributes:
        source_path: Path to source file being compiled.
        config: Compiler configuration.
        source_content: Source file content.
        ast: Abstract syntax tree.
        mir_module: MIR module.
        bytecode_module: Bytecode module.
        optimization_reporter: Optimization statistics reporter.
        profile_data: Profile data for PGO.
        errors: List of compilation errors.
        warnings: List of compilation warnings.
        metadata: Additional compilation metadata.
    """

    source_path: Path
    config: CompilerConfig
    source_content: str = ""
    ast: ASTNode | None = None
    mir_module: MIRModule | None = None
    bytecode_module: BytecodeModule | None = None
    optimization_reporter: OptimizationReporter | None = None
    profile_data: ProfileData | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        """Add a compilation error.

        Args:
            message: Error message.
        """
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a compilation warning.

        Args:
            message: Warning message.
        """
        self.warnings.append(message)

    def has_errors(self) -> bool:
        """Check if compilation has errors.

        Returns:
            True if there are errors.
        """
        return len(self.errors) > 0

    def get_module_name(self) -> str:
        """Get the module name for compilation.

        Returns:
            Module name.
        """
        if self.config.module_name:
            return self.config.module_name
        return self.source_path.stem

    def get_output_path(self) -> Path:
        """Get the output path for compiled module.

        Returns:
            Output file path.
        """
        if self.config.output_path:
            return self.config.output_path
        return self.source_path.with_suffix(".mdbc")

    def should_optimize(self) -> bool:
        """Check if optimization should be performed.

        Returns:
            True if optimization is enabled.
        """
        from machine_dialect.compiler.config import OptimizationLevel

        return self.config.optimization_level > OptimizationLevel.NONE

    def should_dump_mir(self) -> bool:
        """Check if MIR should be dumped.

        Returns:
            True if MIR dumping is enabled.
        """
        return self.config.dump_mir or self.config.mir_phase_only

    def should_generate_bytecode(self) -> bool:
        """Check if bytecode generation should proceed.

        Returns:
            True if bytecode should be generated.
        """
        return not self.config.mir_phase_only

    def print_errors_and_warnings(self) -> None:
        """Print compilation errors and warnings."""
        for warning in self.warnings:
            print(f"Warning: {warning}")

        for error in self.errors:
            print(f"Error: {error}", file=__import__("sys").stderr)

    def get_statistics(self) -> dict[str, Any]:
        """Get compilation statistics.

        Returns:
            Dictionary of compilation statistics.
        """
        stats = {
            "source_file": str(self.source_path),
            "module_name": self.get_module_name(),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }

        if self.mir_module:
            stats["mir_functions"] = len(self.mir_module.functions)
            stats["mir_globals"] = len(self.mir_module.globals)

        if self.optimization_reporter:
            stats["optimizations"] = self.optimization_reporter.generate_summary()

        if self.bytecode_module:
            stats["bytecode_chunks"] = len(self.bytecode_module.chunks)

        return stats
