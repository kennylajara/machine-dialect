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
    OP_STRICT_EQ = auto()
    OP_STRICT_NOT_EQ = auto()
    OP_LT = auto()
    OP_LTE = auto()
    OP_GT = auto()
    OP_GTE = auto()
    OP_NEGATION = auto()
    OP_TWO_STARS = auto()
    OP_CARET = auto()  # Exponentiation operator ^
    OP_THE_NAMES_OF = auto()  # Dictionary keys extraction operator
    OP_THE_CONTENTS_OF = auto()  # Dictionary values extraction operator

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
    PUNCT_HASH_DOUBLE = auto()
    PUNCT_HASH_TRIPLE = auto()
    PUNCT_HASH_QUAD = auto()
    PUNCT_BACKSLASH = auto()
    PUNCT_FRONTMATTER = auto()  # Triple dash (---) for YAML frontmatter
    PUNCT_DASH = auto()  # Single dash (-) for list markers
    PUNCT_APOSTROPHE_S = auto()  # Possessive apostrophe-s ('s) for property access

    # Literals
    LIT_FLOAT = auto()
    LIT_WHOLE_NUMBER = auto()
    LIT_NO = auto()
    LIT_TEXT = auto()
    LIT_TRIPLE_BACKTICK = auto()
    LIT_URL = auto()
    LIT_YES = auto()

    # Special
    MISC_EOF = auto()
    MISC_ILLEGAL = auto()
    MISC_IDENT = auto()
    MISC_STOPWORD = auto()
    MISC_COMMENT = auto()

    # Keywords
    KW_ACTION = auto()
    KW_ADD = auto()  # For list operations: Add _"item"_ to `list`
    KW_AND = auto()
    KW_AS = auto()
    KW_BEHAVIOR = auto()
    KW_BLANK = auto()  # For empty collections: Set `list` to blank
    KW_CLEAR = auto()  # For clearing collections: Clear `dict` or Clear all entries from `dict`
    KW_CONTENT = auto()  # For named lists: content/contents in name-content pairs
    KW_DATATYPE = auto()
    KW_DATE = auto()
    KW_DATETIME = auto()
    KW_DEFAULT = auto()
    KW_DEFINE = auto()
    KW_EACH = auto()  # For iteration: for each item in list
    KW_ELSE = auto()
    KW_EMPTY = auto()
    KW_ENTRYPOINT = auto()
    KW_FILTER = auto()
    KW_FIRST = auto()  # For list access: the first item of
    KW_FLOAT = auto()
    KW_FOR = auto()  # For iteration: for each item in list
    KW_FROM = auto()
    KW_HAS = auto()  # For named lists: if `dict` has key
    KW_IF = auto()
    KW_IN = auto()  # For iteration: for each item in list
    KW_INPUTS = auto()
    KW_INSERT = auto()  # For list operations: Insert _"item"_ at position _3_
    KW_INTERACTION = auto()
    KW_IS = auto()
    KW_ITEM = auto()  # For numeric list access: item _5_ of
    KW_LAST = auto()  # For list access: the last item of
    KW_LIST = auto()
    KW_NAME = auto()  # For named lists: name/names in name-content pairs
    KW_NAMED_LIST = auto()  # Compound type: "named list"
    KW_NEGATION = auto()
    KW_NUMBER = auto()
    KW_OF = auto()  # For list access: item _5_ of `list`
    KW_OPTIONAL = auto()
    KW_OR = auto()
    KW_ORDERED_LIST = auto()  # Compound type: "ordered list"
    KW_OUTPUTS = auto()
    KW_PROMPT = auto()
    KW_REMOVE = auto()  # For list operations: Remove _"item"_ from `list`
    KW_REQUIRED = auto()
    KW_RETURN = auto()
    KW_RULE = auto()
    KW_SAY = auto()
    KW_SECOND = auto()  # For list access: the second item of
    KW_SET = auto()
    KW_TAKE = auto()
    KW_TELL = auto()
    KW_TEMPLATE = auto()
    KW_TEXT = auto()
    KW_THEN = auto()
    KW_THIRD = auto()  # For list access: the third item of
    KW_TIME = auto()
    KW_TO = auto()
    KW_TRAIT = auto()
    KW_UNORDERED_LIST = auto()  # Compound type: "unordered list"
    KW_URL = auto()
    KW_UPDATE = auto()  # For dictionary operations: Update "key" in `dict` to _value_
    KW_USE = auto()
    KW_USING = auto()
    KW_UTILITY = auto()
    KW_VALUE = auto()  # For dictionary operations: Add "key" to `dict` with value _x_
    KW_WHERE = auto()
    KW_WHILE = auto()  # For while loops: While `condition`:
    KW_WHOLE_NUMBER = auto()
    KW_WITH = auto()
    KW_YES_NO = auto()

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
    - Followed by any number of letters, digits, underscores, spaces, hyphens, or apostrophes
    - Cannot be empty
    - Apostrophes cannot be at the beginning/end of the identifier or any word
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

    # Check apostrophe placement rules
    if "'" in literal:
        # Apostrophe cannot be at the beginning or end
        if literal[0] == "'" or literal[-1] == "'":
            return False

        # Split by spaces to check each word
        words = literal.split(" ")
        for word in words:
            if word and "'" in word:
                # Apostrophe cannot be at the beginning or end of any word
                if word[0] == "'" or word[-1] == "'":
                    return False

    # Rest can be alphanumeric, underscore, space, hyphen, or apostrophe
    return all(c.isalnum() or c in ("_", " ", "-", "'") for c in literal[1:])


keywords_mapping: dict[str, TokenType] = {
    # classes methods
    # Define a **blueprint** called `Person` with action (`walk`)
    "action": TokenType.KW_ACTION,
    # List operations: Add _"item"_ to `list`
    "add": TokenType.KW_ADD,
    # Clear collections
    "clear": TokenType.KW_CLEAR,
    # logic and: true and false
    "and": TokenType.KW_AND,
    # Use function:
    #   Use `turn alarm off`.
    #   Use `make noise` where `sound` is _"WEE-OO"_, `volume` is _80_.
    # TODO: Implement proper 'apply' statement with its own token type (KW_APPLY)
    #       Should support: apply rule `add` with **1** and **5**
    #                       apply formula `calculate` with `left` = **1** and `right` = **5**
    # "apply": TokenType.KW_APPLY,  # Reserved for future use
    "Use": TokenType.KW_USE,
    # type indicator: set `a` as integer
    "as": TokenType.KW_AS,
    # behavior for objects
    "behavior": TokenType.KW_BEHAVIOR,
    "behaviors": TokenType.KW_BEHAVIOR,
    "behaviour": TokenType.KW_BEHAVIOR,
    "behaviours": TokenType.KW_BEHAVIOR,
    # blank for empty collections
    "blank": TokenType.KW_BLANK,
    # Named lists: content/contents in name-content pairs
    "content": TokenType.KW_CONTENT,
    "contents": TokenType.KW_CONTENT,
    # default value indicator
    "default": TokenType.KW_DEFAULT,
    # declare function: define a `sum` as function
    "define": TokenType.KW_DEFINE,
    # iteration: for each item in list
    "each": TokenType.KW_EACH,
    # else statement
    "else": TokenType.KW_ELSE,
    # empty collections (lists, dicts)
    "empty": TokenType.KW_EMPTY,
    # entrypoint for execution
    "entrypoint": TokenType.KW_ENTRYPOINT,
    # boolean primitive: false
    "No": TokenType.LIT_NO,
    # filter mini-programs that act as proxy to decide on AI code execution
    "filter": TokenType.KW_FILTER,
    # List access: the first item of
    "first": TokenType.KW_FIRST,
    # float typing: set `a` as float | set `a` to float 3.14
    "Float": TokenType.KW_FLOAT,
    # iteration: for each item in list
    "for": TokenType.KW_FOR,
    # range indicator: from 1 to 10
    "from": TokenType.KW_FROM,
    # Named lists: if `dict` has key
    "has": TokenType.KW_HAS,
    # if condition: if true
    "if": TokenType.KW_IF,
    "when": TokenType.KW_IF,
    "whenever": TokenType.KW_IF,
    "while": TokenType.KW_WHILE,
    # iteration: for each item in list
    "in": TokenType.KW_IN,
    # inputs section for parameters
    "Inputs": TokenType.KW_INPUTS,
    # List operations: Insert _"item"_ at position _3_
    "insert": TokenType.KW_INSERT,
    # interaction for objects
    "interaction": TokenType.KW_INTERACTION,
    "interactions": TokenType.KW_INTERACTION,
    # equal comparator: if `x` is 0
    "is": TokenType.KW_IS,
    # Natural language comparison operators
    # Value equality (==)
    "is equal to": TokenType.OP_EQ,
    "equals": TokenType.OP_EQ,
    "is the same as": TokenType.OP_EQ,
    # Value inequality (!=)
    "is not equal to": TokenType.OP_NOT_EQ,
    "does not equal": TokenType.OP_NOT_EQ,
    "doesn't equal": TokenType.OP_NOT_EQ,
    "is different from": TokenType.OP_NOT_EQ,
    "is not": TokenType.OP_NOT_EQ,
    "isn't": TokenType.OP_NOT_EQ,
    # Strict equality (===)
    "is strictly equal to": TokenType.OP_STRICT_EQ,
    "is exactly equal to": TokenType.OP_STRICT_EQ,
    "is identical to": TokenType.OP_STRICT_EQ,
    # Strict inequality (!==)
    # TODO: Simplify support for comparisons
    "is not strictly equal to": TokenType.OP_STRICT_NOT_EQ,
    "is not exactly equal to": TokenType.OP_STRICT_NOT_EQ,
    "is not identical to": TokenType.OP_STRICT_NOT_EQ,
    "is greater than": TokenType.OP_GT,
    "is more than": TokenType.OP_GT,
    "is less than": TokenType.OP_LT,
    "is under": TokenType.OP_LT,
    "is fewer than": TokenType.OP_LT,
    "is greater than or equal to": TokenType.OP_GTE,
    "is at least": TokenType.OP_GTE,
    "is no less than": TokenType.OP_GTE,
    "is less than or equal to": TokenType.OP_LTE,
    "is at most": TokenType.OP_LTE,
    "is no more than": TokenType.OP_LTE,
    # List access: item _5_ of
    "item": TokenType.KW_ITEM,
    # List access: the last item of
    "last": TokenType.KW_LAST,
    # list data type
    "List": TokenType.KW_LIST,
    # Named lists: name/names in name-content pairs
    "name": TokenType.KW_NAME,
    "names": TokenType.KW_NAME,
    # logic not: not true
    "not": TokenType.KW_NEGATION,
    # numbers
    "Number": TokenType.KW_NUMBER,
    # List access: item _5_ of `list`
    "of": TokenType.KW_OF,
    # Dictionary extraction operators (multi-word)
    "the names of": TokenType.OP_THE_NAMES_OF,
    "the contents of": TokenType.OP_THE_CONTENTS_OF,
    # optional parameter modifier
    "optional": TokenType.KW_OPTIONAL,
    # logic or: true or false
    "or": TokenType.KW_OR,
    # else statement
    "otherwise": TokenType.KW_ELSE,
    # outputs section for parameters
    "Outputs": TokenType.KW_OUTPUTS,
    # prompt for user input or AI
    "prompt": TokenType.KW_PROMPT,
    # List operations: Remove _"item"_ from `list`
    "remove": TokenType.KW_REMOVE,
    # required parameter modifier
    "required": TokenType.KW_REQUIRED,
    # return value.
    "give back": TokenType.KW_RETURN,
    "gives back": TokenType.KW_RETURN,
    # The typical functions: Define a rule called `add` that takes two numbers and returns another number.
    "rule": TokenType.KW_RULE,
    # output/display: Say `message`.
    # TODO: Make 'Say' case-insensitive (currently only accepts capital 'S')
    "Say": TokenType.KW_SAY,
    # List access: the second item of
    "second": TokenType.KW_SECOND,
    # declare variable: set `a` as integer.
    "Set": TokenType.KW_SET,
    # status type
    "Yes/No": TokenType.KW_YES_NO,
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
    # List access: the third item of
    "third": TokenType.KW_THIRD,
    # range indicator: from 1 to 10
    "to": TokenType.KW_TO,
    # classes properties:
    # Define a blueprint called Person with these traits
    "trait": TokenType.KW_TRAIT,
    # boolean primitive: true
    "Yes": TokenType.LIT_YES,
    # using - for capturing function return values in Set statements
    "using": TokenType.KW_USING,
    # Utility (equivalent to function in other languages)
    "Utility": TokenType.KW_UTILITY,
    # parameters:
    #   tell **alice** to **walk**.
    #   tell **alice** to **walk** with `speed` = `10`.
    "where": TokenType.KW_WHERE,
    # Update dictionary entries
    "update": TokenType.KW_UPDATE,
    # Value keyword for dictionary operations
    "value": TokenType.KW_VALUE,
    "with": TokenType.KW_WITH,
    # type indicators
    "URL": TokenType.KW_URL,
    "Date": TokenType.KW_DATE,
    "DateTime": TokenType.KW_DATETIME,
    "Time": TokenType.KW_TIME,
    "DataType": TokenType.KW_DATATYPE,
    "Whole Number": TokenType.KW_WHOLE_NUMBER,
    "Named List": TokenType.KW_NAMED_LIST,
    "Ordered List": TokenType.KW_ORDERED_LIST,
    "Unordered List": TokenType.KW_UNORDERED_LIST,
    # Plural forms map to singular token types
    "actions": TokenType.KW_ACTION,
    "Floats": TokenType.KW_FLOAT,
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
