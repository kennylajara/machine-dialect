from string import Template

# NameError
NAME_UNDEFINED = Template("Name '$name' is not defined")
UNEXPECTED_TOKEN = Template(
    "Unexpected '$token_literal'. Expected a '$expected_token_type', but a got a '$received_token_type'"
)
INVALID_INTEGER_LITERAL = Template("Invalid integer literal: '$literal'")
INVALID_FLOAT_LITERAL = Template("Invalid float literal: '$literal'")
NO_PARSE_FUNCTION = Template("No parse function was found to parse '$literal'")
