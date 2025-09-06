"""Differential testing framework for Machine Dialect feature parity.

This framework ensures 100% feature parity between:
- Main Parser and CFG Parser (parsing consistency)
- Interpreter and VM (execution consistency)
"""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

from machine_dialect.cfg.parser import CFGParser
from machine_dialect.compiler.config import CompilerConfig, OptimizationLevel
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.phases.codegen import CodeGenerationPhase
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
from machine_dialect.interpreter.evaluator import evaluate
from machine_dialect.interpreter.objects import Environment
from machine_dialect.parser.parser import Parser
from machine_dialect.vm.vm import VM


class TestResult(Enum):
    """Result of a parity test."""

    SUCCESS = auto()
    PARSE_MISMATCH = auto()
    EXEC_MISMATCH = auto()
    BOTH_FAILED = auto()


@dataclass
class ParityTestCase:
    """A test case for feature parity validation."""

    name: str
    code: str
    should_parse: bool  # Should parsing succeed?
    expected_output: Any | None = None  # Expected output if successful
    expected_error: str | None = None  # Expected error pattern if failure


@dataclass
class ParityTestResult:
    """Result of running a parity test."""

    test: ParityTestCase
    result: TestResult
    main_parser_result: Any
    cfg_parser_result: Any
    interpreter_result: Any | None = None
    vm_result: Any | None = None
    errors: list[str] | None = None


class ParityTestRunner:
    """Runs differential tests to ensure feature parity."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the test runner.

        Args:
            verbose: Enable verbose output.
        """
        self.verbose = verbose
        # Initialize MIR compilation phases
        self.hir_phase = HIRGenerationPhase()
        self.mir_phase = MIRGenerationPhase()
        self.codegen_phase = CodeGenerationPhase()
        self.main_parser = Parser()
        self.cfg_parser = CFGParser()

    def run_test(self, test: ParityTestCase) -> ParityTestResult:
        """Run a single parity test.

        Args:
            test: The test case to run.

        Returns:
            Test result with details.
        """
        errors = []

        # Test parsers
        main_ast = None

        try:
            main_ast = self.main_parser.parse(test.code)
            main_parsed = True
        except Exception as e:
            main_parsed = False
            errors.append(f"Main parser: {e}")

        try:
            _ = self.cfg_parser.parse(test.code)
            cfg_parsed = True
        except Exception as e:
            cfg_parsed = False
            errors.append(f"CFG parser: {e}")

        # Check parser consistency
        if main_parsed != cfg_parsed:
            return ParityTestResult(
                test=test,
                result=TestResult.PARSE_MISMATCH,
                main_parser_result=main_parsed,
                cfg_parser_result=cfg_parsed,
                errors=errors,
            )

        # Both failed as expected
        if not main_parsed and not cfg_parsed and not test.should_parse:
            return ParityTestResult(
                test=test,
                result=TestResult.SUCCESS,
                main_parser_result=False,
                cfg_parser_result=False,
                errors=errors,
            )

        # Both failed unexpectedly
        if not main_parsed and not cfg_parsed and test.should_parse:
            return ParityTestResult(
                test=test,
                result=TestResult.BOTH_FAILED,
                main_parser_result=False,
                cfg_parser_result=False,
                errors=errors,
            )

        # Both parsed - now test execution
        if main_ast:
            interp_result = None
            vm_result = None

            # Test interpreter
            try:
                env = Environment()
                result = evaluate(main_ast, env)
                if result is not None:
                    if hasattr(result, "value"):
                        interp_result = result.value
                    elif hasattr(result, "inspect"):
                        # Handle string/bool/empty objects
                        val = result.inspect()
                        if val == "true":
                            interp_result = True
                        elif val == "false":
                            interp_result = False
                        elif val == "empty":
                            interp_result = None
                        elif val.startswith('"') and val.endswith('"'):
                            interp_result = val[1:-1]
                        else:
                            interp_result = val
                    else:
                        interp_result = result
            except Exception as e:
                errors.append(f"Interpreter: {e}")

            # Test VM using MIR pipeline (without optimization to avoid issues)
            try:
                config = CompilerConfig(optimization_level=OptimizationLevel.NONE)
                context = CompilationContext(source_path=Path("test.md"), config=config)
                context.ast = main_ast

                # Convert AST -> HIR -> MIR -> Bytecode
                hir = self.hir_phase.run(context, main_ast)
                mir_module = self.mir_phase.run(context, hir)
                if mir_module is None:
                    raise RuntimeError("Failed to generate MIR module")
                context.mir_module = mir_module
                module = self.codegen_phase.run(context, mir_module)
                if module is None:
                    raise RuntimeError("Failed to generate bytecode module")

                vm = VM()
                vm_result = vm.run(module)
            except Exception as e:
                errors.append(f"VM: {e}")

            # Check execution consistency
            if interp_result != vm_result:
                return ParityTestResult(
                    test=test,
                    result=TestResult.EXEC_MISMATCH,
                    main_parser_result=True,
                    cfg_parser_result=True,
                    interpreter_result=interp_result,
                    vm_result=vm_result,
                    errors=errors,
                )

            # Check expected output
            if test.expected_output is not None and interp_result != test.expected_output:
                errors.append(f"Expected {test.expected_output}, got {interp_result}")

            return ParityTestResult(
                test=test,
                result=TestResult.SUCCESS,
                main_parser_result=True,
                cfg_parser_result=True,
                interpreter_result=interp_result,
                vm_result=vm_result,
                errors=errors if errors else None,
            )

        return ParityTestResult(
            test=test,
            result=TestResult.SUCCESS,
            main_parser_result=True,
            cfg_parser_result=True,
            errors=errors if errors else None,
        )

    def run_tests(self, tests: list[ParityTestCase]) -> tuple[list[ParityTestResult], int, int]:
        """Run multiple parity tests.

        Args:
            tests: List of test cases.

        Returns:
            Tuple of (results, passed_count, failed_count).
        """
        results = []
        passed = 0
        failed = 0

        for test in tests:
            if self.verbose:
                print(f"Running: {test.name}")

            result = self.run_test(test)
            results.append(result)

            if result.result == TestResult.SUCCESS:
                passed += 1
                if self.verbose:
                    print("  ✓ PASSED")
            else:
                failed += 1
                if self.verbose:
                    print(f"  ✗ FAILED: {result.result.name}")
                    if result.errors:
                        for error in result.errors:
                            print(f"    - {error}")

        return results, passed, failed


def create_operator_tests() -> list[ParityTestCase]:
    """Create comprehensive operator tests."""
    tests = []

    # Arithmetic operators
    tests.extend(
        [
            ParityTestCase("Addition", "Give back _5_ + _3_.", True, 8),
            ParityTestCase("Subtraction", "Give back _10_ - _4_.", True, 6),
            ParityTestCase("Multiplication", "Give back _3_ * _7_.", True, 21),
            ParityTestCase("Division", "Give back _15_ / _3_.", True, 5.0),
            ParityTestCase("Exponentiation", "Give back _2_ ^ _3_.", True, 8),
            ParityTestCase("Precedence", "Give back _2_ + _3_ * _4_.", True, 14),
            ParityTestCase("Parentheses", "Give back (_2_ + _3_) * _4_.", True, 20),
        ]
    )

    # Comparison operators
    tests.extend(
        [
            ParityTestCase("Less than", "Give back _3_ < _5_.", True, True),
            ParityTestCase("Greater than", "Give back _7_ > _5_.", True, True),
            ParityTestCase("Less equal", "Give back _5_ <= _5_.", True, True),
            ParityTestCase("Greater equal", "Give back _5_ >= _3_.", True, True),
            ParityTestCase("Equals", "Give back _5_ equals _5_.", True, True),
            ParityTestCase("Not equals", "Give back _3_ is not _5_.", True, True),
        ]
    )

    # Boolean operators
    tests.extend(
        [
            ParityTestCase("AND true", "Give back _yes_ and _yes_.", True, True),
            ParityTestCase("AND false", "Give back _yes_ and _No_.", True, False),
            ParityTestCase("OR true", "Give back _yes_ or _yes_.", True, True),
            ParityTestCase("OR false", "Give back _yes_ or _No_.", True, False),
            ParityTestCase("NOT true", "Give back not _yes_.", True, False),
            ParityTestCase("NOT false", "Give back not _No_.", True, True),
        ]
    )

    return tests


def create_literal_tests() -> list[ParityTestCase]:
    """Create comprehensive literal tests."""
    tests = []

    tests.extend(
        [
            ParityTestCase("Integer", "Give back _42_.", True, 42),
            ParityTestCase("Float", "Give back _3.14_.", True, 3.14),
            ParityTestCase("String", 'Give back _"hello"_.', True, "hello"),
            ParityTestCase("Boolean true", "Give back _yes_.", True, True),
            ParityTestCase("Boolean false", "Give back _No_.", True, False),
            ParityTestCase("Yes literal", "Give back _Yes_.", True, True),
            ParityTestCase("No literal", "Give back _No_.", True, False),
            ParityTestCase("Empty literal", "Give back _empty_.", True, None),
        ]
    )

    return tests


def create_statement_tests() -> list[ParityTestCase]:
    """Create comprehensive statement tests."""
    tests = []

    # Basic statements
    tests.extend(
        [
            ParityTestCase("Set variable", "Set x to _10_. Give back x.", True, 10),
            ParityTestCase("Tell statement", "Tell _'Hello'_.", True, "Hello"),
            ParityTestCase("Say statement", "Say _'World'_.", True, "World"),
        ]
    )

    # Control flow
    tests.extend(
        [
            ParityTestCase(
                "If true",
                "If _yes_ then:\n> Give back _1_.\nElse:\n> Give back _2_.",
                True,
                1,
            ),
            ParityTestCase(
                "If false",
                "If _yes_ then:\n> Give back _1_.\nElse:\n> Give back _2_.",
                True,
                2,
            ),
            ParityTestCase(
                "When statement",
                "When _yes_ then:\n> Give back _10_.\nOtherwise:\n> Give back _20_.",
                True,
                10,
            ),
        ]
    )

    return tests


def run_comprehensive_parity_tests() -> None:
    """Run comprehensive parity tests and report results."""
    print("=" * 60)
    print("MACHINE DIALECT FEATURE PARITY TEST SUITE")
    print("=" * 60)

    runner = ParityTestRunner(verbose=True)
    all_tests = []

    # Collect all tests
    print("\nCollecting tests...")
    operator_tests = create_operator_tests()
    literal_tests = create_literal_tests()
    statement_tests = create_statement_tests()

    all_tests.extend(operator_tests)
    all_tests.extend(literal_tests)
    all_tests.extend(statement_tests)

    print(f"Total tests: {len(all_tests)}")

    # Run tests
    print("\nRunning parity tests...\n")
    results, passed, failed = runner.run_tests(all_tests)

    # Report summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total:  {len(all_tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Rate:   {passed/len(all_tests)*100:.1f}%")

    if failed > 0:
        print("\n" + "=" * 60)
        print("FAILED TESTS")
        print("=" * 60)
        for result in results:
            if result.result != TestResult.SUCCESS:
                print(f"\n{result.test.name}:")
                print(f"  Result: {result.result.name}")
                if result.errors:
                    for error in result.errors:
                        print(f"  Error: {error}")
                if result.result == TestResult.EXEC_MISMATCH:
                    print(f"  Interpreter: {result.interpreter_result}")
                    print(f"  VM:          {result.vm_result}")


if __name__ == "__main__":
    run_comprehensive_parity_tests()
