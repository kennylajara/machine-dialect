"""AI Agent for iterative Machine Dialect™ code generation and execution."""

import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from machine_dialect.cfg.openai_generation import generate_with_openai
from machine_dialect.compiler import Compiler, CompilerConfig
from machine_dialect.compiler.config import OptimizationLevel


@dataclass
class AgentResult:
    """Result from agent execution.

    Attributes:
        success: Whether the task was successfully completed.
        iterations: Number of iterations taken.
        code: Final code (if successful).
        output: Program output (if any).
        history: Full iteration history.
    """

    success: bool
    iterations: int
    code: str | None = None
    output: str | None = None
    history: list[dict[str, Any]] | None = None


class Agent:
    """Iterative AI agent for Machine Dialect™ code generation."""

    def __init__(self, client: Any, model: str = "gpt-5", verbose: bool = True):
        """Initialize the agent.

        Args:
            client: OpenAI client instance.
            model: Model to use for generation.
            verbose: Whether to print progress.
        """
        self.client = client
        self.model = model
        self.verbose = verbose
        self.iterations: list[dict[str, Any]] = []
        self.total_tokens_used = 0

    def solve(self, task: str, max_iterations: int = 5) -> AgentResult:
        """Solve a task through iterative code generation.

        Args:
            task: The task description.
            max_iterations: Maximum iterations to attempt.

        Returns:
            AgentResult with solution details.
        """
        # Track overall time
        start_time = time.time()

        if self.verbose:
            print(f"🤖 Agent starting: {task}")
            print(f"   Model: {self.model}")
            print(f"   Max iterations: {max_iterations}")

        self.iterations = []
        current_task = task
        successful_code = None
        final_output = None

        for i in range(max_iterations):
            iteration_num = i + 1

            if self.verbose:
                print(f"\n📍 Iteration {iteration_num}/{max_iterations}")

            # Generate code
            try:
                if self.verbose:
                    print("   Generating code...")

                # Time the generation
                gen_start = time.time()
                code, token_info = self._generate(current_task)
                gen_time = time.time() - gen_start

                # Track token usage
                if token_info:
                    total = token_info.get("total_tokens", 0)
                    prompt = token_info.get("prompt_tokens")
                    completion = token_info.get("completion_tokens")

                    if total:
                        self.total_tokens_used += total

                    if self.verbose:
                        print(f"   ✓ Code generated (CFG-constrained) in {gen_time:.2f}s")

                        # Display token info based on what's available
                        if prompt is not None and completion is not None:
                            print(f"   📊 Tokens: {prompt} prompt + {completion} completion = {total} total")
                        elif total:
                            print(f"   📊 Tokens: {total} total")

                        if self.total_tokens_used > 0:
                            print(f"   📈 Cumulative: {self.total_tokens_used:,} tokens")

                        # Debug: show what was generated
                        print(f"   Debug: Generated code: {code!r}")
                else:
                    if self.verbose:
                        print("   ✓ Code generated (CFG-constrained)")
                        print(f"   Debug: Generated code: {code!r}")

            except Exception as e:
                if self.verbose:
                    print(f"   ✗ Generation failed: {e}")

                self.iterations.append(
                    {"iteration": iteration_num, "code": None, "error": str(e), "phase": "generation"}
                )
                continue

            # Compile and execute
            result = self._execute(code)

            # Record iteration
            self.iterations.append({"iteration": iteration_num, "code": code, "result": result})

            # Check result
            if result["success"]:
                if self.verbose:
                    output_msg = result.get("output", "No output")
                    if result.get("instructions"):
                        print(f"   ✅ Success! Output: {output_msg}")
                        print(f"   📊 Executed {result['instructions']} instructions")
                    else:
                        print(f"   ✅ Success! Output: {output_msg}")

                successful_code = code
                final_output = result.get("output")

                # Optional: Try to optimize if we have iterations left
                if iteration_num < max_iterations and self.verbose:
                    if not self._should_optimize(task, code, result):
                        break
                    current_task = f"Optimize this working solution for: {task}\n\nCurrent code:\n{code}"
                else:
                    break

            else:
                # Failed - prepare for next iteration
                error = result.get("error", "Unknown error")
                phase = result.get("phase", "execution")

                if self.verbose:
                    print(f"   ❌ {phase.capitalize()} error: {error}")

                # Build feedback for next iteration
                current_task = self._build_error_feedback(task, code, error, phase)

        # Calculate total time
        total_time = time.time() - start_time

        # Print final summary
        if self.verbose:
            if self.total_tokens_used > 0:
                print(f"\n💰 Total: {self.total_tokens_used:,} tokens in {total_time:.2f}s")
            else:
                print(f"\n⏱️ Total time: {total_time:.2f}s")

        # Return final result
        return AgentResult(
            success=successful_code is not None,
            iterations=len(self.iterations),
            code=successful_code,
            output=final_output,
            history=self.iterations,
        )

    def _generate(self, task: str) -> tuple[str, dict[str, int]]:
        """Generate code using CFG constraints.

        Args:
            task: Task description with any feedback.

        Returns:
            Tuple of (code, token_info) where token_info contains usage stats.
        """
        # Simplify the task description if it's too complex
        simplified_task = self._simplify_task(task)

        # Use the existing CFG generation
        return generate_with_openai(
            self.client,
            self.model,
            simplified_task,
            max_tokens=800,
            temperature=0.7,  # Will be ignored for GPT-5
        )

    def _simplify_task(self, task: str) -> str:
        """Simplify complex task descriptions for better generation.

        Args:
            task: Original task description.

        Returns:
            Simplified task description.
        """
        # Remove overly complex instructions and focus on core functionality
        simplified = task

        # If task is very long, try to extract the essential parts
        if len(task) > 500:
            # Look for key phrases that indicate the main task
            lines = task.split("\n")
            essential_lines = []

            for line in lines:
                # Keep lines that describe the main task or errors
                if any(
                    keyword in line.lower()
                    for keyword in [
                        "generate",
                        "create",
                        "calculate",
                        "implement",
                        "write",
                        "error:",
                        "failed:",
                        "fix",
                        "please",
                    ]
                ):
                    essential_lines.append(line)

            if essential_lines:
                simplified = "\n".join(essential_lines[:10])  # Limit to 10 most relevant lines

        # Add clarification about Machine Dialect™ syntax
        if "error" not in simplified.lower():
            simplified += (
                "\nNote: Use Machine Dialect™ syntax with backticks for variables and underscores for literals."
            )

        return simplified

    def _execute(self, code: str) -> dict[str, Any]:
        """Compile and execute Machine Dialect™ code.

        Args:
            code: The code to execute.

        Returns:
            Execution result dictionary.
        """
        temp_path = None

        try:
            # Compile without optimizations
            config = CompilerConfig(optimization_level=OptimizationLevel.NONE, verbose=False)
            compiler = Compiler(config)

            if self.verbose:
                print("   Compiling...")

            context = compiler.compile_string(code, module_name="agent_task")

            # Check compilation errors
            if context.has_errors():
                error_msg = "Compilation failed"
                if context.errors:
                    error = context.errors[0]
                    # Convert error object to string
                    error_msg = str(error)
                return {"success": False, "phase": "compilation", "error": error_msg}

            if self.verbose and context.bytecode_module:
                bytecode_size = len(context.bytecode_module.serialize())
                print(f"   ✓ Compiled successfully ({bytecode_size} bytes)")

            # Save bytecode to temporary file
            if context.bytecode_module:
                with tempfile.NamedTemporaryFile(suffix=".mdbc", delete=False) as f:
                    bytecode = context.bytecode_module.serialize()
                    f.write(bytecode)
                    temp_path = f.name
            else:
                raise ValueError("Compilation succeeded but no bytecode generated")

            # Execute with Rust VM
            if self.verbose:
                print("   Executing bytecode...")

            import machine_dialect_vm

            vm = machine_dialect_vm.RustVM()
            vm.load_bytecode(temp_path)
            output = vm.execute()

            # Get instruction count
            instructions = vm.instruction_count()

            return {
                "success": True,
                "phase": "runtime",
                "output": str(output) if output is not None else "",
                "instructions": instructions,
                "bytecode_size": len(bytecode),
            }

        except ImportError:
            return {"success": False, "phase": "runtime", "error": "Rust VM not available. Run ./build_vm.sh first."}
        except Exception as e:
            return {"success": False, "phase": "runtime", "error": str(e)}
        finally:
            # Clean up temp file
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    def _build_error_feedback(self, original_task: str, code: str, error: str, phase: str) -> str:
        """Build task description with error feedback.

        Args:
            original_task: Original task description.
            code: Code that failed.
            error: Error message.
            phase: Phase where error occurred.

        Returns:
            Enhanced task description for retry.
        """
        feedback = f"{original_task}\n\n"
        feedback += f"Previous attempt failed during {phase}:\n"
        feedback += f"Code:\n```\n{code}\n```\n\n"
        feedback += f"Error: {error}\n\n"
        feedback += "Please fix this error and provide a working solution."

        return feedback

    def _should_optimize(self, task: str, code: str, result: dict[str, Any]) -> bool:
        """Decide if we should try to optimize working code.

        Args:
            task: Original task.
            code: Working code.
            result: Execution result.

        Returns:
            Whether to attempt optimization.
        """
        # Simple heuristic: don't optimize if it's already very small
        if result.get("instructions", 0) < 50:
            return False

        # Could add more sophisticated logic here
        return False  # For now, stop on first success
