#!/usr/bin/env python3
"""Comprehensive unit tests for the Machine Dialect™ REPL."""

from unittest.mock import Mock, patch

import pytest

from machine_dialect.repl.repl import REPL


class TestREPLInitialization:
    """Test REPL initialization and configuration."""

    def test_init_default_settings(self) -> None:
        """Test REPL initialization with default settings."""
        repl = REPL()

        assert repl.prompt == "md> "
        assert repl.running is True
        assert repl.debug_tokens is False
        assert repl.show_ast is False
        assert repl.accumulated_source == ""
        assert repl.multiline_buffer == ""
        assert repl.in_multiline_mode is False
        assert repl.hir_phase is not None
        assert repl.vm_runner is not None  # Should try to initialize VM

    def test_init_debug_tokens_mode(self) -> None:
        """Test REPL initialization with debug tokens mode."""
        repl = REPL(debug_tokens=True)

        assert repl.debug_tokens is True
        assert repl.show_ast is False
        assert repl.vm_runner is None  # Should not initialize VM in debug mode

    def test_init_ast_mode(self) -> None:
        """Test REPL initialization with AST display mode."""
        repl = REPL(show_ast=True)

        assert repl.debug_tokens is False
        assert repl.show_ast is True
        assert repl.vm_runner is None  # Should not initialize VM in AST mode

    @patch("machine_dialect.compiler.vm_runner.VMRunner")
    def test_init_vm_runner_import_error(self, mock_vm_runner: Mock) -> None:
        """Test REPL gracefully handles VM import errors."""
        mock_vm_runner.side_effect = ImportError("VM not available")

        with patch("builtins.print") as mock_print:
            repl = REPL()

            assert repl.show_ast is True  # Should fall back to AST mode
            assert repl.vm_runner is None
            mock_print.assert_any_call("Warning: Rust VM not available: VM not available")
            mock_print.assert_any_call("Falling back to AST display mode.")

    @patch("machine_dialect.compiler.vm_runner.VMRunner")
    def test_init_vm_runner_runtime_error(self, mock_vm_runner: Mock) -> None:
        """Test REPL handles VM runtime errors during initialization."""
        mock_vm_runner.side_effect = RuntimeError("VM initialization failed")

        with patch("builtins.print") as mock_print:
            repl = REPL()

            assert repl.show_ast is True
            assert repl.vm_runner is None
            mock_print.assert_any_call("Warning: Rust VM not available: VM initialization failed")


class TestREPLDisplay:
    """Test REPL display methods."""

    @patch("builtins.print")
    def test_print_welcome_vm_mode(self, mock_print: Mock) -> None:
        """Test welcome message in VM execution mode."""
        with patch("machine_dialect.compiler.vm_runner.VMRunner"):
            repl = REPL()
            repl.print_welcome()

            calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
            assert "Machine Dialect™ REPL v0.1.0" in calls
            assert "Mode: Rust VM Execution Mode" in calls
            assert "Type 'exit' to exit, 'help' for help" in calls

    @patch("builtins.print")
    def test_print_welcome_debug_tokens_mode(self, mock_print: Mock) -> None:
        """Test welcome message in token debug mode."""
        repl = REPL(debug_tokens=True)
        repl.print_welcome()

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        assert "Mode: Token Debug Mode" in calls

    @patch("builtins.print")
    def test_print_welcome_ast_mode(self, mock_print: Mock) -> None:
        """Test welcome message in AST display mode."""
        repl = REPL(show_ast=True)
        repl.print_welcome()

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        assert "Mode: HIR/AST Display Mode" in calls

    @patch("builtins.print")
    def test_print_help_vm_mode(self, mock_print: Mock) -> None:
        """Test help message in VM mode."""
        with patch("machine_dialect.compiler.vm_runner.VMRunner"):
            repl = REPL()
            repl.print_help()

            calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
            assert any("Enter Machine Dialect™ code to execute it on the Rust VM." in call for call in calls)
            assert any("reset  - Clear accumulated source" in call for call in calls)

    @patch("builtins.print")
    def test_print_help_debug_tokens_mode(self, mock_print: Mock) -> None:
        """Test help message in debug tokens mode."""
        repl = REPL(debug_tokens=True)
        repl.print_help()

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        assert any("Enter any text to see its tokens." in call for call in calls)
        # Should not show reset command in token debug mode
        assert not any("reset" in call for call in calls)

    @patch("os.system")
    def test_clear_screen_unix(self, mock_system: Mock) -> None:
        """Test screen clearing on Unix systems."""
        with patch("os.name", "posix"):
            repl = REPL()
            repl.clear_screen()
            mock_system.assert_called_once_with("clear")

    @patch("os.system")
    def test_clear_screen_windows(self, mock_system: Mock) -> None:
        """Test screen clearing on Windows systems."""
        with patch("os.name", "nt"):
            repl = REPL()
            repl.clear_screen()
            mock_system.assert_called_once_with("cls")


class TestREPLTokenFormatting:
    """Test token formatting functionality."""

    def test_format_token(self) -> None:
        """Test token formatting for display."""
        from machine_dialect.lexer.tokens import Token, TokenType

        repl = REPL()
        token = Token(TokenType.KW_SET, "Set", line=1, position=1)

        formatted = repl.format_token(token)
        expected = "  KW_SET               | 'Set'"

        assert formatted == expected

    def test_format_token_with_special_characters(self) -> None:
        """Test token formatting with special characters."""
        from machine_dialect.lexer.tokens import Token, TokenType

        repl = REPL()
        token = Token(TokenType.LIT_TEXT, '"hello\nworld"', line=1, position=1)

        formatted = repl.format_token(token)
        # Should properly escape the newline in repr
        assert "LIT_TEXT" in formatted
        assert "'\"hello\\nworld\"'" in formatted


class TestREPLMultilineHandling:
    """Test multi-line input handling."""

    def test_should_continue_multiline_with_colon(self) -> None:
        """Test multi-line continuation with colon ending."""
        repl = REPL()

        assert repl.should_continue_multiline("If _5_ > _3_ then:")
        assert repl.should_continue_multiline("  something:")
        assert not repl.should_continue_multiline("Set x to _10_.")

    def test_should_continue_multiline_with_greater_than(self) -> None:
        """Test multi-line continuation with > marker."""
        repl = REPL()

        assert repl.should_continue_multiline("> _42_.")
        assert repl.should_continue_multiline("  > something else.")
        assert not repl.should_continue_multiline("Regular line.")

    def test_get_multiline_prompt_basic(self) -> None:
        """Test multi-line prompt generation."""
        repl = REPL()

        # No depth should return basic prompt
        repl.multiline_buffer = ""
        assert repl.get_multiline_prompt() == "... "

    def test_get_multiline_prompt_with_depth(self) -> None:
        """Test multi-line prompt with nested blocks."""
        repl = REPL()

        # Set up buffer with > markers
        repl.multiline_buffer = "> _42_."
        prompt = repl.get_multiline_prompt()
        assert prompt == "... "  # Current implementation returns "... " regardless of depth


class TestREPLTokenization:
    """Test tokenization functionality."""

    @patch("builtins.print")
    def test_tokenize_and_print_simple_input(self, mock_print: Mock) -> None:
        """Test tokenizing and printing simple input."""
        repl = REPL(debug_tokens=True)

        repl.tokenize_and_print("Set `x` to _10_.")

        # Check that tokens were printed
        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        token_output = [call for call in calls if "KW_SET" in call or "Tokens" in call]
        assert len(token_output) > 0

    @patch("builtins.print")
    def test_tokenize_and_print_error_handling(self, mock_print: Mock) -> None:
        """Test tokenization error handling."""
        repl = REPL(debug_tokens=True)

        # Mock lexer to raise an exception
        with patch("machine_dialect.repl.repl.Lexer") as mock_lexer_class:
            mock_lexer = Mock()
            mock_lexer.next_token.side_effect = Exception("Lexer error")
            mock_lexer_class.return_value = mock_lexer

            repl.tokenize_and_print("invalid input")

            # Should print error message
            calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
            error_calls = [call for call in calls if "Error:" in call]
            assert len(error_calls) > 0


class TestREPLParsing:
    """Test parsing functionality."""

    def test_parse_and_print_accumulates_source(self) -> None:
        """Test that parsing accumulates successful source."""
        repl = REPL(show_ast=True)

        with patch("machine_dialect.repl.repl.Parser") as mock_parser_class, patch("builtins.print"):
            # Mock successful parsing
            mock_parser = Mock()
            mock_parser.parse.return_value = Mock()
            mock_parser.has_errors.return_value = False
            mock_parser_class.return_value = mock_parser

            # Mock HIR phase
            with patch.object(repl.hir_phase, "run") as mock_hir_run:
                mock_program = Mock()
                mock_program.statements = []
                mock_hir_run.return_value = mock_program

                repl.parse_and_print("Set `x` to _10_.")

                # Source should be accumulated
                assert repl.accumulated_source == "Set `x` to _10_."

    @patch("builtins.print")
    def test_parse_and_print_handles_parser_errors(self, mock_print: Mock) -> None:
        """Test that parsing handles parser errors correctly."""
        repl = REPL(show_ast=True)

        with patch("machine_dialect.repl.repl.Parser") as mock_parser_class:
            # Mock parser with errors
            mock_parser = Mock()
            mock_parser.parse.return_value = Mock()
            mock_parser.has_errors.return_value = True
            mock_parser.errors = ["Parse error: unexpected token"]
            mock_parser_class.return_value = mock_parser

            original_source = repl.accumulated_source
            repl.parse_and_print("invalid syntax")

            # Source should not be updated on error
            assert repl.accumulated_source == original_source

            # Should print error
            calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
            error_calls = [call for call in calls if "Errors found:" in call]
            assert len(error_calls) > 0

    @patch("builtins.print")
    def test_parse_and_print_vm_execution(self, mock_print: Mock) -> None:
        """Test parsing with VM execution."""
        with patch("machine_dialect.compiler.vm_runner.VMRunner") as mock_vm_runner_class:
            mock_vm_runner = Mock()
            mock_vm_runner.execute.return_value = "42"
            mock_vm_runner_class.return_value = mock_vm_runner

            repl = REPL()  # VM mode

            with patch("machine_dialect.repl.repl.Parser") as mock_parser_class:
                # Mock successful parsing
                mock_parser = Mock()
                mock_parser.parse.return_value = Mock()
                mock_parser.has_errors.return_value = False
                mock_parser_class.return_value = mock_parser

                # Mock HIR phase
                with patch.object(repl.hir_phase, "run"):
                    repl.parse_and_print("Set `x` to _10_.")

                    # Should execute code
                    mock_vm_runner.execute.assert_called_once()

                    # Should print result
                    calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
                    result_calls = [call for call in calls if "Execution Result:" in call or "42" in call]
                    assert len(result_calls) > 0

    @patch("builtins.print")
    def test_parse_and_print_vm_execution_error(self, mock_print: Mock) -> None:
        """Test parsing handles VM execution errors."""
        with patch("machine_dialect.compiler.vm_runner.VMRunner") as mock_vm_runner_class:
            mock_vm_runner = Mock()
            mock_vm_runner.execute.side_effect = Exception("Execution failed")
            mock_vm_runner_class.return_value = mock_vm_runner

            repl = REPL()  # VM mode

            with patch("machine_dialect.repl.repl.Parser") as mock_parser_class:
                # Mock successful parsing
                mock_parser = Mock()
                mock_parser.parse.return_value = Mock()
                mock_parser.has_errors.return_value = False
                mock_parser_class.return_value = mock_parser

                # Mock HIR phase
                with patch.object(repl.hir_phase, "run"):
                    repl.parse_and_print("Set `x` to _10_.")

                    # Should print execution error
                    calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
                    error_calls = [call for call in calls if "Execution Error:" in call]
                    assert len(error_calls) > 0


class TestREPLMainLoop:
    """Test the main REPL loop functionality."""

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_exit_command(self, mock_print: Mock, mock_input: Mock) -> None:
        """Test REPL exits on 'exit' command."""
        mock_input.return_value = "exit"

        repl = REPL(debug_tokens=True)  # Use debug mode to avoid VM setup
        exit_code = repl.run()

        assert exit_code == 0
        assert repl.running is False

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        assert "Goodbye!" in calls

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_help_command(self, mock_print: Mock, mock_input: Mock) -> None:
        """Test REPL shows help on 'help' command."""
        mock_input.side_effect = ["help", "exit"]

        repl = REPL(debug_tokens=True)
        exit_code = repl.run()

        assert exit_code == 0

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        help_calls = [call for call in calls if "Available commands:" in call]
        assert len(help_calls) > 0

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("os.system")
    def test_run_clear_command(self, mock_system: Mock, mock_print: Mock, mock_input: Mock) -> None:
        """Test REPL clears screen on 'clear' command."""
        mock_input.side_effect = ["clear", "exit"]

        repl = REPL(debug_tokens=True)
        exit_code = repl.run()

        assert exit_code == 0
        mock_system.assert_called()  # Screen should be cleared

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_reset_command(self, mock_print: Mock, mock_input: Mock) -> None:
        """Test REPL resets accumulated source on 'reset' command."""
        mock_input.side_effect = ["reset", "exit"]

        repl = REPL(show_ast=True)  # Non-debug mode to enable reset
        repl.accumulated_source = "some code"

        exit_code = repl.run()

        assert exit_code == 0
        assert repl.accumulated_source == ""

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        reset_calls = [call for call in calls if "Accumulated source cleared." in call]
        assert len(reset_calls) > 0

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_keyboard_interrupt_normal_mode(self, mock_print: Mock, mock_input: Mock) -> None:
        """Test REPL handles KeyboardInterrupt in normal mode."""
        mock_input.side_effect = KeyboardInterrupt()

        repl = REPL(debug_tokens=True)
        exit_code = repl.run()

        assert exit_code == 0
        assert repl.running is False

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        goodbye_calls = [call for call in calls if "Goodbye!" in call]
        assert len(goodbye_calls) > 0

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_keyboard_interrupt_multiline_mode(self, mock_print: Mock, mock_input: Mock) -> None:
        """Test REPL handles KeyboardInterrupt in multiline mode."""
        repl = REPL(debug_tokens=True)
        repl.in_multiline_mode = True
        repl.multiline_buffer = "some input"

        mock_input.side_effect = KeyboardInterrupt()

        exit_code = repl.run()

        assert exit_code == 0
        assert repl.in_multiline_mode is False
        assert repl.multiline_buffer == ""

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        cancel_calls = [call for call in calls if "Multiline input cancelled." in call]
        assert len(cancel_calls) > 0

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_eof_error(self, mock_print: Mock, mock_input: Mock) -> None:
        """Test REPL handles EOFError (Ctrl+D)."""
        mock_input.side_effect = EOFError()

        repl = REPL(debug_tokens=True)
        exit_code = repl.run()

        assert exit_code == 0
        assert repl.running is False

    @patch("builtins.input")
    @patch("builtins.print")
    def test_run_unexpected_error(self, mock_print: Mock, mock_input: Mock) -> None:
        """Test REPL handles unexpected errors."""
        mock_input.side_effect = RuntimeError("Unexpected error")

        repl = REPL(debug_tokens=True)
        exit_code = repl.run()

        assert exit_code == 1  # Error exit code

        calls = [str(call.args[0]) if call.args else "" for call in mock_print.call_args_list]
        error_calls = [call for call in calls if "Unexpected error:" in call]
        assert len(error_calls) > 0

    @patch("builtins.input")
    def test_run_multiline_input_collection(self, mock_input: Mock) -> None:
        """Test REPL collects multi-line input correctly."""
        mock_input.side_effect = [
            "If _5_ > _3_ then:",  # Start multiline
            "> _42_.",  # Continue multiline
            "",  # End multiline (empty line)
            "exit",  # Exit
        ]

        repl = REPL(show_ast=True)

        with patch.object(repl, "parse_and_print") as mock_parse:
            exit_code = repl.run()

            assert exit_code == 0

            # Should have called parse_and_print with combined input
            mock_parse.assert_called()
            call_args = mock_parse.call_args[0][0]
            assert "If _5_ > _3_ then:" in call_args
            assert "> _42_." in call_args

    @patch("builtins.input")
    def test_run_auto_period_addition(self, mock_input: Mock) -> None:
        """Test REPL automatically adds periods to statements."""
        mock_input.side_effect = [
            "Set `x` to _10_",  # Missing period
            "exit",
        ]

        repl = REPL(show_ast=True)

        with patch.object(repl, "parse_and_print") as mock_parse:
            exit_code = repl.run()

            assert exit_code == 0

            # Should have added period
            mock_parse.assert_called_with("Set `x` to _10_.")

    @patch("builtins.input")
    def test_run_no_auto_period_in_debug_mode(self, mock_input: Mock) -> None:
        """Test REPL doesn't add periods in debug token mode."""
        mock_input.side_effect = ["Set x to 10", "exit"]

        repl = REPL(debug_tokens=True)

        with patch.object(repl, "tokenize_and_print") as mock_tokenize:
            exit_code = repl.run()

            assert exit_code == 0

            # Should not have added period
            mock_tokenize.assert_called_with("Set x to 10")


class TestREPLMainFunction:
    """Test the main function and argument parsing."""

    @patch("sys.argv", ["repl.py"])
    @patch("sys.exit")
    def test_main_default_arguments(self, mock_exit: Mock) -> None:
        """Test main function with default arguments."""
        with patch("machine_dialect.repl.repl.REPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run.return_value = 0
            mock_repl_class.return_value = mock_repl

            from machine_dialect.repl.repl import main

            main()

            mock_repl_class.assert_called_once_with(debug_tokens=False, show_ast=False)
            mock_repl.run.assert_called_once()
            mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["repl.py", "--debug-tokens"])
    @patch("sys.exit")
    def test_main_debug_tokens_flag(self, mock_exit: Mock) -> None:
        """Test main function with debug tokens flag."""
        with patch("machine_dialect.repl.repl.REPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run.return_value = 0
            mock_repl_class.return_value = mock_repl

            from machine_dialect.repl.repl import main

            main()

            mock_repl_class.assert_called_once_with(debug_tokens=True, show_ast=False)

    @patch("sys.argv", ["repl.py", "--ast"])
    @patch("sys.exit")
    def test_main_ast_flag(self, mock_exit: Mock) -> None:
        """Test main function with AST flag."""
        with patch("machine_dialect.repl.repl.REPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run.return_value = 0
            mock_repl_class.return_value = mock_repl

            from machine_dialect.repl.repl import main

            main()

            mock_repl_class.assert_called_once_with(debug_tokens=False, show_ast=True)

    @patch("sys.argv", ["repl.py", "--debug-tokens", "--ast"])
    @patch("sys.exit", side_effect=SystemExit(1))
    @patch("builtins.print")
    def test_main_incompatible_flags(self, mock_print: Mock, mock_exit: Mock) -> None:
        """Test main function handles incompatible flags."""
        from machine_dialect.repl.repl import main

        with pytest.raises(SystemExit):
            main()

        mock_print.assert_called_with("Error: --debug-tokens and --ast flags are not compatible")
        mock_exit.assert_called_with(1)

    @patch("sys.argv", ["repl.py"])
    @patch("sys.exit")
    def test_main_repl_error_exit_code(self, mock_exit: Mock) -> None:
        """Test main function propagates REPL exit codes."""
        with patch("machine_dialect.repl.repl.REPL") as mock_repl_class:
            mock_repl = Mock()
            mock_repl.run.return_value = 1  # Error exit code
            mock_repl_class.return_value = mock_repl

            from machine_dialect.repl.repl import main

            main()

            mock_exit.assert_called_once_with(1)
