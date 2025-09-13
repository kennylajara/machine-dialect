"""Grammar-based generation module for Machine Dialect™ using GPT-5's CFG support."""

from pathlib import Path
from typing import Any


def generate_with_openai(
    client: Any,  # OpenAI client
    model: str,
    task_description: str,
    max_tokens: int = 500,
    temperature: float = 0.7,
) -> str:
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
        Generated Machine Dialect™ code that is guaranteed to be syntactically valid.

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
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "developer",
                "content": (
                    "You are a Machine Dialect™ code generator. Generate code that performs the "
                    "requested task using the Machine Dialect™ language. The output must conform "
                    "to the provided context-free grammar."
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
        # temperature parameter removed - GPT-5 doesn't support it
    )

    # Extract the generated code from the response
    if not response.output or len(response.output) < 2:
        raise ValueError("No valid output from the model")

    # The generated code is in the second output (first is text, second is tool output)
    generated_code = response.output[1].input

    if not generated_code:
        raise ValueError("Empty code generated")

    return str(generated_code)


def _get_machine_dialect_cfg() -> dict[str, Any]:
    """Get the Machine Dialect™ context-free grammar in GPT-5 format.

    Returns:
        Dictionary containing the CFG definition for GPT-5's custom tools.
    """
    # Read the Machine Dialect™ Lark grammar file for GPT-5
    grammar_path = Path(__file__).parent / "machine_dialect.lark"

    with open(grammar_path) as f:
        lark_grammar = f.read()

    return {
        "type": "grammar",
        "syntax": "lark",  # Using Lark syntax as required by GPT-5
        "definition": lark_grammar,
    }


def validate_model_support(model: str) -> bool:
    """Check if a model supports context-free grammar constraints.

    Args:
        model: The model name to check.

    Returns:
        True if the model supports CFG, False otherwise.
    """
    supported_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    return any(supported in model.lower() for supported in supported_models)
