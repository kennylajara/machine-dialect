from enum import (
    Enum,
    auto,
    unique,
)
from typing import (
    NamedTuple,
)

from machine_dialect.helpers.stopwords import ENGLISH_STOPWORDS


@unique
class TokenType(Enum):
    # Operators
    OP_PLUS = auto()
    OP_MINUS = auto()
    OP_STAR = auto()
    OP_DIVISION = auto()
    OP_ASSIGN = auto()
    OP_EQ = auto()
    OP_NOT_EQ = auto()
    OP_LT = auto()
    OP_GT = auto()
    OP_NEGATION = auto()
    OP_TWO_STARS = auto()

    # Delimiters
    DELIM_LPAREN = auto()
    DELIM_RPAREN = auto()
    DELIM_LBRACE = auto()
    DELIM_RBRACE = auto()

    # Punctuation
    PUNCT_SEMICOLON = auto()
    PUNCT_COMMA = auto()
    PUNCT_PERIOD = auto()
    PUNCT_COLON = auto()
    PUNCT_HASH = auto()

    # Literals
    LIT_BACKTICK = auto()
    LIT_FALSE = auto()
    LIT_FLOAT = auto()
    LIT_INT = auto()
    LIT_TEXT = auto()
    LIT_TRIPLE_BACKTICK = auto()
    LIT_TRUE = auto()
    LIT_URL = auto()

    # Special
    MISC_EOF = auto()
    MISC_ILLEGAL = auto()
    MISC_IDENT = auto()
    MISC_STOPWORD = auto()

    # Keywords
    KW_ACTION = auto()
    KW_ACTIONS = auto()
    KW_AND = auto()
    KW_AS = auto()
    KW_ASSIGN = auto()
    KW_BOOL = auto()
    KW_CALL = auto()
    KW_CLASS = auto()
    KW_DEFINE = auto()
    KW_ELSE = auto()
    KW_FLOAT = auto()
    KW_FLOATS = auto()
    KW_FROM = auto()
    KW_IF = auto()
    KW_INT = auto()
    KW_INTS = auto()
    KW_IS = auto()
    KW_NEGATION = auto()
    KW_NOTHING = auto()
    KW_NUMBER = (auto(),)
    KW_NUMBERS = (auto(),)
    KW_OR = auto()
    KW_RETURN = auto()
    KW_RULE = auto()
    KW_SET = auto()
    KW_TAKE = auto()
    KW_TAKES = auto()
    KW_TELL = auto()
    KW_TEXT = auto()
    KW_TEXTS = auto()
    KW_THEN = auto()
    KW_TO = auto()
    KW_TRAIT = auto()
    KW_TRAITS = auto()
    KW_WITH = auto()
    KW_URL = auto()
    KW_URLS = auto()
    KW_DATE = auto()
    KW_DATES = auto()
    KW_DATETIME = auto()
    KW_DATETIMES = auto()
    KW_TIME = auto()
    KW_TIMES = auto()
    KW_DATATYPE = auto()


class Token(NamedTuple):
    type: TokenType
    literal: str
    line: int
    position: int

    def __str__(self) -> str:
        return f"Type: {self.type}, Literal: {self.literal}, Line: {self.line}, Position: {self.position}"


def lookup_token_type(literal: str) -> TokenType:
    keywords: dict[str, TokenType] = {
        # classes methods
        # Define a **blueprint** called `Person` with action (`walk`)
        "action": TokenType.KW_ACTION,
        "actions": TokenType.KW_ACTIONS,
        # logic and: true and false
        "and": TokenType.KW_AND,
        # call function:
        #   apply rule `add` with **1** and **5**`.
        #   apply rule `add` with `left` = **1** and `right` = **5**`.
        "apply": TokenType.KW_CALL,
        # type indicator: set `a` as integer
        "as": TokenType.KW_AS,
        # assign: assign 5 to x
        "assign": TokenType.KW_ASSIGN,
        # boolean:
        "Boolean": TokenType.KW_BOOL,
        # class typing: Define a **blueprint** called `Person`
        "class": TokenType.KW_CLASS,
        # declare function: define a `sum` as function
        "define": TokenType.KW_DEFINE,
        # else statement
        "else": TokenType.KW_ELSE,
        # boolean primitive: false
        "False": TokenType.LIT_FALSE,
        # float typing: set `a` as float | set `a` to float 3.14
        "Float": TokenType.KW_FLOAT,
        "Floats": TokenType.KW_FLOATS,
        # range indicator: from 1 to 10
        "from": TokenType.KW_FROM,
        # if condition: if true
        "if": TokenType.KW_IF,
        # integer typing: set `a` to integer 3
        "Integer": TokenType.KW_INT,
        "Integers": TokenType.KW_INTS,
        # equal comparator: if `x` is 0
        "is": TokenType.KW_IS,
        # logic not: not true
        "not": TokenType.KW_NEGATION,
        # null value
        "Nothing": TokenType.KW_NOTHING,
        # numbers
        "Number": TokenType.KW_NUMBER,
        "Numbers": TokenType.KW_NUMBERS,
        # logic or: true or false
        "or": TokenType.KW_OR,
        # else statement
        "otherwise": TokenType.KW_ELSE,
        # return value.
        "give back": TokenType.KW_RETURN,
        "gives back": TokenType.KW_RETURN,
        # The typical functions: Define a rule called `add` that takes two numbers and returns another number.
        "rule": TokenType.KW_RULE,
        # declare variable: set `a` as integer.
        "Set": TokenType.KW_SET,
        # classes' properties:
        # Define a blueprint called Person with these traits
        "take": TokenType.KW_TAKE,
        "takes": TokenType.KW_TAKES,
        # Call actions
        "Tell": TokenType.KW_TELL,
        # text typing (string)
        "text": TokenType.KW_TEXT,
        "texts": TokenType.KW_TEXTS,
        # separates if statement from block of code: `if true then return x`.
        "then": TokenType.KW_THEN,
        # range indicator: from 1 to 10
        "to": TokenType.KW_TO,
        # classes properties:
        # Define a blueprint called Person with these traits
        "trait": TokenType.KW_TRAIT,
        "traits": TokenType.KW_TRAITS,
        # boolean primitive: true
        "True": TokenType.LIT_TRUE,
        # parameters:
        #   tell **alice** to **walk**.
        #   tell **alice** to **walk** with `speed` = `10`.
        "with": TokenType.KW_WITH,
        # type indicators
        "URL": TokenType.KW_URL,
        "URLs": TokenType.KW_URLS,
        "Date": TokenType.KW_DATE,
        "Dates": TokenType.KW_DATES,
        "DateTime": TokenType.KW_DATETIME,
        "DateTimes": TokenType.KW_DATETIMES,
        "Time": TokenType.KW_TIME,
        "Times": TokenType.KW_TIMES,
        "DataType": TokenType.KW_DATATYPE,
    }

    # First check if it's a keyword
    token_type = keywords.get(literal)
    if token_type is not None:
        return token_type

    # Check if it's a stopword (case-insensitive)
    if literal.lower() in ENGLISH_STOPWORDS:
        return TokenType.MISC_STOPWORD

    # Default to identifier
    return TokenType.MISC_IDENT
