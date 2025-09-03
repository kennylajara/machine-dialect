"""HIR generation phase of compilation.

This module handles the High-level IR generation (desugaring) phase.
"""

from machine_dialect.ast.ast_node import ASTNode
from machine_dialect.compiler.context import CompilationContext


class HIRGenerationPhase:
    """HIR generation (desugaring) phase."""

    def run(self, context: CompilationContext, ast: ASTNode) -> ASTNode:
        """Run HIR generation phase.

        Converts AST to HIR by applying desugaring and canonicalization
        transformations using the to_hir method.

        Args:
            context: Compilation context.
            ast: Abstract syntax tree.

        Returns:
            HIR representation with desugared and canonicalized nodes.
        """
        if context.config.verbose:
            print("Generating HIR")

        # Use to_hir to convert AST to HIR
        # The ast should be a Program which has to_hir method
        from machine_dialect.ast.program import Program

        assert isinstance(ast, Program), "HIR generation expects a Program node"
        hir = ast.to_hir()

        if context.config.verbose:
            print("HIR generation complete")

        return hir
