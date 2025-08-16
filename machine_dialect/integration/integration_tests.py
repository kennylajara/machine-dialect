"""Integration tests for Machine Dialect components.

This module tests that all components (parser, interpreter, compiler, VM, CFG)
can handle the same input and produce consistent results.
"""

from dataclasses import dataclass
from typing import Any

from machine_dialect.cfg.parser import CFGParser
from machine_dialect.codegen.codegen import CodeGenerator
from machine_dialect.interpreter.evaluator import evaluate
from machine_dialect.interpreter.objects import Object
from machine_dialect.parser.parser import Parser
from machine_dialect.vm.vm import VM


@dataclass
class TestCase:
    """Represents a test case for integration testing."""

    name: str
    code: str
    expected_output: Any
    description: str = ""


@dataclass
class TestResult:
    """Result of running a test case through a component."""

    component: str
    success: bool
    output: Any
    error: str | None = None


class IntegrationTestRunner:
    """Runs integration tests across all Machine Dialect components."""

    def __init__(self) -> None:
        """Initialize the integration test runner."""
        self.parser = Parser()
        self.cfg_parser = CFGParser()
        self.code_generator = CodeGenerator()
        self.vm = VM()
        self.test_cases: list[TestCase] = []
        self._setup_test_cases()

    def _setup_test_cases(self) -> None:
        """Set up the test cases for integration testing."""
        self.test_cases = [
            # Basic literals
            TestCase(
                name="integer_literal",
                code="Set x to _42_.",
                expected_output=None,
                description="Test integer literal assignment",
            ),
            TestCase(
                name="float_literal",
                code="Set x to _3.14_.",
                expected_output=None,
                description="Test float literal assignment",
            ),
            TestCase(
                name="string_literal",
                code='Set x to _"hello"_.',
                expected_output=None,
                description="Test string literal assignment",
            ),
            TestCase(
                name="boolean_true",
                code="Set x to _true_.",
                expected_output=None,
                description="Test boolean true literal",
            ),
            TestCase(
                name="boolean_false",
                code="Set x to _false_.",
                expected_output=None,
                description="Test boolean false literal",
            ),
            # Arithmetic expressions
            TestCase(
                name="addition",
                code="Give back _5_ + _3_.",
                expected_output=8,
                description="Test addition operation",
            ),
            TestCase(
                name="subtraction",
                code="Give back _10_ - _4_.",
                expected_output=6,
                description="Test subtraction operation",
            ),
            TestCase(
                name="multiplication",
                code="Give back _3_ * _7_.",
                expected_output=21,
                description="Test multiplication operation",
            ),
            TestCase(
                name="division",
                code="Give back _15_ / _3_.",
                expected_output=5.0,
                description="Test division operation",
            ),
            # Comparison operations
            TestCase(
                name="equals",
                code="Give back _5_ equals _5_.",
                expected_output=True,
                description="Test equality comparison",
            ),
            TestCase(
                name="not_equals",
                code="Give back _5_ is not _3_.",
                expected_output=True,
                description="Test inequality comparison",
            ),
            TestCase(
                name="greater_than",
                code="Give back _7_ > _3_.",
                expected_output=True,
                description="Test greater than comparison",
            ),
            TestCase(
                name="less_than",
                code="Give back _2_ < _8_.",
                expected_output=True,
                description="Test less than comparison",
            ),
            # Conditional statements
            TestCase(
                name="if_statement_true",
                code="If _true_ then:\n> Give back _1_.\nElse:\n> Give back _0_.",
                expected_output=1,
                description="Test if statement with true condition",
            ),
            TestCase(
                name="if_statement_false",
                code="If _false_ then:\n> Give back _1_.\nElse:\n> Give back _0_.",
                expected_output=0,
                description="Test if statement with false condition",
            ),
            TestCase(
                name="if_expression_true",
                code="Give back _'Alice'_ if _true_ else _'Bob'_.",
                expected_output="Alice",
                description="Test if expression with true condition",
            ),
            TestCase(
                name="if_expression_false",
                code="Give back _'Alice'_ if _false_ else _'Bob'_.",
                expected_output="Bob",
                description="Test if expression with false condition",
            ),
            # Complex expressions
            TestCase(
                name="complex_arithmetic",
                code="Give back (_5_ + _3_) * _2_.",
                expected_output=16,
                description="Test complex arithmetic expression with parentheses",
            ),
            TestCase(
                name="logical_and",
                code="Give back _true_ and _true_.",
                expected_output=True,
                description="Test logical AND operation",
            ),
            TestCase(
                name="logical_or",
                code="Give back _false_ or _true_.",
                expected_output=True,
                description="Test logical OR operation",
            ),
            # Prefix operations
            TestCase(
                name="negation",
                code="Give back -_5_.",
                expected_output=-5,
                description="Test unary negation",
            ),
            TestCase(
                name="logical_not_true",
                code="Give back not _true_.",
                expected_output=False,
                description="Test logical NOT operation with true condition",
            ),
            TestCase(
                name="logical_not_false",
                code="Give back not _false_.",
                expected_output=True,
                description="Test logical NOT operation with false condition",
            ),
            # Strict equality operations
            TestCase(
                name="strict_equality_same_type",
                code="Give back _5_ is strictly equal to _5_.",
                expected_output=True,
                description="Test strict equality with same type and value",
            ),
            TestCase(
                name="strict_equality_diff_type",
                code="Give back _5_ is strictly equal to _5.0_.",
                expected_output=False,
                description="Test strict equality with different types",
            ),
            TestCase(
                name="strict_inequality_diff_type",
                code="Give back _5_ is not strictly equal to _5.0_.",
                expected_output=True,
                description="Test strict inequality with different types",
            ),
            TestCase(
                name="strict_inequality_same_type",
                code="Give back _5_ is not strictly equal to _5_.",
                expected_output=False,
                description="Test strict inequality with same type and value",
            ),
            # Value equality for comparison
            TestCase(
                name="value_equality_diff_type",
                code="Give back _5_ equals _5.0_.",
                expected_output=True,
                description="Test value equality across types",
            ),
        ]

    def test_parser(self, test_case: TestCase) -> TestResult:
        """Test the parser component.

        Args:
            test_case: The test case to run.

        Returns:
            TestResult indicating success or failure.
        """
        try:
            ast = self.parser.parse(test_case.code)
            if self.parser.errors:
                return TestResult(
                    component="Parser",
                    success=False,
                    output=None,
                    error=f"Parser errors: {self.parser.errors}",
                )
            return TestResult(component="Parser", success=True, output=ast, error=None)
        except Exception as e:
            return TestResult(component="Parser", success=False, output=None, error=str(e))

    def test_cfg_parser(self, test_case: TestCase) -> TestResult:
        """Test the CFG parser component.

        Args:
            test_case: The test case to run.

        Returns:
            TestResult indicating success or failure.
        """
        try:
            tree = self.cfg_parser.parse(test_case.code)
            return TestResult(component="CFG Parser", success=True, output=tree, error=None)
        except Exception as e:
            return TestResult(component="CFG Parser", success=False, output=None, error=str(e))

    def test_interpreter(self, test_case: TestCase) -> TestResult:
        """Test the interpreter component.

        Args:
            test_case: The test case to run.

        Returns:
            TestResult indicating success or failure.
        """
        try:
            ast = self.parser.parse(test_case.code)
            if self.parser.errors:
                return TestResult(
                    component="Interpreter",
                    success=False,
                    output=None,
                    error=f"Parser errors: {self.parser.errors}",
                )

            result = evaluate(ast)
            # Convert Object to Python value for comparison
            output = self._object_to_python(result)
            success = output == test_case.expected_output if test_case.expected_output is not None else True
            error = None
            if not success and test_case.expected_output is not None:
                error = f"Expected {test_case.expected_output!r}, got {output!r}"
            return TestResult(component="Interpreter", success=success, output=output, error=error)
        except Exception as e:
            return TestResult(component="Interpreter", success=False, output=None, error=str(e))

    def test_vm(self, test_case: TestCase) -> TestResult:
        """Test the VM component.

        Args:
            test_case: The test case to run.

        Returns:
            TestResult indicating success or failure.
        """
        try:
            ast = self.parser.parse(test_case.code)
            if self.parser.errors:
                return TestResult(
                    component="VM",
                    success=False,
                    output=None,
                    error=f"Parser errors: {self.parser.errors}",
                )

            # Compile to bytecode
            module = self.code_generator.compile(ast)
            if self.code_generator.errors:
                return TestResult(
                    component="VM",
                    success=False,
                    output=None,
                    error=f"Compiler errors: {self.code_generator.errors}",
                )

            # Execute in VM
            vm = VM()  # Create fresh VM for each test
            result = vm.run(module)
            success = result == test_case.expected_output if test_case.expected_output is not None else True
            error = None
            if not success and test_case.expected_output is not None:
                error = f"Expected {test_case.expected_output!r}, got {result!r}"
            return TestResult(component="VM", success=success, output=result, error=error)
        except Exception as e:
            return TestResult(component="VM", success=False, output=None, error=str(e))

    def run_test(self, test_case: TestCase) -> dict[str, TestResult]:
        """Run a single test case through all components.

        Args:
            test_case: The test case to run.

        Returns:
            Dictionary mapping component names to their test results.
        """
        results = {}

        # Test each component
        results["Parser"] = self.test_parser(test_case)
        results["CFG Parser"] = self.test_cfg_parser(test_case)
        results["Interpreter"] = self.test_interpreter(test_case)
        results["VM"] = self.test_vm(test_case)

        return results

    def run_all_tests(self) -> dict[str, dict[str, TestResult]]:
        """Run all test cases through all components.

        Returns:
            Dictionary mapping test names to their results for each component.
        """
        all_results = {}
        for test_case in self.test_cases:
            all_results[test_case.name] = self.run_test(test_case)
        return all_results

    def print_results(self, results: dict[str, dict[str, TestResult]]) -> None:
        """Print test results in a formatted table.

        Args:
            results: The test results to print.
        """
        # Print header
        print("\n" + "=" * 80)
        print("INTEGRATION TEST RESULTS")
        print("=" * 80)

        # Components to test
        components = ["Parser", "CFG Parser", "Interpreter", "VM"]

        # Print column headers
        print(f"{'Test Case':<25} | ", end="")
        for comp in components:
            print(f"{comp:<12} | ", end="")
        print("\n" + "-" * 80)

        # Print results for each test
        for test_name, test_results in results.items():
            print(f"{test_name:<25} | ", end="")
            for comp in components:
                result = test_results.get(comp)
                if result:
                    if result.success:
                        status = "✓ PASS"
                    else:
                        status = "✗ FAIL"
                else:
                    status = "? SKIP"
                print(f"{status:<12} | ", end="")
            print()

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("-" * 80)

        for comp in components:
            passed = sum(
                1 for test_results in results.values() if test_results.get(comp, TestResult(comp, False, None)).success
            )
            total = len(results)
            print(f"{comp:<15}: {passed}/{total} passed")

        # Print detailed errors
        print("\n" + "=" * 80)
        print("DETAILED ERRORS")
        print("-" * 80)

        has_errors = False
        for test_name, test_results in results.items():
            for comp, result in test_results.items():
                if result and not result.success and result.error:
                    has_errors = True
                    print(f"\n[{test_name}] {comp}:")
                    print(f"  Error: {result.error}")
                    if result.output is not None:
                        print(f"  Output: {result.output}")

        if not has_errors:
            print("No errors found!")

    def _object_to_python(self, obj: Object | None) -> Any:
        """Convert an interpreter Object to a Python value.

        Args:
            obj: The Object to convert.

        Returns:
            The Python equivalent value.
        """
        if obj is None:
            return None

        from machine_dialect.interpreter.objects import (
            Boolean,
            Empty,
            Float,
            Integer,
            Return,
            String,
        )

        if isinstance(obj, Integer):
            return obj.value
        elif isinstance(obj, Float):
            return obj.value
        elif isinstance(obj, String):
            return obj.value
        elif isinstance(obj, Boolean):
            return obj.value
        elif isinstance(obj, Empty):
            return obj.value  # Returns None
        elif isinstance(obj, Return):
            return self._object_to_python(obj.value)
        else:
            return str(obj)


def test_integration_runner() -> None:
    """Test that all components work together on the same input."""
    runner = IntegrationTestRunner()
    results = runner.run_all_tests()
    runner.print_results(results)

    # Assert that all tests pass for critical components
    for test_name, test_results in results.items():
        # Parser should pass all tests
        parser_result = test_results.get("Parser")
        assert (
            parser_result and parser_result.success
        ), f"Parser failed for {test_name}: {parser_result.error if parser_result else 'No result'}"

        # Interpreter should pass all tests
        interpreter_result = test_results.get("Interpreter")
        assert (
            interpreter_result and interpreter_result.success
        ), f"Interpreter failed for {test_name}: {interpreter_result.error if interpreter_result else 'No result'}"

        # VM should pass all tests
        vm_result = test_results.get("VM")
        assert (
            vm_result and vm_result.success
        ), f"VM failed for {test_name}: {vm_result.error if vm_result else 'No result'}"
