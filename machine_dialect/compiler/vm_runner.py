"""VM Runner - Manages Rust VM execution for Machine Dialect™.

This module provides the integration layer between the Python compiler
pipeline and the Rust VM for executing Machine Dialect™ programs.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from machine_dialect.codegen.register_codegen import (
    RegisterBytecodeGenerator,
)
from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.optimize_mir import optimize_mir
from machine_dialect.parser.parser import Parser


class VMRunner:
    """Manages compilation and execution of Machine Dialect™ code on the Rust VM.

    This class provides a high-level interface for:
    1. Compiling Machine Dialect™ source to bytecode
    2. Loading bytecode into the Rust VM
    3. Executing programs and returning results
    """

    def __init__(self, debug: bool = False, optimize: bool = False) -> None:
        """Initialize the VM runner.

        Args:
            debug: Enable debug output
            optimize: Enable MIR optimizations
        """
        self.debug = debug
        self.optimize = optimize
        self.vm: Any = None
        self._init_vm()

    def _init_vm(self) -> None:
        """Initialize the Rust VM instance."""
        try:
            import machine_dialect_vm

            self.vm = machine_dialect_vm.RustVM()
            if self.debug:
                self.vm.set_debug(True)
        except ImportError as e:
            raise RuntimeError(
                "Rust VM module not available. Please build it first:\n"
                "  ./build_vm.sh\n"
                "or manually:\n"
                "  cd machine_dialect_vm && maturin develop --features pyo3"
            ) from e

    def compile_to_bytecode(self, source: str, source_path: Path | None = None) -> bytes:
        """Compile Machine Dialect™ source code to bytecode.

        Args:
            source: Machine Dialect™ source code
            source_path: Optional path to source file

        Returns:
            Serialized bytecode ready for VM execution

        Raises:
            CompilationError: If compilation fails at any stage
        """
        if source_path is None:
            source_path = Path("<repl>")

        # Step 1: Parse to AST
        parser = Parser()
        ast = parser.parse(source)
        if ast is None:
            raise ValueError("Failed to parse source code")

        # Step 2: Generate HIR
        config = CompilerConfig(verbose=self.debug)
        context = CompilationContext(source_path=source_path, config=config, source_content=source)
        hir_phase = HIRGenerationPhase()
        hir = hir_phase.run(context, ast)
        if hir is None:
            raise ValueError("Failed to generate HIR")

        # Step 3: Generate MIR
        mir_phase = MIRGenerationPhase()
        mir_module = mir_phase.run(context, hir)
        if mir_module is None:
            raise ValueError("Failed to generate MIR")

        # Step 4: Optimize MIR (if enabled)
        if self.optimize:
            mir_module, _ = optimize_mir(mir_module)

        # Step 5: Generate bytecode
        return self._mir_to_bytecode(mir_module)

    def _mir_to_bytecode(self, mir_module: MIRModule) -> bytes:
        """Convert MIR module to bytecode.

        Args:
            mir_module: The MIR module to convert

        Returns:
            Serialized bytecode
        """
        # Generate bytecode
        generator = RegisterBytecodeGenerator()
        bytecode_module = generator.generate(mir_module)

        # Serialize to bytes
        return bytecode_module.serialize()

    def execute(self, source: str) -> Any:
        """Compile and execute Machine Dialect™ source code.

        Args:
            source: Machine Dialect™ source code

        Returns:
            The result of program execution

        Raises:
            RuntimeError: If execution fails
        """
        # Compile to bytecode
        bytecode = self.compile_to_bytecode(source)

        # Write to temporary file (VM loads from file)
        with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
            f.write(bytecode)
            bytecode_path = f.name

        try:
            # Load and execute in VM
            self.vm.load_bytecode(bytecode_path)
            result = self.vm.execute()
            return result
        finally:
            # Clean up temporary file
            Path(bytecode_path).unlink(missing_ok=True)

    def execute_bytecode(self, bytecode: bytes) -> Any:
        """Execute pre-compiled bytecode.

        Args:
            bytecode: Serialized bytecode

        Returns:
            The result of program execution
        """
        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
            f.write(bytecode)
            bytecode_path = f.name

        try:
            self.vm.load_bytecode(bytecode_path)
            result = self.vm.execute()
            return result
        finally:
            Path(bytecode_path).unlink(missing_ok=True)

    def reset(self) -> None:
        """Reset the VM to initial state."""
        self._init_vm()
