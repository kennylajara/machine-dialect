from string import Template

# NameError
NAME_UNDEFINED = Template("Name '$name' is not defined")
UNEXPECTED_TOKEN = Template(
    "Unexpected '$token_literal'. Expected a '$expected_token_type', but a got a '$received_token_type'"
)
