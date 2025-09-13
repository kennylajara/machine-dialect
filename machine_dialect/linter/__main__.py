"""Command-line interface for the Machine Dialect™ linter.

This module provides the CLI for running the linter on Machine Dialect™ files.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from machine_dialect.linter import Linter, Violation


def load_config(config_path: Path | None) -> dict[str, Any]:
    """Load linter configuration from a file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Configuration dictionary.
    """
    if not config_path or not config_path.exists():
        return {}

    with open(config_path) as f:
        if config_path.suffix == ".json":
            return json.load(f)  # type: ignore[no-any-return]
        else:
            # For now, only support JSON
            print(f"Warning: Unsupported config format {config_path.suffix}, using defaults")
            return {}


def format_violation(violation: Violation, filename: str) -> str:
    """Format a violation for display.

    Args:
        violation: The violation to format.
        filename: The filename where the violation occurred.

    Returns:
        A formatted string for display.
    """
    return f"{filename}:{violation}"


def main() -> None:
    """Main entry point for the linter CLI."""
    parser = argparse.ArgumentParser(description="Lint Machine Dialect™ code for style and errors")

    parser.add_argument(
        "files",
        nargs="*",  # Changed from "+" to "*" to make it optional
        type=Path,
        help="Machine Dialect™ files to lint",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only show errors, not warnings",
    )

    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="List all available rules and exit",
    )

    args = parser.parse_args()

    # Handle --list-rules
    if args.list_rules:
        linter = Linter()
        print("Available linting rules:")
        for rule in linter.rules:
            print(f"  {rule.rule_id}: {rule.description}")
        sys.exit(0)

    # Check if files were provided
    if not args.files:
        parser.error("No files specified to lint")

    # Load configuration
    config = load_config(args.config)
    linter = Linter(config)

    # Lint files
    total_violations = 0
    has_errors = False

    for filepath in args.files:
        if not filepath.exists():
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            has_errors = True
            continue

        try:
            violations = linter.lint_file(str(filepath))

            # Filter violations if --quiet
            if args.quiet:
                from machine_dialect.linter.violations import ViolationSeverity

                violations = [v for v in violations if v.severity == ViolationSeverity.ERROR]

            # Display violations
            for violation in violations:
                print(format_violation(violation, str(filepath)))
                if violation.fix_suggestion:
                    print(f"  Suggestion: {violation.fix_suggestion}")

            total_violations += len(violations)

            # Check for errors
            from machine_dialect.linter.violations import ViolationSeverity

            if any(v.severity == ViolationSeverity.ERROR for v in violations):
                has_errors = True

        except Exception as e:
            print(f"Error linting {filepath}: {e}", file=sys.stderr)
            has_errors = True

    # Summary
    if not args.quiet and total_violations > 0:
        print(f"\nFound {total_violations} issue(s)")

    # Exit with error code if there were errors
    sys.exit(1 if has_errors or total_violations > 0 else 0)


if __name__ == "__main__":
    main()
