from machine_dialect.ast import ASTNode, Statement


class Program(ASTNode):
    def __init__(self, statements: list[Statement]) -> None:
        self.statements = statements

    def __str__(self) -> str:
        out: list[str] = []
        for statement in self.statements:
            out.append(str(statement))

        return ".\n".join(out) + ".\n"

    def desugar(self) -> "Program":
        """Desugar the program by recursively desugaring all statements.

        Returns:
            A new Program with desugared statements.
        """
        # Desugar each statement - the desugar method returns Statement
        desugared_statements = [stmt.desugar() for stmt in self.statements]
        return Program(desugared_statements)

    def to_hir(self) -> "Program":
        """Convert AST to HIR by desugaring and then canonicalizing.

        This method first applies desugaring transformations and then
        canonicalizes the literal representations of all nodes.

        Returns:
            A HIR representation of the program.
        """
        # First desugar the program
        desugared = self.desugar()
        # Then canonicalize it
        canonicalized = desugared.canonicalize()
        return canonicalized

    def canonicalize(self) -> "Program":
        """Canonicalize the program by recursively canonicalizing all statements.

        Returns:
            A new Program with canonicalized statements.
        """
        canonicalized_statements = [stmt.canonicalize() for stmt in self.statements]
        return Program(canonicalized_statements)
