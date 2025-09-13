"""Configuration module for Machine Dialect™ AI API settings."""

import configparser
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AIAPIConfig:
    """Configuration for AI API settings.

    Attributes:
        model: The AI model to use (e.g., 'gpt-5', 'gpt-5-mini').
        key: The API key for authentication.
    """

    model: str | None = None
    key: str | None = None

    def is_valid(self) -> bool:
        """Check if the configuration has all required fields.

        Returns:
            True if both model and key are set, False otherwise.
        """
        return self.model is not None and self.key is not None

    def with_defaults(self) -> "AIAPIConfig":
        """Return a config with default values filled in.

        Returns:
            Config with defaults applied where values are missing.
        """
        if self.model is None:
            self.model = "gpt-5"  # Default to GPT-5 for CFG support
        return self


class ConfigLoader:
    """Loader for Machine Dialect™ configuration."""

    CONFIG_FILE_NAME = ".mdconfig"
    ENV_MODEL_KEY = "MD_AI_API_MODEL"
    ENV_API_KEY = "MD_AI_API_KEY"

    def __init__(self) -> None:
        """Initialize the configuration loader."""
        self._config: AIAPIConfig | None = None

    def load(self) -> AIAPIConfig:
        """Load AI API configuration from file or environment.

        Priority order:
        1. .mdconfig file in user's home directory
        2. Environment variables (MD_AI_API_MODEL and MD_AI_API_KEY)
        3. Legacy environment variable (OPENAI_API_KEY) for backward compatibility

        Returns:
            AIAPIConfig object with loaded settings.
        """
        if self._config is not None:
            return self._config

        config = AIAPIConfig()

        # Try to load from .mdconfig file
        config_file_path = Path.home() / self.CONFIG_FILE_NAME
        if config_file_path.exists():
            config = self._load_from_file(config_file_path)

        # Override or fill in with environment variables
        env_model = os.getenv(self.ENV_MODEL_KEY)
        if env_model:
            config.model = env_model

        env_key = os.getenv(self.ENV_API_KEY)
        if env_key:
            config.key = env_key
        elif not config.key:
            # Fallback to legacy OPENAI_API_KEY for backward compatibility
            config.key = os.getenv("OPENAI_API_KEY")

        self._config = config
        return config

    def _load_from_file(self, config_file_path: Path) -> AIAPIConfig:
        """Load configuration from a .mdconfig file.

        Args:
            config_file_path: Path to the configuration file.

        Returns:
            AIAPIConfig object with settings from the file.
        """
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file_path)

        ai_config = AIAPIConfig()

        try:
            ai_section = config_parser["ai-api"]
            ai_config.model = ai_section.get("model")
            ai_config.key = ai_section.get("key")
        except (configparser.NoSectionError, KeyError):
            # Section doesn't exist, return empty config
            pass

        return ai_config

    def get_error_message(self) -> str:
        """Get a helpful error message for missing configuration.

        Returns:
            Error message with instructions for setting up configuration.
        """
        home_dir = Path.home()
        config_path = home_dir / self.CONFIG_FILE_NAME

        return f"""AI API configuration not found.

Please configure the AI API in one of the following ways:

1. Create a {self.CONFIG_FILE_NAME} file in your home directory ({config_path}):

   [ai-api]
   model = gpt-5
   key = your_api_key_here

   Note: Only GPT-5 models (gpt-5, gpt-5-mini, gpt-5-nano) support
   context-free grammar constraints required for Machine Dialect™ generation.

2. Set environment variables:

   export {self.ENV_MODEL_KEY}=gpt-5
   export {self.ENV_API_KEY}=your_api_key_here

3. For backward compatibility, you can also use:

   export OPENAI_API_KEY=your_api_key_here
   (Note: Model will default to gpt-5 if not specified)

To get an API key: https://platform.openai.com/api-keys"""


def get_ai_config() -> AIAPIConfig:
    """Get the AI API configuration.

    This is a convenience function that creates a ConfigLoader
    and loads the configuration.

    Returns:
        AIAPIConfig object with current settings.
    """
    loader = ConfigLoader()
    return loader.load()
