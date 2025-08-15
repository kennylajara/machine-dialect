"""Tests for the code generator."""

from machine_dialect.ast import (
    ExpressionStatement,
    FloatLiteral,
    Identifier,
    InfixExpression,
    IntegerLiteral,
    PrefixExpression,
    Program,
    SetStatement,
)
from machine_dialect.codegen.codegen import CodeGenerator
from machine_dialect.codegen.isa import Opcode
from machine_dialect.lexer import Token, TokenType


def test_compile_integer_literal() -> None:
    """Test compiling integer literals."""
    # Create AST: 42
    expr = IntegerLiteral(Token(TokenType.LIT_INT, "42", 1, 0), 42)
    stmt = ExpressionStatement(Token(TokenType.LIT_INT, "42", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode
    bytecode = module.main_chunk.bytecode
    assert bytecode[0] == Opcode.LOAD_CONST
    assert bytecode[3] == Opcode.POP  # Expression statement pops result

    # Check constant pool
    assert module.main_chunk.constants.get(0) == 42


def test_compile_float_literal() -> None:
    """Test compiling float literals."""
    # Create AST: 3.14
    expr = FloatLiteral(Token(TokenType.LIT_FLOAT, "3.14", 1, 0), 3.14)
    stmt = ExpressionStatement(Token(TokenType.LIT_FLOAT, "3.14", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check constant pool
    assert module.main_chunk.constants.get(0) == 3.14


def test_compile_addition() -> None:
    """Test compiling addition expression."""
    # Create AST: 2 + 3
    left = IntegerLiteral(Token(TokenType.LIT_INT, "2", 1, 0), 2)
    right = IntegerLiteral(Token(TokenType.LIT_INT, "3", 1, 4), 3)
    expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 1, 2), "+", left)
    expr.right = right
    stmt = ExpressionStatement(Token(TokenType.LIT_INT, "2", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode sequence
    bytecode = module.main_chunk.bytecode
    assert bytecode[0] == Opcode.LOAD_CONST  # Load 2
    assert bytecode[3] == Opcode.LOAD_CONST  # Load 3
    assert bytecode[6] == Opcode.ADD
    assert bytecode[7] == Opcode.POP

    # Check constants
    assert module.main_chunk.constants.get(0) == 2
    assert module.main_chunk.constants.get(1) == 3


def test_compile_subtraction() -> None:
    """Test compiling subtraction expression."""
    # Create AST: 5 - 2
    left = IntegerLiteral(Token(TokenType.LIT_INT, "5", 1, 0), 5)
    right = IntegerLiteral(Token(TokenType.LIT_INT, "2", 1, 4), 2)
    expr = InfixExpression(Token(TokenType.OP_MINUS, "-", 1, 2), "-", left)
    expr.right = right
    stmt = ExpressionStatement(Token(TokenType.LIT_INT, "5", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode
    bytecode = module.main_chunk.bytecode
    assert bytecode[6] == Opcode.SUB


def test_compile_multiplication() -> None:
    """Test compiling multiplication expression."""
    # Create AST: 4 * 5
    left = IntegerLiteral(Token(TokenType.LIT_INT, "4", 1, 0), 4)
    right = IntegerLiteral(Token(TokenType.LIT_INT, "5", 1, 4), 5)
    expr = InfixExpression(Token(TokenType.OP_STAR, "*", 1, 2), "*", left)
    expr.right = right
    stmt = ExpressionStatement(Token(TokenType.LIT_INT, "4", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode
    bytecode = module.main_chunk.bytecode
    assert bytecode[6] == Opcode.MUL


def test_compile_division() -> None:
    """Test compiling division expression."""
    # Create AST: 10 / 2
    left = IntegerLiteral(Token(TokenType.LIT_INT, "10", 1, 0), 10)
    right = IntegerLiteral(Token(TokenType.LIT_INT, "2", 1, 5), 2)
    expr = InfixExpression(Token(TokenType.OP_DIVISION, "/", 1, 3), "/", left)
    expr.right = right
    stmt = ExpressionStatement(Token(TokenType.LIT_INT, "10", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode
    bytecode = module.main_chunk.bytecode
    assert bytecode[6] == Opcode.DIV


def test_compile_complex_arithmetic() -> None:
    """Test compiling complex arithmetic expression."""
    # Create AST: (2 + 3) * 4
    # This would be: 2 + 3 * 4 with precedence, but we build explicit tree
    add_left = IntegerLiteral(Token(TokenType.LIT_INT, "2", 1, 0), 2)
    add_right = IntegerLiteral(Token(TokenType.LIT_INT, "3", 1, 4), 3)
    add_expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 1, 2), "+", add_left)
    add_expr.right = add_right

    mul_right = IntegerLiteral(Token(TokenType.LIT_INT, "4", 1, 8), 4)
    expr = InfixExpression(Token(TokenType.OP_STAR, "*", 1, 6), "*", add_expr)
    expr.right = mul_right
    stmt = ExpressionStatement(Token(TokenType.LIT_INT, "2", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode sequence
    bytecode = module.main_chunk.bytecode
    assert bytecode[0] == Opcode.LOAD_CONST  # Load 2
    assert bytecode[3] == Opcode.LOAD_CONST  # Load 3
    assert bytecode[6] == Opcode.ADD  # 2 + 3
    assert bytecode[7] == Opcode.LOAD_CONST  # Load 4
    assert bytecode[10] == Opcode.MUL  # result * 4
    assert bytecode[11] == Opcode.POP


def test_compile_negation() -> None:
    """Test compiling negation (unary minus)."""
    # Create AST: -5
    operand = IntegerLiteral(Token(TokenType.LIT_INT, "5", 1, 1), 5)
    expr = PrefixExpression(Token(TokenType.OP_MINUS, "-", 1, 0), "-")
    expr.right = operand
    stmt = ExpressionStatement(Token(TokenType.OP_MINUS, "-", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode
    bytecode = module.main_chunk.bytecode
    assert bytecode[0] == Opcode.LOAD_CONST  # Load 5
    assert bytecode[3] == Opcode.NEG  # Negate
    assert bytecode[4] == Opcode.POP


def test_compile_set_statement() -> None:
    """Test compiling variable assignment."""
    # Create AST: Set x to 10
    ident = Identifier(Token(TokenType.MISC_IDENT, "x", 1, 4), "x")
    value = IntegerLiteral(Token(TokenType.LIT_INT, "10", 1, 9), 10)
    stmt = SetStatement(Token(TokenType.KW_SET, "Set", 1, 0), ident, value)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode
    bytecode = module.main_chunk.bytecode
    assert bytecode[0] == Opcode.LOAD_CONST  # Load 10
    assert bytecode[3] == Opcode.STORE_GLOBAL  # Store to x

    # Check constants
    assert module.main_chunk.constants.get(0) == 10
    assert module.main_chunk.constants.get(1) == "x"  # Variable name


def test_compile_variable_reference() -> None:
    """Test compiling variable references."""
    # Create AST: Set x to 5, then x + 3
    set_stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0),
        Identifier(Token(TokenType.MISC_IDENT, "x", 1, 4), "x"),
        IntegerLiteral(Token(TokenType.LIT_INT, "5", 1, 9), 5),
    )

    expr = InfixExpression(
        Token(TokenType.OP_PLUS, "+", 2, 2), "+", Identifier(Token(TokenType.MISC_IDENT, "x", 2, 0), "x")
    )
    expr.right = IntegerLiteral(Token(TokenType.LIT_INT, "3", 2, 4), 3)
    expr_stmt = ExpressionStatement(Token(TokenType.MISC_IDENT, "x", 2, 0), expr)

    program = Program([set_stmt, expr_stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode includes variable load
    bytecode = module.main_chunk.bytecode
    # Set x to 5
    assert bytecode[0] == Opcode.LOAD_CONST  # Load 5
    assert bytecode[3] == Opcode.STORE_GLOBAL  # Store to x
    # x + 3
    assert bytecode[6] == Opcode.LOAD_GLOBAL  # Load x
    assert bytecode[9] == Opcode.LOAD_CONST  # Load 3
    assert bytecode[12] == Opcode.ADD
    assert bytecode[13] == Opcode.POP


def test_compile_comparison() -> None:
    """Test compiling comparison operations."""
    # Create AST: 5 > 3
    left = IntegerLiteral(Token(TokenType.LIT_INT, "5", 1, 0), 5)
    right = IntegerLiteral(Token(TokenType.LIT_INT, "3", 1, 4), 3)
    expr = InfixExpression(Token(TokenType.OP_GT, ">", 1, 2), ">", left)
    expr.right = right
    stmt = ExpressionStatement(Token(TokenType.LIT_INT, "5", 1, 0), expr)
    program = Program([stmt])

    # Compile
    gen = CodeGenerator()
    module = gen.compile(program)

    # Check bytecode
    bytecode = module.main_chunk.bytecode
    assert bytecode[6] == Opcode.GT


def test_module_name_parameter() -> None:
    """Test that module name parameter works correctly."""
    # Create a simple AST
    expr = IntegerLiteral(Token(TokenType.LIT_INT, "42", 1, 0), 42)
    stmt = ExpressionStatement(Token(TokenType.LIT_INT, "42", 1, 0), expr)
    program = Program([stmt])

    # Test default module name
    gen = CodeGenerator()
    module_default = gen.compile(program)
    assert module_default.name == "main"

    # Test custom module name
    gen = CodeGenerator()
    module_custom = gen.compile(program, module_name="MyModule")
    assert module_custom.name == "MyModule"

    # Test with filename-like name
    gen = CodeGenerator()
    module_file = gen.compile(program, module_name="calculator")
    assert module_file.name == "calculator"
