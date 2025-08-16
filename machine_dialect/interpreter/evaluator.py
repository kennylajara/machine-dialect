from typing import Any, cast

import machine_dialect.ast as ast
from machine_dialect.errors.messages import NAME_UNDEFINED, UNKNOWN_INFIX_OPERATOR, UNKNOWN_PREFIX_OPERATOR
from machine_dialect.interpreter.objects import (
    URL,
    Boolean,
    Empty,
    Environment,
    Error,
    Float,
    Integer,
    Object,
    Return,
    String,
)
from machine_dialect.lexer import TokenType

TRUE = Boolean(True)
FALSE = Boolean(False)
EMPTY = Empty()


def evaluate(node: ast.ASTNode, env: Environment | None = None) -> Object | None:
    """Evaluate an AST node.

    Args:
        node: The AST node to evaluate.
        env: The environment for variable storage. If None, a new one is created.

    Returns:
        The evaluated object or None.
    """
    if env is None:
        env = Environment()

    node_type: type[Any] = type(node)

    match node_type:
        case ast.BlockStatement:
            node = cast(ast.BlockStatement, node)
            return _evaluate_block_statement(node, env)

        case ast.BooleanLiteral:
            node = cast(ast.BooleanLiteral, node)
            assert node.value is not None
            return Boolean(node.value)

        case ast.EmptyLiteral:
            return EMPTY

        case ast.ExpressionStatement:
            node = cast(ast.ExpressionStatement, node)
            assert node.expression is not None
            return evaluate(node.expression, env)

        case ast.IfStatement:
            node = cast(ast.IfStatement, node)

            return _evaluate_if_statement(node, env)

        case ast.InfixExpression:
            node = cast(ast.InfixExpression, node)
            assert node.right is not None and node.left is not None

            left = evaluate(node.left, env)
            right = evaluate(node.right, env)
            assert left is not None and right is not None

            return _evaluate_infix_expression(node.token.type, left, right)

        case ast.IntegerLiteral:
            node = cast(ast.IntegerLiteral, node)
            assert node.value is not None
            return Integer(node.value)

        case ast.FloatLiteral:
            node = cast(ast.FloatLiteral, node)
            assert node.value is not None
            return Float(node.value)

        case ast.PrefixExpression:
            node = cast(ast.PrefixExpression, node)
            assert node.right is not None
            right = evaluate(node.right, env)
            assert right is not None
            return _evaluate_prefix_expression(node.token.type, right)

        case ast.Program:
            node = cast(ast.Program, node)
            return _evaluate_program(node, env)

        case ast.ReturnStatement:
            node = cast(ast.ReturnStatement, node)
            assert node.return_value is not None
            value = evaluate(node.return_value, env)

            assert value is not None
            return Return(value)

        case ast.StringLiteral:
            node = cast(ast.StringLiteral, node)
            assert node.value is not None
            # Strip the quotes from the string literal value
            value = node.value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            return String(value)

        case ast.URLLiteral:
            node = cast(ast.URLLiteral, node)
            assert node.value is not None
            # Strip the quotes from the URL literal value
            value = node.value
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            return URL(value)

        case ast.ConditionalExpression:
            node = cast(ast.ConditionalExpression, node)
            return _evaluate_conditional_expression(node, env)

        case ast.SetStatement:
            node = cast(ast.SetStatement, node)
            return _evaluate_set_statement(node, env)

        case ast.Identifier:
            node = cast(ast.Identifier, node)
            return _evaluate_identifier(node, env)

        case _:
            return None


def _evaluate_block_statement(node: ast.BlockStatement, env: Environment) -> Object | None:
    result: Object | None = None

    for statement in node.statements:
        result = evaluate(statement, env)
        if result is not None and isinstance(result, Return | Error):
            return result

    return result


def _evaluate_if_statement(if_statement: ast.IfStatement, env: Environment) -> Object | None:
    assert if_statement.condition is not None
    condition = evaluate(if_statement.condition, env)

    assert condition is not None
    if condition == TRUE:
        if if_statement.consequence is not None:
            return evaluate(if_statement.consequence, env)
        return None
    elif condition == FALSE:
        if if_statement.alternative is not None:
            return evaluate(if_statement.alternative, env)
        return None

    return EMPTY


def _evaluate_conditional_expression(node: ast.ConditionalExpression, env: Environment) -> Object | None:
    """Evaluate a conditional (ternary) expression.

    Args:
        node: The ConditionalExpression node to evaluate.

    Returns:
        The result of evaluating either the consequence or alternative expression
        based on the condition.
    """
    assert node.condition is not None
    condition = evaluate(node.condition, env)

    assert condition is not None
    # Check if condition is truthy
    if condition == TRUE or (hasattr(condition, "value") and condition.value):
        if node.consequence is not None:
            return evaluate(node.consequence, env)
        return None
    else:
        if node.alternative is not None:
            return evaluate(node.alternative, env)
        return None


def _evaluate_infix_expression(token_type: TokenType, left: Object, right: Object) -> Object | None:
    match token_type:
        case TokenType.OP_PLUS:
            return left.react_to_infix_operator_addition(right)
        case TokenType.KW_AND:
            return left.react_to_infix_operator_and(right)
        case TokenType.OP_MINUS:
            return left.react_to_infix_operator_substraction(right)
        case TokenType.OP_DIVISION:
            return left.react_to_infix_operator_division(right)
        case TokenType.OP_EQ:
            return left.react_to_infix_operator_equals(right)
        case TokenType.OP_GT:
            return left.react_to_infix_operator_greater_than(right)
        case TokenType.OP_GTE:
            return left.react_to_infix_operator_greater_than_or_equal(right)
        case TokenType.OP_LT:
            return left.react_to_infix_operator_less_than(right)
        case TokenType.OP_LTE:
            return left.react_to_infix_operator_less_than_or_equal(right)
        case TokenType.OP_STAR:
            return left.react_to_infix_operator_multiplication(right)
        case TokenType.OP_NOT_EQ:
            return left.react_to_infix_operator_not_equals(right)
        case TokenType.KW_OR:
            return left.react_to_infix_operator_or(right)
        case TokenType.OP_STRICT_EQ:
            return left.react_to_infix_operator_strict_equals(right)
        case TokenType.OP_STRICT_NOT_EQ:
            return left.react_to_infix_operator_strict_not_equals(right)
        case _:
            # Return an error for unknown infix operators
            error_message = UNKNOWN_INFIX_OPERATOR.format(operator=token_type.name)
            return Error(error_message)


def _evaluate_operator_expression_not(right: Object) -> Object:
    return right.react_to_prefix_operator_not()


def _evaluate_operator_expression_minus(right: Object) -> Object:
    return right.react_to_prefix_operator_minus()


def _evaluate_prefix_expression(token_type: TokenType, right: Object) -> Object:
    match token_type:
        case TokenType.OP_MINUS:
            return right.react_to_prefix_operator_minus()
        case TokenType.KW_NEGATION:
            return right.react_to_prefix_operator_not()
        case _:
            # Return an error for unknown prefix operators
            error_message = UNKNOWN_PREFIX_OPERATOR.format(operator=token_type.name)
            return Error(error_message)


def _evaluate_program(program: ast.Program, env: Environment) -> Object | None:
    result: Object | None = None

    for statement in program.statements:
        result = evaluate(statement, env)

        if result is not None:
            if isinstance(result, Return):
                return result.value
            elif isinstance(result, Error):
                return result

    return result


def _evaluate_set_statement(node: ast.SetStatement, env: Environment) -> Object | None:
    """Evaluate a set (assignment) statement.

    Args:
        node: The SetStatement node to evaluate.
        env: The environment to store the variable in.

    Returns:
        The value that was assigned, or None.
    """
    if node.value is None:
        return Error("SetStatement has no value")

    value = evaluate(node.value, env)
    if value is None:
        return Error("Failed to evaluate SetStatement value")

    if isinstance(value, Error):
        return value

    if node.name is None:
        return Error("SetStatement has no name")

    # Store the value in the environment
    env[node.name.value] = value

    # Return None for statements (they don't produce values)
    return None


def _evaluate_identifier(node: ast.Identifier, env: Environment) -> Object | None:
    """Evaluate an identifier by looking it up in the environment.

    Args:
        node: The Identifier node to evaluate.
        env: The environment to look up the variable in.

    Returns:
        The value from the environment, or an error if not found.
    """
    name = node.value
    if name in env:
        return env[name]

    return Error(NAME_UNDEFINED.format(name=name))
