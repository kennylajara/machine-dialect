#!/usr/bin/env python3
"""Machine Dialect REPL (Read-Eval-Print Loop).

This module provides an interactive REPL for the Machine Dialect language.
It tokenizes input and displays the resulting tokens, helping users understand
how their code is parsed. The REPL also displays any lexical errors encountered.
"""

import sys

from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tokens import Token


class REPL:
    """Interactive REPL for Machine Dialect.

    Provides an interactive environment for testing Machine Dialect syntax
    by tokenizing input and displaying the resulting tokens and any errors.

    Attributes:
        prompt (str): The prompt string displayed to the user.
        running (bool): Flag indicating whether the REPL is running.
    """

    def __init__(self) -> None:
        """Initialize the REPL with default settings."""
        self.prompt = "md> "
        self.running = True

    def print_welcome(self) -> None:
        """Print the welcome message when REPL starts."""
        print("Machine Dialect REPL v0.1.0")
        print("Type 'exit' to exit, 'help' for help")
        print("-" * 50)

    def print_help(self) -> None:
        """Print help information about available commands."""
        print("\nAvailable commands:")
        print("  exit   - Exit the REPL")
        print("  help   - Show this help message")
        print("  clear  - Clear the screen")
        print("\nEnter any text to see its tokens.")
        print("Example: if x > 0 then return true")
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
            lexer = Lexer(input_text)
            errors, tokens = lexer.tokenize()

            # Display any errors first
            if errors:
                print(f"\nErrors ({len(errors)}):")
                print("-" * 50)
                for error in errors:
                    print(f"  {error}")
                print("-" * 50)

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
                elif user_input:
                    # Tokenize and print
                    self.tokenize_and_print(user_input)

            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye!")
                self.running = False
                return 0  # Normal exit via Ctrl+D
            except Exception as e:
                print(f"Unexpected error: {e}")
                return 1  # Error exit

        return 0  # Default normal exit


def main() -> None:
    """Entry point for the REPL"""
    repl = REPL()
    exit_code = repl.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
