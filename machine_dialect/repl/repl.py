#!/usr/bin/env python3
"""
Machine Dialect REPL (Read-Eval-Print Loop)
Tokenizes input and displays the resulting tokens.
"""

from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tokens import Token


class REPL:
    def __init__(self) -> None:
        self.prompt = "md> "
        self.running = True

    def print_welcome(self) -> None:
        print("Machine Dialect REPL v0.1.0")
        print("Type 'exit' or 'quit' to exit, 'help' for help")
        print("-" * 50)

    def print_help(self) -> None:
        print("\nAvailable commands:")
        print("  exit, quit  - Exit the REPL")
        print("  help        - Show this help message")
        print("  clear       - Clear the screen")
        print("\nEnter any text to see its tokens.")
        print("Example: if x > 0 then return true")
        print()

    def clear_screen(self) -> None:
        import os

        os.system("cls" if os.name == "nt" else "clear")

    def format_token(self, token: Token) -> str:
        """Format a token for display"""
        return f"  {token.type.name:<20} | {token.literal!r}"

    def tokenize_and_print(self, input_text: str) -> None:
        """Tokenize the input and print the results"""
        try:
            lexer = Lexer(input_text)
            tokens = list(lexer.tokenize())

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

    def run(self) -> None:
        """Main REPL loop"""
        self.print_welcome()

        while self.running:
            try:
                # Get input
                user_input = input(self.prompt).strip()

                # Check for commands
                if user_input.lower() in ["exit", "quit"]:
                    print("Goodbye!")
                    self.running = False
                    break
                elif user_input.lower() == "help":
                    self.print_help()
                elif user_input.lower() == "clear":
                    self.clear_screen()
                    self.print_welcome()
                elif user_input:
                    # Tokenize and print
                    self.tokenize_and_print(user_input)

            except KeyboardInterrupt:
                print("\nUse 'exit' or 'quit' to exit.")
            except EOFError:
                print("\nGoodbye!")
                self.running = False
                break
            except Exception as e:
                print(f"Unexpected error: {e}")


def main() -> None:
    """Entry point for the REPL"""
    repl = REPL()
    repl.run()


if __name__ == "__main__":
    main()
