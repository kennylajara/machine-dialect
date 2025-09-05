"""Tests for the Virtual Machine."""

from pathlib import Path
from typing import Any

from machine_dialect.ast import (
    ExpressionStatement,
    FloatLiteral,
    Identifier,
    InfixExpression,
    Program,
    SetStatement,
    WholeNumberLiteral,
)
from machine_dialect.codegen.objects import Module
from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.context import CompilationContext
from machine_dialect.compiler.phases.codegen import CodeGenerationPhase
from machine_dialect.compiler.phases.hir_generation import HIRGenerationPhase
from machine_dialect.compiler.phases.mir_generation import MIRGenerationPhase
from machine_dialect.lexer import Token, TokenType
from machine_dialect.vm.disasm import disassemble_chunk
from machine_dialect.vm.vm import VM


def compile_program(program: Program, optimize: bool = True) -> Module:
    """Compile an AST program to bytecode using MIR pipeline.

    Args:
        program: AST program to compile.
        optimize: Whether to enable optimization (default True).

    Returns:
        Compiled bytecode module.
    """
    # Create compilation context
    from machine_dialect.compiler.config import OptimizationLevel

    config = CompilerConfig(optimization_level=OptimizationLevel.STANDARD if optimize else OptimizationLevel.NONE)
    context = CompilationContext(source_path=Path("test.md"), config=config)
    context.ast = program

    # Run compilation phases
    hir_phase = HIRGenerationPhase()
    mir_phase = MIRGenerationPhase()
    codegen_phase = CodeGenerationPhase()

    # Convert AST -> HIR -> MIR -> Bytecode
    hir = hir_phase.run(context, program)
    mir_module = mir_phase.run(context, hir)
    if mir_module is None:
        raise RuntimeError("Failed to generate MIR module")
    context.mir_module = mir_module
    module = codegen_phase.run(context, mir_module)
    if module is None:
        raise RuntimeError("Failed to generate bytecode module")

    return module


def compile_and_run(program: Program) -> Any:
    """Helper to compile and run a program.

    Args:
        program: AST program to compile and run.

    Returns:
        The result of execution.
    """
    module = compile_program(program)
    vm = VM()
    return vm.run(module)


def test_integer_literal() -> None:
    """Test executing integer literal."""
    expr = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 0), 42)
    stmt = ExpressionStatement(Token(TokenType.LIT_WHOLE_NUMBER, "42", 1, 0), expr)
    program = Program([stmt])

    # This will pop the value, so result is None
    result = compile_and_run(program)
    assert result is None


def test_addition() -> None:
    """Test addition of two integers."""
    # Create: 2 + 3
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 0), 2)
    right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 4), 3)
    expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 1, 2), "+", left)
    expr.right = right

    # Keep result on stack by using SetStatement
    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"), expr
    )
    program = Program([stmt])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    # Check global variable
    assert vm.globals["result"] == 5


def test_subtraction() -> None:
    """Test subtraction."""
    # Create: 10 - 3
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "10", 1, 0), 10)
    right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 4), 3)
    expr = InfixExpression(Token(TokenType.OP_MINUS, "-", 1, 2), "-", left)
    expr.right = right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"), expr
    )
    program = Program([stmt])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["result"] == 7


def test_multiplication() -> None:
    """Test multiplication."""
    # Create: 4 * 5
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "4", 1, 0), 4)
    right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 4), 5)
    expr = InfixExpression(Token(TokenType.OP_STAR, "*", 1, 2), "*", left)
    expr.right = right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"), expr
    )
    program = Program([stmt])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["result"] == 20


def test_division() -> None:
    """Test division."""
    # Create: 15 / 3
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "15", 1, 0), 15)
    right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 4), 3)
    expr = InfixExpression(Token(TokenType.OP_DIVISION, "/", 1, 2), "/", left)
    expr.right = right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"), expr
    )
    program = Program([stmt])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["result"] == 5.0


def test_complex_arithmetic() -> None:
    """Test complex arithmetic expression."""
    # Create: (2 + 3) * 4
    add_left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 0), 2)
    add_right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 4), 3)
    add_expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 1, 2), "+", add_left)
    add_expr.right = add_right

    mul_right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "4", 1, 8), 4)
    expr = InfixExpression(Token(TokenType.OP_STAR, "*", 1, 6), "*", add_expr)
    expr.right = mul_right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"), expr
    )
    program = Program([stmt])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["result"] == 20


def test_float_operations() -> None:
    """Test floating point operations."""
    # Create: 3.14 + 2.86
    left = FloatLiteral(Token(TokenType.LIT_FLOAT, "3.14", 1, 0), 3.14)
    right = FloatLiteral(Token(TokenType.LIT_FLOAT, "2.86", 1, 6), 2.86)
    expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 1, 4), "+", left)
    expr.right = right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"), expr
    )
    program = Program([stmt])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert abs(vm.globals["result"] - 6.0) < 0.001


def test_comparison_gt() -> None:
    """Test greater than comparison."""
    # Create: 5 > 3
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 0), 5)
    right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 4), 3)
    expr = InfixExpression(Token(TokenType.OP_GT, ">", 1, 2), ">", left)
    expr.right = right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"), expr
    )
    program = Program([stmt])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["result"] is True


def test_comparison_lt() -> None:
    """Test less than comparison."""
    # Create: 3 < 5
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 0), 3)
    right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 4), 5)
    expr = InfixExpression(Token(TokenType.OP_LT, "<", 1, 2), "<", left)
    expr.right = right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result", 1, 4), "result"), expr
    )
    program = Program([stmt])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["result"] is True


def test_strict_equality() -> None:
    """Test strict equality comparison."""
    # Test: 5 is strictly equal to 5 (should be True)
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 0), 5)
    right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 4), 5)
    expr = InfixExpression(Token(TokenType.OP_STRICT_EQ, "is strictly equal to", 1, 2), "is strictly equal to", left)
    expr.right = right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result1", 1, 4), "result1"), expr
    )

    # Test: 5 is strictly equal to 5.0 (should be False - different types)
    left2 = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 2, 0), 5)
    right2 = FloatLiteral(Token(TokenType.LIT_FLOAT, "5.0", 2, 4), 5.0)
    expr2 = InfixExpression(Token(TokenType.OP_STRICT_EQ, "is strictly equal to", 2, 2), "is strictly equal to", left2)
    expr2.right = right2

    stmt2 = SetStatement(
        Token(TokenType.KW_SET, "Set", 2, 0), Identifier(Token(TokenType.MISC_IDENT, "result2", 2, 4), "result2"), expr2
    )

    program = Program([stmt, stmt2])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["result1"] is True, "5 should be strictly equal to 5"
    assert vm.globals["result2"] is False, "5 should not be strictly equal to 5.0"


def test_strict_inequality() -> None:
    """Test strict inequality comparison."""
    # Test: 5 is not strictly equal to 5.0 (should be True - different types)
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 1, 0), 5)
    right = FloatLiteral(Token(TokenType.LIT_FLOAT, "5.0", 1, 4), 5.0)
    expr = InfixExpression(
        Token(TokenType.OP_STRICT_NOT_EQ, "is not strictly equal to", 1, 2), "is not strictly equal to", left
    )
    expr.right = right

    stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0), Identifier(Token(TokenType.MISC_IDENT, "result1", 1, 4), "result1"), expr
    )

    # Test: 5 is not strictly equal to 5 (should be False - same type and value)
    left2 = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 2, 0), 5)
    right2 = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 2, 4), 5)
    expr2 = InfixExpression(
        Token(TokenType.OP_STRICT_NOT_EQ, "is not strictly equal to", 2, 2), "is not strictly equal to", left2
    )
    expr2.right = right2

    stmt2 = SetStatement(
        Token(TokenType.KW_SET, "Set", 2, 0), Identifier(Token(TokenType.MISC_IDENT, "result2", 2, 4), "result2"), expr2
    )

    program = Program([stmt, stmt2])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["result1"] is True, "5 should not be strictly equal to 5.0"
    assert vm.globals["result2"] is False, "5 should be strictly equal to 5"


def test_variable_assignment_and_reference() -> None:
    """Test variable assignment and reference."""
    # Set x to 10
    set_stmt = SetStatement(
        Token(TokenType.KW_SET, "Set", 1, 0),
        Identifier(Token(TokenType.MISC_IDENT, "x", 1, 4), "x"),
        WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "10", 1, 9), 10),
    )

    # Set y to x + 5
    x_ref = Identifier(Token(TokenType.MISC_IDENT, "x", 2, 0), "x")
    five = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "5", 2, 4), 5)
    add_expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 2, 2), "+", x_ref)
    add_expr.right = five

    set_y = SetStatement(
        Token(TokenType.KW_SET, "Set", 2, 0), Identifier(Token(TokenType.MISC_IDENT, "y", 2, 4), "y"), add_expr
    )

    program = Program([set_stmt, set_y])

    vm = VM()
    module = compile_program(program)
    vm.run(module)

    assert vm.globals["x"] == 10
    assert vm.globals["y"] == 15


def test_disassembler() -> None:
    """Test the disassembler output."""
    # Create simple program: 2 + 3
    left = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 0), 2)
    right = WholeNumberLiteral(Token(TokenType.LIT_WHOLE_NUMBER, "3", 1, 4), 3)
    expr = InfixExpression(Token(TokenType.OP_PLUS, "+", 1, 2), "+", left)
    expr.right = right
    stmt = ExpressionStatement(Token(TokenType.LIT_WHOLE_NUMBER, "2", 1, 0), expr)
    program = Program([stmt])

    # Compile without optimization to ensure ADD instruction is generated
    module = compile_program(program, optimize=False)

    # Disassemble and check output
    output = disassemble_chunk(module.main_chunk)

    # Should contain these instructions
    assert "LOAD_CONST" in output
    assert "ADD" in output
    assert "POP" in output

    # Should show constant values
    assert "; 2" in output
    assert "; 3" in output
