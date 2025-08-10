#!/usr/bin/env python3
"""Machine Dialect CLI.

Main command-line interface for the Machine Dialect language.
Provides commands for compiling, running, and interacting with Machine Dialect programs.
"""

import pickle
import sys
from pathlib import Path

import click

from machine_dialect.codegen.codegen import CodeGenerator
from machine_dialect.codegen.objects import Module
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
def compile(
    source_file: str,
    output: str | None,
    disassemble: bool,
    verbose: bool,
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

    # Generate bytecode
    try:
        codegen = CodeGenerator()
        module = codegen.compile(ast)

        if codegen.has_errors():
            click.echo("Code generation errors:", err=True)
            for error_msg in codegen.get_errors():
                click.echo(f"  {error_msg}", err=True)
            click.echo("\nCompilation failed.", err=True)
            sys.exit(1)

        # Save compiled module
        with open(output_path, "wb") as f:
            pickle.dump(module, f)

        click.echo(f"Successfully compiled to '{output_path}'")

        if verbose:
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
            module = pickle.load(f)
    except FileNotFoundError:
        click.echo(f"Error: File '{bytecode_file}' not found", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading file: {e}", err=True)
        sys.exit(1)

    if not isinstance(module, Module):
        click.echo("Error: File does not contain a valid compiled module", err=True)
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
def shell(tokens: bool) -> None:
    """Start an interactive Machine Dialect shell (REPL)."""
    repl = REPL(debug_tokens=tokens)
    exit_code = repl.run()
    sys.exit(exit_code)


@cli.command()
@click.argument("bytecode_file", type=click.Path(exists=True))
def disasm(bytecode_file: str) -> None:
    """Disassemble a compiled bytecode file."""
    # Load compiled module
    try:
        with open(bytecode_file, "rb") as f:
            module = pickle.load(f)
    except FileNotFoundError:
        click.echo(f"Error: File '{bytecode_file}' not found", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading file: {e}", err=True)
        sys.exit(1)

    if not isinstance(module, Module):
        click.echo("Error: File does not contain a valid compiled module", err=True)
        sys.exit(1)

    # Show disassembly
    print_disassembly(module.main_chunk)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
