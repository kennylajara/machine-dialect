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
        """Convert AST to HIR by desugaring.

        This method applies desugaring transformations which includes
        normalizing operators to their canonical forms.

        Returns:
            A HIR representation of the program.
        """
        # Desugar the program (includes normalization)
        return self.desugar()
