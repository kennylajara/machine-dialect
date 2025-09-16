"""Grammar-based generation module for Machine Dialect™ using GPT-5's CFG support."""

from pathlib import Path
from typing import Any


def generate_with_openai(
    client: Any,  # OpenAI client
    model: str,
    task_description: str,
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> tuple[str, dict[str, Any]]:
    """Generate Machine Dialect™ code using GPT-5's context-free grammar constraints.

    This function uses GPT-5's custom tools with CFG to ensure syntactically correct
    Machine Dialect™ code generation. The model is constrained to only produce
    strings that match the Machine Dialect™ grammar.

    Args:
        client: OpenAI client instance.
        model: Model name (must support CFG, e.g., 'gpt-5').
        task_description: What the code should do.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature (0-2).

    Returns:
        Tuple of (generated_code, token_info) where:
        - generated_code: Machine Dialect™ code that is syntactically valid.
        - token_info: Dictionary with prompt_tokens, completion_tokens, total_tokens.

    Raises:
        ValueError: If the model doesn't support CFG or response is invalid.
    """
    # Check if model supports CFG (currently only GPT-5 family)
    if "gpt-5" not in model.lower():
        raise ValueError(
            f"Model '{model}' does not support context-free grammar constraints. "
            "Please use a GPT-5 model (gpt-5, gpt-5-mini, or gpt-5-nano)."
        )

    # Create the CFG definition for Machine Dialect™
    machine_dialect_cfg = _get_machine_dialect_cfg()

    # Create the API request using GPT-5's custom tools with CFG
    # Note: GPT-5 doesn't support temperature parameter (always uses 1.0)
    import time

    api_start = time.time()

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "developer",
                    "content": (
                        "You are a Machine Dialect™ code generator. Generate code that performs the "
                        "requested task using the Machine Dialect™ language. The output must conform "
                        "to the provided context-free grammar.\n"
                        "IMPORTANT:\n"
                        "- Write in English even if the instruction is in another language.\n"
                        "- Always define variables before trying to use them.\n"
                        "- When creating utilities, define proper Inputs (parameters the utility accepts) "
                        "and Outputs (values it returns) sections.\n"
                        "- Don't hardcode values that should be parameters - use the Inputs section instead."
                    ),
                },
                {"role": "user", "content": f"Generate Machine Dialect™ code for: {task_description}"},
            ],
            tools=[
                {
                    "type": "custom",
                    "name": "machine_dialect_generator",
                    "description": "Generates syntactically valid Machine Dialect™ code",
                    "format": machine_dialect_cfg,
                }
            ],
            parallel_tool_calls=False,
            timeout=30.0,  # 30 second timeout
            # temperature parameter removed - GPT-5 doesn't support it
        )

        api_time = time.time() - api_start
        if api_time > 5.0:  # Log if it takes more than 5 seconds
            print(f"   ⚠️ API call took {api_time:.2f}s")

    except Exception as e:
        api_time = time.time() - api_start
        raise ValueError(f"API call failed after {api_time:.2f}s: {e!s}") from e

    # Extract the generated code from the response
    # The response should have an output_text attribute directly
    if hasattr(response, "output_text"):
        generated_code = response.output_text
    elif hasattr(response, "output"):
        # Fallback to output attribute if output_text doesn't exist
        if isinstance(response.output, list) and len(response.output) > 1:
            # Try to get the second output (tool output)
            tool_output = response.output[1]

            # Check various attributes on the tool output
            if hasattr(tool_output, "text"):
                generated_code = tool_output.text
            elif hasattr(tool_output, "input"):
                generated_code = tool_output.input
            elif hasattr(tool_output, "tool_input"):
                generated_code = tool_output.tool_input
            elif hasattr(tool_output, "content"):
                generated_code = tool_output.content
            else:
                generated_code = str(tool_output)
        elif isinstance(response.output, str):
            generated_code = response.output
        else:
            generated_code = str(response.output)
    else:
        # Last resort: try to extract from string representation
        response_str = str(response)
        if "output_text=" in response_str:
            import re

            match = re.search(r"output_text='([^']*)'", response_str)
            if not match:
                match = re.search(r'output_text="([^"]*)"', response_str)
            if match:
                generated_code = match.group(1)
            else:
                raise ValueError(f"Could not extract code from response: {response_str[:200]}...")
        else:
            raise ValueError(f"Response has no output_text or output attribute: {dir(response)}")

    if not generated_code or generated_code == "None":
        # Provide more helpful error message
        error_msg = "Failed to extract valid code from GPT-5 response.\n"
        error_msg += f"Response type: {type(response).__name__}\n"
        error_msg += f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')][:10]}\n"
        if hasattr(response, "output"):
            error_msg += f"Output type: {type(response.output).__name__}\n"
        error_msg += f"Extracted value: {repr(generated_code[:100]) if generated_code else 'None'}"
        raise ValueError(error_msg)

    # Extract token usage if available
    token_info = {}
    if hasattr(response, "usage"):
        usage = response.usage
        if usage:
            token_info["prompt_tokens"] = getattr(usage, "prompt_tokens", None)
            token_info["completion_tokens"] = getattr(usage, "completion_tokens", None)
            token_info["total_tokens"] = getattr(usage, "total_tokens", None)

            # If individual counts are not available but total is, try to estimate
            if token_info["total_tokens"] and not token_info["prompt_tokens"]:
                # Can't accurately split, just show total
                token_info["prompt_tokens"] = None
                token_info["completion_tokens"] = None

    # Return both code and token info as a tuple
    return (str(generated_code), token_info)


# Cache the grammar to avoid re-reading the file
_cached_grammar: dict[str, Any] | None = None


def _get_machine_dialect_cfg() -> dict[str, Any]:
    """Get the Machine Dialect™ context-free grammar in GPT-5 format.

    Returns:
        Dictionary containing the CFG definition for GPT-5's custom tools.
    """
    global _cached_grammar

    if _cached_grammar is None:
        # Read the Machine Dialect™ Lark grammar file for GPT-5
        grammar_path = Path(__file__).parent / "machine_dialect.lark"

        with open(grammar_path) as f:
            lark_grammar = f.read()

        _cached_grammar = {
            "type": "grammar",
            "syntax": "lark",  # Using Lark syntax as required by GPT-5
            "definition": lark_grammar,
        }

    return _cached_grammar


def validate_model_support(model: str) -> bool:
    """Check if a model supports context-free grammar constraints.

    Args:
        model: The model name to check.

    Returns:
        True if the model supports CFG, False otherwise.
    """
    supported_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    return any(supported in model.lower() for supported in supported_models)
