"""Context Free Grammar module for Machine Dialect™ with GPT-5 integration."""

from .openai_generation import generate_with_openai, validate_model_support
from .parser import CFGParser

__all__ = ["CFGParser", "generate_with_openai", "validate_model_support"]
