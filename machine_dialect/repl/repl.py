#!/usr/bin/env python3
"""Machine Dialect™ REPL (Read-Eval-Print Loop).

This module provides an interactive REPL for the Machine Dialect™ language.
It can operate in multiple modes:
- Default: Execute code using the Rust VM
- Debug tokens (--debug-tokens): Tokenizes input and displays tokens
- AST mode (--ast): Show HIR/AST without executing
"""

import argparse
import sys
from typing import Any

# readline provides command history and line editing, but is not available on Windows
if sys.platform != "win32":
    import readline  # noqa: F401

from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.lexer.lexer import Lexer
from machine_dialect.lexer.tokens import Token
from machine_dialect.parser.parser import Parser


class REPL:
    """Interactive REPL for Machine Dialect™.

    Provides an interactive environment for testing Machine Dialect™ syntax
    by parsing input and displaying the AST or tokens.

    Attributes:
        prompt: The prompt string displayed to the user.
        running: Flag indicating whether the REPL is running.
        debug_tokens: Whether to show tokens instead of AST.
        show_ast: Whether to show AST instead of evaluating.
        accumulated_source: Accumulated source code for parsing.
        multiline_buffer: Buffer for collecting multi-line input.
        in_multiline_mode: Whether currently collecting multi-line input.
        hir_phase: HIR generation phase for desugaring AST nodes.
        vm_runner: Optional VM runner for code execution.
    """

    def __init__(self, debug_tokens: bool = False, show_ast: bool = False) -> None:
        """Initialize the REPL with default settings.

        Args:
            debug_tokens: Whether to show tokens instead of evaluating.
            show_ast: Whether to show AST instead of evaluating.
        """
        self.prompt = "md> "
        self.running = True
        self.debug_tokens = debug_tokens
        self.show_ast = show_ast
        self.accumulated_source = ""
        self.multiline_buffer = ""
        self.in_multiline_mode = False
        self.hir_phase = HIRGenerationPhase()  # HIR generation phase for desugaring
        self.vm_runner: Any = None
        self._init_vm_runner()

    def _init_vm_runner(self) -> None:
        """Initialize the VM runner if not in token/AST debug modes."""
        if not self.debug_tokens and not self.show_ast:
            try:
                from machine_dialect.compiler.vm_runner import VMRunner

                self.vm_runner = VMRunner(debug=False, optimize=True)
            except (ImportError, RuntimeError) as e:
                print(f"Warning: Rust VM not available: {e}")
                print("Falling back to AST display mode.")
                self.show_ast = True

    def print_welcome(self) -> None:
        """Print the welcome message when REPL starts."""
        print("Machine Dialect™ REPL v0.1.0")
        if self.debug_tokens:
            mode = "Token Debug Mode"
        elif self.show_ast:
            mode = "HIR/AST Display Mode"
        elif self.vm_runner:
            mode = "Rust VM Execution Mode"
        else:
            mode = "HIR Mode (desugared AST)"
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
            print("  reset  - Clear accumulated source")

        if self.debug_tokens:
            print("\nEnter any text to see its tokens.")
        elif self.show_ast:
            print("\nEnter Machine Dialect™ code to see its HIR (desugared AST).")
            print("Source is accumulated across lines until an error occurs.")
        elif self.vm_runner:
            print("\nEnter Machine Dialect™ code to execute it on the Rust VM.")
            print("Source is accumulated across lines until an error occurs.")
        else:
            print("\nEnter Machine Dialect™ code to see its HIR (desugared AST).")
            print("Source is accumulated across lines until an error occurs.")

        print("\nMulti-line input:")
        print("  Lines ending with ':' enter multi-line mode")
        print("  Lines starting with '>' continue multi-line input")
        print("  Empty line or line not matching above completes input")
        print("  Ctrl+C cancels multi-line input")

        print("\nExample: Set `x` to _10_.")
        print("\nMulti-line example:")
        print("  md> If _5_ > _3_ then:")
        print("  ... > _42_.")
        print("  ... ")
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

    def should_continue_multiline(self, line: str) -> bool:
        """Check if we should continue collecting multi-line input.

        Args:
            line: The current input line.

        Returns:
            True if we should continue collecting input, False otherwise.
        """
        stripped = line.strip()
        # Continue if line ends with colon or starts with '>'
        return stripped.endswith(":") or stripped.startswith(">")

    def get_multiline_prompt(self) -> str:
        """Get the appropriate prompt for multi-line input.

        Returns:
            The prompt string to use.
        """
        # Count the depth of '>' markers in the buffer
        depth = 0
        for line in self.multiline_buffer.split("\n"):
            stripped = line.strip()
            if stripped.startswith(">"):
                # Count consecutive '>' at the start
                for char in stripped:
                    if char == ">":
                        depth += 1
                    else:
                        break
                break

        if depth > 0:
            return "... "
        else:
            return "... "

    def tokenize_and_print(self, input_text: str) -> None:
        """Tokenize the input and print the results.

        Args:
            input_text: The Machine Dialect™ code to tokenize.

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
        """Parse the input and print the AST or evaluation result.

        Args:
            input_text: The Machine Dialect™ code to parse.

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
            # If successful, update accumulated source
            self.accumulated_source = test_source

            # Generate HIR by desugaring the AST
            # Create a minimal compilation context for HIR generation
            from pathlib import Path

            from machine_dialect.ast.program import Program

            config = CompilerConfig(verbose=False)
            context = CompilationContext(source_path=Path("<repl>"), source_content=test_source, config=config)
            hir = self.hir_phase.run(context, ast)

            # Execute or show AST based on mode
            if self.vm_runner:
                # Execute using Rust VM
                try:
                    result = self.vm_runner.execute(self.accumulated_source)
                    print("\nExecution Result:")
                    print("-" * 50)
                    if result is not None:
                        print(f"  {result}")
                    else:
                        print("  (no return value)")
                    print("-" * 50)
                    print()
                except Exception as e:
                    print(f"\nExecution Error: {e}")
                    print()
            else:
                # Show HIR/AST
                print("\nHIR (desugared AST):")
                print("-" * 50)
                if isinstance(hir, Program) and hir.statements:
                    for node in hir.statements:
                        print(f"  {node}")
                else:
                    print("  (empty)")
                print("-" * 50)
                print()

    def run(self) -> int:
        """Run the main REPL loop.

        Handles user input, command processing, and multi-line input collection.
        Continues until the user exits or an unhandled error occurs.

        Returns:
            Exit code (0 for normal exit, 1 for error exit).
        """
        self.print_welcome()

        while self.running:
            try:
                # Determine prompt based on multiline mode
                if self.in_multiline_mode:
                    prompt = self.get_multiline_prompt()
                else:
                    prompt = self.prompt

                # Get input
                user_input = input(prompt)

                # In multiline mode, handle special cases
                if self.in_multiline_mode:
                    # Check if we should continue multiline
                    if self.should_continue_multiline(user_input):
                        # Add to buffer with newline
                        if self.multiline_buffer:
                            self.multiline_buffer += "\n" + user_input
                        else:
                            self.multiline_buffer = user_input
                        continue
                    else:
                        # End multiline mode - process the complete buffer
                        if self.multiline_buffer:
                            complete_input = self.multiline_buffer + "\n" + user_input
                        else:
                            complete_input = user_input

                        # Reset multiline mode
                        self.multiline_buffer = ""
                        self.in_multiline_mode = False

                        # Process the complete input
                        user_input = complete_input
                else:
                    # Check for commands (only in normal mode)
                    if user_input.strip().lower() == "exit":
                        print("Goodbye!")
                        self.running = False
                        return 0  # Normal exit
                    elif user_input.strip().lower() == "help":
                        self.print_help()
                        continue
                    elif user_input.strip().lower() == "clear":
                        self.clear_screen()
                        self.print_welcome()
                        # Also clear accumulated source
                        if not self.debug_tokens:
                            self.accumulated_source = ""
                        continue
                    elif user_input.strip().lower() == "reset" and not self.debug_tokens:
                        # Reset accumulated source in AST mode
                        self.accumulated_source = ""
                        print("Accumulated source cleared.")
                        continue

                    # Check if we should enter multiline mode
                    if not self.debug_tokens and self.should_continue_multiline(user_input):
                        self.in_multiline_mode = True
                        self.multiline_buffer = user_input
                        continue

                # Process non-empty input
                if user_input.strip():
                    # Auto-append period if missing (for non-token mode)
                    if not self.debug_tokens and not user_input.strip().endswith("."):
                        user_input = user_input + "."

                    # Process input based on mode
                    if self.debug_tokens:
                        self.tokenize_and_print(user_input)
                    else:
                        self.parse_and_print(user_input)

            except (KeyboardInterrupt, EOFError):
                # Handle Ctrl+C and Ctrl+D
                if self.in_multiline_mode:
                    # Cancel multiline mode
                    print("\nMultiline input cancelled.")
                    self.multiline_buffer = ""
                    self.in_multiline_mode = False
                else:
                    print("\nGoodbye!")
                    self.running = False
                    return 0  # Normal exit via Ctrl+D
            except Exception as e:
                print(f"Unexpected error: {e}")
                # Reset multiline mode on error
                if self.in_multiline_mode:
                    self.multiline_buffer = ""
                    self.in_multiline_mode = False
                return 1  # Error exit

        return 0  # Default normal exit


def main() -> None:
    """Entry point for the Machine Dialect™ REPL.

    Parses command line arguments and starts the appropriate REPL mode.
    Supports token debug mode and AST display mode via command line flags.
    """
    parser = argparse.ArgumentParser(description="Machine Dialect™ REPL")
    parser.add_argument(
        "--debug-tokens",
        action="store_true",
        help="Run in token debug mode (show tokens)",
    )
    parser.add_argument(
        "--ast",
        action="store_true",
        help="Run in AST mode (show AST instead of evaluating)",
    )
    args = parser.parse_args()

    # Check for incompatible flags
    if args.debug_tokens and args.ast:
        print("Error: --debug-tokens and --ast flags are not compatible")
        sys.exit(1)

    repl = REPL(debug_tokens=args.debug_tokens, show_ast=args.ast)
    exit_code = repl.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
