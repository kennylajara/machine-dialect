from string import Template


class ErrorTemplate(Template):
    pass


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
