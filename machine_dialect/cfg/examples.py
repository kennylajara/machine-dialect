"""Examples and usage of the CFG module for Machine Dialect™.

This module provides demonstration examples of how to use the CFG (Context-Free Grammar)
parser for Machine Dialect™ code. It includes examples of parsing variable assignments,
conditional statements, logical operations, and code validation.

The examples show:
- Basic parsing of Machine Dialect™ syntax
- Handling conditional statements with if/else blocks
- Working with logical operations and boolean values
- Code validation to check syntax correctness
- Pretty-printing of Abstract Syntax Trees (AST)

Example:
    Run all examples from the command line::

        $ python -m machine_dialect.cfg.examples
"""

from machine_dialect.cfg import CFGParser


def example_parse_code() -> None:
    """Demonstrate parsing Machine Dialect™ code with the CFG parser.

    This function shows three examples of parsing Machine Dialect™ code:
    1. Simple variable assignment and arithmetic operations
    2. Conditional statements with if/else blocks
    3. Logical operations with boolean values

    Each example prints the original code, attempts to parse it, and displays
    the resulting Abstract Syntax Tree (AST) if successful.

    Raises:
        ValueError: If any of the code examples fail to parse.

    Example:
        >>> example_parse_code()
        Example 1: Simple arithmetic
        Code: ...
        Parse successful!
        AST: ...
    """
    parser = CFGParser()

    # Example 1: Simple variable assignment and output
    code1 = """
    Set `x` to _10_.
    Set `y` to _20_.
    Set `sum` to `x` + `y`.
    Say `sum`.
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
    Set `age` to _18_.
    If `age` is greater than _17_ then:
    > Say _"You are an adult."_.
    Else:
    > Say _"You are a minor."_.
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
    Set `is_raining` to _yes_.
    Set `have_umbrella` to _no_.
    Set `get_wet` to `is_raining` and not `have_umbrella`.
    If `get_wet` then:
    > Say _"You will get wet!"_.
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
    """Demonstrate creating prompts for GPT-5 CFG generation.

    This function serves as a placeholder for future CFG generation
    functionality using GPT-5 or similar language models. Once implemented,
    it will show how to create prompts that guide AI models to generate
    valid Machine Dialect™ code following the CFG rules.

    Note:
        This functionality is not yet implemented and will be added
        in a future version.

    Todo:
        * Implement prompt generation for CFG-based code generation
        * Add examples of different prompt types
        * Include validation of generated code
    """
    # Placeholder for CFG generation examples
    print("CFG generation functionality coming soon.")


def example_validate_code() -> None:
    """Demonstrate validation of Machine Dialect™ code syntax.

    This function shows examples of both valid and invalid Machine Dialect™
    code to illustrate the validation capabilities of the CFG parser.
    It demonstrates common syntax errors like missing backticks around
    variables and missing periods at the end of statements.

    The function validates:
    - Valid code with proper syntax (backticks, periods)
    - Invalid code with missing syntax elements

    Example:
        >>> example_validate_code()
        Validating valid code:
        Set `name` to "Alice".
        Say name.
        ✓ Code is valid!
    """
    parser = CFGParser()

    # Valid code
    valid_code = """
    Set `name` to _"Alice"_.
    Say `name`.
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
    """Run all CFG parser examples in sequence.

    This function executes all the example functions to demonstrate
    the full capabilities of the CFG parser for Machine Dialect™.
    It runs parsing examples, generation prompt examples, and
    validation examples, separating each section with visual dividers
    for clarity.

    The execution order is:
    1. Parsing examples - demonstrating code parsing
    2. Generation prompt examples - placeholder for future features
    3. Validation examples - showing syntax validation

    Example:
        >>> main()
        ============================================================
        CFG Parser Examples
        ============================================================
        ...
    """
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
