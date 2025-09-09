from enum import Enum, IntEnum, auto


class Precedence(IntEnum):
    # Lowest precedence. Used as a default precedence when we don't know yet the actual precedence
    LOWEST = 0
    # Assignment, Addition assignment, Subtraction assignment, Multiplication assignment,
    # Division assignment, Modulus assignment
    ASSIGNMENT = 1
    # Ternary conditional
    TERNARY = 2
    # Logical OR
    LOGICAL_OR = 3
    # Logical AND
    LOGICAL_AND = 4
    # Bitwise inclusive OR
    BITWISE_INCL_OR = 5
    # Bitwise exclusive OR
    BITWISE_EXCL_OR = 6
    # Bitwise AND
    BITWISE_INCL_AND = 7
    # Relational Symmetric Comparison: equal, different
    REL_SYM_COMP = 8
    # Relational Asymmetric Comparison: GT, GTE, LT, LTE and type comparison
    REL_ASYM_COMP = 9
    # Bitwise Shift
    BITWISE_SHIFT = 10
    # Mathematical Addition, subtraction
    MATH_ADD_SUB = 11
    # Mathematical product, division, and modulus
    MATH_PROD_DIV_MOD = 12
    # Mathematical exponentiation
    MATH_EXPONENT = 13
    # Unary pre-increment, Unary pre-decrement, Unary plus, Unary minus,
    # Unary logical negation, Unary bitwise complement, Unary type cast
    UNARY_SIMPLIFIED = 14
    # Unary post-increment, Unary post-decrement
    UNARY_POST_OPERATOR = 15
    # Parentheses, Array subscript, Member selection
    GROUP = 16


class Associativity(Enum):
    RIGHT_TO_LEFT = auto()
    LEFT_TO_RIGHT = auto()
