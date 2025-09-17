"""Comprehensive test suite for validating parity between main parser and CFG parser.

This test suite ensures that both the main recursive descent parser and the CFG (Lark-based)
parser handle all Machine Dialect™ language constructs consistently. Tests verify that both
parsers either succeed or fail for the same input, documenting any parity gaps.

The goal is 100% feature parity - any test marked with xfail indicates a parity gap that
needs to be fixed in the CFG parser implementation.
"""

from typing import Any

import pytest
from lark import Tree

from machine_dialect.ast.ast_node import ASTNode
from machine_dialect.cfg import CFGParser
from machine_dialect.parser import Parser

# =============================================================================
# Helper Functions
# =============================================================================


def parse_with_main(code: str) -> tuple[bool, ASTNode | None, str | None]:
    """Parse code with the main parser.

    Args:
        code: Machine Dialect™ source code

    Returns:
        Tuple of (success, ast_or_none, error_message_or_none)
    """
    try:
        parser = Parser()
        ast = parser.parse(code, check_semantics=False)

        # For parity testing, we only care about SYNTAX errors, not semantic errors.
        # The main parser does semantic validation (undefined variables, type errors, etc.)
        # but the CFG parser only does syntax validation.
        #
        # We consider parsing successful if there are no syntax errors,
        # even if there are semantic errors like undefined variables.
        if hasattr(parser, "errors") and parser.errors:
            from machine_dialect.errors.exceptions import MDSyntaxError

            syntax_errors = [err for err in parser.errors if isinstance(err, MDSyntaxError)]
            if syntax_errors:
                error_messages = [str(err) for err in syntax_errors]
                return (False, None, "; ".join(error_messages))

        return (True, ast, None)
    except Exception as e:
        return (False, None, str(e))


def parse_with_cfg(code: str) -> tuple[bool, Tree[Any] | None, str | None]:
    """Parse code with the CFG parser.

    Args:
        code: Machine Dialect™ source code

    Returns:
        Tuple of (success, tree_or_none, error_message_or_none)
    """
    try:
        parser = CFGParser()
        tree = parser.parse(code)
        return (True, tree, None)
    except Exception as e:
        return (False, None, str(e))


def check_parity(code: str, should_succeed: bool = True) -> tuple[bool, str]:
    """Check if both parsers agree on the given code.

    Args:
        code: Machine Dialect™ source code
        should_succeed: Whether the code should parse successfully

    Returns:
        Tuple of (parity_achieved, diagnostic_message)
    """
    main_success, _main_ast, main_error = parse_with_main(code)
    cfg_success, _cfg_tree, cfg_error = parse_with_cfg(code)

    if main_success == cfg_success:
        if main_success == should_succeed:
            return (True, f"✓ Both parsers {'succeeded' if main_success else 'failed'} as expected")
        else:
            expected = "success" if should_succeed else "failure"
            return (
                True,
                f"⚠ Both parsers {'succeeded' if main_success else 'failed'} but expected {expected}",
            )
    else:
        msg = "✗ Parser disagreement:\n"
        msg += f"  Main parser: {'succeeded' if main_success else f'failed - {main_error}'}\n"
        msg += f"  CFG parser:  {'succeeded' if cfg_success else f'failed - {cfg_error}'}"
        return (False, msg)


def assert_both_succeed(code: str, msg: str = "") -> None:
    """Assert that both parsers successfully parse the code."""
    main_success, _, main_error = parse_with_main(code)
    cfg_success, _, cfg_error = parse_with_cfg(code)

    if not (main_success and cfg_success):
        error_msg = "Expected both parsers to succeed\n"
        error_msg += f"  Main parser: {'succeeded' if main_success else f'failed - {main_error}'}\n"
        error_msg += f"  CFG parser:  {'succeeded' if cfg_success else f'failed - {cfg_error}'}"
        if msg:
            error_msg = f"{msg}\n{error_msg}"
        pytest.fail(error_msg)


def assert_both_fail(code: str, msg: str = "") -> None:
    """Assert that both parsers fail to parse the code."""
    main_success, _, main_error = parse_with_main(code)
    cfg_success, _, cfg_error = parse_with_cfg(code)

    if main_success or cfg_success:
        error_msg = "Expected both parsers to fail\n"
        error_msg += f"  Main parser: {'succeeded (should fail)' if main_success else f'failed - {main_error}'}\n"
        error_msg += f"  CFG parser:  {'succeeded (should fail)' if cfg_success else f'failed - {cfg_error}'}"
        if msg:
            error_msg = f"{msg}\n{error_msg}"
        pytest.fail(error_msg)


def assert_parity(code: str, msg: str = "") -> None:
    """Assert that both parsers agree (both succeed or both fail)."""
    main_success, _, _ = parse_with_main(code)
    cfg_success, _, _ = parse_with_cfg(code)

    if main_success != cfg_success:
        _, diagnostic = check_parity(code)
        pytest.fail(f"{msg}\n{diagnostic}" if msg else diagnostic)


# =============================================================================
# Test Classes
# =============================================================================


class TestBasicConstructs:
    """Test parity for basic language constructs."""

    def test_empty_program(self) -> None:
        """Empty programs should be handled consistently."""
        assert_parity("")
        assert_parity("   ")
        assert_parity("\n\n")

    def test_simple_assignment(self) -> None:
        """Simple Set statements should work in both parsers."""
        assert_both_succeed("Set `x` to _10_.")
        assert_both_succeed("Set `y` to _42_.")
        assert_both_succeed("Set `result` to _0_.")

    def test_give_back_statement(self) -> None:
        """Give back statements should work in both parsers."""
        assert_both_succeed("Give back _42_.")
        assert_both_succeed('Give back _"Hello"_.')
        assert_both_succeed("Give back `x`.")
        assert_both_succeed("Gives back _42_.")  # Alternative form

    def test_multiple_statements(self) -> None:
        """Multiple statements should work in both parsers."""
        code = """Set `x` to _10_.
Set `y` to _20_.
Give back `x` + `y`."""
        assert_both_succeed(code)

    @pytest.mark.xfail(reason="Main parser has issues with comments")
    def test_comments(self) -> None:
        """Comments should be handled consistently."""
        assert_both_succeed("# This is a comment")
        assert_both_succeed("Set `x` to _10_. # Comment after statement")
        assert_both_succeed("# Comment\nSet `x` to _10_.")


class TestLiterals:
    """Test parity for all literal types."""

    def test_integer_literals(self) -> None:
        """Integer literals should work in both parsers."""
        assert_both_succeed("Give back _42_.")
        assert_both_succeed("Give back _0_.")
        assert_both_succeed("Give back _-5_.")
        assert_both_succeed("Give back _999999_.")

    def test_float_literals(self) -> None:
        """Float literals should work in both parsers."""
        assert_both_succeed("Give back _3.14_.")
        assert_both_succeed("Give back _0.0_.")
        assert_both_succeed("Give back _-2.5_.")
        assert_both_succeed("Give back _123.456789_.")

    def test_string_literals(self) -> None:
        """String literals should work in both parsers."""
        assert_both_succeed('Give back _"Hello"_.')
        assert_both_succeed("Give back _'World'_.")
        assert_both_succeed('Give back _"Machine Dialect™"_.')
        assert_both_succeed('Give back _""_.')  # Empty string

    def test_boolean_literals(self) -> None:
        """Boolean literals should work in both parsers."""
        assert_both_succeed("Give back _yes_.")
        assert_both_succeed("Give back _no_.")
        assert_both_succeed("Give back _Yes_.")
        assert_both_succeed("Give back _No_.")

    def test_empty_literal(self) -> None:
        """Empty literal should work in both parsers."""
        assert_both_succeed("Give back _empty_.")
        assert_both_succeed("Set `x` to _empty_.")

    def test_url_literals(self) -> None:
        """URL literals should work in both parsers."""
        assert_both_succeed('Give back _"https://example.com"_.')
        assert_both_succeed('Give back _"http://localhost:3000"_.')
        assert_both_succeed('Give back _"https://api.example.com/v1/users?id=123"_.')

    def test_list_literals(self) -> None:
        """List literals should work in both parsers."""
        assert_both_succeed("Set `items` to:\n- _1_.\n- _2_.\n- _3_.")

    @pytest.mark.xfail(reason="CFG parser doesn't support dictionary literals")
    def test_dictionary_literals(self) -> None:
        """Dictionary literals should work in both parsers."""
        assert_both_succeed('Set `person` to:\n- `name`: _"Alice"_.\n`age`: _30_.')


class TestIdentifiers:
    """Test parity for different identifier formats."""

    def test_simple_identifiers(self) -> None:
        """Simple identifiers should work in both parsers."""
        assert_both_succeed("Set `x` to _10_.")
        assert_both_succeed("Set `variable` to _42_.")
        assert_both_succeed("Set `my_var` to _5_.")

    def test_backtick_identifiers(self) -> None:
        """Backtick identifiers should work in both parsers."""
        assert_both_succeed("Set `x` to _10_.")
        assert_both_succeed("Set `my_variable` to _42_.")
        assert_both_succeed("Give back `result`.")

    def test_multiword_backtick_identifiers(self) -> None:
        """Multi-word backtick identifiers should work in both parsers."""
        assert_both_succeed("Set `my special variable` to _10_.")
        assert_both_succeed('Set `user name` to _"Alice"_.')

    @pytest.mark.xfail(reason="CFG parser doesn't support bold variables")
    def test_bold_variables(self) -> None:
        """Bold variable syntax should work in both parsers."""
        assert_both_succeed("Set **x** to _10_.")
        assert_both_succeed("Give back **result**.")


class TestOperators:
    """Test parity for all operators."""

    def test_arithmetic_operators(self) -> None:
        """Arithmetic operators should work in both parsers."""
        assert_both_succeed("Give back _5_ + _3_.")
        assert_both_succeed("Give back _10_ - _4_.")
        assert_both_succeed("Give back _3_ * _7_.")
        assert_both_succeed("Give back _15_ / _3_.")
        assert_both_succeed("Give back _2_ ^ _3_.")  # Exponentiation

    def test_comparison_operators(self) -> None:
        """Comparison operators should work in both parsers."""
        assert_both_succeed("Give back _5_ < _10_.")
        assert_both_succeed("Give back _10_ > _5_.")
        assert_both_succeed("Give back _5_ <= _5_.")
        assert_both_succeed("Give back _10_ >= _10_.")

    def test_equality_operators(self) -> None:
        """Equality operators should work in both parsers."""
        assert_both_succeed("Give back _5_ equals _5_.")
        assert_both_succeed("Give back _5_ is equal to _5_.")
        assert_both_succeed("Give back _5_ is the same as _5_.")
        assert_both_succeed("Give back _5_ is not equal to _10_.")
        assert_both_succeed("Give back _5_ does not equal _10_.")

    def test_strict_equality_operators(self) -> None:
        """Strict equality operators should work in both parsers."""
        assert_both_succeed("Give back _5_ is strictly equal to _5_.")
        assert_both_succeed("Give back _5_ is exactly equal to _5_.")
        assert_both_succeed("Give back _5_ is identical to _5_.")
        assert_both_succeed("Give back _5_ is not strictly equal to _5.0_.")

    def test_boolean_operators(self) -> None:
        """Boolean operators should work in both parsers."""
        assert_both_succeed("Give back _yes_ and _yes_.")
        assert_both_succeed("Give back _yes_ or _no_.")
        assert_both_succeed("Give back not _yes_.")
        assert_both_succeed("Give back not (_yes_ and _no_).")

    def test_natural_language_comparisons(self) -> None:
        """Natural language comparison forms should work in both parsers."""
        assert_both_succeed("Give back _5_ is less than _10_.")
        assert_both_succeed("Give back _10_ is greater than _5_.")
        assert_both_succeed("Give back _5_ is less than or equal to _5_.")
        assert_both_succeed("Give back _10_ is greater than or equal to _10_.")

    def test_alternative_comparison_forms(self) -> None:
        """Alternative comparison forms should work in both parsers."""
        assert_both_succeed("Give back _5_ is more than _3_.")
        assert_both_succeed("Give back _3_ is under _5_.")
        assert_both_succeed("Give back _5_ is at least _5_.")
        assert_both_succeed("Give back _5_ is at most _5_.")

    def test_operator_precedence(self) -> None:
        """Operator precedence should work in both parsers."""
        assert_both_succeed("Give back _2_ + _3_ * _4_.")
        assert_both_succeed("Give back (_2_ + _3_) * _4_.")
        assert_both_succeed("Give back _10_ - _2_ - _3_.")
        assert_both_succeed("Give back _yes_ or _no_ and _yes_.")


class TestControlFlow:
    """Test parity for control flow statements."""

    def test_simple_if(self) -> None:
        """Simple if statements should work in both parsers."""
        code = """If _yes_ then:
> Give back _1_."""
        assert_both_succeed(code)

    def test_if_else(self) -> None:
        """If-else statements should work in both parsers."""
        code = """If `x` > _0_ then:
> Give back _"positive"_.
Else:
> Give back _"non-positive"_."""
        assert_both_succeed(code)

    def test_when_otherwise(self) -> None:
        """When-otherwise (if-else aliases) should work in both parsers."""
        code = """When `x` > _0_ then:
> Give back _"positive"_.
Otherwise:
> Give back _"non-positive"_."""
        assert_both_succeed(code)

    def test_nested_if(self) -> None:
        """Nested if statements should work in both parsers."""
        code = """If `x` > _0_ then:
> If `x` > _10_ then:
>> Give back _"large"_.
> Else:
>> Give back _"small"_."""
        assert_both_succeed(code)

    def test_conditional_expression(self) -> None:
        """Conditional expressions should work in both parsers."""
        assert_both_succeed("Give back _'yes'_ if _yes_ else _'no'_.")
        assert_both_succeed("Set `result` to _1_ if `x` > _0_ else _-1_.")

    def test_while_loop(self) -> None:
        """While loops should work in both parsers."""
        code = """Set `i` to _0_.
While `i` < _10_:
> Set `i` to `i` + _1_."""
        assert_both_succeed(code)

    def test_for_each_loop(self) -> None:
        """For each loops should work in both parsers."""
        code = """For each `item` in `items`:
> Say `item`."""
        assert_both_succeed(code)


class TestFunctions:
    """Test parity for function-related features."""

    @pytest.mark.xfail(reason="CFG parser doesn't support Define statements")
    def test_define_variable(self) -> None:
        """Define statements for variables should work in both parsers."""
        assert_both_succeed("Define x as Integer.")
        assert_both_succeed("Define name as Text.")
        assert_both_succeed("Define flag as Boolean.")

    def test_use_statement(self) -> None:
        """Use statements (modern call syntax) should work in both parsers."""
        assert_both_succeed('Use `print` with _"Hello"_.')
        assert_both_succeed("Use `calculate` with _10_, _20_.")

    @pytest.mark.xfail(reason="Named arguments with 'where' clause not fully supported")
    def test_named_arguments(self) -> None:
        """Named arguments should work in both parsers."""
        assert_both_succeed("Use `calculate` where `x` is _10_, `y` is _20_.")
        assert_both_succeed('Call `print` where `message` is _"Hello"_.')

    def test_set_using(self) -> None:
        """Set using syntax should work in both parsers."""
        assert_both_succeed("Set `result` using `calculate` with _10_, _20_.")
        assert_both_succeed("Set `value` using `square` where `x` is _5_.")

    def test_say_statement(self) -> None:
        """Say statements should work in both parsers."""
        assert_both_succeed('Say _"Hello, World!"_.')
        assert_both_succeed("Say `message`.")

    def test_tell_statement(self) -> None:
        """Tell statements (Say alias) should work in both parsers."""
        assert_both_succeed('Tell _"Hello, World!"_.')
        assert_both_succeed("Tell `message`.")

    @pytest.mark.xfail(reason="CFG parser has limited action support")
    def test_action_statement(self) -> None:
        """Action statements should work in both parsers."""
        code = """Action greet with `name` as Text:
> Say _"Hello, "_ + `name`."""
        assert_both_succeed(code)

    @pytest.mark.xfail(reason="CFG parser has limited interaction support")
    def test_interaction_statement(self) -> None:
        """Interaction statements should work in both parsers."""
        code = """Interaction respond:
> Say _"Response sent"_."""
        assert_both_succeed(code)

    def test_utility_definition(self) -> None:
        """Utility definitions should work in both parsers."""
        code = """### Utility: `add`
<details>
<summary>Adds two numbers.</summary>

> Give back `x` + `y`.

</details>"""
        assert_both_succeed(code)


class TestAdvancedFeatures:
    """Test parity for advanced language features."""

    @pytest.mark.xfail(reason="CFG parser doesn't support type annotations")
    def test_type_annotations(self) -> None:
        """Type annotations should work in both parsers."""
        assert_both_succeed("Set `x` as Integer to _5_.")
        assert_both_succeed('Set `name` as Text to _"Alice"_.')
        assert_both_succeed("Set `flag` as Boolean to _yes_.")

    @pytest.mark.xfail(reason="CFG parser doesn't support default parameters")
    def test_default_parameters(self) -> None:
        """Default parameters should work in both parsers."""
        code = """Action greet with `name` as Text = _"World"_:
> Say _"Hello, "_ + `name`."""
        assert_both_succeed(code)

    @pytest.mark.xfail(reason="LaTeX math blocks not implemented in either parser")
    def test_latex_math(self) -> None:
        """LaTeX math blocks should work in both parsers."""
        assert_both_succeed("Set `equation` to $$x^2 + y^2 = z^2$$.")
        assert_both_succeed("Give back $$\\frac{1}{2}$$.")

    @pytest.mark.xfail(reason="CFG parser doesn't support markdown headers in code")
    def test_markdown_headers(self) -> None:
        """Markdown headers should work in both parsers."""
        code = """# Main Program
Set x to _10_.
## Section
Give back x."""
        assert_both_succeed(code)

    @pytest.mark.xfail(reason="HTML tags not implemented in either parser")
    def test_html_tags(self) -> None:
        """HTML documentation tags should work in both parsers."""
        code = """<details>
<summary>This is a summary</summary>
Set x to _10_.
</details>"""
        assert_both_succeed(code)


class TestErrorCases:
    """Test parity for error cases - both parsers should fail."""

    @pytest.mark.xfail(reason="CFG parser doesn't require periods at end of statements")
    def test_missing_period(self) -> None:
        """Missing period should fail in both parsers."""
        assert_both_fail("Set `z` to _10_")
        assert_both_fail("Give back _42_")

    def test_missing_to_keyword(self) -> None:
        """Missing 'to' keyword should fail in both parsers."""
        assert_both_fail("Set `x` _10_.")

    def test_undefined_syntax(self) -> None:
        """Undefined syntax should fail in both parsers."""
        assert_both_fail("Do something weird.")
        assert_both_fail("Random garbage text.")

    def test_unclosed_string(self) -> None:
        """Unclosed strings should fail in both parsers."""
        assert_both_fail('Give back _"unclosed.')
        assert_both_fail("Give back _'unclosed.")

    def test_invalid_operators(self) -> None:
        """Invalid operators should fail in both parsers."""
        assert_both_fail("Give back _5_ %% _3_.")  # Invalid operator
        assert_both_fail("Give back _5_ <> _3_.")  # Invalid operator

    def test_malformed_if(self) -> None:
        """Malformed if statements should fail in both parsers."""
        assert_both_fail("If `x` > _0_ Give back _1_.")  # Missing then:
        assert_both_fail("If `x` > _0_ then Give back _1_.")  # Missing colon

    @pytest.mark.xfail(reason="Parsers may handle empty blocks differently")
    def test_empty_blocks(self) -> None:
        """Empty blocks should be handled consistently."""
        assert_parity("If `x` > _0_ then:\n")  # Empty then block
        assert_parity("If `x` > _0_ then:\n>\n")  # Block with just marker


class TestComplexPrograms:
    """Test parity for complete programs."""

    def test_simple_calculator(self) -> None:
        """Simple calculator program should work in both parsers."""
        code = """Set `x` to _10_.
Set `y` to _20_.
Set `sum` to `x` + `y`.
Set `product` to `x` * `y`.
Give back `sum`."""
        assert_both_succeed(code)

    def test_conditional_logic(self) -> None:
        """Program with conditional logic should work in both parsers."""
        code = """Set `score` to _85_.
If `score` >= _90_ then:
> Give back _"A"_.
Else:
> If `score` >= _80_ then:
>> Give back _"B"_.
> Else:
>> Give back _"C"_."""
        assert_both_succeed(code)

    @pytest.mark.xfail(reason="While loops and Define statements not fully supported in both parsers")
    def test_factorial_function(self) -> None:
        """Factorial function should work in both parsers."""
        code = """Define `n` as Integer.
Set `n` to _5_.
Set `result` to _1_.
Set `i` to _1_.
While `i` <= `n`:
> Set `result` to `result` * `i`.
> Set `i` to `i` + _1_.
Give back `result`."""
        assert_both_succeed(code)

    def test_mixed_operators(self) -> None:
        """Programs with mixed operators should work in both parsers."""
        code = """Set `foo` to _10_.
Set `bar` to _20_.
Set `baz` to _30_.
Set `result` to (`foo` + `bar`) * `baz` - _100_.
Set `check` to `result` > _0_ and `result` < _1000_.
Give back `check`."""
        assert_both_succeed(code)

    @pytest.mark.xfail(reason="CFG parser doesn't support lists")
    def test_list_operations(self) -> None:
        """List operations should work in both parsers."""
        code = """Set `items` to:
- _1_.
- _2_.
- _3_.

Add _4_ to `items`.
Set `first` to the first item of `items`.
Give back `first`."""
        assert_both_succeed(code)


class TestEdgeCases:
    """Test parity for edge cases and boundary conditions."""

    def test_very_long_identifier(self) -> None:
        """Very long identifiers should be handled consistently."""
        long_name = "a" * 100
        assert_parity(f"Set `{long_name}` to _10_.")

    def test_deeply_nested_expressions(self) -> None:
        """Deeply nested expressions should be handled consistently."""
        code = "Give back (((((_1_ + _2_) * _3_) - _4_) / _5_) + _6_)."
        assert_both_succeed(code)

    def test_unicode_in_strings(self) -> None:
        """Unicode in strings should work in both parsers."""
        assert_both_succeed('Give back _"Hello 世界 🌍"_.')
        assert_both_succeed('Give back _"Emoji: 😀😁😂"_.')

    def test_special_characters_in_strings(self) -> None:
        """Special characters in strings should work in both parsers."""
        assert_both_succeed('Give back _"Line\\nbreak"_.')
        assert_both_succeed('Give back _"Tab\\there"_.')
        assert_both_succeed('Give back _"Quote: \\"test\\""_.')

    def test_mixed_statement_types(self) -> None:
        """Mixed statement types in one program should work."""
        code = """Set `x` to _10_.
Define `y` as Integer.
If `x` > _5_ then:
> Say _"Large"_.
Call `print` with `x`.
Give back `x`."""
        assert_parity(code)  # Just check parity, don't assume success

    def test_whitespace_variations(self) -> None:
        """Different whitespace should be handled consistently."""
        assert_parity("Set  `x`   to    _10_  .")
        assert_parity("Set\t`x`\tto\t_10_\t.")
        assert_parity("Set\n`x`\nto\n_10_\n.")


# =============================================================================
# Summary Test
# =============================================================================


class TestParityReport:
    """Generate a parity report showing what works and what doesn't."""

    def test_generate_parity_report(self) -> None:
        """Generate a comprehensive parity report."""
        test_cases = [
            ("Simple assignment", "Set `x` to _10_."),
            ("Backtick identifier", "Set `var` to _10_."),
            ("Bold variable", "Set **var** to _10_."),
            ("While loop", "While `x` < _10_:\n> Set `x` to `x` + _1_."),
            ("For each loop", "For each `item` in `items`:\n> Say `item`."),
            ("Define statement", "Define `x` as Integer."),
            ("Use statement", 'Use `print` with _"Hi"_.'),
            ("Named arguments", "Use `fn` where `x` is _10_."),
            ("Set using", "Set `r` using `fn` with _10_."),
            ("Action", 'Action fn:\n> Say _"Hi"_.'),
            ("Utility", "### Utility: `fn`"),
            ("Type annotation", "Set `x` as Integer to _5_."),
            ("List literal", "Set `items` to [_1_, _2_]."),
            ("Dict literal", "Set `d` to {`x`: _1_}."),
            ("LaTeX math", "Set `eq` to $$x^2$$."),
        ]

        results = []
        for name, code in test_cases:
            main_success, _, _ = parse_with_main(code)
            cfg_success, _, _ = parse_with_cfg(code)
            parity = "✓" if main_success == cfg_success else "✗"
            results.append((name, main_success, cfg_success, parity))

        # Print report (will show in test output with -s flag)
        print("\n" + "=" * 60)
        print("PARSER PARITY REPORT")
        print("=" * 60)
        print(f"{'Feature':<20} {'Main':<6} {'CFG':<6} {'Parity':<6}")
        print("-" * 60)

        for name, main, cfg, parity in results:
            main_str = "✓" if main else "✗"
            cfg_str = "✓" if cfg else "✗"
            print(f"{name:<20} {main_str:<6} {cfg_str:<6} {parity:<6}")

        print("-" * 60)
        parity_count = sum(1 for _, _, _, p in results if p == "✓")
        total = len(results)
        print(f"Parity achieved: {parity_count}/{total} ({parity_count * 100 / total:.1f}%)")
        print("=" * 60)

        # This test always passes - it's just for reporting
        assert True
