"""End-to-end test for Fibonacci utility execution."""

from pathlib import Path
from typing import Any

import pytest

from machine_dialect.compiler.config import CompilerConfig, OptimizationLevel
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.pipeline import CompilationPipeline
from machine_dialect.mir.mir_interpreter import MIRInterpreter

FIBONACCI_SOURCE = """---
title: Fibonacci Test
type: program
---

### **Utility**: `Fibonacci`

<details>
<summary>Calculate the nth Fibonacci number recursively</summary>

> If `n` is less than or equal to _1_:
> > Give back `n`.
> Else:
> > Define `n_minus_1` as Whole Number. \\
> > Set `n_minus_1` to `n` - _1_. \\
> > Define `n_minus_2` as Whole Number. \\
> > Set `n_minus_2` to `n` - _2_. \\
> > Define `fib_1` as Whole Number. \\
> > Set `fib_1` using `Fibonacci` with `n_minus_1`. \\
> > Define `fib_2` as Whole Number. \\
> > Set `fib_2` using `Fibonacci` with `n_minus_2`. \\
> > Define `result` as Whole Number. \\
> > Set `result` to `fib_1` + `fib_2`. \\
> > Give back `result`.

</details>

#### Inputs:

- `n` **as** Whole Number (required)

#### Outputs:

- `result`

Define `m` as Whole Number.
Set `m` to _10_.

Define `final result` as Whole Number.
Set `final result` using `Fibonacci` with `m`.

Say _"Fibonacci of 10 is:"_.
Say `final result`.
"""


class TestFibonacciE2E:
    """End-to-end tests for Fibonacci utility."""

    @pytest.mark.parametrize(
        "optimization_level",
        [
            OptimizationLevel.NONE,
            OptimizationLevel.BASIC,
            OptimizationLevel.STANDARD,
            OptimizationLevel.AGGRESSIVE,
        ],
    )
    def test_fibonacci_compiles_all_levels(self, optimization_level: OptimizationLevel) -> None:
        """Test that Fibonacci compiles at all optimization levels.

        Args:
            optimization_level: The optimization level to test.
        """
        # Create compiler config with specified optimization level
        config = CompilerConfig(optimization_level=optimization_level)
        pipeline = CompilationPipeline(config=config)

        # Create compilation context
        source_path = Path("test_fibonacci.md")
        context = CompilationContext(source_path=source_path, config=config)
        context.source_content = FIBONACCI_SOURCE

        # Compile
        result = pipeline.compile(context)

        # Verify compilation succeeded
        assert not result.has_errors(), f"Compilation failed at {optimization_level}: {result.errors}"
        assert result.mir_module is not None, f"No MIR generated at {optimization_level}"
        assert result.bytecode_module is not None, f"No bytecode generated at {optimization_level}"

    def test_fibonacci_mir_interpreter_execution(self, capsys: Any) -> None:
        """Test that Fibonacci executes correctly with MIR interpreter.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr.
        """
        # Create compiler config with standard optimization
        config = CompilerConfig(optimization_level=OptimizationLevel.STANDARD)
        pipeline = CompilationPipeline(config=config)

        # Create compilation context
        source_path = Path("test_fibonacci.md")
        context = CompilationContext(source_path=source_path, config=config)
        context.source_content = FIBONACCI_SOURCE

        # Compile
        result = pipeline.compile(context)

        assert not result.has_errors(), f"Compilation failed: {result.errors}"
        assert result.mir_module is not None, "No MIR generated"

        # Execute with MIR interpreter
        interpreter = MIRInterpreter()
        interpreter.interpret_module(result.mir_module)

        # Get output from interpreter
        output_lines = interpreter.get_output()

        # Verify output contains expected strings
        assert len(output_lines) >= 2, f"Expected at least 2 lines of output, got: {output_lines}"
        assert output_lines[0] == "Fibonacci of 10 is:", (
            f"First line should be 'Fibonacci of 10 is:', got: {output_lines[0]}"
        )
        assert output_lines[1] == "55", f"Second line should be '55', got: {output_lines[1]}"

    def test_fibonacci_all_levels_produce_same_result(self, capsys: Any) -> None:
        """Test that all optimization levels produce the same result.

        Args:
            capsys: Pytest fixture for capturing stdout/stderr.
        """
        expected_output = ["Fibonacci of 10 is:", "55"]

        for level in OptimizationLevel:
            # Clear any previous output
            capsys.readouterr()

            # Create compiler config with this optimization level
            config = CompilerConfig(optimization_level=level)
            pipeline = CompilationPipeline(config=config)

            # Create compilation context
            source_path = Path("test_fibonacci.md")
            context = CompilationContext(source_path=source_path, config=config)
            context.source_content = FIBONACCI_SOURCE

            # Compile
            result = pipeline.compile(context)

            assert not result.has_errors(), f"Compilation failed at {level}: {result.errors}"
            assert result.mir_module is not None, f"No MIR generated at {level}"

            # Execute with MIR interpreter
            interpreter = MIRInterpreter()
            interpreter.interpret_module(result.mir_module)

            # Get output from interpreter
            output_lines = interpreter.get_output()

            assert output_lines == expected_output, (
                f"Output mismatch at {level}. Expected {expected_output}, got {output_lines}"
            )
