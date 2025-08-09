from string import Template
from typing import Any


class ErrorTemplate(Template):
    """Custom template class that prevents direct string usage in error messages."""

    def format(self, **kwargs: Any) -> str:
        """Format the template with keyword arguments.

        This is a more Pythonic alternative to substitute().
        """
        return self.substitute(**kwargs)


# NameError
NAME_UNDEFINED = ErrorTemplate("Name '$name' is not defined")
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
EXPECTED_DETAILS_CLOSE = ErrorTemplate("Expected </details> tag after action body, got $token_type")
UNEXPECTED_BLOCK_DEPTH = ErrorTemplate("Unexpected block depth: expected $expected '>' but got $actual")
