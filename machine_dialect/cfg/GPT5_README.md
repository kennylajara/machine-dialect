# Using GPT-5 with Machine Dialect CFG

Now that GPT-5 is released with Context Free Grammar support, you can generate syntactically
perfect Machine Dialect code!

## Quick Start

### 1. Install OpenAI SDK

```bash
pip install openai
# or
uv pip install openai
```

### 2. Set your API key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Generate Machine Dialect Code

```python
from openai import OpenAI
from machine_dialect.cfg.gpt5_integration import GPT5CFGGenerator

# Initialize
client = OpenAI()
generator = GPT5CFGGenerator()

# Generate code for a task
code = generator.generate_with_openai(
    client=client,
    task_description="Calculate the sum of two numbers",
    temperature=0.3,
    max_tokens=200
)

print(code)
# Output:
# Set `first_number` to 10.
# Set `second_number` to 20.  
# Set `sum` to first_number + second_number.
# Say sum.
```

## Complete Example

Run the full example:

```bash
python use_gpt5_cfg.py
```

This will:

- Generate code for multiple tasks
- Validate all generated code
- Show that CFG ensures 100% syntactic correctness

## Command Line Usage

```bash
# Generate code for a specific task
python -m machine_dialect.cfg.generate_with_gpt5 "Calculate the area of a circle with radius 5"

# With options
python -m machine_dialect.cfg.generate_with_gpt5 \
    "Find the maximum of three numbers" \
    --temperature 0.2 \
    --max-tokens 300 \
    --save output.md
```

## How CFG Works with GPT-5

The Context Free Grammar constrains GPT-5's token generation:

1. **Grammar Rules**: Define exact syntax patterns
1. **Token Constraints**: At each step, only valid tokens can be generated
1. **Guaranteed Validity**: Output MUST follow the grammar

Example grammar rule:

```ebnf
set_statement ::= "Set" ws "`" identifier "`" ws "to" ws expression "."
```

This ensures GPT-5 can only generate:

- `Set` keyword (case variations allowed)
- Backticks around identifier
- `to` keyword
- Valid expression
- Period at the end

## API Request Structure

The module creates requests like:

```python
{
    "model": "gpt-5",
    "messages": [...],
    "response_format": {
        "type": "cfg",
        "cfg": {
            "grammar": "program ::= statement | statement program ..."
        }
    }
}
```

## Supported Machine Dialect Features

The CFG covers:

- ✅ Variable assignment (`Set`)
- ✅ Output (`Say`)
- ✅ Conditionals (`if`/`else`)
- ✅ Math operations (`+`, `-`, `*`, `/`)
- ✅ Logical operations (`and`, `or`, `not`)
- ✅ Comparisons (symbolic and natural language)
- ✅ All literals (integers, floats, strings, booleans, empty)

## Benefits

1. **100% Syntactic Correctness**: No syntax errors possible
1. **Consistent Output**: Same grammar rules every time
1. **No Post-Processing**: Output is ready to use
1. **Type Safety**: Grammar ensures proper types

## Validation

Always validate generated code:

```python
from machine_dialect.cfg import CFGParser

parser = CFGParser()
is_valid = parser.validate(generated_code)
```

## Temperature Settings

- `0.0 - 0.3`: Deterministic, best for examples
- `0.4 - 0.7`: Balanced creativity
- `0.8 - 1.0`: More creative solutions

## Limitations

- Grammar is simplified (no Actions/Interactions)
- Identifiers with spaces work in backticks
- Some natural language operators need exact phrasing

## Troubleshooting

If generation fails:

1. Check API key is set
1. Verify GPT-5 access in your OpenAI account
1. Try lower temperature for more predictable output
1. Check grammar file for any syntax issues

## Next Steps

1. Extend grammar for more features
1. Add semantic validation
1. Create domain-specific variations
1. Build IDE integration with real-time generation
