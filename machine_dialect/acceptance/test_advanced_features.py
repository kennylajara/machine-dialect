"""Advanced feature tests for Machine Dialect feature parity.

This module tests advanced language features including functions,
type annotations, and control flow constructs.
"""

import pytest

from machine_dialect.acceptance.parity_test_framework import ParityTestCase, ParityTestRunner


def create_utility_tests() -> list[ParityTestCase]:
    """Create tests for utility (function) definitions."""
    tests = []

    tests.extend(
        [
            # Basic utility definition
            ParityTestCase(
                "Simple utility",
                """### **Square**: `square`
Give back _5_ * _5_.""",
                True,
                25,
            ),
            # Utility with parameters
            ParityTestCase(
                "Utility with param",
                """### **Add One**: `add_one`
#### Inputs:
- x: Number
Give back x + _1_.""",
                True,
                None,  # Just definition, no execution
            ),
            # Using a utility
            ParityTestCase(
                "Use utility",
                """### **Double**: `double`
#### Inputs:
- n: Number
Give back n * _2_.

Use double with _10_.""",
                True,
                20,
            ),
            # Utility with multiple parameters
            ParityTestCase(
                "Multi-param utility",
                """### **Add**: `add`
#### Inputs:
- a: Number
- b: Number
Give back a + b.

Use add with _3_, _4_.""",
                True,
                7,
            ),
        ]
    )

    return tests


def create_action_interaction_tests() -> list[ParityTestCase]:
    """Create tests for Actions and Interactions."""
    tests = []

    tests.extend(
        [
            # Basic action
            ParityTestCase(
                "Simple action",
                """Action greet:
> Say _"Hello!"_.
""",
                True,
                None,  # Actions don't return values
            ),
            # Action with parameters
            ParityTestCase(
                "Action with param",
                """Action greet_person with name:
> Say _"Hello, "_ + name + _"!"_.
""",
                True,
                None,
            ),
            # Interaction
            ParityTestCase(
                "Simple interaction",
                """Interaction get_name:
> Give back _"Alice"_.
""",
                True,
                None,  # Just definition
            ),
            # Interaction with parameters
            ParityTestCase(
                "Interaction with param",
                """Interaction calculate with x, y:
> Give back x + y.
""",
                True,
                None,
            ),
        ]
    )

    return tests


def create_control_flow_tests() -> list[ParityTestCase]:
    """Create tests for advanced control flow."""
    tests = []

    tests.extend(
        [
            # When statement (alias for If)
            ParityTestCase(
                "When statement",
                """When _true_ then:
> Give back _"yes"_.
Otherwise:
> Give back _"no"_.""",
                True,
                "yes",
            ),
            # Nested conditions
            ParityTestCase(
                "Nested if",
                """Set x to _10_.
If x > _5_ then:
> If x < _15_ then:
>> Give back _"medium"_.
> Else:
>> Give back _"large"_.
Else:
> Give back _"small"_.""",
                True,
                "medium",
            ),
            # Complex conditional expression
            ParityTestCase(
                "Nested conditional expr",
                "Give back _'positive'_ if _5_ > _0_ else (_'zero'_ if _5_ equals _0_ else _'negative'_).",
                True,
                "positive",
            ),
        ]
    )

    return tests


def create_type_annotation_tests() -> list[ParityTestCase]:
    """Create tests for type annotations."""
    tests = []

    tests.extend(
        [
            # Type annotations in Set
            ParityTestCase(
                "Set with type",
                "Set x as Integer to _42_. Give back x.",
                True,
                42,
            ),
            ParityTestCase(
                "Set float type",
                "Set pi as Float to _3.14_. Give back pi.",
                True,
                3.14,
            ),
            ParityTestCase(
                "Set text type",
                'Set name as Text to _"Alice"_. Give back name.',
                True,
                "Alice",
            ),
            # Type checking
            ParityTestCase(
                "Type check integer",
                "Set x to _42_. Give back x is Integer.",
                True,
                True,
            ),
            ParityTestCase(
                "Type check string",
                'Set s to _"hello"_. Give back s is Text.',
                True,
                True,
            ),
        ]
    )

    return tests


def create_named_argument_tests() -> list[ParityTestCase]:
    """Create tests for named arguments."""
    tests = []

    tests.extend(
        [
            # Named arguments with 'where'
            ParityTestCase(
                "Named args simple",
                """### **Subtract**: `subtract`
#### Inputs:
- minuend: Number
- subtrahend: Number
Give back minuend - subtrahend.

Use subtract where minuend is _10_, subtrahend is _3_.""",
                True,
                7,
            ),
            # Named args different order
            ParityTestCase(
                "Named args reordered",
                """### **Divide**: `divide`
#### Inputs:
- dividend: Number
- divisor: Number
Give back dividend / divisor.

Use divide where divisor is _2_, dividend is _10_.""",
                True,
                5.0,
            ),
        ]
    )

    return tests


def create_default_parameter_tests() -> list[ParityTestCase]:
    """Create tests for default parameters."""
    tests = []

    tests.extend(
        [
            # Default parameter values
            ParityTestCase(
                "Default param",
                """### **Greet**: `greet`
#### Inputs:
- name: Text = _"World"_
Give back _"Hello, "_ + name + _"!"_.

Use greet.""",
                True,
                "Hello, World!",
            ),
            ParityTestCase(
                "Override default",
                """### **Greet**: `greet`
#### Inputs:
- name: Text = _"World"_
Give back _"Hello, "_ + name + _"!"_.

Use greet with _"Alice"_.""",
                True,
                "Hello, Alice!",
            ),
        ]
    )

    return tests


def create_special_keyword_tests() -> list[ParityTestCase]:
    """Create tests for special keywords."""
    tests = []

    tests.extend(
        [
            # Tell statement (alias for Say)
            ParityTestCase(
                "Tell statement",
                'Tell _"Hello from Tell"_.',
                True,
                "Hello from Tell",
            ),
            # Set using (function call in assignment)
            ParityTestCase(
                "Set using",
                """### **Square**: `square`
#### Inputs:
- n: Number
Give back n * n.

Set result using square with _5_.
Give back result.""",
                True,
                25,
            ),
            # Empty literal
            ParityTestCase(
                "Empty value",
                "Give back _empty_.",
                True,
                None,
            ),
            # Empty check
            ParityTestCase(
                "Check empty",
                "Set x to _empty_. Give back x equals _empty_.",
                True,
                True,
            ),
        ]
    )

    return tests


def run_advanced_feature_tests() -> tuple[int, int]:
    """Run all advanced feature tests and return results.

    Returns:
        Tuple of (passed_count, failed_count).
    """
    print("=" * 60)
    print("ADVANCED FEATURE TEST SUITE")
    print("=" * 60)

    runner = ParityTestRunner(verbose=False)
    all_tests = []

    # Collect all tests
    print("\nCollecting tests...")
    utility_tests = create_utility_tests()
    action_tests = create_action_interaction_tests()
    control_tests = create_control_flow_tests()
    type_tests = create_type_annotation_tests()
    named_arg_tests = create_named_argument_tests()
    default_tests = create_default_parameter_tests()
    keyword_tests = create_special_keyword_tests()

    all_tests.extend(utility_tests)
    all_tests.extend(action_tests)
    all_tests.extend(control_tests)
    all_tests.extend(type_tests)
    all_tests.extend(named_arg_tests)
    all_tests.extend(default_tests)
    all_tests.extend(keyword_tests)

    print(f"Total advanced feature tests: {len(all_tests)}")
    print(f"  Utilities: {len(utility_tests)}")
    print(f"  Actions/Interactions: {len(action_tests)}")
    print(f"  Control flow: {len(control_tests)}")
    print(f"  Type annotations: {len(type_tests)}")
    print(f"  Named arguments: {len(named_arg_tests)}")
    print(f"  Default parameters: {len(default_tests)}")
    print(f"  Special keywords: {len(keyword_tests)}")

    # Run tests
    print("\nRunning advanced feature tests...")
    results, passed, failed = runner.run_tests(all_tests)

    # Report results by category
    categories = {
        "Utilities": utility_tests,
        "Actions": action_tests,
        "Control": control_tests,
        "Types": type_tests,
        "Named Args": named_arg_tests,
        "Defaults": default_tests,
        "Keywords": keyword_tests,
    }

    print("\n" + "=" * 60)
    print("RESULTS BY CATEGORY")
    print("=" * 60)

    for cat_name, cat_tests in categories.items():
        cat_results = [r for r in results if r.test in cat_tests]
        cat_passed = sum(1 for r in cat_results if r.result.name == "SUCCESS")
        print(f"{cat_name:12} : {cat_passed}/{len(cat_results)} passed")

    # Overall summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"Total:  {len(all_tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    if len(all_tests) > 0:
        print(f"Rate:   {passed/len(all_tests)*100:.1f}%")

    # Show failures if any
    if failed > 0:
        print("\n" + "=" * 60)
        print("FAILED TESTS")
        print("=" * 60)
        for result in results:
            if result.result.name != "SUCCESS":
                print(f"\n{result.test.name}:")
                print(f"  Result: {result.result.name}")
                if result.errors:
                    for error in result.errors:
                        print(f"  Error: {error}")
                if result.result.name == "EXEC_MISMATCH":
                    print(f"  Interpreter: {result.interpreter_result}")
                    print(f"  VM:          {result.vm_result}")

    return passed, failed


# ========== Pytest Test Functions ==========


def test_utilities() -> None:
    """Test utility (function) definitions for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_utility_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Utility tests failed:\n" + "\n".join(failures))


def test_actions_interactions() -> None:
    """Test Actions and Interactions for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_action_interaction_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Action/Interaction tests failed:\n" + "\n".join(failures))


def test_advanced_control_flow() -> None:
    """Test advanced control flow for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_control_flow_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Control flow tests failed:\n" + "\n".join(failures))


def test_type_annotations() -> None:
    """Test type annotations for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_type_annotation_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Type annotation tests failed:\n" + "\n".join(failures))


def test_named_arguments() -> None:
    """Test named arguments for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_named_argument_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Named argument tests failed:\n" + "\n".join(failures))


def test_default_parameters() -> None:
    """Test default parameters for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_default_parameter_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Default parameter tests failed:\n" + "\n".join(failures))


def test_special_keywords() -> None:
    """Test special keywords for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_special_keyword_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Special keyword tests failed:\n" + "\n".join(failures))


if __name__ == "__main__":
    passed, failed = run_advanced_feature_tests()
    if failed > 0:
        exit(1)
