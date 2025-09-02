"""HIR generation phase of compilation.

This module handles the High-level IR generation (desugaring) phase.
"""

from machine_dialect.ast.ast_node import ASTNode
from machine_dialect.compiler.context import CompilationContext


class HIRGenerationPhase:
    """HIR generation (desugaring) phase."""

    def run(self, context: CompilationContext, ast: ASTNode) -> ASTNode:
        """Run HIR generation phase.

        Currently, this is a pass-through as we don't have a separate
        HIR representation. In the future, this would handle desugaring
        of complex AST constructs into simpler forms.

        Args:
            context: Compilation context.
            ast: Abstract syntax tree.

        Returns:
            HIR representation (currently just the AST).
        """
        if context.config.verbose:
            print("Generating HIR (desugaring)...")

        # TODO: Implement actual desugaring transformations
        # For now, HIR is the same as AST
        hir = ast

        if context.config.verbose:
            print("HIR generation complete")

        return hir
