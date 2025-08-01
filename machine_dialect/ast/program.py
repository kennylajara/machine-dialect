from machine_dialect.ast import ASTNode, Statement


class Program(ASTNode):
    def __init__(self, statements: list[Statement]) -> None:
        self.statements = statements

    def token_literal(self) -> str:
        if len(self.statements) > 0:
            return self.statements[0].token_literal()

        return ""

    def __str__(self) -> str:
        out: list[str] = []
        for statement in self.statements:
            out.append(str(statement))

        return "".join(out)
