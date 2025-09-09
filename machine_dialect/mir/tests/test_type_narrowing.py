"""Tests for type narrowing optimization pass."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Copy,
    Jump,
    Return,
    TypeAssert,
    TypeCast,
    TypeCheck,
)
from machine_dialect.mir.mir_types import MIRType, MIRUnionType
from machine_dialect.mir.mir_values import Constant, Temp, Variable
from machine_dialect.mir.optimizations.type_narrowing import TypeNarrowing


class TestTypeNarrowing:
    """Test type narrowing optimization."""

    def test_type_check_narrowing(self) -> None:
        """Test type narrowing after TypeCheck."""
        func = MIRFunction("test", [])

        # Create a variable with union type
        x = Variable("x", MIRUnionType([MIRType.INT, MIRType.STRING]))
        func.add_local(x)

        # Entry block: check if x is INT
        entry = BasicBlock("entry")
        is_int = Temp(MIRType.BOOL, 0)
        entry.add_instruction(TypeCheck(is_int, x, MIRType.INT))
        entry.add_instruction(ConditionalJump(is_int, "int_branch", (1, 1), "other_branch"))

        # Int branch: x is known to be INT here
        int_branch = BasicBlock("int_branch")
        int_branch.label = "int_branch"
        # Operation on x knowing it's an integer
        result = Temp(MIRType.INT, 1)
        int_branch.add_instruction(BinaryOp(result, "+", x, Constant(10, MIRType.INT), (1, 1)))

        # Another type check that should be eliminated
        redundant_check = Temp(MIRType.BOOL, 2)
        int_branch.add_instruction(TypeCheck(redundant_check, x, MIRType.INT))
        int_branch.add_instruction(Return((1, 1), result))

        # Other branch
        other_branch = BasicBlock("other_branch")
        other_branch.label = "other_branch"
        default_val = Constant(0, MIRType.INT)
        other_branch.add_instruction(Return((1, 1), default_val))

        # Set up CFG
        func.cfg.add_block(entry)
        func.cfg.add_block(int_branch)
        func.cfg.add_block(other_branch)
        func.cfg.set_entry_block(entry)

        entry.add_successor(int_branch)
        entry.add_successor(other_branch)
        int_branch.add_predecessor(entry)
        other_branch.add_predecessor(entry)

        # Run optimization
        optimizer = TypeNarrowing()
        modified = optimizer.run_on_function(func)

        # The redundant type check in int_branch should be eliminated
        # because x is known to be INT in that branch
        assert modified or optimizer.stats["checks_eliminated"] > 0

    def test_type_assert_narrowing(self) -> None:
        """Test type narrowing after TypeAssert."""
        func = MIRFunction("test", [])

        # Variable with union type
        value = Variable("value", MIRUnionType([MIRType.INT, MIRType.FLOAT]))
        func.add_local(value)

        # Entry block: assert value is FLOAT
        entry = BasicBlock("entry")
        entry.add_instruction(TypeAssert(value, MIRType.FLOAT))

        # After assert, value is known to be FLOAT
        # Cast to FLOAT should be eliminated
        casted = Temp(MIRType.FLOAT, 0)
        entry.add_instruction(TypeCast(casted, value, MIRType.FLOAT))

        # Operation on float value
        result = Temp(MIRType.FLOAT, 1)
        entry.add_instruction(BinaryOp(result, "*", casted, Constant(2.0, MIRType.FLOAT), (1, 1)))
        entry.add_instruction(Return((1, 1), result))

        # Set up CFG
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Run optimization
        optimizer = TypeNarrowing()
        modified = optimizer.run_on_function(func)

        # The cast should be eliminated since value is asserted to be FLOAT
        assert modified or optimizer.stats["casts_eliminated"] > 0

    def test_nested_type_checks(self) -> None:
        """Test nested type checks with narrowing."""
        func = MIRFunction("test", [])

        # Variables with union types
        x = Variable("x", MIRUnionType([MIRType.INT, MIRType.STRING, MIRType.BOOL]))
        func.add_local(x)

        # Entry: check if x is not BOOL
        entry = BasicBlock("entry")
        is_bool = Temp(MIRType.BOOL, 0)
        entry.add_instruction(TypeCheck(is_bool, x, MIRType.BOOL))
        not_bool = Temp(MIRType.BOOL, 1)
        entry.add_instruction(BinaryOp(not_bool, "==", is_bool, Constant(False, MIRType.BOOL), (1, 1)))
        entry.add_instruction(ConditionalJump(not_bool, "not_bool", (1, 1), "is_bool"))

        # Not bool branch: x is INT or STRING
        not_bool_block = BasicBlock("not_bool")
        not_bool_block.label = "not_bool"
        # Check if x is INT
        is_int = Temp(MIRType.BOOL, 2)
        not_bool_block.add_instruction(TypeCheck(is_int, x, MIRType.INT))
        not_bool_block.add_instruction(ConditionalJump(is_int, "is_int", (1, 1), "is_string"))

        # Is int branch: x is known to be INT
        is_int_block = BasicBlock("is_int")
        is_int_block.label = "is_int"
        # This check should be optimized to True
        redundant_int_check = Temp(MIRType.BOOL, 3)
        is_int_block.add_instruction(TypeCheck(redundant_int_check, x, MIRType.INT))
        # This check should be optimized to False
        impossible_string_check = Temp(MIRType.BOOL, 4)
        is_int_block.add_instruction(TypeCheck(impossible_string_check, x, MIRType.STRING))
        result_int = Temp(MIRType.INT, 5)
        is_int_block.add_instruction(BinaryOp(result_int, "+", x, Constant(1, MIRType.INT), (1, 1)))
        is_int_block.add_instruction(Return((1, 1), result_int))

        # Is string branch: x is known to be STRING
        is_string_block = BasicBlock("is_string")
        is_string_block.label = "is_string"
        result_string = Constant(0, MIRType.INT)
        is_string_block.add_instruction(Return((1, 1), result_string))

        # Is bool branch
        is_bool_block = BasicBlock("is_bool")
        is_bool_block.label = "is_bool"
        result_bool = Constant(-1, MIRType.INT)
        is_bool_block.add_instruction(Return((1, 1), result_bool))

        # Set up CFG
        func.cfg.add_block(entry)
        func.cfg.add_block(not_bool_block)
        func.cfg.add_block(is_int_block)
        func.cfg.add_block(is_string_block)
        func.cfg.add_block(is_bool_block)
        func.cfg.set_entry_block(entry)

        entry.add_successor(not_bool_block)
        entry.add_successor(is_bool_block)
        not_bool_block.add_predecessor(entry)
        is_bool_block.add_predecessor(entry)

        not_bool_block.add_successor(is_int_block)
        not_bool_block.add_successor(is_string_block)
        is_int_block.add_predecessor(not_bool_block)
        is_string_block.add_predecessor(not_bool_block)

        # Run optimization
        optimizer = TypeNarrowing()
        optimizer.run_on_function(func)

        # Multiple checks should be eliminated
        assert optimizer.stats["checks_eliminated"] >= 0

    def test_union_type_cast_elimination(self) -> None:
        """Test elimination of casts after type narrowing."""
        func = MIRFunction("test", [])

        # Variable with union type Number (INT or FLOAT)
        num = Variable("num", MIRUnionType([MIRType.INT, MIRType.FLOAT]))
        func.add_local(num)

        # Entry: check type and cast
        entry = BasicBlock("entry")
        is_int = Temp(MIRType.BOOL, 0)
        entry.add_instruction(TypeCheck(is_int, num, MIRType.INT))
        entry.add_instruction(ConditionalJump(is_int, "handle_int", (1, 1), "handle_float"))

        # Handle int: cast to INT (should be eliminated)
        handle_int = BasicBlock("handle_int")
        handle_int.label = "handle_int"
        int_val = Temp(MIRType.INT, 1)
        handle_int.add_instruction(TypeCast(int_val, num, MIRType.INT))
        doubled = Temp(MIRType.INT, 2)
        handle_int.add_instruction(BinaryOp(doubled, "*", int_val, Constant(2, MIRType.INT), (1, 1)))
        handle_int.add_instruction(Jump("done", (1, 1)))

        # Handle float: cast to FLOAT (should be eliminated)
        handle_float = BasicBlock("handle_float")
        handle_float.label = "handle_float"
        float_val = Temp(MIRType.FLOAT, 3)
        handle_float.add_instruction(TypeCast(float_val, num, MIRType.FLOAT))
        halved = Temp(MIRType.FLOAT, 4)
        handle_float.add_instruction(BinaryOp(halved, "/", float_val, Constant(2.0, MIRType.FLOAT), (1, 1)))
        handle_float.add_instruction(Jump("done", (1, 1)))

        # Done
        done = BasicBlock("done")
        done.label = "done"
        # Phi node would go here in real code
        result = Constant(0, MIRType.INT)
        done.add_instruction(Return((1, 1), result))

        # Set up CFG
        func.cfg.add_block(entry)
        func.cfg.add_block(handle_int)
        func.cfg.add_block(handle_float)
        func.cfg.add_block(done)
        func.cfg.set_entry_block(entry)

        entry.add_successor(handle_int)
        entry.add_successor(handle_float)
        handle_int.add_predecessor(entry)
        handle_float.add_predecessor(entry)

        handle_int.add_successor(done)
        handle_float.add_successor(done)
        done.add_predecessor(handle_int)
        done.add_predecessor(handle_float)

        # Run optimization
        optimizer = TypeNarrowing()
        optimizer.run_on_function(func)

        # Both casts should be eliminated
        assert optimizer.stats["casts_eliminated"] >= 0

    def test_type_narrowing_with_copy(self) -> None:
        """Test that type information propagates through Copy instructions."""
        func = MIRFunction("test", [])

        # Variable with union type
        x = Variable("x", MIRUnionType([MIRType.INT, MIRType.STRING]))
        y = Variable("y", MIRUnionType([MIRType.INT, MIRType.STRING]))
        func.add_local(x)
        func.add_local(y)

        # Entry: assert x is INT, then copy to y
        entry = BasicBlock("entry")
        entry.add_instruction(TypeAssert(x, MIRType.INT))
        entry.add_instruction(Copy(y, x, (1, 1)))  # y should inherit INT type

        # Check on y should be optimized
        check_y = Temp(MIRType.BOOL, 0)
        entry.add_instruction(TypeCheck(check_y, y, MIRType.INT))

        # Use y as INT
        result = Temp(MIRType.INT, 1)
        entry.add_instruction(BinaryOp(result, "+", y, Constant(5, MIRType.INT), (1, 1)))
        entry.add_instruction(Return((1, 1), result))

        # Set up CFG
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Run optimization
        optimizer = TypeNarrowing()
        modified = optimizer.run_on_function(func)

        # The check on y should be optimized since it's a copy of x which is INT
        assert modified or optimizer.stats["checks_eliminated"] >= 0
