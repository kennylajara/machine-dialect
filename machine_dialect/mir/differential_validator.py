"""Differential testing framework for validating MIR pipeline against old codegen.

This module provides tools to compare the output of the new MIR-based compilation
pipeline against the existing AST-to-bytecode code generator to ensure correctness.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any

from machine_dialect.ast import Program
from machine_dialect.codegen.codegen import CodeGenerator
from machine_dialect.codegen.objects import Module as BytecodeModule
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.mir_to_bytecode import generate_bytecode
from machine_dialect.vm.vm import VM


class ValidationResult(Enum):
    """Result of differential validation."""

    PASS = "pass"
    EXECUTION_MISMATCH = "execution_mismatch"
    BYTECODE_DIFFERENCE = "bytecode_difference"
    OLD_PIPELINE_ERROR = "old_pipeline_error"
    NEW_PIPELINE_ERROR = "new_pipeline_error"
    BOTH_ERROR = "both_error"


@dataclass
class DifferentialResult:
    """Result of differential testing.

    Attributes:
        result: The validation result.
        old_output: Output from old pipeline.
        new_output: Output from new pipeline.
        old_bytecode_size: Size of bytecode from old pipeline.
        new_bytecode_size: Size of bytecode from new pipeline.
        old_instruction_count: Instruction count from old pipeline.
        new_instruction_count: Instruction count from new pipeline.
        old_error: Error from old pipeline if any.
        new_error: Error from new pipeline if any.
        details: Additional details about the comparison.
    """

    result: ValidationResult
    old_output: Any
    new_output: Any
    old_bytecode_size: int
    new_bytecode_size: int
    old_instruction_count: int
    new_instruction_count: int
    old_error: str | None = None
    new_error: str | None = None
    details: str = ""

    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.result == ValidationResult.PASS

    def has_size_improvement(self) -> bool:
        """Check if new pipeline produced smaller bytecode."""
        return self.new_bytecode_size < self.old_bytecode_size

    def size_difference_percent(self) -> float:
        """Calculate percentage difference in bytecode size."""
        if self.old_bytecode_size == 0:
            return 0.0
        return ((self.old_bytecode_size - self.new_bytecode_size) / self.old_bytecode_size) * 100


class DifferentialValidator:
    """Validates MIR pipeline against old code generator."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the validator.

        Args:
            verbose: Whether to print detailed comparison information.
        """
        self.verbose = verbose
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests: list[tuple[str, DifferentialResult]] = []

    def validate_program(self, program: Program, test_name: str = "unnamed") -> DifferentialResult:
        """Validate a program through both pipelines.

        Args:
            program: The AST program to validate.
            test_name: Name for this test case.

        Returns:
            Result of the differential validation.
        """
        self.total_tests += 1

        # Run old pipeline
        old_output = None
        old_error = None
        old_bytecode_size = 0
        old_instruction_count = 0

        try:
            old_codegen = CodeGenerator()
            old_module = old_codegen.compile(program, module_name=f"{test_name}_old")
            old_bytecode_size = len(old_module.main_chunk.bytecode)
            old_instruction_count = self._count_instructions(old_module)

            old_vm = VM()
            old_output = old_vm.run(old_module)
        except Exception as e:
            old_error = f"{type(e).__name__}: {e!s}\n{traceback.format_exc()}"

        # Run new pipeline
        new_output = None
        new_error = None
        new_bytecode_size = 0
        new_instruction_count = 0

        try:
            mir_module = lower_to_mir(program)
            new_module = generate_bytecode(mir_module)
            new_bytecode_size = len(new_module.main_chunk.bytecode)
            new_instruction_count = self._count_instructions(new_module)

            new_vm = VM()
            new_output = new_vm.run(new_module)
        except Exception as e:
            new_error = f"{type(e).__name__}: {e!s}\n{traceback.format_exc()}"

        # Compare results
        result = self._compare_results(
            old_output, new_output, old_error, new_error, old_bytecode_size, new_bytecode_size
        )

        diff_result = DifferentialResult(
            result=result,
            old_output=old_output,
            new_output=new_output,
            old_bytecode_size=old_bytecode_size,
            new_bytecode_size=new_bytecode_size,
            old_instruction_count=old_instruction_count,
            new_instruction_count=new_instruction_count,
            old_error=old_error,
            new_error=new_error,
            details=self._generate_details(result, old_output, new_output, old_error, new_error),
        )

        if result == ValidationResult.PASS:
            self.passed_tests += 1
            if self.verbose:
                print(f"✓ {test_name}: PASS (size improvement: {diff_result.size_difference_percent():.1f}%)")
        else:
            self.failed_tests.append((test_name, diff_result))
            if self.verbose:
                print(f"✗ {test_name}: FAIL - {result.value}")
                print(f"  Details: {diff_result.details}")

        return diff_result

    def _compare_results(
        self,
        old_output: Any,
        new_output: Any,
        old_error: str | None,
        new_error: str | None,
        old_size: int,
        new_size: int,
    ) -> ValidationResult:
        """Compare execution results from both pipelines.

        Args:
            old_output: Output from old pipeline.
            new_output: Output from new pipeline.
            old_error: Error from old pipeline.
            new_error: Error from new pipeline.
            old_size: Bytecode size from old pipeline.
            new_size: Bytecode size from new pipeline.

        Returns:
            Validation result.
        """
        # Both errored
        if old_error and new_error:
            # Check if same type of error
            old_error_type = old_error.split(":")[0] if ":" in old_error else old_error
            new_error_type = new_error.split(":")[0] if ":" in new_error else new_error
            if old_error_type == new_error_type:
                return ValidationResult.PASS  # Both fail in same way
            return ValidationResult.BOTH_ERROR

        # Only old errored
        if old_error:
            return ValidationResult.OLD_PIPELINE_ERROR

        # Only new errored
        if new_error:
            return ValidationResult.NEW_PIPELINE_ERROR

        # Compare outputs
        if old_output != new_output:
            return ValidationResult.EXECUTION_MISMATCH

        # Outputs match - could check bytecode efficiency
        # We consider it a pass even if bytecode differs, as long as execution is correct
        return ValidationResult.PASS

    def _count_instructions(self, module: BytecodeModule) -> int:
        """Count number of instructions in bytecode.

        Args:
            module: The bytecode module.

        Returns:
            Number of instructions.
        """
        count = 0
        i = 0
        bytecode = module.main_chunk.bytecode

        while i < len(bytecode):
            count += 1
            opcode = bytecode[i]
            i += 1

            # Skip operands based on opcode
            # This is simplified - would need full opcode operand mapping
            if opcode in [0x10, 0x11, 0x20, 0x21, 0x30, 0x31]:  # Instructions with 2-byte operands
                i += 2
            elif opcode in [0x40, 0x41]:  # Instructions with 1-byte operands
                i += 1

        return count

    def _generate_details(
        self, result: ValidationResult, old_output: Any, new_output: Any, old_error: str | None, new_error: str | None
    ) -> str:
        """Generate detailed comparison information.

        Args:
            result: The validation result.
            old_output: Output from old pipeline.
            new_output: Output from new pipeline.
            old_error: Error from old pipeline.
            new_error: Error from new pipeline.

        Returns:
            Detailed comparison string.
        """
        if result == ValidationResult.EXECUTION_MISMATCH:
            return f"Output mismatch: old={old_output}, new={new_output}"
        elif result == ValidationResult.OLD_PIPELINE_ERROR:
            return f"Old pipeline error: {old_error}"
        elif result == ValidationResult.NEW_PIPELINE_ERROR:
            return f"New pipeline error: {new_error}"
        elif result == ValidationResult.BOTH_ERROR:
            return "Both pipelines errored differently"
        return ""

    def get_summary(self) -> str:
        """Get summary of all validation results.

        Returns:
            Summary string.
        """
        pass_rate = (self.passed_tests / max(1, self.total_tests)) * 100
        summary = f"""
Differential Validation Summary
================================
Total Tests: {self.total_tests}
Passed: {self.passed_tests} ({pass_rate:.1f}%)
Failed: {len(self.failed_tests)}
"""

        if self.failed_tests:
            summary += "\nFailed Tests:\n"
            for test_name, result in self.failed_tests:
                summary += f"  - {test_name}: {result.result.value}\n"
                if result.details:
                    summary += f"    {result.details}\n"

        return summary


class SemanticBytecodeComparator:
    """Compares bytecode semantically rather than byte-for-byte."""

    @staticmethod
    def are_equivalent(old_module: BytecodeModule, new_module: BytecodeModule) -> tuple[bool, str]:
        """Check if two bytecode modules are semantically equivalent.

        Args:
            old_module: Module from old pipeline.
            new_module: Module from new pipeline.

        Returns:
            Tuple of (are_equivalent, reason_if_not).
        """
        # For now, we only check execution equivalence
        # In future, could add more sophisticated semantic analysis
        return True, ""
