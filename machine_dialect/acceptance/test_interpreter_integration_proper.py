"""Proper integration tests for Machine Dialect using IntegrationTestRunner.

These tests validate that all components handle the same input correctly,
and clearly show which components support which features.
"""

import pytest

from machine_dialect.acceptance.integration_tests import (
    IntegrationTestCase,
    IntegrationTestRunner,
)


class TestMachineDialectIntegration:
    """Integration tests that run through all components."""

    @pytest.fixture
    def runner(self) -> IntegrationTestRunner:
        """Create a test runner for integration tests."""
        return IntegrationTestRunner()

    def test_extended_test_cases(self, runner: IntegrationTestRunner) -> None:
        """Test additional cases including utilities which VM doesn't support yet."""
        # Add new test cases including utilities
        additional_cases = [
            # Basic utility definition and call (VM will fail)
            IntegrationTestCase(
                name="utility_simple",
                code="""
### **Utility**: `get_answer`

<details>
<summary>Returns 42.</summary>

> Give back _42_.

</details>

Use `get_answer`.
""",
                expected_output=42,
                description="Test simple utility without parameters",
            ),
            # Utility with parameters (VM will fail)
            IntegrationTestCase(
                name="utility_with_params",
                code="""
### **Utility**: `add`

<details>
<summary>Adds two numbers.</summary>

> Give back `a` + `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Use `add` with _10_, _20_.
""",
                expected_output=30,
                description="Test utility with positional parameters",
            ),
            # Set using utility (VM will fail)
            IntegrationTestCase(
                name="set_using_utility",
                code="""
### **Utility**: `square`

<details>
<summary>Squares a number.</summary>

> Give back `n` * `n`.

</details>

#### Inputs:
- `n` **as** Number (required)

Set `result` using `square` with _5_.
Give back `result`.
""",
                expected_output=25,
                description="Test Set with using keyword for utility calls",
            ),
            # Utility with named arguments (VM will fail)
            IntegrationTestCase(
                name="utility_named_args",
                code="""
### **Utility**: `divide`

<details>
<summary>Divides two numbers.</summary>

> Give back `dividend` / `divisor`.

</details>

#### Inputs:
- `dividend` **as** Number (required)
- `divisor` **as** Number (required)

Use `divide` where `divisor` is _4_, `dividend` is _100_.
""",
                expected_output=25.0,
                description="Test utility with named arguments",
            ),
            # Complex utility with conditionals (VM will fail)
            IntegrationTestCase(
                name="utility_conditional",
                code="""
### **Utility**: `max`

<details>
<summary>Returns the maximum of two numbers.</summary>

> If `a` > `b` then:
> > Give back `a`.
> Else:
> > Give back `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Use `max` with _15_, _8_.
""",
                expected_output=15,
                description="Test utility with conditional logic",
            ),
            # Say statement (should work in interpreter)
            IntegrationTestCase(
                name="say_statement",
                code='Say _"Hello, World!"_.',
                expected_output=None,
                description="Test Say statement",
            ),
            # Empty value
            IntegrationTestCase(
                name="empty_value",
                code="Give back _empty_.",
                expected_output=None,
                description="Test empty literal",
            ),
            # Complex nested expression
            IntegrationTestCase(
                name="complex_nested",
                code="Set `a` to _10_. Set `b` to _5_. Set `c` to _2_. Give back (`a` + `b`) * `c` - _10_ / `b`.",
                expected_output=28.0,
                description="Test complex nested arithmetic",
            ),
            # Conditional expression
            IntegrationTestCase(
                name="conditional_expr",
                code="Set `x` to _10_. Give back `x` if `x` > _5_ else _0_.",
                expected_output=10,
                description="Test conditional expression",
            ),
        ]

        # Run each additional test case
        for test_case in additional_cases:
            results = runner.run_test(test_case)

            # Parser should always pass
            assert results["Parser"].success, f"Parser failed for {test_case.name}: {results['Parser'].error}"

            # Interpreter should pass
            assert results[
                "Interpreter"
            ].success, f"Interpreter failed for {test_case.name}: {results['Interpreter'].error}"

            # VM should now pass all tests including utilities
            if test_case.expected_output is not None:  # Skip None checks for Say statements
                assert results["VM"].success, f"VM failed for {test_case.name}: {results['VM'].error}"
                # Check output matches expected
                if results["VM"].success:
                    assert results["VM"].output == test_case.expected_output, (
                        f"VM output mismatch for {test_case.name}: "
                        f"expected {test_case.expected_output}, got {results['VM'].output}"
                    )

    def test_original_test_cases_all_pass(self, runner: IntegrationTestRunner) -> None:
        """Test that all original test cases pass in all components."""
        results = runner.run_all_tests()

        skipped_tests = []
        for test_name, test_results in results.items():
            # Check if test was skipped (all components will have same skip status)
            if test_results["Parser"].error and test_results["Parser"].error.startswith("SKIPPED:"):
                skipped_tests.append((test_name, test_results["Parser"].error))
                continue

            # All components should pass for the original test cases
            assert test_results["Parser"].success, f"Parser failed for {test_name}"
            assert test_results["Interpreter"].success, f"Interpreter failed for {test_name}"
            assert test_results["VM"].success, f"VM failed for {test_name}"
            # CFG parser might fail but we don't enforce it

        # Report skipped tests if any
        if skipped_tests:
            print(f"\nSkipped {len(skipped_tests)} tests:")
            for test_name, reason in skipped_tests:
                print(f"  - {test_name}: {reason[8:]}")  # Remove "SKIPPED: " prefix

    def test_error_handling_cases(self, runner: IntegrationTestRunner) -> None:
        """Test error handling across components."""
        error_cases = [
            IntegrationTestCase(
                name="undefined_variable",
                code="Give back `undefined_var`.",
                expected_output=None,  # Expect an error
                description="Test undefined variable error",
            ),
            IntegrationTestCase(
                name="undefined_utility",
                code="Use `undefined_function` with _10_.",
                expected_output=None,  # Expect an error
                description="Test undefined utility error",
            ),
        ]

        for test_case in error_cases:
            results = runner.run_test(test_case)

            # Parser should succeed (syntactically valid)
            assert results["Parser"].success, f"Parser failed for {test_case.name}"

            # Interpreter should handle the error gracefully (not crash)
            # The error will be in the output as an Error object
            # We don't assert success because evaluate returns an Error object

    def test_print_comprehensive_report(self, runner: IntegrationTestRunner) -> None:
        """Generate a comprehensive report showing component support."""
        # Add utility test cases to show VM limitations
        utility_cases = [
            IntegrationTestCase(
                name="utility_basic",
                code="""
### **Utility**: `identity`

<details>
<summary>Returns input unchanged.</summary>

> Give back `x`.

</details>

#### Inputs:
- `x` **as** Number (required)

Use `identity` with _42_.
""",
                expected_output=42,
                description="Basic utility test",
            ),
        ]

        # Add to runner's test cases
        runner.test_cases.extend(utility_cases)

        # Run all tests and print results
        results = runner.run_all_tests()
        runner.print_results(results)


def test_comprehensive_integration() -> None:
    """Run a comprehensive integration test showing all component capabilities."""
    runner = IntegrationTestRunner()

    # Define comprehensive test cases
    comprehensive_cases = [
        # Working in all components
        IntegrationTestCase(
            name="basic_arithmetic",
            code="Give back _10_ + _5_.",
            expected_output=15,
            description="Basic arithmetic - all components support",
        ),
        IntegrationTestCase(
            name="variables",
            code="Set `x` to _100_. Give back `x`.",
            expected_output=100,
            description="Variables - all components support",
        ),
        IntegrationTestCase(
            name="if_statement",
            code="If _true_ then:\n> Give back _1_.\nElse:\n> Give back _0_.",
            expected_output=1,
            description="Control flow - all components support",
        ),
        # Working only in Parser and Interpreter
        IntegrationTestCase(
            name="utility_definition",
            code="""
### **Utility**: `double`

<details>
<summary>Doubles a number.</summary>

> Give back `n` * _2_.

</details>

#### Inputs:
- `n` **as** Number (required)

Use `double` with _21_.
""",
            expected_output=42,
            description="Utilities - Parser/Interpreter only",
        ),
        IntegrationTestCase(
            name="set_using",
            code="""
### **Utility**: `triple`

<details>
<summary>Triples a number.</summary>

> Give back `n` * _3_.

</details>

#### Inputs:
- `n` **as** Number (required)

Set `result` using `triple` with _7_.
Give back `result`.
""",
            expected_output=21,
            description="Set using - Parser/Interpreter only",
        ),
    ]

    print("\n" + "=" * 80)
    print("COMPREHENSIVE COMPONENT CAPABILITY TEST")
    print("=" * 80)
    print("\nThis test demonstrates which components support which features:\n")

    for test_case in comprehensive_cases:
        results = runner.run_test(test_case)

        print(f"\n{test_case.name} ({test_case.description}):")
        print(f"  Code: {test_case.code[:50]}..." if len(test_case.code) > 50 else f"  Code: {test_case.code}")
        print(f"  Expected: {test_case.expected_output}")
        print("  Results:")
        for component, result in results.items():
            status = "✓ PASS" if result.success else "✗ FAIL"
            print(f"    {component:<15}: {status}")
            if not result.success and result.error:
                print(f"                     Error: {result.error[:60]}...")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("-" * 80)
    print("✓ Parser and Interpreter: Full support for all features including utilities")
    print("✗ VM/CodeGen: No support for utilities (UtilityStatement, CallStatement)")
    print("? CFG Parser: Limited support, may fail on complex syntax")
    print("=" * 80)


if __name__ == "__main__":
    # Run the comprehensive test when executed directly
    test_comprehensive_integration()
