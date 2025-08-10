#!/usr/bin/env python3
"""Machine Dialect REPL (Read-Eval-Print Loop).

This module provides an interactive REPL for the Machine Dialect language.
It can operate in two modes:
- Default: Parses input and displays the AST
- Debug tokens (--debug-tokens): Tokenizes input and displays tokens
"""

import argparse
import sys

from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tokens import Token
from machine_dialect.parser.parser import Parser


class REPL:
    """Interactive REPL for Machine Dialect.

    Provides an interactive environment for testing Machine Dialect syntax
    by parsing input and displaying the AST or tokens.

    Attributes:
        prompt (str): The prompt string displayed to the user.
        running (bool): Flag indicating whether the REPL is running.
        debug_tokens (bool): Whether to show tokens instead of AST.
        accumulated_source (str): Accumulated source code for parsing.
    """

    def __init__(self, debug_tokens: bool = False) -> None:
        """Initialize the REPL with default settings.

        Args:
            debug_tokens: Whether to show tokens instead of AST.
        """
        self.prompt = "md> "
        self.running = True
        self.debug_tokens = debug_tokens
        self.accumulated_source = ""

    def print_welcome(self) -> None:
        """Print the welcome message when REPL starts."""
        print("Machine Dialect REPL v0.1.0")
        mode = "Token Debug Mode" if self.debug_tokens else "AST Mode"
        print(f"Mode: {mode}")
        print("Type 'exit' to exit, 'help' for help")
        print("-" * 50)

    def print_help(self) -> None:
        """Print help information about available commands."""
        print("\nAvailable commands:")
        print("  exit   - Exit the REPL")
        print("  help   - Show this help message")
        print("  clear  - Clear the screen")
        if not self.debug_tokens:
            print("  reset  - Clear accumulated source (AST mode only)")

        if self.debug_tokens:
            print("\nEnter any text to see its tokens.")
        else:
            print("\nEnter Machine Dialect code to see its AST.")
            print("Source is accumulated across lines until an error occurs.")
        print("\nExample: Set `x` to _10_.")
        print()

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        import os

        os.system("cls" if os.name == "nt" else "clear")

    def format_token(self, token: Token) -> str:
        """Format a token for display.

        Args:
            token: The token to format.

        Returns:
            A formatted string representation of the token.
        """
        return f"  {token.type.name:<20} | {token.literal!r}"

    def tokenize_and_print(self, input_text: str) -> None:
        """Tokenize the input and print the results.

        Args:
            input_text: The Machine Dialect code to tokenize.

        Note:
            This method handles both successful tokenization and error cases,
            displaying any lexical errors before showing the tokens.
        """
        try:
            from machine_dialect.lexer.tokens import TokenType

            lexer = Lexer(input_text)

            # Stream tokens
            tokens = []
            while True:
                token = lexer.next_token()
                tokens.append(token)
                if token.type == TokenType.MISC_EOF:
                    break

            print(f"\nTokens ({len(tokens)}):")
            print("-" * 50)
            print(f"  {'Type':<20} | Literal")
            print("-" * 50)

            for token in tokens:
                print(self.format_token(token))

            print("-" * 50)
            print()

        except Exception as e:
            print(f"Error: {e}")
            print()

    def parse_and_print(self, input_text: str) -> None:
        """Parse the input and print the AST.

        Args:
            input_text: The Machine Dialect code to parse.

        Note:
            This method accumulates source code and attempts to parse it.
            If parsing fails, it shows the error and removes the problematic line.
        """
        # Add new input to accumulated source
        if self.accumulated_source:
            # Add a newline separator if we have existing content
            test_source = self.accumulated_source + "\n" + input_text
        else:
            test_source = input_text

        # Create parser and parse
        parser = Parser()
        ast = parser.parse(test_source)

        # Check for errors
        if parser.has_errors():
            # Show parser errors but don't update accumulated source
            print("\nErrors found:")
            print("-" * 50)
            for error in parser.errors:
                print(f"  {error}")
            print("-" * 50)
            print("(Input not added to accumulated source)")
            print()
        else:
            # If successful, update accumulated source and print AST
            self.accumulated_source = test_source

            print("\nAST:")
            print("-" * 50)
            if ast and ast.statements:
                for node in ast.statements:
                    print(f"  {node}")
            else:
                print("  (empty)")
            print("-" * 50)
            print()

    def run(self) -> int:
        """Main REPL loop. Returns exit code."""
        self.print_welcome()

        while self.running:
            try:
                # Get input
                user_input = input(self.prompt).strip()

                # Check for commands
                if user_input.lower() == "exit":
                    print("Goodbye!")
                    self.running = False
                    return 0  # Normal exit
                elif user_input.lower() == "help":
                    self.print_help()
                elif user_input.lower() == "clear":
                    self.clear_screen()
                    self.print_welcome()
                    # Also clear accumulated source in AST mode
                    if not self.debug_tokens:
                        self.accumulated_source = ""
                elif user_input.lower() == "reset" and not self.debug_tokens:
                    # Reset accumulated source in AST mode
                    self.accumulated_source = ""
                    print("Accumulated source cleared.")
                elif user_input:
                    # Process input based on mode
                    if self.debug_tokens:
                        self.tokenize_and_print(user_input)
                    else:
                        self.parse_and_print(user_input)

            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                self.running = False
                return 0  # Normal exit via Ctrl+D
            except Exception as e:
                print(f"Unexpected error: {e}")
                return 1  # Error exit

        return 0  # Default normal exit


def main() -> None:
    """Entry point for the REPL."""
    parser = argparse.ArgumentParser(description="Machine Dialect REPL")
    parser.add_argument(
        "--debug-tokens",
        action="store_true",
        help="Run in token debug mode (show tokens instead of AST)",
    )
    args = parser.parse_args()

    repl = REPL(debug_tokens=args.debug_tokens)
    exit_code = repl.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
