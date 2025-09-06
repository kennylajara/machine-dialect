"""Comprehensive regression detection combining performance and correctness.

This module extends the existing regression detector to include both
performance metrics and functional correctness validation.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from machine_dialect.ast import Program
from machine_dialect.mir.benchmarks.compilation_benchmark import BenchmarkResult
from machine_dialect.mir.benchmarks.regression_detector import (
    RegressionDetector,
    RegressionResult,
    RegressionThresholds,
)
from machine_dialect.mir.hir_to_mir import lower_to_mir
from machine_dialect.mir.mir_to_bytecode import generate_bytecode
from machine_dialect.vm.vm import VM


@dataclass
class CorrectnessResult:
    """Result of correctness validation.

    Attributes:
        test_name: Name of the test.
        program_hash: Hash of the program AST.
        expected_output: Expected execution output.
        actual_output: Actual execution output.
        is_correct: Whether output matches expected.
        error: Any error that occurred.
        details: Additional details.
    """

    test_name: str
    program_hash: str
    expected_output: Any
    actual_output: Any
    is_correct: bool
    error: str | None = None
    details: str = ""


@dataclass
class ComprehensiveRegressionResult:
    """Combined performance and correctness regression result.

    Attributes:
        test_name: Name of the test.
        performance_results: Performance regression results.
        correctness_result: Correctness validation result.
        commit_hash: Git commit hash if available.
        has_regression: Whether any regression was detected.
        has_correctness_issue: Whether output is incorrect.
        has_performance_issue: Whether performance regressed.
    """

    test_name: str
    performance_results: list[RegressionResult]
    correctness_result: CorrectnessResult
    commit_hash: str | None
    has_regression: bool
    has_correctness_issue: bool
    has_performance_issue: bool


class ComprehensiveRegressionDetector(RegressionDetector):
    """Enhanced regression detector with correctness validation."""

    def __init__(
        self,
        baseline_path: Path | None = None,
        thresholds: RegressionThresholds | None = None,
        expected_outputs_path: Path | None = None,
    ) -> None:
        """Initialize comprehensive regression detector.

        Args:
            baseline_path: Path to performance baseline file.
            thresholds: Performance regression thresholds.
            expected_outputs_path: Path to expected outputs file.
        """
        super().__init__(baseline_path, thresholds)
        self.expected_outputs_path = expected_outputs_path or Path("expected_outputs.json")
        self.expected_outputs: dict[str, Any] = {}

        if self.expected_outputs_path.exists():
            self.load_expected_outputs()

    def load_expected_outputs(self) -> None:
        """Load expected outputs from file."""
        with open(self.expected_outputs_path) as f:
            self.expected_outputs = json.load(f)

    def save_expected_outputs(self) -> None:
        """Save expected outputs to file."""
        with open(self.expected_outputs_path, "w") as f:
            json.dump(self.expected_outputs, f, indent=2, default=str)

    def hash_program(self, program: Program) -> str:
        """Generate hash of program AST.

        Args:
            program: The AST program.

        Returns:
            SHA256 hash of program.
        """
        program_str = str(program)
        return hashlib.sha256(program_str.encode()).hexdigest()

    def get_git_commit(self) -> str | None:
        """Get current git commit hash.

        Returns:
            Git commit hash or None.
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def validate_correctness(self, program: Program, test_name: str) -> CorrectnessResult:
        """Validate functional correctness of compilation.

        Args:
            program: The AST program.
            test_name: Name of the test.

        Returns:
            Correctness validation result.
        """
        program_hash = self.hash_program(program)

        # Compile and execute
        try:
            mir_module = lower_to_mir(program)
            bytecode_module = generate_bytecode(mir_module)

            vm = VM()
            actual_output = vm.run(bytecode_module)
            error = None
        except Exception as e:
            actual_output = None
            error = str(e)

        # Get expected output
        expected_key = f"{test_name}_{program_hash[:8]}"
        expected_output = self.expected_outputs.get(expected_key)

        # If no expected output, this is a new test or first run
        if expected_output is None:
            self.expected_outputs[expected_key] = actual_output if error is None else f"ERROR: {error}"
            self.save_expected_outputs()
            expected_output = self.expected_outputs[expected_key]

        # Check correctness
        is_correct = (actual_output == expected_output) if error is None else (f"ERROR: {error}" == expected_output)

        details = ""
        if not is_correct:
            actual_repr = actual_output if error is None else f"ERROR: {error}"
            details = f"Expected: {expected_output!r}, Got: {actual_repr!r}"

        return CorrectnessResult(
            test_name=test_name,
            program_hash=program_hash,
            expected_output=expected_output,
            actual_output=actual_output if error is None else f"ERROR: {error}",
            is_correct=is_correct,
            error=error,
            details=details,
        )

    def comprehensive_check(
        self, program: Program, test_name: str, benchmark_result: BenchmarkResult | None = None
    ) -> ComprehensiveRegressionResult:
        """Perform comprehensive regression check.

        Args:
            program: The AST program.
            test_name: Name of the test.
            benchmark_result: Optional pre-computed benchmark result.

        Returns:
            Comprehensive regression result.
        """
        # Get git commit
        commit_hash = self.get_git_commit()

        # Check correctness
        correctness_result = self.validate_correctness(program, test_name)

        # Check performance if we have baseline and benchmark
        performance_results = []
        if self.baseline and benchmark_result:
            performance_results = self.check_regression(benchmark_result)

        # Determine if we have any issues
        has_correctness_issue = not correctness_result.is_correct
        has_performance_issue = any(r.is_regression for r in performance_results)
        has_regression = has_correctness_issue or has_performance_issue

        return ComprehensiveRegressionResult(
            test_name=test_name,
            performance_results=performance_results,
            correctness_result=correctness_result,
            commit_hash=commit_hash,
            has_regression=has_regression,
            has_correctness_issue=has_correctness_issue,
            has_performance_issue=has_performance_issue,
        )

    def generate_comprehensive_report(self, results: list[ComprehensiveRegressionResult]) -> str:
        """Generate comprehensive regression report.

        Args:
            results: List of comprehensive results.

        Returns:
            Formatted report.
        """
        report = "=" * 60 + "\n"
        report += "COMPREHENSIVE REGRESSION ANALYSIS REPORT\n"
        report += "=" * 60 + "\n\n"

        # Summary
        total = len(results)
        correctness_issues = sum(1 for r in results if r.has_correctness_issue)
        performance_issues = sum(1 for r in results if r.has_performance_issue)

        report += f"Total Tests: {total}\n"
        report += f"Correctness Issues: {correctness_issues}\n"
        report += f"Performance Issues: {performance_issues}\n"

        if results and results[0].commit_hash:
            report += f"Git Commit: {results[0].commit_hash[:8]}\n"

        report += "\n"

        # Critical correctness issues first
        if correctness_issues > 0:
            report += "⚠️  CRITICAL: CORRECTNESS ISSUES DETECTED\n"
            report += "-" * 40 + "\n"
            for result in results:
                if result.has_correctness_issue:
                    report += f"\n❌ {result.test_name}:\n"
                    report += f"   {result.correctness_result.details}\n"

        # Performance regressions
        if performance_issues > 0:
            report += "\n⚠️  PERFORMANCE REGRESSIONS DETECTED\n"
            report += "-" * 40 + "\n"
            for result in results:
                if result.has_performance_issue:
                    report += f"\n{result.test_name}:\n"
                    for perf in result.performance_results:
                        if perf.is_regression:
                            report += f"  ❌ {perf.metric_name}: {perf.percent_change:+.1f}%\n"
                            report += f"     {perf.details}\n"

        # Performance improvements
        improvements = []
        for result in results:
            for perf in result.performance_results:
                if perf.is_improvement:
                    improvements.append((result.test_name, perf))

        if improvements:
            report += "\n✅ PERFORMANCE IMPROVEMENTS\n"
            report += "-" * 40 + "\n"
            for test_name, perf in improvements:
                report += f"{test_name} - {perf.metric_name}: {abs(perf.percent_change):.1f}% faster\n"

        if correctness_issues == 0 and performance_issues == 0:
            report += "\n✅ All tests passed without regression!\n"

        return report


def create_regression_suite() -> dict[str, Program]:
    """Create a standard regression test suite.

    Returns:
        Dictionary of test name to AST program.
    """
    from machine_dialect.ast import (
        BlockStatement,
        Identifier,
        IfStatement,
        InfixExpression,
        Program,
        ReturnStatement,
        SetStatement,
        StringLiteral,
        WholeNumberLiteral,
    )
    from machine_dialect.lexer.tokens import Token, TokenType

    def _token(token_type: TokenType, value: str = "") -> Token:
        return Token(token_type, value, 0, 0)

    def _create_infix(left: Any, op: str, right: Any) -> InfixExpression:
        op_map = {
            "+": TokenType.OP_PLUS,
            "-": TokenType.OP_MINUS,
            "*": TokenType.OP_STAR,
            "/": TokenType.OP_DIVISION,
            ">": TokenType.OP_GT,
            "<": TokenType.OP_LT,
        }
        token = _token(op_map.get(op, TokenType.OP_PLUS), op)
        infix = InfixExpression(token, op, left)
        infix.right = right
        return infix

    tests = {}

    # Test 1: Simple arithmetic
    tests["arithmetic"] = Program(
        [
            SetStatement(
                _token(TokenType.KW_SET, "set"),
                Identifier(_token(TokenType.MISC_IDENT, "x"), "x"),
                _create_infix(
                    WholeNumberLiteral(_token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
                    "+",
                    WholeNumberLiteral(_token(TokenType.LIT_WHOLE_NUMBER, "20"), 20),
                ),
            ),
            ReturnStatement(
                _token(TokenType.KW_RETURN, "return"),
                Identifier(_token(TokenType.MISC_IDENT, "x"), "x"),
            ),
        ]
    )

    # Test 2: Control flow
    if_stmt = IfStatement(
        _token(TokenType.KW_IF, "if"),
        _create_infix(
            Identifier(_token(TokenType.MISC_IDENT, "x"), "x"),
            ">",
            WholeNumberLiteral(_token(TokenType.LIT_WHOLE_NUMBER, "10"), 10),
        ),
    )
    consequence = BlockStatement(_token(TokenType.OP_GT, ">"))
    consequence.statements = [
        SetStatement(
            _token(TokenType.KW_SET, "set"),
            Identifier(_token(TokenType.MISC_IDENT, "result"), "result"),
            StringLiteral(_token(TokenType.LIT_TEXT, "greater"), "greater"),
        ),
    ]
    if_stmt.consequence = consequence

    tests["control_flow"] = Program(
        [
            SetStatement(
                _token(TokenType.KW_SET, "set"),
                Identifier(_token(TokenType.MISC_IDENT, "x"), "x"),
                WholeNumberLiteral(_token(TokenType.LIT_WHOLE_NUMBER, "15"), 15),
            ),
            if_stmt,
            ReturnStatement(
                _token(TokenType.KW_RETURN, "return"),
                Identifier(_token(TokenType.MISC_IDENT, "result"), "result"),
            ),
        ]
    )

    # Add more regression tests as needed

    return tests
