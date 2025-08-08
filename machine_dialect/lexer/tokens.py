from enum import (
    Enum,
    auto,
    unique,
)
from typing import (
    NamedTuple,
)

from machine_dialect.helpers.stopwords import ENGLISH_STOPWORDS


class TokenMetaType(Enum):
    OP = "operator"
    DELIM = "delimiter"
    PUNCT = "punctuation"
    LIT = "literal"
    MISC = "misc"
    KW = "keyword"
    TAG = "tag"


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
    OP_LTE = auto()
    OP_GT = auto()
    OP_GTE = auto()
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
    MISC_COMMENT = auto()

    # Keywords
    KW_ACTION = auto()
    KW_AND = auto()
    KW_AS = auto()
    KW_BEHAVIOR = auto()
    KW_BOOL = auto()
    KW_CALL = auto()
    KW_DATATYPE = auto()
    KW_DATE = auto()
    KW_DATETIME = auto()
    KW_DEFINE = auto()
    KW_ELSE = auto()
    KW_EMPTY = auto()
    KW_ENTRYPOINT = auto()
    KW_FILTER = auto()
    KW_FLOAT = auto()
    KW_FROM = auto()
    KW_IF = auto()
    KW_INT = auto()
    KW_INTERACTION = auto()
    KW_IS = auto()
    KW_LIST = auto()
    KW_NEGATION = auto()
    KW_NOTHING = auto()
    KW_NUMBER = auto()
    KW_OR = auto()
    KW_PROMPT = auto()
    KW_RETURN = auto()
    KW_RULE = auto()
    KW_SET = auto()
    KW_TAKE = auto()
    KW_TELL = auto()
    KW_TEMPLATE = auto()
    KW_TEXT = auto()
    KW_THEN = auto()
    KW_TIME = auto()
    KW_TO = auto()
    KW_TRAIT = auto()
    KW_URL = auto()
    KW_WITH = auto()

    # Tags
    TAG_SUMMARY_START = auto()
    TAG_SUMMARY_END = auto()
    TAG_DETAILS_START = auto()
    TAG_DETAILS_END = auto()

    @property
    def meta_type(self) -> TokenMetaType:
        name_str = getattr(self, "name", "")
        if name_str.startswith("KW_"):
            return TokenMetaType.KW
        if name_str.startswith("DELIM_"):
            return TokenMetaType.DELIM
        if name_str.startswith("PUNCT_"):
            return TokenMetaType.PUNCT
        if name_str.startswith("LIT_"):
            return TokenMetaType.LIT
        if name_str.startswith("OP_"):
            return TokenMetaType.OP
        if name_str.startswith("TAG_"):
            return TokenMetaType.TAG

        return TokenMetaType.MISC


class Token(NamedTuple):
    type: TokenType
    literal: str
    line: int
    position: int

    def __str__(self) -> str:
        return f"Type: {self.type}, Literal: {self.literal}, Line: {self.line}, Position: {self.position}"


def is_valid_identifier(literal: str) -> bool:
    """Check if a string is a valid identifier.

    Valid identifiers:
    - Start with a letter (a-z, A-Z) or underscore (_)
    - Followed by any number of letters, digits, underscores, spaces, or hyphens
    - Cannot be empty
    - Special case: underscore followed by only digits is ILLEGAL (e.g., _42, _123)
    - Special case: underscore(s) + digits + underscore(s) is ILLEGAL (e.g., _42_, __42__)
    """
    if not literal:
        return False

    # First character must be letter or underscore
    if not (literal[0].isalpha() or literal[0] == "_"):
        return False

    # Check for invalid underscore number patterns
    if literal[0] == "_":
        # Remove leading underscores and check if the first character is a digit
        stripped = literal.lstrip("_")
        if stripped and stripped[0].isdigit():
            # This is an invalid pattern like _42, __42, _123abc, etc.
            return False

    # Rest can be alphanumeric, underscore, space, or hyphen
    return all(c.isalnum() or c in ("_", " ", "-") for c in literal[1:])


keywords_mapping: dict[str, TokenType] = {
    # classes methods
    # Define a **blueprint** called `Person` with action (`walk`)
    "action": TokenType.KW_ACTION,
    # logic and: true and false
    "and": TokenType.KW_AND,
    # call function:
    #   apply rule `add` with **1** and **5**`.
    #   apply rule `add` with `left` = **1** and `right` = **5**`.
    "apply": TokenType.KW_CALL,
    # type indicator: set `a` as integer
    "as": TokenType.KW_AS,
    # behavior for objects
    "behavior": TokenType.KW_BEHAVIOR,
    # boolean:
    "Boolean": TokenType.KW_BOOL,
    # declare function: define a `sum` as function
    "define": TokenType.KW_DEFINE,
    # else statement
    "else": TokenType.KW_ELSE,
    # empty collections (lists, dicts)
    "empty": TokenType.KW_EMPTY,
    # entrypoint for execution
    "entrypoint": TokenType.KW_ENTRYPOINT,
    # boolean primitive: false
    "False": TokenType.LIT_FALSE,
    # filter mini-programs that act as proxy to decide on AI code execution
    "filter": TokenType.KW_FILTER,
    # float typing: set `a` as float | set `a` to float 3.14
    "Float": TokenType.KW_FLOAT,
    # range indicator: from 1 to 10
    "from": TokenType.KW_FROM,
    # if condition: if true
    "if": TokenType.KW_IF,
    "when": TokenType.KW_IF,
    "whenever": TokenType.KW_IF,
    # integer typing: set `a` to integer 3
    "Integer": TokenType.KW_INT,
    # interaction for objects
    "interaction": TokenType.KW_INTERACTION,
    # equal comparator: if `x` is 0
    "is": TokenType.KW_IS,
    # Natural language comparison operators
    "is equal to": TokenType.OP_EQ,
    "is same as": TokenType.OP_EQ,
    "equals": TokenType.OP_EQ,
    "is exactly": TokenType.OP_EQ,
    "is not": TokenType.OP_NOT_EQ,
    "isn't": TokenType.OP_NOT_EQ,
    "is not equal to": TokenType.OP_NOT_EQ,
    "doesn't equal": TokenType.OP_NOT_EQ,
    "is different from": TokenType.OP_NOT_EQ,
    "is greater than": TokenType.OP_GT,
    "is more than": TokenType.OP_GT,
    "is less than": TokenType.OP_LT,
    "is under": TokenType.OP_LT,
    "is fewer than": TokenType.OP_LT,
    "is greater or equal to": TokenType.OP_GTE,
    "is at least": TokenType.OP_GTE,
    "is no less than": TokenType.OP_GTE,
    "is less than or equal to": TokenType.OP_LTE,
    "is at most": TokenType.OP_LTE,
    "is no more than": TokenType.OP_LTE,
    # list data type
    "List": TokenType.KW_LIST,
    # logic not: not true
    "not": TokenType.KW_NEGATION,
    # null value
    "Nothing": TokenType.KW_NOTHING,
    # numbers
    "Number": TokenType.KW_NUMBER,
    # logic or: true or false
    "or": TokenType.KW_OR,
    # else statement
    "otherwise": TokenType.KW_ELSE,
    # prompt for user input or AI
    "prompt": TokenType.KW_PROMPT,
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
    # Call actions
    "Tell": TokenType.KW_TELL,
    # template (equivalent to class in other languages)
    "template": TokenType.KW_TEMPLATE,
    # text typing (string)
    "text": TokenType.KW_TEXT,
    # separates if statement from block of code: `if true then return x`.
    "then": TokenType.KW_THEN,
    # range indicator: from 1 to 10
    "to": TokenType.KW_TO,
    # classes properties:
    # Define a blueprint called Person with these traits
    "trait": TokenType.KW_TRAIT,
    # boolean primitive: true
    "True": TokenType.LIT_TRUE,
    # parameters:
    #   tell **alice** to **walk**.
    #   tell **alice** to **walk** with `speed` = `10`.
    "with": TokenType.KW_WITH,
    # type indicators
    "URL": TokenType.KW_URL,
    "Date": TokenType.KW_DATE,
    "DateTime": TokenType.KW_DATETIME,
    "Time": TokenType.KW_TIME,
    "DataType": TokenType.KW_DATATYPE,
    # Plural forms map to singular token types
    "actions": TokenType.KW_ACTION,
    "Floats": TokenType.KW_FLOAT,
    "Integers": TokenType.KW_INT,
    "Numbers": TokenType.KW_NUMBER,
    "takes": TokenType.KW_TAKE,
    "texts": TokenType.KW_TEXT,
    "traits": TokenType.KW_TRAIT,
    "URLs": TokenType.KW_URL,
    "Dates": TokenType.KW_DATE,
    "DateTimes": TokenType.KW_DATETIME,
    "Times": TokenType.KW_TIME,
}


lowercase_keywords_mapping: dict[str, str] = {key.lower(): key for key in keywords_mapping}


# Tag tokens mapping (case-insensitive)
TAG_TOKENS: dict[str, TokenType] = {
    "<summary>": TokenType.TAG_SUMMARY_START,
    "</summary>": TokenType.TAG_SUMMARY_END,
    "<details>": TokenType.TAG_DETAILS_START,
    "</details>": TokenType.TAG_DETAILS_END,
}


def lookup_tag_token(literal: str) -> tuple[TokenType | None, str]:
    """Lookup a tag token from the literal.

    Args:
        literal: The tag literal to lookup (e.g., '<summary>', '</details>')

    Returns:
        Tuple of (TokenType, canonical_literal) if found, (None, literal) otherwise.
        Canonical form is always lowercase.
    """
    # Convert to lowercase for case-insensitive comparison
    lowercase_literal = literal.lower()

    if lowercase_literal in TAG_TOKENS:
        return TAG_TOKENS[lowercase_literal], lowercase_literal

    return None, literal


def lookup_token_type(literal: str) -> tuple[TokenType, str]:
    # First check if it's a keyword (case-insensitive)
    lowercase_literal = literal.lower()
    if lowercase_literal in lowercase_keywords_mapping:
        canonical_form = lowercase_keywords_mapping[lowercase_literal]
        token_type = keywords_mapping[canonical_form]
        return token_type, canonical_form

    # Check if it's a stopword (case-insensitive)
    if lowercase_literal in ENGLISH_STOPWORDS:
        return TokenType.MISC_STOPWORD, literal

    # Only return MISC_IDENT if it's a valid identifier
    if is_valid_identifier(literal):
        return TokenType.MISC_IDENT, literal

    # If not a valid identifier, it's illegal
    return TokenType.MISC_ILLEGAL, literal
