"""Tests for MIR TAC instructions."""

from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    Label,
    LoadConst,
    LoadVar,
    Phi,
    Return,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, FunctionRef, Temp, Variable


class TestBinaryOp:
    """Test binary operation instruction."""

    def test_binary_op_creation(self) -> None:
        """Test creating binary operations."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        add_op = BinaryOp(t0, "+", t1, t2, (1, 1))
        assert str(add_op) == "t0 = t1 + t2"
        assert add_op.dest == t0
        assert add_op.op == "+"
        assert add_op.left == t1
        assert add_op.right == t2

    def test_binary_op_uses_and_defs(self) -> None:
        """Test uses and defs for binary operations."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        mul_op = BinaryOp(t0, "*", t1, t2, (1, 1))
        assert mul_op.get_uses(), [t1 == t2]
        assert mul_op.get_defs() == [t0]

    def test_binary_op_replace_use(self) -> None:
        """Test replacing uses in binary operations."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)
        t3 = Temp(MIRType.INT, temp_id=3)

        sub_op = BinaryOp(t0, "-", t1, t2, (1, 1))
        sub_op.replace_use(t1, t3)
        assert sub_op.left == t3
        assert sub_op.right == t2
        assert str(sub_op) == "t0 = t3 - t2"

    def test_comparison_operators(self) -> None:
        """Test comparison operators."""
        t0 = Temp(MIRType.BOOL, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        eq_op = BinaryOp(t0, "==", t1, t2, (1, 1))
        assert str(eq_op) == "t0 = t1 == t2"

        lt_op = BinaryOp(t0, "<", t1, t2, (1, 1))
        assert str(lt_op) == "t0 = t1 < t2"

        ge_op = BinaryOp(t0, ">=", t1, t2, (1, 1))
        assert str(ge_op) == "t0 = t1 >= t2"


class TestUnaryOp:
    """Test unary operation instruction."""

    def test_unary_op_creation(self) -> None:
        """Test creating unary operations."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)

        neg_op = UnaryOp(t0, "-", t1, (1, 1))
        assert str(neg_op) == "t0 = - t1"
        assert neg_op.dest == t0
        assert neg_op.op == "-"
        assert neg_op.operand == t1

    def test_unary_op_uses_and_defs(self) -> None:
        """Test uses and defs for unary operations."""
        t0 = Temp(MIRType.BOOL, temp_id=0)
        t1 = Temp(MIRType.BOOL, temp_id=1)

        not_op = UnaryOp(t0, "not", t1, (1, 1))
        assert not_op.get_uses() == [t1]
        assert not_op.get_defs() == [t0]

    def test_unary_op_replace_use(self) -> None:
        """Test replacing uses in unary operations."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        neg_op = UnaryOp(t0, "-", t1, (1, 1))
        neg_op.replace_use(t1, t2)
        assert neg_op.operand == t2
        assert str(neg_op) == "t0 = - t2"


class TestCopy:
    """Test copy instruction."""

    def test_copy_creation(self) -> None:
        """Test creating copy instructions."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)

        copy = Copy(t0, t1, (1, 1))
        assert str(copy) == "t0 = t1"
        assert copy.dest == t0
        assert copy.source == t1

    def test_copy_with_constant(self) -> None:
        """Test copy with constant source."""
        t0 = Temp(MIRType.INT, temp_id=0)
        c = Constant(42)

        copy = Copy(t0, c, (1, 1))
        assert str(copy) == "t0 = 42"

    def test_copy_uses_and_defs(self) -> None:
        """Test uses and defs for copy instructions."""
        v = Variable("x", MIRType.INT)
        t = Temp(MIRType.INT, temp_id=0)

        copy = Copy(v, t, (1, 1))
        assert copy.get_uses() == [t]
        assert copy.get_defs() == [v]


class TestLoadConst:
    """Test load constant instruction."""

    def test_load_const_creation(self) -> None:
        """Test creating load constant instructions."""
        t0 = Temp(MIRType.INT, temp_id=0)
        load = LoadConst(t0, 42, (1, 1))

        assert str(load) == "t0 = 42"
        assert load.dest == t0
        assert load.constant.value == 42

    def test_load_const_with_different_types(self) -> None:
        """Test load constant with various types."""
        t0 = Temp(MIRType.FLOAT, temp_id=0)
        t1 = Temp(MIRType.STRING, temp_id=1)
        t2 = Temp(MIRType.BOOL, temp_id=2)

        load_float = LoadConst(t0, 3.14, (1, 1))
        assert str(load_float) == "t0 = 3.14"

        load_str = LoadConst(t1, "hello", (1, 1))
        assert str(load_str) == 't1 = "hello"'

        load_bool = LoadConst(t2, True, (1, 1))
        assert str(load_bool) == "t2 = True"

    def test_load_const_uses_and_defs(self) -> None:
        """Test uses and defs for load constant."""
        t0 = Temp(MIRType.INT, temp_id=0)
        load = LoadConst(t0, 100, (1, 1))

        assert load.get_uses() == []  # Constants are not uses
        assert load.get_defs() == [t0]


class TestLoadVar:
    """Test load variable instruction."""

    def test_load_var_creation(self) -> None:
        """Test creating load variable instructions."""
        t0 = Temp(MIRType.INT, temp_id=0)
        v = Variable("x", MIRType.INT)

        load = LoadVar(t0, v, (1, 1))
        assert str(load) == "t0 = x"
        assert load.dest == t0
        assert load.var == v

    def test_load_var_with_versioned_variable(self) -> None:
        """Test load with SSA versioned variable."""
        t0 = Temp(MIRType.INT, temp_id=0)
        v = Variable("x", MIRType.INT, version=2)

        load = LoadVar(t0, v, (1, 1))
        assert str(load) == "t0 = x.2"

    def test_load_var_uses_and_defs(self) -> None:
        """Test uses and defs for load variable."""
        t0 = Temp(MIRType.INT, temp_id=0)
        v = Variable("counter", MIRType.INT)

        load = LoadVar(t0, v, (1, 1))
        assert load.get_uses() == [v]
        assert load.get_defs() == [t0]


class TestStoreVar:
    """Test store variable instruction."""

    def test_store_var_creation(self) -> None:
        """Test creating store variable instructions."""
        v = Variable("x", MIRType.INT)
        t0 = Temp(MIRType.INT, temp_id=0)

        store = StoreVar(v, t0, (1, 1))
        assert str(store) == "x = t0"
        assert store.var == v
        assert store.source == t0

    def test_store_var_with_constant(self) -> None:
        """Test store with constant source."""
        v = Variable("count", MIRType.INT)
        c = Constant(10)

        store = StoreVar(v, c, (1, 1))
        assert str(store) == "count = 10"

    def test_store_var_uses_and_defs(self) -> None:
        """Test uses and defs for store variable."""
        v = Variable("result", MIRType.FLOAT)
        t = Temp(MIRType.FLOAT, temp_id=0)

        store = StoreVar(v, t, (1, 1))
        assert store.get_uses() == [t]
        assert store.get_defs() == [v]


class TestCall:
    """Test function call instruction."""

    def test_call_creation(self) -> None:
        """Test creating call instructions."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)
        func = FunctionRef("add")

        call = Call(t0, func, [t1, t2], (1, 1))
        assert str(call), "t0 = call @add(t1 == t2)"
        assert call.dest == t0
        assert call.func == func
        assert call.args, [t1 == t2]

    def test_call_without_return(self) -> None:
        """Test void call without destination."""
        t0 = Temp(MIRType.STRING, temp_id=0)
        func = FunctionRef("print")

        call = Call(None, func, [t0], (1, 1))
        assert str(call) == "call @print(t0)"
        assert call.dest is None

    def test_call_with_string_function_name(self) -> None:
        """Test call with string function name."""
        t0 = Temp(MIRType.INT, temp_id=0)
        call = Call(t0, "factorial", [Constant(5)], (1, 1))
        assert str(call) == "t0 = call @factorial(5)"
        assert isinstance(call.func, FunctionRef)

    def test_call_uses_and_defs(self) -> None:
        """Test uses and defs for call instructions."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        call = Call(t0, "max", [t1, t2], (1, 1))
        assert call.get_uses(), [t1 == t2]
        assert call.get_defs() == [t0]

        void_call = Call(None, "print", [t1], (1, 1))
        assert void_call.get_uses() == [t1]
        assert void_call.get_defs() == []

    def test_call_replace_use(self) -> None:
        """Test replacing argument values."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)
        t3 = Temp(MIRType.INT, temp_id=3)

        call = Call(t0, "compute", [t1, t2], (1, 1))
        call.replace_use(t1, t3)
        assert call.args, [t3 == t2]


class TestReturn:
    """Test return instruction."""

    def test_return_with_value(self) -> None:
        """Test return with value."""
        t0 = Temp(MIRType.INT, temp_id=0)
        ret = Return((1, 1), t0)
        assert str(ret) == "return t0"
        assert ret.value == t0

    def test_return_without_value(self) -> None:
        """Test void return."""
        ret = Return((1, 1))
        assert str(ret) == "return"
        assert ret.value is None

    def test_return_uses_and_defs(self) -> None:
        """Test uses and defs for return."""
        t0 = Temp(MIRType.INT, temp_id=0)
        ret = Return((1, 1), t0)
        assert ret.get_uses() == [t0]
        assert ret.get_defs() == []

        void_ret = Return((1, 1))
        assert void_ret.get_uses() == []
        assert void_ret.get_defs() == []


class TestJump:
    """Test unconditional jump instruction."""

    def test_jump_creation(self) -> None:
        """Test creating jump instructions."""
        jump = Jump("loop_start", (1, 1))
        assert str(jump) == "goto loop_start"
        assert jump.label == "loop_start"

    def test_jump_uses_and_defs(self) -> None:
        """Test uses and defs for jump."""
        jump = Jump("exit", (1, 1))
        assert jump.get_uses() == []
        assert jump.get_defs() == []


class TestConditionalJump:
    """Test conditional jump instruction."""

    def test_conditional_jump_with_else(self) -> None:
        """Test conditional jump with else branch."""
        t0 = Temp(MIRType.BOOL, temp_id=0)
        cjump = ConditionalJump(t0, "then_block", (1, 1), "else_block")

        assert str(cjump) == "if t0 goto then_block else else_block"
        assert cjump.condition == t0
        assert cjump.true_label == "then_block"
        assert cjump.false_label == "else_block"

    def test_conditional_jump_without_else(self) -> None:
        """Test conditional jump with fallthrough."""
        t0 = Temp(MIRType.BOOL, temp_id=0)
        cjump = ConditionalJump(t0, "skip", (1, 1))

        assert str(cjump) == "if t0 goto skip"
        assert cjump.true_label == "skip"
        assert cjump.false_label is None

    def test_conditional_jump_uses_and_defs(self) -> None:
        """Test uses and defs for conditional jump."""
        t0 = Temp(MIRType.BOOL, temp_id=0)
        cjump = ConditionalJump(t0, "L1", (1, 1), "L2")

        assert cjump.get_uses() == [t0]
        assert cjump.get_defs() == []

    def test_conditional_jump_replace_use(self) -> None:
        """Test replacing condition value."""
        t0 = Temp(MIRType.BOOL, temp_id=0)
        t1 = Temp(MIRType.BOOL, temp_id=1)
        cjump = ConditionalJump(t0, "L1", (1, 1))

        cjump.replace_use(t0, t1)
        assert cjump.condition == t1


class TestPhi:
    """Test SSA phi node instruction."""

    def test_phi_creation(self) -> None:
        """Test creating phi nodes."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)

        phi = Phi(t0, [(t1, "block1"), (t2, "block2")], (1, 1))
        assert str(phi), "t0 = φ(t1:block1 == t2:block2)"
        assert phi.dest == t0
        assert phi.incoming, [(t1, "block1"), (t2 == "block2")]

    def test_phi_add_incoming(self) -> None:
        """Test adding incoming values to phi node."""
        v = Variable("x", MIRType.INT, version=3)
        v1 = Variable("x", MIRType.INT, version=1)
        v2 = Variable("x", MIRType.INT, version=2)

        phi = Phi(v, [(v1, "entry")], (1, 1))
        phi.add_incoming(v2, "loop")

        assert len(phi.incoming) == 2
        assert phi.incoming[1], v2 == "loop"

    def test_phi_uses_and_defs(self) -> None:
        """Test uses and defs for phi nodes."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        c = Constant(0)

        phi = Phi(t0, [(t1, "loop"), (c, "entry")], (1, 1))
        assert phi.get_uses(), [t1 == c]
        assert phi.get_defs() == [t0]

    def test_phi_replace_use(self) -> None:
        """Test replacing incoming values in phi node."""
        t0 = Temp(MIRType.INT, temp_id=0)
        t1 = Temp(MIRType.INT, temp_id=1)
        t2 = Temp(MIRType.INT, temp_id=2)
        t3 = Temp(MIRType.INT, temp_id=3)

        phi = Phi(t0, [(t1, "L1"), (t2, "L2")], (1, 1))
        phi.replace_use(t1, t3)

        assert phi.incoming[0], t3 == "L1"
        assert phi.incoming[1], t2 == "L2"


class TestLabel:
    """Test label pseudo-instruction."""

    def test_label_creation(self) -> None:
        """Test creating labels."""
        label = Label("loop_start", (1, 1))
        assert str(label) == "loop_start:"
        assert label.name == "loop_start"

    def test_label_uses_and_defs(self) -> None:
        """Test uses and defs for labels."""
        label = Label("exit", (1, 1))
        assert label.get_uses() == []
        assert label.get_defs() == []
