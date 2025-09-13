"""Tests for the AI-based Machine Dialect™ code generation module."""

from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from machine_dialect.cfg.generate_with_ai import generate_code, main


class TestGenerateCode:
    """Test the generate_code function."""

    @patch("machine_dialect.cfg.generate_with_ai.ConfigLoader")
    @patch("machine_dialect.cfg.generate_with_ai.CFGParser")
    def test_generate_code_with_valid_config(self, mock_parser_class: Mock, mock_loader_class: Mock) -> None:
        """Test successful code generation with valid configuration."""
        # Setup mocks
        mock_loader = mock_loader_class.return_value
        mock_config = MagicMock()
        mock_config.key = "test-api-key"
        mock_config.model = "gpt-3.5-turbo"
        mock_loader.load.return_value = mock_config

        mock_parser = mock_parser_class.return_value
        mock_parser.validate.return_value = True

        # Call function
        result = generate_code(
            task="calculate area",
            temperature=0.5,
            max_tokens=300,
            validate=True,
        )

        # Verify result contains example code
        assert "Set `width` to" in result
        assert "Set `height` to" in result
        assert "Set `area` to" in result

        # Verify mocks were called
        mock_loader.load.assert_called_once()
        mock_parser.validate.assert_called_once()

    @patch("machine_dialect.cfg.generate_with_ai.ConfigLoader")
    @patch("machine_dialect.cfg.generate_with_ai.CFGParser")
    def test_generate_code_with_api_key_override(self, mock_parser_class: Mock, mock_loader_class: Mock) -> None:
        """Test that API key parameter overrides config."""
        # Setup mocks
        mock_loader = mock_loader_class.return_value
        mock_config = MagicMock()
        mock_config.key = "config-api-key"
        mock_config.model = "gpt-3.5-turbo"
        mock_loader.load.return_value = mock_config

        mock_parser = mock_parser_class.return_value
        mock_parser.validate.return_value = True

        # Call with API key override
        result = generate_code(
            task="test task",
            api_key="override-api-key",
            validate=True,
        )

        # Verify the config was overridden
        assert mock_config.key == "override-api-key"
        assert result is not None

    @patch("machine_dialect.cfg.generate_with_ai.ConfigLoader")
    @patch("machine_dialect.cfg.generate_with_ai.CFGParser")
    def test_generate_code_with_model_override(self, mock_parser_class: Mock, mock_loader_class: Mock) -> None:
        """Test that model parameter overrides config."""
        # Setup mocks
        mock_loader = mock_loader_class.return_value
        mock_config = MagicMock()
        mock_config.key = "test-api-key"
        mock_config.model = "gpt-3.5-turbo"
        mock_loader.load.return_value = mock_config

        mock_parser = mock_parser_class.return_value
        mock_parser.validate.return_value = True

        # Call with model override
        result = generate_code(
            task="test task",
            model="gpt-4",
            validate=True,
        )

        # Verify the config was overridden
        assert mock_config.model == "gpt-4"
        assert result is not None

    @patch("machine_dialect.cfg.generate_with_ai.ConfigLoader")
    def test_generate_code_missing_api_key(self, mock_loader_class: Mock) -> None:
        """Test error when API key is not configured."""
        # Setup mocks - no API key
        mock_loader = mock_loader_class.return_value
        mock_config = MagicMock()
        mock_config.key = None
        mock_config.model = "gpt-3.5-turbo"
        mock_loader.load.return_value = mock_config
        mock_loader.get_error_message.return_value = "Please configure API key"

        # Should raise ValueError
        with pytest.raises(ValueError, match="Please configure API key"):
            generate_code(task="test task")

    @patch("machine_dialect.cfg.generate_with_ai.ConfigLoader")
    def test_generate_code_missing_model(self, mock_loader_class: Mock) -> None:
        """Test error when model is not configured."""
        # Setup mocks - no model
        mock_loader = mock_loader_class.return_value
        mock_config = MagicMock()
        mock_config.key = "test-api-key"
        mock_config.model = None
        mock_loader.load.return_value = mock_config
        mock_loader.get_error_message.return_value = "Please configure model"

        # Should raise ValueError
        with pytest.raises(ValueError, match="No AI model configured"):
            generate_code(task="test task")

    @patch("machine_dialect.cfg.generate_with_ai.ConfigLoader")
    @patch("machine_dialect.cfg.generate_with_ai.CFGParser")
    @patch("builtins.print")
    def test_generate_code_without_validation(
        self, mock_print: Mock, mock_parser_class: Mock, mock_loader_class: Mock
    ) -> None:
        """Test code generation without validation."""
        # Setup mocks
        mock_loader = mock_loader_class.return_value
        mock_config = MagicMock()
        mock_config.key = "test-api-key"
        mock_config.model = "gpt-3.5-turbo"
        mock_loader.load.return_value = mock_config

        mock_parser = mock_parser_class.return_value

        # Call without validation
        result = generate_code(
            task="test task",
            validate=False,
        )

        # Verify parser was not instantiated/called
        mock_parser.validate.assert_not_called()
        assert result is not None

    @patch("machine_dialect.cfg.generate_with_ai.ConfigLoader")
    @patch("machine_dialect.cfg.generate_with_ai.CFGParser")
    @patch("builtins.print")
    def test_generate_code_with_invalid_syntax(
        self, mock_print: Mock, mock_parser_class: Mock, mock_loader_class: Mock
    ) -> None:
        """Test code generation when validation fails."""
        # Setup mocks
        mock_loader = mock_loader_class.return_value
        mock_config = MagicMock()
        mock_config.key = "test-api-key"
        mock_config.model = "gpt-3.5-turbo"
        mock_loader.load.return_value = mock_config

        mock_parser = mock_parser_class.return_value
        mock_parser.validate.return_value = False

        # Call with validation
        result = generate_code(
            task="test task",
            validate=True,
        )

        # Verify validation was attempted and failed message printed
        mock_parser.validate.assert_called_once()
        # Check that error message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("✗ Generated code has syntax errors" in str(call) for call in print_calls)
        assert result is not None

    @patch("machine_dialect.cfg.generate_with_ai.ConfigLoader")
    @patch("machine_dialect.cfg.generate_with_ai.CFGParser")
    @patch("builtins.print")
    def test_generate_code_temperature_and_tokens(
        self, mock_print: Mock, mock_parser_class: Mock, mock_loader_class: Mock
    ) -> None:
        """Test that temperature and max_tokens parameters are used."""
        # Setup mocks
        mock_loader = mock_loader_class.return_value
        mock_config = MagicMock()
        mock_config.key = "test-api-key"
        mock_config.model = "gpt-4"
        mock_loader.load.return_value = mock_config

        mock_parser = mock_parser_class.return_value
        mock_parser.validate.return_value = True

        # Call with custom temperature and tokens
        result = generate_code(
            task="complex task",
            temperature=0.2,
            max_tokens=1000,
            validate=True,
        )

        # Verify parameters were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Temperature: 0.2" in str(call) for call in print_calls)
        assert any("Max tokens: 1000" in str(call) for call in print_calls)
        assert result is not None


class TestMain:
    """Test the main function."""

    @patch("sys.argv", ["prog", "calculate area"])
    @patch("machine_dialect.cfg.generate_with_ai.generate_code")
    def test_main_basic_task(self, mock_generate: Mock) -> None:
        """Test main with basic task argument."""
        mock_generate.return_value = "Generated code"

        result = main()

        assert result == 0
        mock_generate.assert_called_once_with(
            task="calculate area",
            api_key=None,
            model=None,
            temperature=0.7,
            max_tokens=500,
            validate=True,
        )

    @patch("sys.argv", ["prog", "test task", "--api-key", "my-key", "--model", "gpt-4"])
    @patch("machine_dialect.cfg.generate_with_ai.generate_code")
    def test_main_with_overrides(self, mock_generate: Mock) -> None:
        """Test main with API key and model overrides."""
        mock_generate.return_value = "Generated code"

        result = main()

        assert result == 0
        mock_generate.assert_called_once_with(
            task="test task",
            api_key="my-key",
            model="gpt-4",
            temperature=0.7,
            max_tokens=500,
            validate=True,
        )

    @patch("sys.argv", ["prog", "test task", "--temperature", "0.3", "--max-tokens", "1000"])
    @patch("machine_dialect.cfg.generate_with_ai.generate_code")
    def test_main_with_generation_params(self, mock_generate: Mock) -> None:
        """Test main with temperature and max-tokens parameters."""
        mock_generate.return_value = "Generated code"

        result = main()

        assert result == 0
        mock_generate.assert_called_once_with(
            task="test task",
            api_key=None,
            model=None,
            temperature=0.3,
            max_tokens=1000,
            validate=True,
        )

    @patch("sys.argv", ["prog", "test task", "--no-validate"])
    @patch("machine_dialect.cfg.generate_with_ai.generate_code")
    def test_main_without_validation(self, mock_generate: Mock) -> None:
        """Test main with --no-validate flag."""
        mock_generate.return_value = "Generated code"

        result = main()

        assert result == 0
        mock_generate.assert_called_once_with(
            task="test task",
            api_key=None,
            model=None,
            temperature=0.7,
            max_tokens=500,
            validate=False,
        )

    @patch("sys.argv", ["prog", "test task", "--save", "output.md"])
    @patch("machine_dialect.cfg.generate_with_ai.generate_code")
    @patch("builtins.open", new_callable=mock_open)
    @patch("builtins.print")
    def test_main_with_save_file(self, mock_print: Mock, mock_file: Mock, mock_generate: Mock) -> None:
        """Test main with --save option to write to file."""
        mock_generate.return_value = "Generated code content"

        result = main()

        assert result == 0
        mock_generate.assert_called_once()

        # Verify file was written
        mock_file.assert_called_once_with("output.md", "w")
        mock_file().write.assert_called_once_with("Generated code content")

        # Verify success message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Code saved to: output.md" in str(call) for call in print_calls)

    @patch("sys.argv", ["prog", "test task"])
    @patch("machine_dialect.cfg.generate_with_ai.generate_code")
    @patch("builtins.print")
    def test_main_with_exception(self, mock_print: Mock, mock_generate: Mock) -> None:
        """Test main when generate_code raises an exception."""
        mock_generate.side_effect = ValueError("API key not configured")

        result = main()

        assert result == 1
        mock_generate.assert_called_once()

        # Verify error message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Error: API key not configured" in str(call) for call in print_calls)

    @patch("sys.argv", ["prog", "complex task", "--save", "/invalid/path/file.md"])
    @patch("machine_dialect.cfg.generate_with_ai.generate_code")
    @patch("builtins.open", side_effect=OSError("Permission denied"))
    @patch("builtins.print")
    def test_main_with_save_error(self, mock_print: Mock, mock_file: Mock, mock_generate: Mock) -> None:
        """Test main when saving to file fails."""
        mock_generate.return_value = "Generated code"

        result = main()

        assert result == 1
        mock_generate.assert_called_once()

        # Verify error message was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Error: Permission denied" in str(call) for call in print_calls)

    def test_main_as_script(self) -> None:
        """Test that main can be called as a script."""
        with patch("sys.argv", ["prog", "test"]):
            with patch("machine_dialect.cfg.generate_with_ai.generate_code") as mock_gen:
                mock_gen.return_value = "code"
                # Import and run the module as __main__
                import machine_dialect.cfg.generate_with_ai as module

                # Simulate running as script
                with patch.object(module, "__name__", "__main__"):
                    # This would normally trigger the if __name__ == "__main__" block
                    # but we'll call main directly for testing
                    exit_code = module.main()
                    assert exit_code == 0
