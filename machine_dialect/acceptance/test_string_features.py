"""String feature tests for Machine Dialect feature parity.

This module tests string handling including escaping, unicode, and
multi-line strings across all components.
"""

import pytest

from machine_dialect.acceptance.parity_test_framework import ParityTestCase, ParityTestRunner


def create_escape_sequence_tests() -> list[ParityTestCase]:
    """Create tests for string escape sequences."""
    tests = []

    tests.extend(
        [
            # Basic escape sequences
            ParityTestCase("Newline escape", r'Give back _"Line 1\nLine 2"_.', True, "Line 1\nLine 2"),
            ParityTestCase("Tab escape", r'Give back _"Col1\tCol2"_.', True, "Col1\tCol2"),
            ParityTestCase("Quote escape", r'Give back _"He said \"Hello\""_.', True, 'He said "Hello"'),
            ParityTestCase("Single quote string", "Give back _'Hello World'_.", True, "Hello World"),
            ParityTestCase("Single quote escape", r"Give back _'It\'s great'_.", True, "It's great"),
            ParityTestCase("Backslash escape", r'Give back _"Path\\to\\file"_.', True, "Path\\to\\file"),
            # Multiple escapes
            ParityTestCase(
                "Multiple escapes",
                r'Give back _"Line 1\n\tIndented\n\"Quoted\""_.',
                True,
                'Line 1\n\tIndented\n"Quoted"',
            ),
            # Raw strings (no escaping)
            ParityTestCase("Carriage return", r'Give back _"Hello\rWorld"_.', True, "Hello\rWorld"),
            ParityTestCase("Form feed", r'Give back _"Page\fBreak"_.', True, "Page\fBreak"),
            ParityTestCase("Vertical tab", r'Give back _"Vertical\vTab"_.', True, "Vertical\vTab"),
        ]
    )

    return tests


def create_unicode_tests() -> list[ParityTestCase]:
    """Create tests for Unicode string handling."""
    tests = []

    tests.extend(
        [
            # Basic Unicode
            ParityTestCase("Chinese characters", 'Give back _"你好世界"_.', True, "你好世界"),
            ParityTestCase("Japanese characters", 'Give back _"こんにちは"_.', True, "こんにちは"),
            ParityTestCase("Arabic characters", 'Give back _"مرحبا"_.', True, "مرحبا"),
            ParityTestCase("Emoji", 'Give back _"Hello 🌍 World 🚀"_.', True, "Hello 🌍 World 🚀"),
            ParityTestCase("Mixed scripts", 'Give back _"Hello 世界 مرحبا"_.', True, "Hello 世界 مرحبا"),
            # Unicode escapes
            ParityTestCase("Unicode escape basic", r'Give back _"\u0048\u0065\u006C\u006C\u006F"_.', True, "Hello"),
            ParityTestCase("Unicode escape emoji", r'Give back _"\u{1F600}"_.', True, "😀"),
            # Complex Unicode
            ParityTestCase(
                "Mathematical symbols",
                'Give back _"∀x ∈ ℝ: x² ≥ 0"_.',  # noqa: RUF001
                True,
                "∀x ∈ ℝ: x² ≥ 0",  # noqa: RUF001
            ),
            ParityTestCase(
                "Box drawing",
                'Give back _"┌─┐│ │└─┘"_.',
                True,
                "┌─┐│ │└─┘",
            ),
        ]
    )

    return tests


def create_string_operation_tests() -> list[ParityTestCase]:
    """Create tests for string operations."""
    tests = []

    tests.extend(
        [
            # String concatenation (if supported)
            ParityTestCase(
                "String concatenation",
                'Give back _"Hello"_ + _" "_ + _"World"_.',
                True,
                "Hello World",
            ),
            ParityTestCase(
                "String with number concat",
                'Give back _"Number: "_ + _"42"_.',
                True,
                "Number: 42",
            ),
            # String comparison
            ParityTestCase("String equality true", 'Give back _"hello"_ equals _"hello"_.', True, True),
            ParityTestCase("String equality false", 'Give back _"hello"_ equals _"world"_.', True, False),
            ParityTestCase("String less than", 'Give back _"apple"_ < _"banana"_.', True, True),
            ParityTestCase("String greater than", 'Give back _"zebra"_ > _"apple"_.', True, True),
            # Empty strings
            ParityTestCase("Empty string", 'Give back _""_.', True, ""),
            ParityTestCase("Empty string equals", 'Give back _""_ equals _""_.', True, True),
            ParityTestCase("Empty string concat", 'Give back _""_ + _"text"_ + _""_.', True, "text"),
        ]
    )

    return tests


def create_multiline_string_tests() -> list[ParityTestCase]:
    """Create tests for multi-line strings."""
    tests = []

    tests.extend(
        [
            # Multi-line strings with actual newlines
            ParityTestCase(
                "Multi-line literal",
                """Give back _"Line 1
Line 2
Line 3"_.""",
                True,
                "Line 1\nLine 2\nLine 3",
            ),
            # Mixed quotes
            ParityTestCase(
                "Mixed quotes in string",
                """Give back _"She said 'Hello' to him"_.""",
                True,
                "She said 'Hello' to him",
            ),
            ParityTestCase(
                "Double in single quotes",
                """Give back _'He said "Hi" back'_.""",
                True,
                'He said "Hi" back',
            ),
        ]
    )

    return tests


def create_special_string_tests() -> list[ParityTestCase]:
    """Create tests for special string cases."""
    tests = []

    tests.extend(
        [
            # Very long strings
            ParityTestCase(
                "Long string",
                f'Give back _"{"a" * 1000}"_.',
                True,
                "a" * 1000,
            ),
            # Strings with special patterns
            ParityTestCase(
                "URL in string",
                'Give back _"Visit https://example.com for more"_.',
                True,
                "Visit https://example.com for more",
            ),
            ParityTestCase(
                "Path in string",
                'Give back _"/home/user/documents/file.txt"_.',
                True,
                "/home/user/documents/file.txt",
            ),
            ParityTestCase(
                "Windows path",
                r'Give back _"C:\\Users\\Documents\\file.txt"_.',
                True,
                "C:\\Users\\Documents\\file.txt",
            ),
            # Strings with code
            ParityTestCase(
                "Code in string",
                'Give back _"Set x to _42_."_.',
                True,
                "Set x to _42_.",
            ),
            ParityTestCase(
                "JSON in string",
                r'Give back _"{\"key\": \"value\", \"number\": 42}"_.',
                True,
                '{"key": "value", "number": 42}',
            ),
        ]
    )

    return tests


def run_string_feature_tests() -> tuple[int, int]:
    """Run all string feature tests and return results.

    Returns:
        Tuple of (passed_count, failed_count).
    """
    print("=" * 60)
    print("STRING FEATURE TEST SUITE")
    print("=" * 60)

    runner = ParityTestRunner(verbose=False)
    all_tests = []

    # Collect all string tests
    print("\nCollecting tests...")
    escape_tests = create_escape_sequence_tests()
    unicode_tests = create_unicode_tests()
    operation_tests = create_string_operation_tests()
    multiline_tests = create_multiline_string_tests()
    special_tests = create_special_string_tests()

    all_tests.extend(escape_tests)
    all_tests.extend(unicode_tests)
    all_tests.extend(operation_tests)
    all_tests.extend(multiline_tests)
    all_tests.extend(special_tests)

    print(f"Total string tests: {len(all_tests)}")
    print(f"  Escape sequences: {len(escape_tests)}")
    print(f"  Unicode: {len(unicode_tests)}")
    print(f"  Operations: {len(operation_tests)}")
    print(f"  Multi-line: {len(multiline_tests)}")
    print(f"  Special cases: {len(special_tests)}")

    # Run tests
    print("\nRunning string tests...")
    results, passed, failed = runner.run_tests(all_tests)

    # Report results by category
    categories = {
        "Escapes": escape_tests,
        "Unicode": unicode_tests,
        "Operations": operation_tests,
        "Multi-line": multiline_tests,
        "Special": special_tests,
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


def test_escape_sequences() -> None:
    """Test string escape sequences for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_escape_sequence_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Escape sequence tests failed:\n" + "\n".join(failures))


def test_unicode_strings() -> None:
    """Test Unicode string handling for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_unicode_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Unicode string tests failed:\n" + "\n".join(failures))


def test_string_operations() -> None:
    """Test string operations for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_string_operation_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("String operation tests failed:\n" + "\n".join(failures))


def test_multiline_strings() -> None:
    """Test multi-line string handling for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_multiline_string_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Multi-line string tests failed:\n" + "\n".join(failures))


def test_special_strings() -> None:
    """Test special string cases for parity."""
    runner = ParityTestRunner(verbose=False)
    tests = create_special_string_tests()
    results, passed, failed = runner.run_tests(tests)

    if failed > 0:
        failures = []
        for result in results:
            if result.result.name != "SUCCESS":
                failures.append(f"{result.test.name}: {result.result.name}")
        pytest.fail("Special string tests failed:\n" + "\n".join(failures))


if __name__ == "__main__":
    passed, failed = run_string_feature_tests()
    if failed > 0:
        exit(1)
