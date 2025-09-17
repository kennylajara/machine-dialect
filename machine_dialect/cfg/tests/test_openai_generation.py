"""Tests for the grammar-based OpenAI generation module."""

from unittest.mock import MagicMock

import pytest

from machine_dialect.cfg.openai_generation import _get_machine_dialect_cfg, generate_with_openai, validate_model_support


class TestGenerateWithOpenAI:
    """Test the grammar-based generate_with_openai function."""

    def test_gpt5_cfg_generation(self) -> None:
        """Test generation with GPT-5 using context-free grammar."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()

        # Set up the response to have output_text directly (primary path)
        mock_response.output_text = "Set x to _10_.\nGive back x."
        # Also set up output as fallback
        mock_output = MagicMock()
        mock_output.input = "Set x to _10_.\nGive back x."
        mock_response.output = [MagicMock(), mock_output]  # First is text, second is tool output

        mock_client.responses.create.return_value = mock_response

        result = generate_with_openai(
            client=mock_client,
            model="gpt-5",
            task_description="set x to 10 and display it",
            max_tokens=200,
            temperature=0.7,
        )

        # Result should be a tuple of (code, token_info)
        assert isinstance(result, tuple)
        assert len(result) == 2
        code, token_info = result
        assert code == "Set x to _10_.\nGive back x."
        assert isinstance(token_info, dict)

        # Verify API call structure
        call_args = mock_client.responses.create.call_args
        assert call_args.kwargs["model"] == "gpt-5"
        # Note: GPT-5 doesn't support max_completion_tokens or temperature
        assert "max_completion_tokens" not in call_args.kwargs
        assert "temperature" not in call_args.kwargs
        assert call_args.kwargs["parallel_tool_calls"] is False

        # Check that custom tool with CFG was provided
        tools = call_args.kwargs["tools"]
        assert len(tools) == 1
        assert tools[0]["type"] == "custom"
        assert tools[0]["name"] == "machine_dialect_generator"
        assert "format" in tools[0]

        # Check CFG format - now using Lark syntax
        cfg = tools[0]["format"]
        assert cfg["type"] == "grammar"
        assert cfg["syntax"] == "lark"
        assert "definition" in cfg
        # The definition is now a Lark grammar string
        assert isinstance(cfg["definition"], str)
        assert "start:" in cfg["definition"]
        assert "statement:" in cfg["definition"]

    def test_non_gpt5_model_raises_error(self) -> None:
        """Test that non-GPT-5 models raise an error."""
        mock_client = MagicMock()

        with pytest.raises(ValueError, match="does not support context-free grammar"):
            generate_with_openai(client=mock_client, model="gpt-4o", task_description="test task", max_tokens=100)

        # Should not have made any API calls
        mock_client.responses.create.assert_not_called()

    def test_gpt5_mini_supported(self) -> None:
        """Test that gpt-5-mini is recognized as supporting CFG."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Set up the response to have output_text directly
        mock_response.output_text = 'Give back _"Hello"_.'
        # Also set up output as fallback
        mock_output = MagicMock()
        mock_output.input = 'Give back _"Hello"_.'
        mock_response.output = [MagicMock(), mock_output]
        mock_client.responses.create.return_value = mock_response

        result = generate_with_openai(
            client=mock_client, model="gpt-5-mini", task_description="say hello", max_tokens=50
        )

        # Result should be a tuple of (code, token_info)
        assert isinstance(result, tuple)
        assert len(result) == 2
        code, token_info = result
        assert code == 'Give back _"Hello"_.'
        assert isinstance(token_info, dict)
        assert mock_client.responses.create.called

    def test_empty_response_raises_error(self) -> None:
        """Test that empty response raises ValueError."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Make response have no valid attributes
        mock_response.output_text = None
        mock_response.output = []  # Empty output
        mock_client.responses.create.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to extract valid code"):
            generate_with_openai(client=mock_client, model="gpt-5", task_description="test task", max_tokens=100)

    def test_empty_code_raises_error(self) -> None:
        """Test that empty generated code raises ValueError."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Set up response to have empty code
        mock_response.output_text = ""  # Empty code
        del mock_response.output  # Remove output attribute
        mock_client.responses.create.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to extract valid code"):
            generate_with_openai(client=mock_client, model="gpt-5", task_description="test task", max_tokens=100)

    def test_input_messages_structure(self) -> None:
        """Test that input messages are structured correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        # Set up the response to have output_text directly
        mock_response.output_text = "test"
        # Also set up output as fallback
        mock_output = MagicMock()
        mock_output.input = "test"
        mock_response.output = [MagicMock(), mock_output]
        mock_client.responses.create.return_value = mock_response

        result = generate_with_openai(
            client=mock_client, model="gpt-5-nano", task_description="test task", max_tokens=50
        )
        assert isinstance(result, tuple)  # Verify it returns a tuple

        # Get the input messages passed to the API
        call_args = mock_client.responses.create.call_args
        messages = call_args.kwargs["input"]

        assert len(messages) == 2

        # Developer message
        assert messages[0]["role"] == "developer"
        assert "Machine Dialect™ code generator" in messages[0]["content"]
        assert "context-free grammar" in messages[0]["content"]

        # User message
        assert messages[1]["role"] == "user"
        assert "test task" in messages[1]["content"]


class TestValidateModelSupport:
    """Test the validate_model_support function."""

    def test_gpt5_models_supported(self) -> None:
        """Test that GPT-5 models are recognized as supported."""
        assert validate_model_support("gpt-5") is True
        assert validate_model_support("GPT-5") is True
        assert validate_model_support("gpt-5-mini") is True
        assert validate_model_support("GPT-5-MINI") is True
        assert validate_model_support("gpt-5-nano") is True
        assert validate_model_support("gpt-5-Nano") is True

    def test_non_gpt5_models_not_supported(self) -> None:
        """Test that non-GPT-5 models are not supported."""
        assert validate_model_support("gpt-4") is False
        assert validate_model_support("gpt-4o") is False
        assert validate_model_support("gpt-3.5-turbo") is False
        assert validate_model_support("claude-3") is False
        assert validate_model_support("gemini-pro") is False

    def test_partial_matches(self) -> None:
        """Test models with GPT-5 in the name are supported."""
        assert validate_model_support("gpt-5-2025-08-07") is True
        assert validate_model_support("gpt-5-mini-latest") is True
        assert validate_model_support("custom-gpt-5-model") is True


class TestMachineDialectCFG:
    """Test the Machine Dialect™ CFG structure."""

    def test_cfg_structure(self) -> None:
        """Test that the CFG has the correct structure."""
        cfg = _get_machine_dialect_cfg()

        # Check top-level structure
        assert cfg["type"] == "grammar"
        assert cfg["syntax"] == "lark"  # Now using Lark syntax
        assert "definition" in cfg

        # The definition is now a Lark grammar string
        definition = cfg["definition"]
        assert isinstance(definition, str)

        # Check that key rules exist in the Lark grammar
        assert "start:" in definition or "program:" in definition
        assert "statement:" in definition
        assert "set_stmt:" in definition
        assert "give_back_stmt:" in definition
        assert "if_stmt:" in definition
        assert "expression:" in definition

        # Check that terminals are defined (using new literal patterns)
        assert "LITERAL_" in definition or "IDENT" in definition
        assert "IDENTIFIER" in definition

    def test_lark_grammar_content(self) -> None:
        """Test that the Lark grammar has expected content."""
        cfg = _get_machine_dialect_cfg()
        grammar = cfg["definition"]

        # Check for statement rules
        assert "program:" in grammar or "start:" in grammar
        assert "statement:" in grammar
        assert "set_stmt" in grammar
        assert "give_back_stmt" in grammar

        # Check for set and give back statements
        assert 'set_stmt: "Set"i identifier "to"i expression' in grammar
        assert 'give_back_stmt: ("Give"i "back"i | "Gives"i "back"i) expression' in grammar

        # Check for expression rules
        assert "expression:" in grammar or "expr:" in grammar
        assert "or" in grammar.lower()
        assert "and" in grammar.lower()

        # Check for comparison operators
        assert '"<"' in grammar
        assert '">"' in grammar
        assert '"equals"i' in grammar or "equals" in grammar.lower()

        # Check for arithmetic operators
        assert '"+"' in grammar
        assert '"-"' in grammar
        assert '"*"' in grammar
        assert '"/"' in grammar

    def test_grammar_terminals(self) -> None:
        """Test that terminals are properly defined in Lark grammar."""
        cfg = _get_machine_dialect_cfg()
        grammar = cfg["definition"]

        # Check terminal definitions (new pattern with literals)
        assert "IDENTIFIER" in grammar or "IDENT" in grammar
        assert "LITERAL_" in grammar  # Check for literal patterns

        # Check whitespace handling
        assert "%import common.WS" in grammar
        assert "%ignore WS" in grammar
