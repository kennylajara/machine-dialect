from string import Template

# NameError
NAME_UNDEFINED = Template("Name '$name' is not defined")
UNEXPECTED_TOKEN = Template(
    "Unexpected '$token_literal'. Expected a '$expected_token_type', but a got a '$received_token_type'"
)
INVALID_INTEGER_LITERAL = Template("Invalid integer literal: '$literal'")
INVALID_FLOAT_LITERAL = Template("Invalid float literal: '$literal'")
NO_PARSE_FUNCTION = Template("No suitable parse function was found to handle '$literal'")
EXPECTED_EXPRESSION_AFTER_OPERATOR = Template("expected expression after operator '$operator', got $got")
UNEXPECTED_TOKEN_AT_START = Template("unexpected token '$token' at start of expression")
EXPECTED_EXPRESSION = Template("expected expression, got $got")
