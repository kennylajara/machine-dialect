"""Parsing phase of compilation.

This module handles the syntactic analysis phase of compilation.
"""

from machine_dialect.ast.ast_node import ASTNode
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.parser.parser import Parser


class ParsingPhase:
    """Syntactic analysis phase."""

    def run(self, context: CompilationContext) -> ASTNode | None:
        """Run parsing phase.

        Args:
            context: Compilation context.

        Returns:
            AST root node or None if parsing failed.
        """
        if context.config.verbose:
            print("Parsing source into AST...")

        parser = Parser()

        ast = parser.parse(context.source_content)

        # Check for parsing errors
        if parser.has_errors():
            for error in parser.errors:
                context.add_error(f"Parse error: {error}")
            return None

        if context.config.verbose:
            print("Successfully parsed AST")

        return ast
