from typing import cast

import machine_dialect.ast as ast
from machine_dialect.interpreter.objects import (
    URL,
    Boolean,
    Empty,
    Float,
    Integer,
    Object,
    String,
)


class Evaluator:
    def evaluate(self, node: ast.ASTNode) -> Object | None:
        node_type = type(node)

        match node_type:
            case ast.Program:
                node = cast(ast.Program, node)

                return self._evaluate_statements(node.statements)

            case ast.ExpressionStatement:
                node = cast(ast.ExpressionStatement, node)

                assert node.expression is not None
                return self.evaluate(node.expression)

            case ast.IntegerLiteral:
                node = cast(ast.IntegerLiteral, node)
                assert node.value is not None
                return Integer(node.value)

            case ast.FloatLiteral:
                node = cast(ast.FloatLiteral, node)
                assert node.value is not None
                return Float(node.value)

            case ast.BooleanLiteral:
                node = cast(ast.BooleanLiteral, node)
                assert node.value is not None
                return Boolean(node.value)

            case ast.EmptyLiteral:
                return Empty()

            case ast.StringLiteral:
                node = cast(ast.StringLiteral, node)
                assert node.value is not None
                return String(node.value)

            case ast.URLLiteral:
                node = cast(ast.URLLiteral, node)
                assert node.value is not None
                return URL(node.value)

            case _:
                return None

    def _evaluate_statements(self, statements: list[ast.Statement]) -> Object | None:
        result: Object | None = None

        for statement in statements:
            result = self.evaluate(statement)

        return result
