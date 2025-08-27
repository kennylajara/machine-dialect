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
