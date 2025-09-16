from string import Template
from typing import Any


class ErrorTemplate(Template):
    """Custom template class that prevents direct string usage in error messages.

    DO NOT USE THIS CLASS DIRECTLY, USE THE CONSTANTS DEFINED BELOW"""

    def format(self, **kwargs: Any) -> str:
        """Format the template with keyword arguments.

        This is a more Pythonic alternative to substitute().
        """
        return self.substitute(**kwargs)


# NameError
NAME_UNDEFINED = ErrorTemplate("Name '$name' is not defined")
VARIABLE_NOT_DEFINED = ErrorTemplate(
    "Variable '$name' is not defined. Use 'Define `$name` as <type>.' to define it first"
)
VARIABLE_ALREADY_DEFINED = ErrorTemplate(
    "Variable '$name' is already defined at line $original_line. Cannot redefine variables in the same scope"
)
ASSIGNMENT_TYPE_MISMATCH = ErrorTemplate(
    "Cannot assign $actual_type value to variable '$variable' of type $expected_type"
)
UNEXPECTED_TOKEN = ErrorTemplate(
    "Unexpected '$token_literal'. Expected a '$expected_token_type', but a got a '$received_token_type'"
)
INVALID_INTEGER_LITERAL = ErrorTemplate("Invalid integer literal: '$literal'")
INVALID_FLOAT_LITERAL = ErrorTemplate("Invalid float literal: '$literal'")
NO_PARSE_FUNCTION = ErrorTemplate("No suitable parse function was found to handle '$literal'")
EXPECTED_EXPRESSION_AFTER_OPERATOR = ErrorTemplate("expected expression after operator '$operator', got $got")
UNEXPECTED_TOKEN_AT_START = ErrorTemplate("unexpected token '$token' at start of expression")
EXPECTED_EXPRESSION = ErrorTemplate("expected expression, got $got")

# Block and control flow errors
EMPTY_IF_CONSEQUENCE = ErrorTemplate("If statement must have a non-empty consequence block")
EMPTY_ELSE_BLOCK = ErrorTemplate("Else/otherwise block must not be empty. If no alternative is needed, omit it.")
EMPTY_WHILE_BODY = ErrorTemplate("While loop must have a non-empty body block")
EMPTY_FOR_EACH_BODY = ErrorTemplate("For-each loop must have a non-empty body block")
EXPECTED_DETAILS_CLOSE = ErrorTemplate("Expected </details> tag after action body, got $token_type")
EXPECTED_BLOCK_MARKER = ErrorTemplate("Expected block marker '>', got $token_type")
EXPECTED_PREFIX_OPERATOR = ErrorTemplate("Expected prefix operator, got $token_type")
MISSING_DEPTH_TRANSITION = ErrorTemplate(
    "After nested blocks ($nested_depth), add a blank line with just '$parent_depth' "
    "before continuing at the parent depth. Found '$token_type' at line $line"
)
UNEXPECTED_BLOCK_DEPTH = ErrorTemplate("Unexpected block depth: expected $expected '>' but got $actual")

# Collection and list errors
INVALID_NAMED_LIST_KEY = ErrorTemplate("Named list keys must be string literals. Got $literal")

# Use statement errors
EXPECTED_FUNCTION_NAME = ErrorTemplate("Expected identifier for function name, got $token_type")
EXPECTED_IDENTIFIER_FOR_NAMED_ARG = ErrorTemplate("Expected identifier for named argument, got $type_name")
POSITIONAL_AFTER_NAMED = ErrorTemplate("Positional arguments cannot appear after named arguments")
INVALID_ARGUMENT_VALUE = ErrorTemplate("Invalid argument value: '$literal'")
MISSING_COMMA_BETWEEN_ARGS = ErrorTemplate("Expected comma between arguments")

# Generic parser errors
EXPECTED_TOKEN_AFTER = ErrorTemplate("Expected $expected after $after")
EXPECTED_IDENTIFIER_AFTER = ErrorTemplate("Expected $what identifier after $after")
EXPECTED_TOKEN = ErrorTemplate("Expected $token, got $got_token_type")
ILLEGAL_CHARACTER = ErrorTemplate("Expected $expected but found illegal character '$character'")
ILLEGAL_TOKEN = ErrorTemplate("Illegal token: '$token'")
UNEXPECTED_STATEMENT = ErrorTemplate("Unexpected statement type: $type")
UNHANDLED_OPERATION = ErrorTemplate("Unhandled $what operation: $operation")
INVALID_TYPE_NAME = ErrorTemplate("'$name' is not a valid type name. Expected one of: $valid_types")

# Interpreter errors
UNKNOWN_PREFIX_OPERATOR = ErrorTemplate("Unknown prefix operator: $operator")
UNKNOWN_INFIX_OPERATOR = ErrorTemplate("Unknown infix operator: $operator")
TYPE_MISMATCH = ErrorTemplate(
    "Type mismatch: cannot apply operator '$operator' to operands of type '$left_type' and '$right_type'"
)
UNSUPPORTED_OPERATION = ErrorTemplate("Unsupported operation: '$operation' on type '$type'")
DIVISION_BY_ZERO = ErrorTemplate("Division by zero")
UNSUPPORTED_OPERAND_TYPE = ErrorTemplate("Unsupported operand type(s) for $operator: '$left_type' and '$right_type'")
UNSUPPORTED_UNARY_OPERAND = ErrorTemplate("Unsupported operand type for unary $operator: '$type'")
