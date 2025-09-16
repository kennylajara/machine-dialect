#!/usr/bin/env python3
"""Machine Dialect™ CLI.

Main command-line interface for the Machine Dialect™ language.
Provides commands for compiling, running, and interacting with Machine Dialect™ programs.
"""

import sys
from pathlib import Path

import click

from machine_dialect.compiler import Compiler, CompilerConfig
from machine_dialect.repl.repl import REPL


@click.group()
@click.version_option(version="0.1.0", prog_name="Machine Dialect™")
def cli() -> None:
    """Machine Dialect™ - Natural language programming in Markdown."""
    pass


@cli.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path (default: source.mdbc)",
)
@click.option(
    "-d",
    "--disassemble",
    is_flag=True,
    help="Show disassembly after compilation",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed compilation information",
)
@click.option(
    "-m",
    "--module-name",
    type=str,
    help="Name for the compiled module (default: source file name)",
)
@click.option(
    "--dump-mir",
    is_flag=True,
    help="Dump MIR representation after generation",
)
@click.option(
    "--show-cfg",
    type=click.Path(),
    help="Export control flow graph to DOT file",
)
@click.option(
    "--opt-report",
    is_flag=True,
    help="Show optimization report after compilation",
)
@click.option(
    "--mir-phase",
    is_flag=True,
    help="Stop after MIR generation (no bytecode)",
)
@click.option(
    "--opt-level",
    type=click.Choice(["0", "1", "2", "3"]),
    default="2",
    help="Optimization level (0=none, 3=aggressive)",
)
def compile(
    source_file: str,
    output: str | None,
    disassemble: bool,
    verbose: bool,
    module_name: str | None,
    dump_mir: bool,
    show_cfg: str | None,
    opt_report: bool,
    mir_phase: bool,
    opt_level: str,
) -> None:
    """Compile a Machine Dialect™ source file to bytecode."""
    # Create compiler configuration from CLI options
    config = CompilerConfig.from_cli_options(
        opt_level=opt_level,
        dump_mir=dump_mir,
        show_cfg=show_cfg,
        opt_report=opt_report,
        verbose=verbose or disassemble,
        mir_phase=mir_phase,
        output=output,
        module_name=module_name,
    )

    # Create compiler instance
    compiler = Compiler(config)

    # Compile the file
    success = compiler.compile_file(source_file, output)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    help="Enable debug mode",
)
def run(file: str, debug: bool) -> None:
    """Run a Machine Dialect™ file (source .md or compiled .mdbc)."""
    from pathlib import Path

    file_path = Path(file)
    extension = file_path.suffix.lower()

    if extension == ".md":
        # Run source file with MIR interpreter
        _run_interpreted(file_path, debug)
    elif extension == ".mdbc":
        # Run compiled bytecode with Rust VM
        _run_compiled(file, debug)
    else:
        click.echo(f"Error: Unsupported file type '{extension}'", err=True)
        click.echo("Supported extensions: .md (source), .mdbc (compiled bytecode)", err=True)
        sys.exit(1)


def _run_interpreted(source_path: Path, debug: bool) -> None:
    """Run source file with MIR interpreter."""
    from machine_dialect.compiler.config import CompilerConfig
    from machine_dialect.compiler.context import CompilationContext
    from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
    from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
    from machine_dialect.mir.mir_interpreter import MIRInterpreter
    from machine_dialect.parser.parser import Parser

    try:
        # Read source file
        with open(source_path, encoding="utf-8") as f:
            source = f.read()

        if debug:
            click.echo(f"Interpreting {source_path}...")

        # Parse to AST
        parser = Parser()
        ast = parser.parse(source)
        if ast is None:
            # Check if parser has errors and display them
            if parser.has_errors():
                for error in parser.errors:
                    click.echo(f"Parse error: {error}", err=True)
            else:
                click.echo("Error: Failed to parse source", err=True)
            sys.exit(1)

        # Generate HIR
        config = CompilerConfig(verbose=debug)
        context = CompilationContext(source_path=source_path, config=config, source_content=source)
        hir_phase = HIRGenerationPhase()
        hir = hir_phase.run(context, ast)
        if hir is None:
            click.echo("Error: Failed to generate HIR", err=True)
            sys.exit(1)

        # Generate MIR
        mir_phase = MIRGenerationPhase()
        mir_module = mir_phase.run(context, hir)
        if mir_module is None:
            click.echo("Error: Failed to generate MIR", err=True)
            sys.exit(1)

        # TODO: Fix optimizer bug where it removes necessary variable stores in SSA form
        # The optimizer incorrectly identifies stores like `n_minus_1.0 = t6` as dead code
        # and removes them, but keeps the corresponding loads like `t10 = n_minus_1.0`,
        # causing "Undefined variable" errors at runtime.
        #
        # Example of the bug:
        # BEFORE optimization:
        #   n_minus_1.0 = t6    # This gets removed
        #   t10 = n_minus_1.0   # This stays, causing error
        #
        # Temporarily disable optimization until the dead code elimination pass
        # is fixed to properly track SSA variable usage across basic blocks.
        #
        # To reproduce the bug, uncomment the line below and run:
        # python -m machine_dialect run benchmark/fibonacci.md
        #
        # mir_module, _ = optimize_mir(mir_module, optimization_level=2)

        # Interpret MIR
        interpreter = MIRInterpreter()
        result = interpreter.interpret_module(mir_module, trace=debug)

        # Display result only in debug mode
        if debug and result is not None:
            click.echo(f"Result: {result}")

        # Display output if any
        output = interpreter.get_output()
        if output:
            for line in output:
                click.echo(line)

    except Exception as e:
        click.echo(f"Runtime error: {e}", err=True)
        if debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def _run_compiled(bytecode_file: str, debug: bool) -> None:
    """Run compiled bytecode with Rust VM."""
    try:
        # Import the Rust VM module
        # Add the site-packages path to ensure we get the compiled module
        import site
        import sys as _sys

        site_packages = site.getsitepackages()
        for path in site_packages:
            if path not in _sys.path:
                _sys.path.insert(0, path)

        import machine_dialect_vm

        # Create VM instance
        vm = machine_dialect_vm.RustVM()

        # Enable debug mode if requested
        if debug:
            vm.set_debug(True)
            click.echo("Debug mode enabled")

        # Load and execute bytecode
        if debug:
            click.echo(f"Loading bytecode from: {bytecode_file}")
        vm.load_bytecode(bytecode_file)

        if debug:
            click.echo("Executing bytecode...")
        result = vm.execute()

        # Display result only in debug mode
        if debug and result is not None:
            click.echo(f"Result: {result}")

        if debug:
            click.echo(f"Instructions executed: {vm.instruction_count()}")

    except ImportError as e:
        click.echo("Error: Rust VM module not found", err=True)
        click.echo("Please build the Rust VM first:", err=True)
        click.echo("  ./build_vm.sh", err=True)
        click.echo(f"Details: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Runtime error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--tokens",
    is_flag=True,
    help="Run in token debug mode",
)
@click.option(
    "--ast",
    is_flag=True,
    help="Run in AST mode (show AST instead of evaluating)",
)
def shell(tokens: bool, ast: bool) -> None:
    """Start an interactive Machine Dialect™ shell (REPL)."""
    if tokens and ast:
        click.echo("Error: --tokens and --ast flags are not compatible", err=True)
        sys.exit(1)
    repl = REPL(debug_tokens=tokens, show_ast=ast)
    exit_code = repl.run()
    sys.exit(exit_code)


@cli.command()
@click.argument("bytecode_file", type=click.Path(exists=True))
def disasm(bytecode_file: str) -> None:
    """Disassemble a compiled bytecode file."""
    # TODO: Implement disassembly for new register-based bytecode
    # The code below will be re-enabled once bytecode generation is implemented
    # try:
    #     with open(bytecode_file, "rb") as f:
    #         module = deserialize_module(f)
    # except FileNotFoundError:
    #     click.echo(f"Error: File '{bytecode_file}' not found", err=True)
    #     sys.exit(1)
    # except InvalidMagicError as e:
    #     click.echo(f"Error: {e}", err=True)
    #     sys.exit(1)
    # except SerializationError as e:
    #     click.echo(f"Error loading file: {e}", err=True)
    #     sys.exit(1)
    # except Exception as e:
    #     click.echo(f"Error loading file: {e}", err=True)
    #     sys.exit(1)

    click.echo("Disassembly not yet implemented for register-based bytecode", err=True)
    sys.exit(1)


@cli.command()
@click.argument("task", nargs=-1, required=True)
@click.option(
    "--iterations",
    type=int,
    default=5,
    help="Maximum iterations to attempt (default: 5)",
)
@click.option(
    "--api-key",
    help="AI API key (or set in .mdconfig file or MD_AI_API_KEY env var)",
)
@click.option(
    "--model",
    help="AI model to use (e.g., gpt-5). If not specified, uses .mdconfig or env vars",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Save final code to file",
)
@click.option(
    "--save-history",
    type=click.Path(),
    help="Save iteration history to JSON file",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Minimal output",
)
def agent(
    task: tuple[str, ...],
    iterations: int,
    api_key: str | None,
    model: str | None,
    output: str | None,
    save_history: str | None,
    quiet: bool,
) -> None:
    """Iteratively develop Machine Dialect™ code with AI assistance.

    The agent will automatically generate, compile, execute, and fix code
    until it successfully completes the task or reaches the iteration limit.

    Examples:
        machine-dialect agent "calculate the factorial of 5"
        machine-dialect agent "sort a list of numbers" --iterations 3
        machine-dialect agent "check if a number is prime" --output prime.md
    """
    # Join task arguments
    task_description = " ".join(task)

    if not task_description.strip():
        click.echo("Error: Task description cannot be empty", err=True)
        sys.exit(1)

    # Load configuration
    from machine_dialect.cfg.config import ConfigLoader

    loader = ConfigLoader()
    config = loader.load()

    # Override with command-line arguments if provided
    if api_key:
        config.key = api_key
    if model:
        config.model = model

    # Check configuration
    if not config.key:
        click.echo("Error: No API key configured", err=True)
        click.echo(loader.get_error_message(), err=True)
        sys.exit(1)

    if not config.model:
        click.echo("Error: No AI model configured", err=True)
        click.echo(loader.get_error_message(), err=True)
        sys.exit(1)

    try:
        # Import OpenAI
        try:
            from openai import OpenAI
        except ImportError:
            click.echo("Error: OpenAI library not installed", err=True)
            click.echo("Install with: pip install openai", err=True)
            sys.exit(1)

        # Initialize client
        client = OpenAI(api_key=config.key)

        # Create agent
        from machine_dialect.agent import Agent

        agent = Agent(client, config.model, verbose=not quiet)

        # Solve the task
        result = agent.solve(task_description, max_iterations=iterations)

        # Display results
        if not quiet:
            click.echo("\n" + "=" * 60)

        if result.success:
            click.echo(f"✨ SUCCESS in {result.iterations} iteration(s)!")
            if result.output:
                click.echo(f"Output: {result.output}")

            # Save code if requested
            if output and result.code:
                with open(output, "w") as f:
                    f.write(result.code)
                click.echo(f"\nCode saved to: {output}")
            elif not quiet:
                click.echo("\nFinal code:")
                click.echo("-" * 40)
                click.echo(result.code)
                click.echo("-" * 40)

        else:
            click.echo(f"❌ Failed after {result.iterations} iterations", err=True)
            if not quiet:
                click.echo("Try with more iterations or a clearer task description.", err=True)

        # Save history if requested
        if save_history and result.history:
            import json

            with open(save_history, "w") as f:
                json.dump(result.history, f, indent=2)
            click.echo(f"History saved to: {save_history}")

        # Exit with appropriate code
        sys.exit(0 if result.success else 1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if not quiet:
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("task", nargs=-1, required=True)
@click.option(
    "--api-key",
    help="AI API key (or set in .mdconfig file or MD_AI_API_KEY env var)",
)
@click.option(
    "--model",
    help="AI model to use (e.g., gpt-5, gpt-5-mini). If not specified, uses .mdconfig or env vars",
)
@click.option(
    "-t",
    "--temperature",
    type=float,
    default=0.7,
    help="Sampling temperature 0-2 (default: 0.7)",
)
@click.option(
    "-m",
    "--max-tokens",
    type=int,
    default=400,
    help="Maximum tokens to generate (default: 400)",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Save generated code to file",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Validate generated code syntax (default: validate)",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed generation information",
)
def llm(
    task: tuple[str, ...],
    api_key: str | None,
    model: str | None,
    temperature: float,
    max_tokens: int,
    output: str | None,
    validate: bool,
    verbose: bool,
) -> None:
    """Generate Machine Dialect™ code using AI models.

    Examples:
        machine-dialect llm "calculate the factorial of 5"
        machine-dialect llm "check if age 18 can vote" --output vote_check.md
        machine-dialect llm "sum numbers from 1 to 10" -t 0.1 -m 500

    Note: Escape backticks in your task description or use single quotes:
        machine-dialect llm 'Sum `r` and `s`, being r=11 and s=45'
    """
    # Join task arguments into a single string
    task_description = " ".join(task)

    if not task_description.strip():
        click.echo("Error: Task description cannot be empty", err=True)
        sys.exit(1)

    # Load configuration
    from machine_dialect.cfg.config import ConfigLoader

    loader = ConfigLoader()
    config = loader.load()

    # Override with command-line arguments if provided
    if api_key:
        config.key = api_key
    if model:
        config.model = model

    # Check if configuration is valid
    if not config.key:
        click.echo("Error: No API key configured", err=True)
        click.echo(loader.get_error_message(), err=True)
        sys.exit(1)

    if not config.model:
        click.echo("Error: No AI model configured", err=True)
        click.echo(loader.get_error_message(), err=True)
        sys.exit(1)

    try:
        # Import OpenAI and our generator
        try:
            from openai import OpenAI
        except ImportError:
            click.echo("Error: OpenAI library not installed", err=True)
            click.echo("Install with: pip install openai", err=True)
            sys.exit(1)

        from machine_dialect.cfg import CFGParser
        from machine_dialect.cfg.openai_generation import generate_with_openai

        if verbose:
            click.echo(f"Model: {config.model}")
            click.echo(f"Task: {task_description}")
            click.echo(f"Temperature: {temperature}")
            click.echo(f"Max tokens: {max_tokens}")
            click.echo("-" * 50)

        # Initialize OpenAI client
        client = OpenAI(api_key=config.key)

        # Generate code
        click.echo(f"Generating Machine Dialect™ code with {config.model}...")

        try:
            generated_code, _token_info = generate_with_openai(
                client=client,
                model=config.model,
                task_description=task_description,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Check what we got
            if not generated_code:
                click.echo("Error: Empty response from API", err=True)
                sys.exit(1)

        except Exception as e:
            click.echo(f"Error: API call failed - {e}", err=True)
            sys.exit(1)

        # Only show output if we actually got code
        click.echo("\n" + "=" * 50)
        click.echo("Generated Code:")
        click.echo("=" * 50)
        click.echo(generated_code)
        click.echo("=" * 50)

        # Validate if requested
        if validate:
            click.echo("\nValidating syntax...")
            parser = CFGParser()

            try:
                is_valid = parser.validate(generated_code)
                if is_valid:
                    click.echo("✓ Generated code is syntactically valid!")

                    if verbose:
                        tree = parser.parse(generated_code)
                        click.echo("\nAST Preview:")
                        ast_str = parser.pretty_print(tree)
                        # Show first few lines
                        for line in ast_str.split("\n")[:8]:
                            click.echo(f"  {line}")
                        if len(ast_str.split("\n")) > 8:
                            click.echo("  ...")
                else:
                    click.echo("✗ Generated code has syntax errors", err=True)
            except Exception as e:
                click.echo(f"✗ Validation error: {e}", err=True)

        # Save to file if requested
        if output:
            try:
                with open(output, "w") as f:
                    f.write(generated_code)
                click.echo(f"\n✓ Code saved to: {output}")
            except Exception as e:
                click.echo(f"Error saving file: {e}", err=True)
                sys.exit(1)

        if verbose:
            click.echo("\n" + "-" * 50)
            click.echo("Generation complete!")
            click.echo("CFG ensures 100% syntactic correctness")

    except ImportError as e:
        click.echo(f"Error: Missing required module: {e}", err=True)
        click.echo("Make sure Lark is installed: pip install lark", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
