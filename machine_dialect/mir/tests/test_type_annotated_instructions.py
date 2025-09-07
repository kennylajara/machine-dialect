"""Tests for type-annotated MIR instructions."""

from machine_dialect.lexer.tokens import Token, TokenType
from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    LoadConst,
    NarrowType,
    TypeAssert,
    TypeCast,
    TypeCheck,
)
from machine_dialect.mir.mir_types import MIRType, MIRUnionType
from machine_dialect.mir.mir_values import Constant, Temp, Variable


class TestTypeAnnotatedInstructions:
    """Test type-annotated MIR instructions."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.dummy_token = Token(TokenType.KW_SET, "Set", 1, 1)

    def test_type_cast_instruction(self) -> None:
        """Test TypeCast instruction creation and properties."""
        src = Variable("x", MIRType.INT)
        dest = Temp(MIRType.FLOAT, 0)

        cast = TypeCast(dest, src, MIRType.FLOAT)

        assert str(cast) == "t0 = cast(x, float)"
        assert cast.get_uses() == [src]
        assert cast.get_defs() == [dest]
        assert cast.target_type == MIRType.FLOAT

    def test_type_cast_to_union(self) -> None:
        """Test TypeCast to union type."""
        src = Variable("x", MIRType.INT)
        union_type = MIRUnionType([MIRType.INT, MIRType.STRING])
        dest = Temp(union_type, 1)

        cast = TypeCast(dest, src, union_type)

        assert str(cast) == "t1 = cast(x, Union[int, string])"
        assert cast.target_type == union_type

    def test_type_check_instruction(self) -> None:
        """Test TypeCheck instruction creation and properties."""
        var = Variable("x", MIRUnionType([MIRType.INT, MIRType.STRING]))
        result = Temp(MIRType.BOOL, 2)

        check = TypeCheck(result, var, MIRType.INT)

        assert str(check) == "t2 = is_type(x, int)"
        assert check.get_uses() == [var]
        assert check.get_defs() == [result]
        assert check.check_type == MIRType.INT

    def test_type_check_union_type(self) -> None:
        """Test TypeCheck with union type check."""
        var = Variable("y", MIRType.UNKNOWN)
        result = Temp(MIRType.BOOL, 3)
        union_type = MIRUnionType([MIRType.FLOAT, MIRType.BOOL])

        check = TypeCheck(result, var, union_type)

        assert str(check) == "t3 = is_type(y, Union[float, bool])"
        assert check.check_type == union_type

    def test_type_assert_instruction(self) -> None:
        """Test TypeAssert instruction creation and properties."""
        var = Variable("z", MIRType.UNKNOWN)

        assertion = TypeAssert(var, MIRType.STRING)

        assert str(assertion) == "assert_type(z, string)"
        assert assertion.get_uses() == [var]
        assert assertion.get_defs() == []
        assert assertion.assert_type == MIRType.STRING

    def test_type_assert_union(self) -> None:
        """Test TypeAssert with union type."""
        var = Variable("w", MIRType.UNKNOWN)
        union_type = MIRUnionType([MIRType.INT, MIRType.FLOAT])

        assertion = TypeAssert(var, union_type)

        assert str(assertion) == "assert_type(w, Union[int, float])"
        assert assertion.assert_type == union_type

    def test_narrow_type_instruction(self) -> None:
        """Test NarrowType instruction creation and properties."""
        # Variable with union type
        union_var = Variable("u", MIRUnionType([MIRType.INT, MIRType.STRING]))
        # After type check, narrow to specific type
        narrowed = Temp(MIRType.INT, 4)

        narrow = NarrowType(narrowed, union_var, MIRType.INT)

        assert str(narrow) == "t4 = narrow(u, int)"
        assert narrow.get_uses() == [union_var]
        assert narrow.get_defs() == [narrowed]
        assert narrow.narrow_type == MIRType.INT

    def test_replace_use_in_type_cast(self) -> None:
        """Test replacing uses in TypeCast instruction."""
        old_var = Variable("old", MIRType.INT)
        new_var = Variable("new", MIRType.INT)
        dest = Temp(MIRType.FLOAT, 5)

        cast = TypeCast(dest, old_var, MIRType.FLOAT)
        cast.replace_use(old_var, new_var)

        assert cast.value == new_var
        assert str(cast) == "t5 = cast(new, float)"

    def test_replace_use_in_type_check(self) -> None:
        """Test replacing uses in TypeCheck instruction."""
        old_var = Variable("old", MIRType.UNKNOWN)
        new_var = Variable("new", MIRType.UNKNOWN)
        result = Temp(MIRType.BOOL, 6)

        check = TypeCheck(result, old_var, MIRType.STRING)
        check.replace_use(old_var, new_var)

        assert check.value == new_var
        assert str(check) == "t6 = is_type(new, string)"

    def test_replace_use_in_type_assert(self) -> None:
        """Test replacing uses in TypeAssert instruction."""
        old_var = Variable("old", MIRType.UNKNOWN)
        new_var = Variable("new", MIRType.UNKNOWN)

        assertion = TypeAssert(old_var, MIRType.BOOL)
        assertion.replace_use(old_var, new_var)

        assert assertion.value == new_var
        assert str(assertion) == "assert_type(new, bool)"

    def test_replace_use_in_narrow_type(self) -> None:
        """Test replacing uses in NarrowType instruction."""
        old_var = Variable("old", MIRUnionType([MIRType.INT, MIRType.FLOAT]))
        new_var = Variable("new", MIRUnionType([MIRType.INT, MIRType.FLOAT]))
        dest = Temp(MIRType.INT, 7)

        narrow = NarrowType(dest, old_var, MIRType.INT)
        narrow.replace_use(old_var, new_var)

        assert narrow.value == new_var
        assert str(narrow) == "t7 = narrow(new, int)"

    def test_type_cast_in_basic_block(self) -> None:
        """Test adding TypeCast instruction to a basic block."""
        func = MIRFunction("test", [])
        block = BasicBlock("entry")

        # Create a cast from int to float
        int_var = Variable("x", MIRType.INT)
        float_temp = Temp(MIRType.FLOAT, 8)

        block.add_instruction(LoadConst(int_var, Constant(42, MIRType.INT), (1, 1)))
        block.add_instruction(TypeCast(float_temp, int_var, MIRType.FLOAT))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        assert len(block.instructions) == 2
        assert isinstance(block.instructions[0], LoadConst)
        assert isinstance(block.instructions[1], TypeCast)

    def test_type_narrowing_flow(self) -> None:
        """Test typical type narrowing flow with type check and narrow."""
        func = MIRFunction("test", [])
        block = BasicBlock("entry")

        # Variable with union type
        union_var = Variable("v", MIRUnionType([MIRType.INT, MIRType.STRING]))

        # Check if it's an int
        is_int = Temp(MIRType.BOOL, 9)
        block.add_instruction(TypeCheck(is_int, union_var, MIRType.INT))

        # If check passes, narrow to int
        narrowed_int = Temp(MIRType.INT, 10)
        block.add_instruction(NarrowType(narrowed_int, union_var, MIRType.INT))

        func.cfg.add_block(block)
        func.cfg.set_entry_block(block)

        assert len(block.instructions) == 2
        assert isinstance(block.instructions[0], TypeCheck)
        assert isinstance(block.instructions[1], NarrowType)
