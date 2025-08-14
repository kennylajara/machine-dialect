"""Examples and usage of the CFG module for Machine Dialect."""

from machine_dialect.cfg import CFGParser


def example_parse_code() -> None:
    """Example of parsing Machine Dialect code with the CFG parser."""
    parser = CFGParser()

    # Example 1: Simple variable assignment and output
    code1 = """
    Set `x` to 10.
    Set `y` to 20.
    Set `sum` to x + y.
    Say sum.
    """

    print("Example 1: Simple arithmetic")
    print("Code:", code1)
    try:
        tree = parser.parse(code1)
        print("Parse successful!")
        print("AST:")
        print(parser.pretty_print(tree))
    except ValueError as e:
        print(f"Parse failed: {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 2: Conditional statement
    code2 = """
    Set `age` to 18.
    if age is greater than 17 then {
        Say "You are an adult.".
    } else {
        Say "You are a minor.".
    }
    """

    print("Example 2: Conditional")
    print("Code:", code2)
    try:
        tree = parser.parse(code2)
        print("Parse successful!")
        print("AST:")
        print(parser.pretty_print(tree))
    except ValueError as e:
        print(f"Parse failed: {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 3: Logical operations
    code3 = """
    Set `is_raining` to True.
    Set `have_umbrella` to False.
    Set `get_wet` to is_raining and not have_umbrella.
    if get_wet then {
        Say "You will get wet!".
    }
    """

    print("Example 3: Logical operations")
    print("Code:", code3)
    try:
        tree = parser.parse(code3)
        print("Parse successful!")
        print("AST:")
        print(parser.pretty_print(tree))
    except ValueError as e:
        print(f"Parse failed: {e}")


def example_generate_prompt() -> None:
    """Example of creating prompts for GPT-5 CFG generation."""
    # Placeholder for CFG generation examples
    print("CFG generation functionality coming soon.")


def example_validate_code() -> None:
    """Example of validating Machine Dialect code."""
    parser = CFGParser()

    # Valid code
    valid_code = """
    Set `name` to "Alice".
    Say name.
    """

    print("Validating valid code:")
    print(valid_code)
    if parser.validate(valid_code):
        print("✓ Code is valid!")
    else:
        print("✗ Code is invalid!")

    print("\n" + "=" * 50 + "\n")

    # Invalid code
    invalid_code = """
    Set x to 10
    Say x
    """

    print("Validating invalid code (missing backticks and periods):")
    print(invalid_code)
    if parser.validate(invalid_code):
        print("✓ Code is valid!")
    else:
        print("✗ Code is invalid!")


def main() -> None:
    """Run all examples."""
    print("=" * 60)
    print("CFG Parser Examples")
    print("=" * 60)
    print()

    print("1. PARSING EXAMPLES")
    print("-" * 40)
    example_parse_code()

    print("\n2. GENERATION PROMPT EXAMPLES")
    print("-" * 40)
    example_generate_prompt()

    print("\n3. VALIDATION EXAMPLES")
    print("-" * 40)
    example_validate_code()

    print("\n" + "=" * 60)
    print("Examples complete!")


if __name__ == "__main__":
    main()
