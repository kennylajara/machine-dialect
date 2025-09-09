from machine_dialect.lexer.tokens import TokenType

# Single-character tokens
CHAR_TO_TOKEN_MAP = {
    "+": TokenType.OP_PLUS,
    "-": TokenType.OP_MINUS,
    "*": TokenType.OP_STAR,
    "/": TokenType.OP_DIVISION,
    "^": TokenType.OP_CARET,
    "=": TokenType.OP_ASSIGN,
    "<": TokenType.OP_LT,
    ">": TokenType.OP_GT,
    "(": TokenType.DELIM_LPAREN,
    ")": TokenType.DELIM_RPAREN,
    "{": TokenType.DELIM_LBRACE,
    "}": TokenType.DELIM_RBRACE,
    ";": TokenType.PUNCT_SEMICOLON,
    ",": TokenType.PUNCT_COMMA,
    ".": TokenType.PUNCT_PERIOD,
    ":": TokenType.PUNCT_COLON,
    "#": TokenType.PUNCT_HASH,
    "\\": TokenType.PUNCT_BACKSLASH,
}
