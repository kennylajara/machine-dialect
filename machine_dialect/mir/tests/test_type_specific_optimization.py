"""Tests for type-specific MIR optimization pass."""

from machine_dialect.ast import (
    DefineStatement,
    Identifier,
    Program,
    SetStatement,
    WholeNumberLiteral,
)
from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.hir_to_mir import HIRToMIRLowering
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Copy,
    LoadConst,
    UnaryOp,
)
from machine_dialect.mir.mir_types import MIRType, MIRUnionType
from machine_dialect.mir.mir_values import Constant, Temp, Variable
from machine_dialect.mir.optimizations.type_specific import TypeSpecificOptimization


class TestTypeSpecificOptimization:
    """Test type-specific MIR optimization."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.optimizer = TypeSpecificOptimization()
        self.dummy_token = Token(TokenType.KW_DEFINE, "Define", 1, 1)

    def test_integer_constant_folding(self) -> None:
        """Test integer constant folding with type information."""
        # Create a function with integer variables
        func = MIRFunction("test", [])

        # Add typed locals
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add integer arithmetic: result = 5 + 3
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "+", Constant(5, MIRType.INT), Constant(3, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was folded
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value == 8
        assert self.optimizer.stats["constant_folded"] == 1

    def test_float_constant_folding(self) -> None:
        """Test float constant folding with type information."""
        func = MIRFunction("test", [])

        # Create a basic block
        block = BasicBlock("entry")

        # Add float arithmetic: result = 3.14 * 2.0
        result = Temp(MIRType.FLOAT, 0)
        block.add_instruction(
            BinaryOp(result, "*", Constant(3.14, MIRType.FLOAT), Constant(2.0, MIRType.FLOAT), (1, 1))
        )

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was folded
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value == 6.28
        assert self.optimizer.stats["constant_folded"] == 1

    def test_boolean_short_circuit_and_false(self) -> None:
        """Test boolean short-circuit optimization for AND with False."""
        func = MIRFunction("test", [])

        # Create a basic block
        block = BasicBlock("entry")

        # Add boolean operation: result = False and x
        x = Variable("x", MIRType.BOOL)
        result = Temp(MIRType.BOOL, 0)
        block.add_instruction(BinaryOp(result, "and", Constant(False, MIRType.BOOL), x, (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was short-circuited
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value is False
        assert self.optimizer.stats["boolean_optimized"] == 1

    def test_boolean_short_circuit_or_true(self) -> None:
        """Test boolean short-circuit optimization for OR with True."""
        func = MIRFunction("test", [])

        # Create a basic block
        block = BasicBlock("entry")

        # Add boolean operation: result = True or x
        x = Variable("x", MIRType.BOOL)
        result = Temp(MIRType.BOOL, 0)
        block.add_instruction(BinaryOp(result, "or", Constant(True, MIRType.BOOL), x, (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was short-circuited
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value is True

    def test_integer_identity_add_zero(self) -> None:
        """Test integer identity optimization: x + 0 -> x."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x + 0
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "+", x, Constant(0, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was simplified
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], Copy)
        assert block.instructions[0].source == x

    def test_integer_multiply_by_zero(self) -> None:
        """Test integer optimization: x * 0 -> 0."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x * 0
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "*", x, Constant(0, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was simplified
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value == 0

    def test_unary_negation_constant_folding(self) -> None:
        """Test unary negation constant folding."""
        func = MIRFunction("test", [])

        # Create a basic block
        block = BasicBlock("entry")

        # Add unary operation: result = -42
        result = Temp(MIRType.INT, 0)
        block.add_instruction(UnaryOp(result, "-", Constant(42, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was folded
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value == -42

    def test_union_type_handling(self) -> None:
        """Test handling of union types."""
        func = MIRFunction("test", [])

        # Add variable with union type metadata
        x = Variable("x", MIRType.UNKNOWN)
        x.union_type = MIRUnionType([MIRType.INT, MIRType.STRING])
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation with union type variable
        result = Temp(MIRType.UNKNOWN, 0)
        block.add_instruction(BinaryOp(result, "+", x, Constant(1, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization - should not optimize due to unknown runtime type
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was not modified (can't optimize union types)
        assert not modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], BinaryOp)

    def test_string_concatenation_folding(self) -> None:
        """Test string concatenation constant folding."""
        func = MIRFunction("test", [])

        # Create a basic block
        block = BasicBlock("entry")

        # Add string concatenation: result = "Hello, " + "World!"
        result = Temp(MIRType.STRING, 0)
        block.add_instruction(
            BinaryOp(result, "+", Constant("Hello, ", MIRType.STRING), Constant("World!", MIRType.STRING), (1, 1))
        )

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was folded
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value == "Hello, World!"

    def test_comparison_constant_folding(self) -> None:
        """Test comparison operation constant folding."""
        func = MIRFunction("test", [])

        # Create a basic block
        block = BasicBlock("entry")

        # Add comparison: result = 5 < 10
        result = Temp(MIRType.BOOL, 0)
        block.add_instruction(BinaryOp(result, "<", Constant(5, MIRType.INT), Constant(10, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was folded
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value is True

    def test_integration_with_hir_lowering(self) -> None:
        """Test integration with HIR to MIR lowering."""
        # Create a program with type definitions
        program = Program(
            [
                DefineStatement(self.dummy_token, Identifier(self.dummy_token, "x"), ["Whole Number"], None),
                DefineStatement(self.dummy_token, Identifier(self.dummy_token, "y"), ["Whole Number"], None),
                SetStatement(
                    self.dummy_token, Identifier(self.dummy_token, "x"), WholeNumberLiteral(self.dummy_token, 5)
                ),
                SetStatement(
                    self.dummy_token, Identifier(self.dummy_token, "y"), WholeNumberLiteral(self.dummy_token, 10)
                ),
            ]
        )

        # Lower to MIR
        lowering = HIRToMIRLowering()
        mir_module = lowering.lower_program(program)

        # Get the main function
        main_func = mir_module.get_function("__main__")
        assert main_func is not None

        # Check that type information was propagated
        assert "x" in lowering.type_context
        assert lowering.type_context["x"] == MIRType.INT
        assert "y" in lowering.type_context
        assert lowering.type_context["y"] == MIRType.INT

    def test_strength_reduction_multiply_power_of_two(self) -> None:
        """Test strength reduction: x * 8 -> x << 3."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x * 8
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "*", x, Constant(8, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was converted to shift
        assert modified
        assert len(block.instructions) == 1
        from machine_dialect.mir.mir_instructions import ShiftOp

        assert isinstance(block.instructions[0], ShiftOp)
        assert block.instructions[0].op == "<<"
        assert isinstance(block.instructions[0].right, Constant)
        assert block.instructions[0].right.value == 3  # 8 = 2^3

    def test_strength_reduction_divide_power_of_two(self) -> None:
        """Test strength reduction: x / 16 -> x >> 4."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x / 16
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "/", x, Constant(16, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was converted to shift
        assert modified
        assert len(block.instructions) == 1
        from machine_dialect.mir.mir_instructions import ShiftOp

        assert isinstance(block.instructions[0], ShiftOp)
        assert block.instructions[0].op == ">>"
        assert isinstance(block.instructions[0].right, Constant)
        assert block.instructions[0].right.value == 4  # 16 = 2^4

    def test_modulo_power_of_two(self) -> None:
        """Test strength reduction: x % 32 -> x & 31."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x % 32
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "%", x, Constant(32, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was converted to bitwise AND
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], BinaryOp)
        assert block.instructions[0].op == "&"
        assert isinstance(block.instructions[0].right, Constant)
        assert block.instructions[0].right.value == 31  # 32 - 1

    def test_self_subtraction(self) -> None:
        """Test self-operation: x - x -> 0."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x - x
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "-", x, x, (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was simplified
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value == 0

    def test_self_division(self) -> None:
        """Test self-operation: x / x -> 1."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x / x
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "/", x, x, (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was simplified
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value == 1

    def test_self_equality(self) -> None:
        """Test self-comparison: x == x -> True."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x == x
        result = Temp(MIRType.BOOL, 0)
        block.add_instruction(BinaryOp(result, "==", x, x, (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was simplified
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], LoadConst)
        assert block.instructions[0].constant.value is True

    def test_multiply_by_two_to_addition(self) -> None:
        """Test optimization: x * 2 -> x + x."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.INT)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x * 2
        result = Temp(MIRType.INT, 0)
        block.add_instruction(BinaryOp(result, "*", x, Constant(2, MIRType.INT), (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was converted to addition
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], BinaryOp)
        assert block.instructions[0].op == "+"
        assert block.instructions[0].left == x
        assert block.instructions[0].right == x

    def test_boolean_idempotent_and(self) -> None:
        """Test boolean idempotent: x and x -> x."""
        func = MIRFunction("test", [])

        # Add typed local
        x = Variable("x", MIRType.BOOL)
        func.add_local(x)

        # Create a basic block
        block = BasicBlock("entry")

        # Add operation: result = x and x
        result = Temp(MIRType.BOOL, 0)
        block.add_instruction(BinaryOp(result, "and", x, x, (1, 1)))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        # Run optimization
        modified = self.optimizer.run_on_function(func)

        # Check that the operation was simplified
        assert modified
        assert len(block.instructions) == 1
        assert isinstance(block.instructions[0], Copy)
        assert block.instructions[0].source == x
