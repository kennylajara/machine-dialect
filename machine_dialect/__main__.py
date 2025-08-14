#!/usr/bin/env python3
"""Machine Dialect CLI.

Main command-line interface for the Machine Dialect language.
Provides commands for compiling, running, and interacting with Machine Dialect programs.
"""

import sys
from pathlib import Path

import click

from machine_dialect.codegen.codegen import CodeGenerator
from machine_dialect.codegen.serializer import (
    InvalidMagicError,
    SerializationError,
    deserialize_module,
    serialize_module,
)
from machine_dialect.parser.parser import Parser
from machine_dialect.repl.repl import REPL
from machine_dialect.vm.disasm import print_disassembly
from machine_dialect.vm.vm import VM


@click.group()
@click.version_option(version="0.1.0", prog_name="Machine Dialect")
def cli() -> None:
    """Machine Dialect - Natural language programming in Markdown."""
    pass


@cli.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path (default: source.mdc)",
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
def compile(
    source_file: str,
    output: str | None,
    disassemble: bool,
    verbose: bool,
    module_name: str | None,
) -> None:
    """Compile a Machine Dialect source file to bytecode."""
    source_path = Path(source_file)

    # Default output file
    if output is None:
        output_path = source_path.with_suffix(".mdc")
    else:
        output_path = Path(output)

    # Read source file
    try:
        with open(source_path, encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        click.echo(f"Error: File '{source_file}' not found", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)
        sys.exit(1)

    if verbose:
        click.echo(f"Compiling '{source_file}'...")

    # Parse source
    parser = Parser()
    ast = parser.parse(source)

    if parser.has_errors():
        click.echo("Parsing errors:", err=True)
        for error in parser.errors:
            click.echo(f"  {error}", err=True)
        click.echo("\nCompilation failed.", err=True)
        sys.exit(1)

    # Determine module name
    if module_name is None:
        # Use source file name (without extension) as default
        module_name = source_path.stem
        # TODO: Option 2 - Extract module name from YAML frontmatter if present
        # This would require updating the parser to handle frontmatter like:
        # ---
        # name: MyProgram
        # version: 1.0.0
        # ---

    # Generate bytecode
    try:
        codegen = CodeGenerator()
        module = codegen.compile(ast, module_name=module_name)

        if codegen.has_errors():
            click.echo("Code generation errors:", err=True)
            for error_msg in codegen.get_errors():
                click.echo(f"  {error_msg}", err=True)
            click.echo("\nCompilation failed.", err=True)
            sys.exit(1)

        # Save compiled module using new binary format
        with open(output_path, "wb") as f:
            serialize_module(module, f)

        click.echo(f"Successfully compiled to '{output_path}'")

        if verbose:
            click.echo(f"  Module name: {module.name}")
            click.echo(f"  Main chunk: {module.main_chunk.size()} bytes")
            click.echo(f"  Constants: {module.main_chunk.constants.size()}")

        # Show disassembly if requested
        if disassemble:
            click.echo("\n" + "=" * 50)
            print_disassembly(module.main_chunk)

    except Exception as e:
        click.echo(f"Error during compilation: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("bytecode_file", type=click.Path(exists=True))
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    help="Enable debug mode (show VM state)",
)
def run(bytecode_file: str, debug: bool) -> None:
    """Run a compiled Machine Dialect bytecode file."""
    # Load compiled module
    try:
        with open(bytecode_file, "rb") as f:
            module = deserialize_module(f)
    except FileNotFoundError:
        click.echo(f"Error: File '{bytecode_file}' not found", err=True)
        sys.exit(1)
    except InvalidMagicError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except SerializationError as e:
        click.echo(f"Error loading file: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading file: {e}", err=True)
        sys.exit(1)

    if debug:
        click.echo(f"Running '{bytecode_file}' in debug mode...")
        click.echo("-" * 50)

    # Execute in VM
    try:
        vm = VM(debug=debug)
        result = vm.run(module)

        if debug:
            click.echo("-" * 50)

        if result is not None:
            click.echo(f"Result: {result}")

        # Show final globals if any
        if vm.globals and debug:
            click.echo("\nGlobal variables:")
            for name, value in vm.globals.items():
                click.echo(f"  {name} = {value}")

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
    """Start an interactive Machine Dialect shell (REPL)."""
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
    # Load compiled module
    try:
        with open(bytecode_file, "rb") as f:
            module = deserialize_module(f)
    except FileNotFoundError:
        click.echo(f"Error: File '{bytecode_file}' not found", err=True)
        sys.exit(1)
    except InvalidMagicError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except SerializationError as e:
        click.echo(f"Error loading file: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading file: {e}", err=True)
        sys.exit(1)

    # Show disassembly
    print_disassembly(module.main_chunk)


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
    """Generate Machine Dialect code using AI models.

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
        click.echo(f"Generating Machine Dialect code with {config.model}...")

        try:
            generated_code = generate_with_openai(
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
