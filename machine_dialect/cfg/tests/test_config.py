"""Tests for the configuration module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from machine_dialect.cfg.config import AIAPIConfig, ConfigLoader, get_ai_config


class TestAIAPIConfig:
    """Test AIAPIConfig dataclass."""

    def test_is_valid_with_both_fields(self) -> None:
        """Test is_valid returns True when both fields are set."""
        config = AIAPIConfig(model="gpt-4o", key="test-key")
        assert config.is_valid() is True

    def test_is_valid_with_missing_model(self) -> None:
        """Test is_valid returns False when model is missing."""
        config = AIAPIConfig(key="test-key")
        assert config.is_valid() is False

    def test_is_valid_with_missing_key(self) -> None:
        """Test is_valid returns False when key is missing."""
        config = AIAPIConfig(model="gpt-4o")
        assert config.is_valid() is False

    def test_is_valid_with_both_missing(self) -> None:
        """Test is_valid returns False when both fields are missing."""
        config = AIAPIConfig()
        assert config.is_valid() is False


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_load_from_config_file(self) -> None:
        """Test loading configuration from .mdconfig file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".mdconfig"
            config_file.write_text(
                """[ai-api]
model = gpt-4o-mini
key = test-api-key-123
"""
            )

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                loader = ConfigLoader()
                config = loader.load()

                assert config.model == "gpt-4o-mini"
                assert config.key == "test-api-key-123"

    def test_load_from_environment_variables(self) -> None:
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {"MD_AI_API_MODEL": "gpt-4-turbo", "MD_AI_API_KEY": "env-key-456"}):
            with patch.object(Path, "exists", return_value=False):
                loader = ConfigLoader()
                config = loader.load()

                assert config.model == "gpt-4-turbo"
                assert config.key == "env-key-456"

    def test_environment_overrides_file_partially(self) -> None:
        """Test that environment variables can override file config partially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".mdconfig"
            config_file.write_text(
                """[ai-api]
model = gpt-3.5-turbo
key = file-key
"""
            )

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                with patch.dict(os.environ, {"MD_AI_API_MODEL": "gpt-4o"}):
                    loader = ConfigLoader()
                    config = loader.load()

                    # Model from env, key from file
                    assert config.model == "gpt-4o"
                    assert config.key == "file-key"

    def test_legacy_openai_key_fallback(self) -> None:
        """Test fallback to OPENAI_API_KEY for backward compatibility."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "legacy-key-789"}):
            with patch.object(Path, "exists", return_value=False):
                loader = ConfigLoader()
                config = loader.load()

                assert config.key == "legacy-key-789"
                assert config.model is None  # No model specified

    def test_md_key_overrides_openai_key(self) -> None:
        """Test that MD_AI_API_KEY takes precedence over OPENAI_API_KEY."""
        with patch.dict(os.environ, {"MD_AI_API_KEY": "new-key", "OPENAI_API_KEY": "old-key"}):
            with patch.object(Path, "exists", return_value=False):
                loader = ConfigLoader()
                config = loader.load()

                assert config.key == "new-key"

    def test_missing_config_section(self) -> None:
        """Test handling of missing [ai-api] section in config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".mdconfig"
            config_file.write_text(
                """[other-section]
some = value
"""
            )

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                loader = ConfigLoader()
                config = loader.load()

                assert config.model is None
                assert config.key is None

    def test_empty_config_file(self) -> None:
        """Test handling of empty config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".mdconfig"
            config_file.write_text("")

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                loader = ConfigLoader()
                config = loader.load()

                assert config.model is None
                assert config.key is None

    def test_get_error_message(self) -> None:
        """Test error message generation."""
        loader = ConfigLoader()
        error_msg = loader.get_error_message()

        assert "AI API configuration not found" in error_msg
        assert ".mdconfig" in error_msg
        assert "MD_AI_API_MODEL" in error_msg
        assert "MD_AI_API_KEY" in error_msg
        assert "OPENAI_API_KEY" in error_msg

    def test_config_caching(self) -> None:
        """Test that configuration is cached after first load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".mdconfig"
            config_file.write_text(
                """[ai-api]
model = gpt-4o
key = test-key
"""
            )

            with patch.object(Path, "home", return_value=Path(tmpdir)):
                loader = ConfigLoader()
                config1 = loader.load()

                # Modify the file
                config_file.write_text(
                    """[ai-api]
model = different-model
key = different-key
"""
                )

                # Should still get cached config
                config2 = loader.load()

                assert config1.model == config2.model
                assert config1.key == config2.key
                assert config2.model == "gpt-4o"


class TestGetAIConfig:
    """Test the convenience function get_ai_config."""

    def test_get_ai_config(self) -> None:
        """Test that get_ai_config returns a valid config."""
        with patch.dict(os.environ, {"MD_AI_API_MODEL": "test-model", "MD_AI_API_KEY": "test-key"}):
            with patch.object(Path, "exists", return_value=False):
                config = get_ai_config()

                assert isinstance(config, AIAPIConfig)
                assert config.model == "test-model"
                assert config.key == "test-key"
