#!/usr/bin/env python3
"""Generate Machine Dialect™ code using AI models.

This module provides functionality to generate Machine Dialect™ code using
AI language models (such as OpenAI's GPT models). It includes code generation,
validation, and configuration management for AI API integration.

The module supports:
- Generating Machine Dialect™ code from natural language descriptions
- Validating generated code against the CFG parser
- Flexible configuration through environment variables or config files
- Command-line interface for code generation tasks
- Saving generated code to files

Note:
    OpenAI integration is currently commented out. Uncomment the relevant
    sections when the OpenAI library is installed.

Example:
    Generate code from the command line::

        $ python -m machine_dialect.cfg.generate_with_ai "calculate rectangle area"
        $ python -m machine_dialect.cfg.generate_with_ai "sort a list" --model gpt-4
"""

import argparse

from machine_dialect.cfg import CFGParser

# Uncomment when you have OpenAI installed
# from openai import OpenAI
from machine_dialect.cfg.config import ConfigLoader


def generate_code(
    task: str,
    api_key: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 500,
    validate: bool = True,
) -> str:
    """Generate Machine Dialect™ code for a given task.

    Args:
        task: Description of what the code should do.
        api_key: AI API key (overrides config/env).
        model: AI model to use (overrides config/env).
        temperature: Sampling temperature (0-2, lower = more deterministic).
        max_tokens: Maximum tokens to generate.
        validate: Whether to validate generated code.

    Returns:
        Generated Machine Dialect™ code.

    Raises:
        ValueError: If API key or model is not configured.

    Example:
        >>> code = generate_code(
        ...     "calculate area",
        ...     model="gpt-3.5-turbo",
        ...     temperature=0.5
        ... )
        >>> print(code)
        Set `width` to 10.
        ...
    """
    # Load configuration
    loader = ConfigLoader()
    config = loader.load()

    # Override with function arguments if provided
    if api_key:
        config.key = api_key
    if model:
        config.model = model

    # Check configuration
    if not config.key:
        raise ValueError(loader.get_error_message())
    if not config.model:
        raise ValueError("No AI model configured. " + loader.get_error_message())

    # Create OpenAI client
    # Uncomment when you have OpenAI installed:
    # from openai import OpenAI
    # client = OpenAI(api_key=config.key)

    print(f"\nModel: {config.model}")
    print(f"Task: {task}")
    print(f"Temperature: {temperature}")
    print(f"Max tokens: {max_tokens}")

    # Actual API call (uncomment when you have OpenAI):
    # print(f"\nGenerating code with {config.model}...")
    # generated_code = generate_with_openai(client, config.model, task, max_tokens, temperature)

    # For demonstration, show configuration
    print("\n" + "=" * 60)
    print("Configuration:")
    print("=" * 60)
    print(f"Model: {config.model}")
    print(f"API Key: {'*' * 10 if config.key else 'Not configured'}")

    # Example of what would be returned
    example_code = """Set `width` to 10.
Set `height` to 5.
Set `area` to width * height.
Say "The area is: ".
Say area."""

    print("\n" + "=" * 60)
    print(f"Example Generated Code (what {config.model} would return):")
    print("=" * 60)
    print(example_code)

    # Validate if requested
    if validate:
        print("\n" + "=" * 60)
        print("Validating generated code...")
        print("=" * 60)

        parser = CFGParser()
        is_valid = parser.validate(example_code)

        if is_valid:
            print("✓ Generated code is syntactically valid!")
        else:
            print("✗ Generated code has syntax errors")

    return example_code


def main() -> int:
    """Main entry point for the AI code generation script.

    Parses command-line arguments and generates Machine Dialect™ code
    based on the provided task description. Supports configuration
    overrides, validation, and saving output to files.

    Returns:
        Exit code: 0 for success, 1 for errors.

    Example:
        >>> # Generate code for calculating area
        >>> sys.argv = ['prog', 'calculate area of rectangle']
        >>> main()
        0
    """
    parser = argparse.ArgumentParser(description="Generate Machine Dialect™ code using AI models")
    parser.add_argument("task", help="Description of what the code should do")
    parser.add_argument("--api-key", help="AI API key (overrides config/env)")
    parser.add_argument("--model", help="AI model to use (overrides config/env)")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature (0-2, default: 0.7)")
    parser.add_argument("--max-tokens", type=int, default=500, help="Maximum tokens to generate (default: 500)")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation of generated code")
    parser.add_argument("--save", help="Save generated code to file")

    args = parser.parse_args()

    try:
        code = generate_code(
            task=args.task,
            api_key=args.api_key,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            validate=not args.no_validate,
        )

        if args.save:
            with open(args.save, "w") as f:
                f.write(code)
            print(f"\nCode saved to: {args.save}")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
