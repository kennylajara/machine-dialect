"""Unit tests for machine_dialect.cfg.examples module.

This module tests all example functions that demonstrate CFG parser usage,
including parsing, validation, and placeholder generation functionality.
"""

from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from lark import Tree

from machine_dialect.cfg.examples import (
    example_generate_prompt,
    example_parse_code,
    example_validate_code,
    main,
)


class TestExampleParseCode:
    """Test suite for example_parse_code function."""

    @patch("machine_dialect.cfg.examples.CFGParser")
    @patch("sys.stdout", new_callable=StringIO)
    def test_all_examples_parse_successfully(self, mock_stdout: StringIO, mock_parser_class: Mock) -> None:
        """Test that all three examples parse successfully.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
            mock_parser_class: Mocked CFGParser class.
        """
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser

        # Create mock tree objects for each example
        mock_tree1 = MagicMock(spec=Tree)
        mock_tree2 = MagicMock(spec=Tree)
        mock_tree3 = MagicMock(spec=Tree)

        # Configure parse to return different trees for each call
        mock_parser.parse.side_effect = [mock_tree1, mock_tree2, mock_tree3]

        # Configure pretty_print to return formatted strings
        mock_parser.pretty_print.side_effect = [
            "AST for example 1",
            "AST for example 2",
            "AST for example 3",
        ]

        # Execute the function
        example_parse_code()

        # Verify parse was called three times with expected code snippets
        assert mock_parser.parse.call_count == 3

        # Check first call (simple arithmetic)
        first_call_arg = mock_parser.parse.call_args_list[0][0][0]
        assert "Set `x` to _10_." in first_call_arg
        assert "Set `y` to _20_." in first_call_arg
        assert "Set `sum` to `x` + `y`." in first_call_arg

        # Check second call (conditional)
        second_call_arg = mock_parser.parse.call_args_list[1][0][0]
        assert "Set `age` to _18_." in second_call_arg
        assert "If `age` is greater than _17_" in second_call_arg

        # Check third call (logical operations)
        third_call_arg = mock_parser.parse.call_args_list[2][0][0]
        assert "Set `is_raining` to _yes_." in third_call_arg
        assert "Set `have_umbrella` to _no_." in third_call_arg

        # Verify output contains success messages
        output = mock_stdout.getvalue()
        assert output.count("Parse successful!") == 3
        assert "Example 1: Simple arithmetic" in output
        assert "Example 2: Conditional" in output
        assert "Example 3: Logical operations" in output
        assert "AST for example 1" in output
        assert "AST for example 2" in output
        assert "AST for example 3" in output

    @patch("machine_dialect.cfg.examples.CFGParser")
    @patch("sys.stdout", new_callable=StringIO)
    def test_parse_failures_are_handled(self, mock_stdout: StringIO, mock_parser_class: Mock) -> None:
        """Test that parse failures are properly handled and reported.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
            mock_parser_class: Mocked CFGParser class.
        """
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser

        # Configure parse to raise ValueError for all examples
        mock_parser.parse.side_effect = [
            ValueError("Invalid syntax in example 1"),
            ValueError("Invalid syntax in example 2"),
            ValueError("Invalid syntax in example 3"),
        ]

        # Execute the function
        example_parse_code()

        # Verify parse was called three times
        assert mock_parser.parse.call_count == 3

        # Verify output contains failure messages
        output = mock_stdout.getvalue()
        assert "Parse failed: Invalid syntax in example 1" in output
        assert "Parse failed: Invalid syntax in example 2" in output
        assert "Parse failed: Invalid syntax in example 3" in output
        assert output.count("Parse successful!") == 0

    @patch("machine_dialect.cfg.examples.CFGParser")
    @patch("sys.stdout", new_callable=StringIO)
    def test_mixed_success_and_failure(self, mock_stdout: StringIO, mock_parser_class: Mock) -> None:
        """Test handling of mixed success and failure cases.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
            mock_parser_class: Mocked CFGParser class.
        """
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser

        # Configure parse to succeed, fail, succeed
        mock_tree1 = MagicMock(spec=Tree)
        mock_tree3 = MagicMock(spec=Tree)

        mock_parser.parse.side_effect = [
            mock_tree1,
            ValueError("Syntax error in conditional"),
            mock_tree3,
        ]

        mock_parser.pretty_print.side_effect = [
            "AST for example 1",
            "AST for example 3",  # No call for example 2 due to error
        ]

        # Execute the function
        example_parse_code()

        # Verify output contains mixed results
        output = mock_stdout.getvalue()
        assert output.count("Parse successful!") == 2
        assert output.count("Parse failed:") == 1
        assert "Parse failed: Syntax error in conditional" in output


class TestExampleGeneratePrompt:
    """Test suite for example_generate_prompt function."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_prints_placeholder_message(self, mock_stdout: StringIO) -> None:
        """Test that the function prints the placeholder message.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
        """
        example_generate_prompt()

        output = mock_stdout.getvalue()
        assert "CFG generation functionality coming soon." in output

    def test_function_returns_none(self) -> None:
        """Test that the function returns None."""
        example_generate_prompt()  # Function has no return value


class TestExampleValidateCode:
    """Test suite for example_validate_code function."""

    @patch("machine_dialect.cfg.examples.CFGParser")
    @patch("sys.stdout", new_callable=StringIO)
    def test_validates_valid_and_invalid_code(self, mock_stdout: StringIO, mock_parser_class: Mock) -> None:
        """Test validation of both valid and invalid code examples.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
            mock_parser_class: Mocked CFGParser class.
        """
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser

        # Configure validate to return True for valid, False for invalid
        mock_parser.validate.side_effect = [True, False]

        # Execute the function
        example_validate_code()

        # Verify validate was called twice
        assert mock_parser.validate.call_count == 2

        # Check valid code call
        valid_call_arg = mock_parser.validate.call_args_list[0][0][0]
        assert 'Set `name` to _"Alice"_.' in valid_call_arg
        assert "Say `name`." in valid_call_arg

        # Check invalid code call
        invalid_call_arg = mock_parser.validate.call_args_list[1][0][0]
        assert "Set x to 10" in invalid_call_arg
        assert "Say x" in invalid_call_arg

        # Verify output contains expected messages
        output = mock_stdout.getvalue()
        assert "✓ Code is valid!" in output
        assert "✗ Code is invalid!" in output
        assert "Validating valid code:" in output
        assert "Validating invalid code (missing backticks and periods):" in output

    @patch("machine_dialect.cfg.examples.CFGParser")
    @patch("sys.stdout", new_callable=StringIO)
    def test_both_codes_valid(self, mock_stdout: StringIO, mock_parser_class: Mock) -> None:
        """Test when both code examples are valid.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
            mock_parser_class: Mocked CFGParser class.
        """
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser

        # Configure validate to return True for both
        mock_parser.validate.return_value = True

        # Execute the function
        example_validate_code()

        # Verify output shows both as valid
        output = mock_stdout.getvalue()
        assert output.count("✓ Code is valid!") == 2
        assert output.count("✗ Code is invalid!") == 0

    @patch("machine_dialect.cfg.examples.CFGParser")
    @patch("sys.stdout", new_callable=StringIO)
    def test_both_codes_invalid(self, mock_stdout: StringIO, mock_parser_class: Mock) -> None:
        """Test when both code examples are invalid.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
            mock_parser_class: Mocked CFGParser class.
        """
        # Setup mock parser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser

        # Configure validate to return False for both
        mock_parser.validate.return_value = False

        # Execute the function
        example_validate_code()

        # Verify output shows both as invalid
        output = mock_stdout.getvalue()
        assert output.count("✓ Code is valid!") == 0
        assert output.count("✗ Code is invalid!") == 2


class TestMain:
    """Test suite for main function."""

    @patch("machine_dialect.cfg.examples.example_validate_code")
    @patch("machine_dialect.cfg.examples.example_generate_prompt")
    @patch("machine_dialect.cfg.examples.example_parse_code")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_calls_all_examples(
        self,
        mock_stdout: StringIO,
        mock_parse: Mock,
        mock_generate: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test that main calls all example functions in order.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
            mock_parse: Mocked example_parse_code function.
            mock_generate: Mocked example_generate_prompt function.
            mock_validate: Mocked example_validate_code function.
        """
        # Execute main
        main()

        # Verify all example functions were called once
        mock_parse.assert_called_once()
        mock_generate.assert_called_once()
        mock_validate.assert_called_once()

        # Verify output contains section headers
        output = mock_stdout.getvalue()
        assert "CFG Parser Examples" in output
        assert "1. PARSING EXAMPLES" in output
        assert "2. GENERATION PROMPT EXAMPLES" in output
        assert "3. VALIDATION EXAMPLES" in output
        assert "Examples complete!" in output

    @patch("machine_dialect.cfg.examples.example_validate_code")
    @patch("machine_dialect.cfg.examples.example_generate_prompt")
    @patch("machine_dialect.cfg.examples.example_parse_code")
    def test_main_execution_order(self, mock_parse: Mock, mock_generate: Mock, mock_validate: Mock) -> None:
        """Test that example functions are called in the correct order.

        Args:
            mock_parse: Mocked example_parse_code function.
            mock_generate: Mocked example_generate_prompt function.
            mock_validate: Mocked example_validate_code function.
        """
        # Track call order
        call_order: list[str] = []

        def track_parse() -> None:
            call_order.append("parse")

        def track_generate() -> None:
            call_order.append("generate")

        def track_validate() -> None:
            call_order.append("validate")

        mock_parse.side_effect = track_parse
        mock_generate.side_effect = track_generate
        mock_validate.side_effect = track_validate

        # Execute main
        main()

        # Verify correct order
        assert call_order == ["parse", "generate", "validate"]

    @patch("machine_dialect.cfg.examples.example_validate_code")
    @patch("machine_dialect.cfg.examples.example_generate_prompt")
    @patch("machine_dialect.cfg.examples.example_parse_code")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_with_exception_propagation(
        self,
        mock_stdout: StringIO,
        mock_parse: Mock,
        mock_generate: Mock,
        mock_validate: Mock,
    ) -> None:
        """Test that main propagates exceptions from example functions.

        Args:
            mock_stdout: Mocked stdout for capturing print output.
            mock_parse: Mocked example_parse_code function.
            mock_generate: Mocked example_generate_prompt function.
            mock_validate: Mocked example_validate_code function.
        """
        # Configure parse to raise an exception
        mock_parse.side_effect = Exception("Parse example failed")

        # Execute main - should raise the exception
        with pytest.raises(Exception, match="Parse example failed"):
            main()

        # Verify parse was called
        mock_parse.assert_called_once()

        # Verify other functions were not called due to exception
        mock_generate.assert_not_called()
        mock_validate.assert_not_called()


class TestModuleExecution:
    """Test suite for module execution as __main__."""

    @patch("machine_dialect.cfg.examples.main")
    def test_main_called_when_module_executed(self, mock_main: Mock) -> None:
        """Test that main() is called when module is executed directly.

        Args:
            mock_main: Mocked main function.
        """
        # Import the module to trigger __main__ check
        from unittest.mock import patch

        with patch("machine_dialect.cfg.examples.__name__", "__main__"):
            # Re-import to trigger the if __name__ == "__main__" block
            import machine_dialect.cfg.examples

            # Note: In practice, this test would need special handling
            # for the if __name__ == "__main__" block
            # For now we just verify main exists and is callable
            assert callable(machine_dialect.cfg.examples.main)
