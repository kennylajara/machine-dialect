"""Acceptance tests for Machine Dialect components.

This module tests that all components (parser, CFG parser, compiler/VM)
handle ALL features. Tests are expected to fail for unsupported features.
NO WORKAROUNDS - all components are tested equally.
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
class IntegrationTestCase:
    """Represents a test case for acceptance testing."""

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
    """Runs acceptance tests across all Machine Dialect components."""

    def __init__(self) -> None:
        """Initialize the acceptance test runner."""
        self.test_cases: list[IntegrationTestCase] = []
        self.parser = Parser()
        self.cfg_parser = CFGParser()
        self.code_generator = CodeGenerator()
        self.vm = VM()
        self._setup_test_cases()

    def _setup_test_cases(self) -> None:
        """Set up ALL test cases for acceptance testing."""
        self.test_cases = [
            # ========== BASIC LITERALS ==========
            IntegrationTestCase(
                name="integer_literal",
                code="Give back _42_.",
                expected_output=42,
                description="Integer literal",
            ),
            IntegrationTestCase(
                name="float_literal",
                code="Give back _3.14_.",
                expected_output=3.14,
                description="Float literal",
            ),
            IntegrationTestCase(
                name="string_literal",
                code='Give back _"hello"_.',
                expected_output="hello",
                description="String literal",
            ),
            IntegrationTestCase(
                name="boolean_true",
                code="Give back _true_.",
                expected_output=True,
                description="Boolean true literal",
            ),
            IntegrationTestCase(
                name="boolean_false",
                code="Give back _false_.",
                expected_output=False,
                description="Boolean false literal",
            ),
            IntegrationTestCase(
                name="boolean_yes",
                code="Give back _Yes_.",
                expected_output=True,
                description="Boolean Yes as true",
            ),
            IntegrationTestCase(
                name="boolean_no",
                code="Give back _No_.",
                expected_output=False,
                description="Boolean No as false",
            ),
            IntegrationTestCase(
                name="empty_literal",
                code="Give back _empty_.",
                expected_output=None,
                description="Empty (null) literal",
            ),
            IntegrationTestCase(
                name="url_literal",
                code='Give back _"https://example.com"_.',
                expected_output="https://example.com",
                description="URL literal",
            ),
            # ========== VARIABLE OPERATIONS ==========
            IntegrationTestCase(
                name="set_integer",
                code="Set x to _42_. Give back x.",
                expected_output=42,
                description="Set and retrieve integer variable",
            ),
            IntegrationTestCase(
                name="set_float",
                code="Set x to _3.14_. Give back x.",
                expected_output=3.14,
                description="Set and retrieve float variable",
            ),
            IntegrationTestCase(
                name="set_string",
                code='Set x to _"hello"_. Give back x.',
                expected_output="hello",
                description="Set and retrieve string variable",
            ),
            IntegrationTestCase(
                name="set_boolean",
                code="Set x to _true_. Give back x.",
                expected_output=True,
                description="Set and retrieve boolean variable",
            ),
            IntegrationTestCase(
                name="variable_reassignment",
                code="Set x to _10_. Set x to _20_. Give back x.",
                expected_output=20,
                description="Variable reassignment",
            ),
            # ========== ARITHMETIC OPERATIONS ==========
            IntegrationTestCase(
                name="addition",
                code="Give back _5_ + _3_.",
                expected_output=8,
                description="Addition operation",
            ),
            IntegrationTestCase(
                name="subtraction",
                code="Give back _10_ - _4_.",
                expected_output=6,
                description="Subtraction operation",
            ),
            IntegrationTestCase(
                name="multiplication",
                code="Give back _3_ * _7_.",
                expected_output=21,
                description="Multiplication operation",
            ),
            IntegrationTestCase(
                name="division",
                code="Give back _15_ / _3_.",
                expected_output=5.0,
                description="Division operation",
            ),
            IntegrationTestCase(
                name="complex_arithmetic",
                code="Give back (_5_ + _3_) * _2_.",
                expected_output=16,
                description="Complex arithmetic with parentheses",
            ),
            IntegrationTestCase(
                name="negation",
                code="Give back -_5_.",
                expected_output=-5,
                description="Unary negation",
            ),
            # ========== COMPARISON OPERATIONS ==========
            IntegrationTestCase(
                name="equals",
                code="Give back _5_ equals _5_.",
                expected_output=True,
                description="Equality comparison",
            ),
            IntegrationTestCase(
                name="not_equals",
                code="Give back _5_ is not _3_.",
                expected_output=True,
                description="Inequality comparison",
            ),
            IntegrationTestCase(
                name="greater_than",
                code="Give back _7_ > _3_.",
                expected_output=True,
                description="Greater than comparison",
            ),
            IntegrationTestCase(
                name="less_than",
                code="Give back _2_ < _8_.",
                expected_output=True,
                description="Less than comparison",
            ),
            IntegrationTestCase(
                name="greater_or_equal",
                code="Give back _5_ >= _5_.",
                expected_output=True,
                description="Greater or equal comparison",
            ),
            IntegrationTestCase(
                name="less_or_equal",
                code="Give back _3_ <= _5_.",
                expected_output=True,
                description="Less or equal comparison",
            ),
            # ========== NATURAL LANGUAGE OPERATORS ==========
            IntegrationTestCase(
                name="is_equal_to",
                code="Give back _5_ is equal to _5_.",
                expected_output=True,
                description="Natural language equality",
            ),
            IntegrationTestCase(
                name="is_not_equal_to",
                code="Give back _5_ is not equal to _3_.",
                expected_output=True,
                description="Natural language inequality",
            ),
            IntegrationTestCase(
                name="is_greater_than",
                code="Give back _7_ is greater than _3_.",
                expected_output=True,
                description="Natural language greater than",
            ),
            IntegrationTestCase(
                name="is_less_than",
                code="Give back _2_ is less than _8_.",
                expected_output=True,
                description="Natural language less than",
            ),
            IntegrationTestCase(
                name="is_more_than",
                code="Give back _7_ is more than _3_.",
                expected_output=True,
                description="Alternative natural language greater than",
            ),
            IntegrationTestCase(
                name="is_under",
                code="Give back _2_ is under _8_.",
                expected_output=True,
                description="Alternative natural language less than",
            ),
            IntegrationTestCase(
                name="is_at_least",
                code="Give back _5_ is at least _5_.",
                expected_output=True,
                description="Natural language greater or equal",
            ),
            IntegrationTestCase(
                name="is_at_most",
                code="Give back _3_ is at most _5_.",
                expected_output=True,
                description="Natural language less or equal",
            ),
            # ========== STRICT EQUALITY ==========
            IntegrationTestCase(
                name="strict_equality_same",
                code="Give back _5_ is strictly equal to _5_.",
                expected_output=True,
                description="Strict equality same type",
            ),
            IntegrationTestCase(
                name="strict_equality_diff",
                code="Give back _5_ is strictly equal to _5.0_.",
                expected_output=False,
                description="Strict equality different types",
            ),
            IntegrationTestCase(
                name="strict_inequality",
                code="Give back _5_ is not strictly equal to _5.0_.",
                expected_output=True,
                description="Strict inequality",
            ),
            IntegrationTestCase(
                name="is_identical_to",
                code="Give back _5_ is identical to _5_.",
                expected_output=True,
                description="Alternative strict equality",
            ),
            IntegrationTestCase(
                name="is_exactly_equal_to",
                code="Give back _5_ is exactly equal to _5_.",
                expected_output=True,
                description="Another alternative strict equality",
            ),
            # ========== LOGICAL OPERATIONS ==========
            IntegrationTestCase(
                name="logical_and",
                code="Give back _true_ and _true_.",
                expected_output=True,
                description="Logical AND operation",
            ),
            IntegrationTestCase(
                name="logical_or",
                code="Give back _false_ or _true_.",
                expected_output=True,
                description="Logical OR operation",
            ),
            IntegrationTestCase(
                name="logical_not",
                code="Give back not _true_.",
                expected_output=False,
                description="Logical NOT operation",
            ),
            # ========== CONTROL FLOW ==========
            IntegrationTestCase(
                name="if_statement_true",
                code="If _true_ then:\n> Give back _1_.\nElse:\n> Give back _0_.",
                expected_output=1,
                description="If statement with true condition",
            ),
            IntegrationTestCase(
                name="if_statement_false",
                code="If _false_ then:\n> Give back _1_.\nElse:\n> Give back _0_.",
                expected_output=0,
                description="If statement with false condition",
            ),
            IntegrationTestCase(
                name="if_expression",
                code="Give back _'yes'_ if _true_ else _'no'_.",
                expected_output="yes",
                description="Conditional expression",
            ),
            IntegrationTestCase(
                name="when_statement",
                code="When _true_ then:\n> Give back _1_.\nOtherwise:\n> Give back _0_.",
                expected_output=1,
                description="When/Otherwise alternative syntax",
            ),
            IntegrationTestCase(
                name="nested_if",
                code="""Set x to _10_.
If x > _5_ then:
> If x > _8_ then:
> > Give back _100_.
> Else:
> > Give back _50_.
Else:
> Give back _0_.""",
                expected_output=100,
                description="Nested if statements",
            ),
            # ========== SAY STATEMENT ==========
            IntegrationTestCase(
                name="say_string",
                code='Say _"Hello, World!"_.',
                expected_output=None,
                description="Say statement with string",
            ),
            IntegrationTestCase(
                name="say_variable",
                code='Set msg to _"Hello"_. Say msg.',
                expected_output=None,
                description="Say statement with variable",
            ),
            IntegrationTestCase(
                name="tell_statement",
                code='Tell _"Hello, World!"_.',
                expected_output=None,
                description="Tell statement alternative",
            ),
            # ========== UTILITY DEFINITIONS ==========
            IntegrationTestCase(
                name="utility_no_params",
                code="""
### **Utility**: `get_answer`

<details>
<summary>Returns the answer to everything.</summary>

> Give back _42_.

</details>

Use `get_answer`.
""",
                expected_output=42,
                description="Utility without parameters",
            ),
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
                description="Utility with positional parameters",
            ),
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
                description="Utility with named arguments",
            ),
            IntegrationTestCase(
                name="utility_default_params",
                code="""
### **Utility**: `greet`

<details>
<summary>Creates a greeting.</summary>

> Give back `greeting`.

</details>

#### Inputs:
- `name` **as** Text (required)
- `greeting` **as** Text (optional, default: _"Hello"_)

Use `greet` with _"World"_.
""",
                expected_output="Hello",
                description="Utility with default parameters",
            ),
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
                description="Utility with conditional logic",
            ),
            IntegrationTestCase(
                name="utility_recursive",
                code="""
### **Utility**: `factorial`

<details>
<summary>Calculates factorial.</summary>

> If `n` <= _1_ then:
> > Give back _1_.
> Else:
> > Set `n_minus_1` to `n` - _1_.
> > Set `sub_factorial` using `factorial` with `n_minus_1`.
> > Give back `n` * `sub_factorial`.

</details>

#### Inputs:
- `n` **as** Number (required)

Use `factorial` with _5_.
""",
                expected_output=120,
                description="Recursive utility",
            ),
            # ========== SET USING ==========
            IntegrationTestCase(
                name="set_using_basic",
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
                description="Set using utility call",
            ),
            IntegrationTestCase(
                name="set_using_named",
                code="""
### **Utility**: `subtract`

<details>
<summary>Subtracts two numbers.</summary>

> Give back `minuend` - `subtrahend`.

</details>

#### Inputs:
- `minuend` **as** Number (required)
- `subtrahend` **as** Number (required)

Set `result` using `subtract` where `subtrahend` is _7_, `minuend` is _20_.
Give back `result`.
""",
                expected_output=13,
                description="Set using with named arguments",
            ),
            # ========== BACKTICK IDENTIFIERS ==========
            IntegrationTestCase(
                name="backtick_variable",
                code="Set `my_var` to _42_. Give back `my_var`.",
                expected_output=42,
                description="Backtick identifier in variable",
            ),
            IntegrationTestCase(
                name="backtick_multiword",
                code="Set `my special variable` to _100_. Give back `my special variable`.",
                expected_output=100,
                description="Multi-word backtick identifier",
            ),
            # ========== BOLD VARIABLES ==========
            IntegrationTestCase(
                name="bold_variable",
                code="Set **x** to _42_. Give back **x**.",
                expected_output=42,
                description="Bold variable syntax",
            ),
            IntegrationTestCase(
                name="bold_multiword",
                code="Set **my variable** to _100_. Give back **my variable**.",
                expected_output=100,
                description="Multi-word bold variable",
            ),
            # ========== ACTIONS AND INTERACTIONS ==========
            IntegrationTestCase(
                name="action_basic",
                code="""
Action calculate_sum with a as Number, b as Number:
> Give back a + b.

Use calculate_sum with _10_, _20_.
""",
                expected_output=30,
                description="Basic action definition",
            ),
            IntegrationTestCase(
                name="interaction_basic",
                code="""
Interaction get_user_data:
> Give back _"user data"_.

Use get_user_data.
""",
                expected_output="user data",
                description="Basic interaction definition",
            ),
            # ========== TYPE ANNOTATIONS ==========
            IntegrationTestCase(
                name="type_integer",
                code="""
### **Utility**: `process`

<details>
<summary>Process integer.</summary>

> Give back `x`.

</details>

#### Inputs:
- `x` **as** Integer (required)

Use `process` with _42_.
""",
                expected_output=42,
                description="Integer type annotation",
            ),
            IntegrationTestCase(
                name="type_float",
                code="""
### **Utility**: `process`

<details>
<summary>Process float.</summary>

> Give back `x`.

</details>

#### Inputs:
- `x` **as** Float (required)

Use `process` with _3.14_.
""",
                expected_output=3.14,
                description="Float type annotation",
            ),
            IntegrationTestCase(
                name="type_boolean",
                code="""
### **Utility**: `process`

<details>
<summary>Process boolean.</summary>

> Give back `x`.

</details>

#### Inputs:
- `x` **as** Boolean (required)

Use `process` with _true_.
""",
                expected_output=True,
                description="Boolean type annotation",
            ),
            IntegrationTestCase(
                name="type_text",
                code="""
### **Utility**: `process`

<details>
<summary>Process text.</summary>

> Give back `x`.

</details>

#### Inputs:
- `x` **as** Text (required)

Use `process` with _"hello"_.
""",
                expected_output="hello",
                description="Text type annotation",
            ),
            IntegrationTestCase(
                name="type_url",
                code="""
### **Utility**: `process`

<details>
<summary>Process URL.</summary>

> Give back `x`.

</details>

#### Inputs:
- `x` **as** URL (required)

Use `process` with _"https://example.com"_.
""",
                expected_output="https://example.com",
                description="URL type annotation",
            ),
            # ========== COMPLEX NESTED STRUCTURES ==========
            IntegrationTestCase(
                name="nested_utilities",
                code="""
### **Utility**: `double`

<details>
<summary>Doubles a number.</summary>

> Give back `n` * _2_.

</details>

#### Inputs:
- `n` **as** Number (required)

### **Utility**: `quadruple`

<details>
<summary>Quadruples a number.</summary>

> Set `doubled` using `double` with `n`.
> Set `result` using `double` with `doubled`.
> Give back `result`.

</details>

#### Inputs:
- `n` **as** Number (required)

Use `quadruple` with _5_.
""",
                expected_output=20,
                description="Nested utility calls",
            ),
            IntegrationTestCase(
                name="complex_workflow",
                code="""
### **Utility**: `calculate_discount`

<details>
<summary>Calculates discount amount.</summary>

> Give back `price` * `rate` / _100_.

</details>

#### Inputs:
- `price` **as** Number (required)
- `rate` **as** Number (required)

### **Utility**: `apply_discount`

<details>
<summary>Applies discount to price.</summary>

> Set `discount` using `calculate_discount` where `price` is `original`, `rate` is `percent`.
> Give back `original` - `discount`.

</details>

#### Inputs:
- `original` **as** Number (required)
- `percent` **as** Number (required)

Set `final` using `apply_discount` where `original` is _100_, `percent` is _20_.
Give back `final`.
""",
                expected_output=80.0,
                description="Complex utility workflow",
            ),
            # ========== OUTPUTS SECTION ==========
            IntegrationTestCase(
                name="utility_with_outputs",
                code="""
### **Utility**: `get_pi`

<details>
<summary>Returns pi.</summary>

> Give back _3.14159_.

</details>

#### Outputs:
- Returns Float

Use `get_pi`.
""",
                expected_output=3.14159,
                description="Utility with outputs section",
            ),
            # ========== DEPRECATED CALL SYNTAX ==========
            IntegrationTestCase(
                name="call_syntax",
                code="""
### **Utility**: `add`

<details>
<summary>Adds two numbers.</summary>

> Give back `a` + `b`.

</details>

#### Inputs:
- `a` **as** Number (required)
- `b` **as** Number (required)

Call `add` with _10_, _20_.
""",
                expected_output=30,
                description="Deprecated Call syntax",
            ),
        ]

    def test_parser(self, test_case: IntegrationTestCase) -> TestResult:
        """Test the parser component.

        Args:
            test_case: The test case to run.

        Returns:
            TestResult indicating success or failure.
        """
        try:
            parser = Parser()
            ast = parser.parse(test_case.code)
            if parser.errors:
                return TestResult(
                    component="Parser",
                    success=False,
                    output=None,
                    error=f"Parser errors: {parser.errors}",
                )
            return TestResult(component="Parser", success=True, output=ast, error=None)
        except Exception as e:
            return TestResult(component="Parser", success=False, output=None, error=str(e))

    def test_cfg_parser(self, test_case: IntegrationTestCase) -> TestResult:
        """Test the CFG parser component.

        Args:
            test_case: The test case to run.

        Returns:
            TestResult indicating success or failure.
        """
        try:
            cfg_parser = CFGParser()
            tree = cfg_parser.parse(test_case.code)
            return TestResult(component="CFG Parser", success=True, output=tree, error=None)
        except Exception as e:
            return TestResult(component="CFG Parser", success=False, output=None, error=str(e))

    def test_interpreter(self, test_case: IntegrationTestCase) -> TestResult:
        """Test the interpreter component.

        Args:
            test_case: The test case to run.

        Returns:
            TestResult indicating success or failure.
        """
        try:
            parser = Parser()
            ast = parser.parse(test_case.code)
            if parser.errors:
                return TestResult(
                    component="Interpreter",
                    success=False,
                    output=None,
                    error=f"Parser errors: {parser.errors}",
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

    def test_vm(self, test_case: IntegrationTestCase) -> TestResult:
        """Test the VM component.

        Args:
            test_case: The test case to run.

        Returns:
            TestResult indicating success or failure.
        """
        try:
            parser = Parser()
            ast = parser.parse(test_case.code)
            if parser.errors:
                return TestResult(
                    component="VM",
                    success=False,
                    output=None,
                    error=f"Parser errors: {parser.errors}",
                )

            # Compile to bytecode
            code_generator = CodeGenerator()
            module = code_generator.compile(ast)
            if code_generator.errors:
                return TestResult(
                    component="VM",
                    success=False,
                    output=None,
                    error=f"Compiler errors: {code_generator.errors}",
                )

            # Execute in VM
            vm = VM()
            result = vm.run(module)
            success = result == test_case.expected_output if test_case.expected_output is not None else True
            error = None
            if not success and test_case.expected_output is not None:
                error = f"Expected {test_case.expected_output!r}, got {result!r}"
            return TestResult(component="VM", success=success, output=result, error=error)
        except Exception as e:
            return TestResult(component="VM", success=False, output=None, error=str(e))

    def run_test(self, test_case: IntegrationTestCase) -> dict[str, TestResult]:
        """Run a single test case through all components.

        Args:
            test_case: The test case to run.

        Returns:
            Dictionary mapping component names to their test results.
        """
        results = {}

        # Test ALL components - NO CONDITIONS, NO WORKAROUNDS
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
        print("\n" + "=" * 100)
        print("ACCEPTANCE TEST RESULTS - ALL FEATURES TESTED EQUALLY")
        print("NO WORKAROUNDS - FAILURES ARE EXPECTED FOR UNSUPPORTED FEATURES")
        print("=" * 100)

        # Components to test
        components = ["Parser", "CFG Parser", "Interpreter", "VM"]

        # Print column headers
        print(f"{'Test Case':<30} | ", end="")
        for comp in components:
            print(f"{comp:<12} | ", end="")
        print("\n" + "-" * 100)

        # Print results for each test
        for test_name, test_results in results.items():
            print(f"{test_name:<30} | ", end="")
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
        print("\n" + "=" * 100)
        print("SUMMARY")
        print("-" * 100)

        for comp in components:
            passed = sum(
                1 for test_results in results.values() if test_results.get(comp, TestResult(comp, False, None)).success
            )
            total = len(results)
            percentage = (passed / total * 100) if total > 0 else 0
            print(f"{comp:<15}: {passed}/{total} passed ({percentage:.1f}%)")

        # Print detailed errors (sample)
        print("\n" + "=" * 100)
        print("SAMPLE ERRORS (showing first 10 failures per component)")
        print("-" * 100)

        for comp in components:
            print(f"\n{comp}:")
            error_count = 0
            for test_name, test_results in results.items():
                if error_count >= 10:
                    remaining = sum(
                        1
                        for t_name, t_results in results.items()
                        if t_name not in list(results.keys())[:error_count]
                        and t_results.get(comp)
                        and not t_results[comp].success
                    )
                    if remaining > 0:
                        print(f"  ... and {remaining} more failures")
                    break
                result = test_results.get(comp)
                if result and not result.success and result.error:
                    error_count += 1
                    # Truncate long error messages
                    error_msg = result.error[:80] + "..." if len(result.error) > 80 else result.error
                    print(f"  [{test_name}]: {error_msg}")

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
            URL,
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
        elif isinstance(obj, URL):
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
    """Test that all components work on all features - failures expected."""
    runner = IntegrationTestRunner()
    results = runner.run_all_tests()
    runner.print_results(results)

    # NO ASSERTIONS - we expect failures
    # This test documents what each component supports
