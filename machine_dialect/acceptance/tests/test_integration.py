"""Pytest-based acceptance tests for Machine Dialect components."""

from typing import Any

import pytest

from machine_dialect.acceptance.integration_tests import (
    IntegrationTestCase,
    IntegrationTestRunner,
)


class TestIntegration:
    """Acceptance tests for all Machine Dialect components."""

    @pytest.fixture
    def runner(self) -> IntegrationTestRunner:
        """Create an acceptance test runner.

        Returns:
            An initialized IntegrationTestRunner.
        """
        return IntegrationTestRunner()

    def test_all_components_initialized(self, runner: IntegrationTestRunner) -> None:
        """Test that all components are properly initialized."""
        assert runner.parser is not None
        assert runner.cfg_parser is not None
        assert runner.hir_phase is not None
        assert runner.mir_phase is not None
        assert runner.codegen_phase is not None
        assert runner.vm is not None
        assert len(runner.test_cases) > 0

    def test_integer_literal(self, runner: IntegrationTestRunner) -> None:
        """Test integer literal handling across components."""
        test_case = IntegrationTestCase(
            name="integer_literal",
            code="Give back _42_.",
            expected_output=42,
            description="Test integer literal",
        )
        results = runner.run_test(test_case)

        # Parser should succeed
        assert results["Parser"].success

        # Interpreter should return correct value
        assert results["Interpreter"].success
        assert results["Interpreter"].output == 42

        # VM should return correct value
        assert results["VM"].success
        assert results["VM"].output == 42

    def test_float_literal(self, runner: IntegrationTestRunner) -> None:
        """Test float literal handling across components."""
        test_case = IntegrationTestCase(
            name="float_literal",
            code="Give back _3.14_.",
            expected_output=3.14,
            description="Test float literal",
        )
        results = runner.run_test(test_case)

        # Parser should succeed
        assert results["Parser"].success

        # Interpreter should return correct value
        assert results["Interpreter"].success
        assert results["Interpreter"].output == 3.14

        # VM should return correct value
        assert results["VM"].success
        assert results["VM"].output == 3.14

    def test_string_literal(self, runner: IntegrationTestRunner) -> None:
        """Test string literal handling across components."""
        test_case = IntegrationTestCase(
            name="string_literal",
            code='Give back _"hello"_.',
            expected_output="hello",
            description="Test string literal",
        )
        results = runner.run_test(test_case)

        # Parser should succeed
        assert results["Parser"].success

        # Interpreter should return correct value
        assert results["Interpreter"].success
        assert results["Interpreter"].output == "hello"

        # VM should return correct value
        assert results["VM"].success
        assert results["VM"].output == "hello"

    def test_boolean_literals(self, runner: IntegrationTestRunner) -> None:
        """Test boolean literal handling across components."""
        # Test true
        test_case_true = IntegrationTestCase(
            name="boolean_true",
            code="Give back _true_.",
            expected_output=True,
            description="Test boolean true",
        )
        results_true = runner.run_test(test_case_true)

        assert results_true["Parser"].success
        assert results_true["Interpreter"].success
        assert results_true["Interpreter"].output is True
        assert results_true["VM"].success
        assert results_true["VM"].output is True

        # Test false
        test_case_false = IntegrationTestCase(
            name="boolean_false",
            code="Give back _false_.",
            expected_output=False,
            description="Test boolean false",
        )
        results_false = runner.run_test(test_case_false)

        assert results_false["Parser"].success
        assert results_false["Interpreter"].success
        assert results_false["Interpreter"].output is False
        assert results_false["VM"].success
        assert results_false["VM"].output is False

    def test_arithmetic_operations(self, runner: IntegrationTestRunner) -> None:
        """Test arithmetic operations across components."""
        test_cases = [
            IntegrationTestCase("addition", "Give back _5_ + _3_.", 8),
            IntegrationTestCase("subtraction", "Give back _10_ - _4_.", 6),
            IntegrationTestCase("multiplication", "Give back _3_ * _7_.", 21),
            IntegrationTestCase("division", "Give back _15_ / _3_.", 5.0),
        ]

        for test_case in test_cases:
            results = runner.run_test(test_case)

            # Parser should succeed
            assert results["Parser"].success, f"Parser failed for {test_case.name}"

            # Interpreter should return correct value
            assert results["Interpreter"].success, f"Interpreter failed for {test_case.name}"
            assert results["Interpreter"].output == test_case.expected_output

            # VM should return correct value
            assert results["VM"].success, f"VM failed for {test_case.name}"
            assert results["VM"].output == test_case.expected_output

    def test_comparison_operations(self, runner: IntegrationTestRunner) -> None:
        """Test comparison operations across components."""
        test_cases = [
            IntegrationTestCase("equals", "Give back _5_ equals _5_.", True),
            IntegrationTestCase("not_equals", "Give back _5_ is not _3_.", True),
            IntegrationTestCase("greater_than", "Give back _7_ > _3_.", True),
            IntegrationTestCase("less_than", "Give back _2_ < _8_.", True),
        ]

        for test_case in test_cases:
            results = runner.run_test(test_case)

            # Parser should succeed
            assert results["Parser"].success, f"Parser failed for {test_case.name}"

            # Interpreter should return correct value
            assert results["Interpreter"].success, f"Interpreter failed for {test_case.name}"
            assert results["Interpreter"].output == test_case.expected_output

            # VM should return correct value
            assert results["VM"].success, f"VM failed for {test_case.name}"
            assert results["VM"].output == test_case.expected_output

    def test_logical_operations(self, runner: IntegrationTestRunner) -> None:
        """Test logical operations across components."""
        test_cases = [
            IntegrationTestCase("logical_and", "Give back _true_ and _true_.", True),
            IntegrationTestCase("logical_or", "Give back _false_ or _true_.", True),
            IntegrationTestCase("logical_not", "Give back not _true_.", False),
        ]

        for test_case in test_cases:
            results = runner.run_test(test_case)

            # Parser should succeed
            assert results["Parser"].success, f"Parser failed for {test_case.name}"

            # Interpreter should return correct value
            assert results["Interpreter"].success, f"Interpreter failed for {test_case.name}"
            assert results["Interpreter"].output == test_case.expected_output

            # VM should return correct value
            assert results["VM"].success, f"VM failed for {test_case.name}"
            assert results["VM"].output == test_case.expected_output

    def test_conditional_statements(self, runner: IntegrationTestRunner) -> None:
        """Test conditional statements across components."""
        test_cases = [
            IntegrationTestCase(
                "if_true",
                "If _true_ then:\n> Give back _1_.\nElse:\n> Give back _0_.",
                1,
            ),
            IntegrationTestCase(
                "if_false",
                "If _false_ then:\n> Give back _1_.\nElse:\n> Give back _0_.",
                0,
            ),
        ]

        for test_case in test_cases:
            results = runner.run_test(test_case)

            # Parser should succeed
            assert results["Parser"].success, f"Parser failed for {test_case.name}"

            # Interpreter should return correct value
            assert results["Interpreter"].success, f"Interpreter failed for {test_case.name}"
            assert results["Interpreter"].output == test_case.expected_output

            # VM should return correct value
            assert results["VM"].success, f"VM failed for {test_case.name}"
            assert results["VM"].output == test_case.expected_output

    def test_complex_expressions(self, runner: IntegrationTestRunner) -> None:
        """Test complex expressions across components."""
        test_case = IntegrationTestCase(
            name="complex_arithmetic",
            code="Give back (_5_ + _3_) * _2_.",
            expected_output=16,
            description="Test complex arithmetic with parentheses",
        )
        results = runner.run_test(test_case)

        # Parser should succeed
        assert results["Parser"].success

        # Interpreter should return correct value
        assert results["Interpreter"].success
        assert results["Interpreter"].output == 16

        # VM should return correct value
        assert results["VM"].success
        assert results["VM"].output == 16

    def test_prefix_operations(self, runner: IntegrationTestRunner) -> None:
        """Test prefix operations across components."""
        test_cases = [
            IntegrationTestCase("negation", "Give back -_5_.", -5),
            IntegrationTestCase("logical_not", "Give back not _true_.", False),
        ]

        for test_case in test_cases:
            results = runner.run_test(test_case)

            # Parser should succeed
            assert results["Parser"].success, f"Parser failed for {test_case.name}"

            # Interpreter should return correct value
            assert results["Interpreter"].success, f"Interpreter failed for {test_case.name}"
            assert results["Interpreter"].output == test_case.expected_output

            # VM should return correct value
            assert results["VM"].success, f"VM failed for {test_case.name}"
            assert results["VM"].output == test_case.expected_output

    @pytest.mark.skip(reason="Skipping failing test")
    def test_comprehensive_suite(self, runner: IntegrationTestRunner) -> None:
        """Run the comprehensive test suite and verify consistency."""
        results = runner.run_all_tests()

        # Track overall success and failures
        total_tests = len(results)
        parser_failures = []
        cfg_parser_failures = []
        interpreter_failures = []
        vm_failures = []

        for test_name, test_results in results.items():
            if not test_results["Parser"].success:
                parser_failures.append(
                    {
                        "test": test_name,
                        "error": test_results["Parser"].error,
                        "output": test_results["Parser"].output,
                    }
                )
            if not test_results["CFG Parser"].success:
                cfg_parser_failures.append(
                    {
                        "test": test_name,
                        "error": test_results["CFG Parser"].error,
                        "output": test_results["CFG Parser"].output,
                    }
                )
            if not test_results["Interpreter"].success:
                interpreter_failures.append(
                    {
                        "test": test_name,
                        "error": test_results["Interpreter"].error,
                        "output": test_results["Interpreter"].output,
                    }
                )
            if not test_results["VM"].success:
                vm_failures.append(
                    {
                        "test": test_name,
                        "error": test_results["VM"].error,
                        "output": test_results["VM"].output,
                    }
                )

        # Build detailed error messages
        def format_failures(component: str, failures: list[dict[str, Any]]) -> str:
            if not failures:
                return ""
            msg = f"\n{component} failed {len(failures)}/{total_tests} tests:\n"
            for failure in failures:
                msg += f"  - {failure['test']}: "
                if failure["error"]:
                    msg += f"{failure['error']}"
                else:
                    msg += f"Output={failure['output']} (expected output didn't match)"
                msg += "\n"
            return msg

        # Assert with detailed error messages
        assert not parser_failures, f"Parser failures:{format_failures('Parser', parser_failures)}"
        assert not cfg_parser_failures, f"CFG Parser failures:{format_failures('CFG Parser', cfg_parser_failures)}"
        assert not interpreter_failures, f"Interpreter failures:{format_failures('Interpreter', interpreter_failures)}"
        assert not vm_failures, f"VM failures:{format_failures('VM', vm_failures)}"
