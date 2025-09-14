"""Tests for Loop Invariant Code Motion optimization."""

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    ConditionalJump,
    Copy,
    Jump,
    LoadConst,
    Print,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp, Variable
from machine_dialect.mir.pass_manager import PassManager


def create_simple_loop_function() -> MIRFunction:
    """Create a function with a simple loop containing invariant code.

    Equivalent to:
    def simple_loop(n):
        i = 0
        while i < n:
            x = 10      # Loop invariant
            y = x * 2   # Loop invariant
            z = i + y   # Not invariant (depends on i)
            i = i + 1
        return z
    """
    func = MIRFunction("simple_loop", [Variable("n", MIRType.INT)])

    # Create blocks
    entry = func.cfg.get_or_create_block("entry")
    loop_header = func.cfg.get_or_create_block("loop_header")
    loop_body = func.cfg.get_or_create_block("loop_body")
    loop_exit = func.cfg.get_or_create_block("loop_exit")

    # Set entry block
    func.cfg.entry_block = entry

    # Entry block: i = 0
    i_var = Variable("i", MIRType.INT)
    n_var = Variable("n", MIRType.INT)
    entry.instructions = [
        LoadConst(i_var, Constant(0), (1, 1)),
        Jump("loop_header", (1, 1)),
    ]
    func.cfg.connect(entry, loop_header)

    # Loop header: if i < n goto body else exit
    cond_temp = Temp(MIRType.BOOL, 0)
    loop_header.instructions = [
        BinaryOp(cond_temp, "<", i_var, n_var, (1, 1)),
        ConditionalJump(cond_temp, "loop_body", (1, 1), "loop_exit"),
    ]
    func.cfg.connect(loop_header, loop_body)
    func.cfg.connect(loop_header, loop_exit)

    # Loop body: x = 10, y = x * 2, z = i + y, i = i + 1
    x_var = Variable("x", MIRType.INT)
    y_var = Variable("y", MIRType.INT)
    z_var = Variable("z", MIRType.INT)
    i_plus_one = Temp(MIRType.INT, 1)
    loop_body.instructions = [
        LoadConst(x_var, Constant(10), (1, 1)),  # Invariant
        BinaryOp(y_var, "*", x_var, Constant(2), (1, 1)),  # Invariant
        BinaryOp(z_var, "+", i_var, y_var, (1, 1)),  # Not invariant
        BinaryOp(i_plus_one, "+", i_var, Constant(1), (1, 1)),
        Copy(i_var, i_plus_one, (1, 1)),
        Jump("loop_header", (1, 1)),
    ]
    func.cfg.connect(loop_body, loop_header)

    # Loop exit: return z
    loop_exit.instructions = [Return((1, 1), z_var)]

    return func


def create_nested_loop_function() -> MIRFunction:
    """Create a function with nested loops and invariant code.

    Equivalent to:
    def nested_loops(n, m):
        result = 0
        for i in range(n):
            x = n * 2  # Invariant to inner loop
            for j in range(m):
                y = m * 3  # Invariant to inner loop
                z = x + y  # Invariant to inner loop
                result = result + z + i + j
        return result
    """
    func = MIRFunction("nested_loops", [Variable("n", MIRType.INT), Variable("m", MIRType.INT)])

    # Create blocks
    entry = func.cfg.get_or_create_block("entry")
    outer_header = func.cfg.get_or_create_block("outer_header")
    outer_body = func.cfg.get_or_create_block("outer_body")
    inner_header = func.cfg.get_or_create_block("inner_header")
    inner_body = func.cfg.get_or_create_block("inner_body")
    inner_exit = func.cfg.get_or_create_block("inner_exit")
    outer_exit = func.cfg.get_or_create_block("outer_exit")

    # Variables
    n_var = Variable("n", MIRType.INT)
    m_var = Variable("m", MIRType.INT)
    i_var = Variable("i", MIRType.INT)
    j_var = Variable("j", MIRType.INT)
    x_var = Variable("x", MIRType.INT)
    y_var = Variable("y", MIRType.INT)
    z_var = Variable("z", MIRType.INT)
    result_var = Variable("result", MIRType.INT)

    # Set entry block
    func.cfg.entry_block = entry

    # Entry: result = 0, i = 0
    entry.instructions = [
        LoadConst(result_var, Constant(0), (1, 1)),
        LoadConst(i_var, Constant(0), (1, 1)),
        Jump("outer_header", (1, 1)),
    ]
    func.cfg.connect(entry, outer_header)

    # Outer header: if i < n goto outer_body else outer_exit
    outer_cond = Temp(MIRType.BOOL, 10)
    outer_header.instructions = [
        BinaryOp(outer_cond, "<", i_var, n_var, (1, 1)),
        ConditionalJump(outer_cond, "outer_body", (1, 1), "outer_exit"),
    ]
    func.cfg.connect(outer_header, outer_body)
    func.cfg.connect(outer_header, outer_exit)

    # Outer body: x = n * 2, j = 0
    outer_body.instructions = [
        BinaryOp(x_var, "*", n_var, Constant(2), (1, 1)),  # Invariant to inner loop
        LoadConst(j_var, Constant(0), (1, 1)),
        Jump("inner_header", (1, 1)),
    ]
    func.cfg.connect(outer_body, inner_header)

    # Inner header: if j < m goto inner_body else inner_exit
    inner_cond = Temp(MIRType.BOOL, 11)
    inner_header.instructions = [
        BinaryOp(inner_cond, "<", j_var, m_var, (1, 1)),
        ConditionalJump(inner_cond, "inner_body", (1, 1), "inner_exit"),
    ]
    func.cfg.connect(inner_header, inner_body)
    func.cfg.connect(inner_header, inner_exit)

    # Inner body: y = m * 3, z = x + y, result = result + z + i + j, j = j + 1
    temp1 = Temp(MIRType.INT, 12)
    temp2 = Temp(MIRType.INT, 13)
    temp3 = Temp(MIRType.INT, 14)
    j_plus_one = Temp(MIRType.INT, 16)
    inner_body.instructions = [
        BinaryOp(y_var, "*", m_var, Constant(3), (1, 1)),  # Invariant
        BinaryOp(z_var, "+", x_var, y_var, (1, 1)),  # Invariant
        BinaryOp(temp1, "+", result_var, z_var, (1, 1)),
        BinaryOp(temp2, "+", temp1, i_var, (1, 1)),
        BinaryOp(temp3, "+", temp2, j_var, (1, 1)),
        Copy(result_var, temp3, (1, 1)),
        BinaryOp(j_plus_one, "+", j_var, Constant(1), (1, 1)),
        Copy(j_var, j_plus_one, (1, 1)),
        Jump("inner_header", (1, 1)),
    ]
    func.cfg.connect(inner_body, inner_header)

    # Inner exit: i = i + 1, goto outer_header
    i_plus_one = Temp(MIRType.INT, 17)
    inner_exit.instructions = [
        BinaryOp(i_plus_one, "+", i_var, Constant(1), (1, 1)),
        Copy(i_var, i_plus_one, (1, 1)),
        Jump("outer_header", (1, 1)),
    ]
    func.cfg.connect(inner_exit, outer_header)

    # Outer exit: return result
    outer_exit.instructions = [Return((1, 1), result_var)]

    return func


def create_loop_with_side_effects() -> MIRFunction:
    """Create a loop with side effects that shouldn't be hoisted.

    Equivalent to:
    def loop_with_side_effects(n):
        i = 0
        while i < n:
            x = 10          # Invariant
            print(x)        # Side effect - don't hoist
            y = x * 2       # Invariant but after side effect
            i = i + 1
        return i
    """
    func = MIRFunction("loop_with_side_effects", [Variable("n", MIRType.INT)])

    # Create blocks
    entry = func.cfg.get_or_create_block("entry")
    loop_header = func.cfg.get_or_create_block("loop_header")
    loop_body = func.cfg.get_or_create_block("loop_body")
    loop_exit = func.cfg.get_or_create_block("loop_exit")

    # Variables
    i_var = Variable("i", MIRType.INT)
    n_var = Variable("n", MIRType.INT)
    x_var = Variable("x", MIRType.INT)
    y_var = Variable("y", MIRType.INT)

    # Set entry block
    func.cfg.entry_block = entry

    # Entry block
    entry.instructions = [
        LoadConst(i_var, Constant(0), (1, 1)),
        Jump("loop_header", (1, 1)),
    ]
    func.cfg.connect(entry, loop_header)

    # Loop header
    cond_temp = Temp(MIRType.BOOL, 20)
    loop_header.instructions = [
        BinaryOp(cond_temp, "<", i_var, n_var, (1, 1)),
        ConditionalJump(cond_temp, "loop_body", (1, 1), "loop_exit"),
    ]
    func.cfg.connect(loop_header, loop_body)
    func.cfg.connect(loop_header, loop_exit)

    # Loop body
    i_plus_one = Temp(MIRType.INT, 21)
    loop_body.instructions = [
        LoadConst(x_var, Constant(10), (1, 1)),  # Invariant
        Print(x_var, (1, 1)),  # Side effect - don't hoist
        BinaryOp(y_var, "*", x_var, Constant(2), (1, 1)),  # Invariant but after print
        BinaryOp(i_plus_one, "+", i_var, Constant(1), (1, 1)),
        Copy(i_var, i_plus_one, (1, 1)),
        Jump("loop_header", (1, 1)),
    ]
    func.cfg.connect(loop_body, loop_header)

    # Loop exit
    loop_exit.instructions = [Return((1, 1), i_var)]

    return func


class TestLICM:
    """Test suite for LICM optimization."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.pass_manager = PassManager()
        # Register all passes including dependencies
        from machine_dialect.mir.optimizations import register_all_passes

        register_all_passes(self.pass_manager)

    def test_simple_loop_hoisting(self) -> None:
        """Test hoisting invariant code from a simple loop."""
        func = create_simple_loop_function()
        module = MIRModule("test")
        module.functions[func.name] = func

        # Set up and run LICM with proper analysis manager
        from machine_dialect.mir.tests.test_optimization_helpers import run_optimization_with_analyses

        modified = run_optimization_with_analyses(
            self.pass_manager,
            "licm",
            func,
            required_analyses=["dominance", "loop-analysis", "use-def-chains"],
        )

        assert modified, "LICM should modify the function"

        # Check that invariant instructions were hoisted
        # Either a new preheader was created or entry block is used as preheader
        # First, check if instructions were actually hoisted by looking at the loop body
        loop_body = None
        for block in func.cfg.blocks.values():
            if "loop_body" in block.label:
                loop_body = block
                break

        assert loop_body is not None, "Loop body should exist"

        # Check if the invariant instructions are still in the loop body
        # If LICM worked, they should have been removed
        loop_has_load_const_10 = any(
            isinstance(inst, LoadConst) and hasattr(inst.constant, "value") and inst.constant.value == 10
            for inst in loop_body.instructions
        )
        from machine_dialect.mir.mir_values import Constant as ConstantValue

        loop_has_mult = any(
            isinstance(inst, BinaryOp)
            and inst.op == "*"
            and isinstance(inst.right, ConstantValue)
            and inst.right.value == 2
            for inst in loop_body.instructions
        )

        # If LICM worked, these should NOT be in the loop body anymore
        assert not loop_has_load_const_10, (
            f"LoadConst(10) should be removed from loop body, instructions: {loop_body.instructions}"
        )
        assert not loop_has_mult, (
            f"BinaryOp(*) should be removed from loop body, instructions: {loop_body.instructions}"
        )

        # Check statistics from the actual instance that ran
        if hasattr(self.pass_manager, "_last_run_pass"):
            licm = self.pass_manager._last_run_pass
            stats = licm.get_statistics()
            assert stats["hoisted"] >= 2, "At least 2 instructions should be hoisted"
            assert stats["loops_processed"] >= 1, "At least 1 loop should be processed"

    def test_nested_loop_hoisting(self) -> None:
        """Test hoisting from nested loops."""
        func = create_nested_loop_function()
        module = MIRModule("test")
        module.functions[func.name] = func

        # Run LICM with proper analysis setup
        from machine_dialect.mir.tests.test_optimization_helpers import run_optimization_with_analyses

        modified = run_optimization_with_analyses(
            self.pass_manager,
            "licm",
            func,
            required_analyses=["dominance", "loop-analysis", "use-def-chains"],
        )

        assert modified, "LICM should modify nested loops"

        # Check that some instructions were hoisted
        if hasattr(self.pass_manager, "_last_run_pass"):
            licm = self.pass_manager._last_run_pass
            stats = licm.get_statistics()
            assert stats["hoisted"] > 0, "Instructions should be hoisted from inner loop"
            assert stats["loops_processed"] >= 1, "At least inner loop should be processed"

    def test_side_effects_not_hoisted(self) -> None:
        """Test that instructions with side effects are not hoisted."""
        func = create_loop_with_side_effects()
        module = MIRModule("test")
        module.functions[func.name] = func

        # Run LICM with proper analysis setup
        from machine_dialect.mir.tests.test_optimization_helpers import run_optimization_with_analyses

        run_optimization_with_analyses(
            self.pass_manager,
            "licm",
            func,
            required_analyses=["dominance", "loop-analysis", "use-def-chains"],
        )

        # The function might be modified (preheader creation)
        # but Print should not be hoisted

        # Check that Print is still in loop body
        loop_body = None
        for block in func.cfg.blocks.values():
            if "loop_body" in block.label:
                loop_body = block
                break

        assert loop_body is not None, "Loop body should exist"

        has_print = any(isinstance(inst, Print) for inst in loop_body.instructions)
        assert has_print, "Print should remain in loop body (not hoisted)"

    def test_no_loops_no_modification(self) -> None:
        """Test that functions without loops are not modified."""
        func = MIRFunction("no_loops", [Variable("x", MIRType.INT)])

        # Simple function: return x * 2
        entry = func.cfg.get_or_create_block("entry")
        func.cfg.entry_block = entry
        x_var = Variable("x", MIRType.INT)
        result = Temp(MIRType.INT, 30)
        entry.instructions = [
            BinaryOp(result, "*", x_var, Constant(2), (1, 1)),
            Return((1, 1), result),
        ]

        # Run LICM with proper analysis setup
        from machine_dialect.mir.tests.test_optimization_helpers import run_optimization_with_analyses

        modified = run_optimization_with_analyses(
            self.pass_manager,
            "licm",
            func,
            required_analyses=["dominance", "loop-analysis", "use-def-chains"],
        )

        assert not modified, "Function without loops should not be modified"

        if hasattr(self.pass_manager, "_last_run_pass"):
            licm = self.pass_manager._last_run_pass
            stats = licm.get_statistics()
            assert stats["hoisted"] == 0, "No instructions should be hoisted"
            assert stats["loops_processed"] == 0, "No loops should be processed"

    def test_loop_variant_not_hoisted(self) -> None:
        """Test that loop-variant code is not hoisted."""
        func = MIRFunction("loop_variant", [Variable("n", MIRType.INT)])

        # Create a loop where all computations depend on loop variable
        entry = func.cfg.get_or_create_block("entry")
        header = func.cfg.get_or_create_block("header")
        body = func.cfg.get_or_create_block("body")
        exit_block = func.cfg.get_or_create_block("exit")

        i_var = Variable("i", MIRType.INT)
        n_var = Variable("n", MIRType.INT)
        x_var = Variable("x", MIRType.INT)
        y_var = Variable("y", MIRType.INT)

        # Set entry block
        func.cfg.entry_block = entry

        # Entry
        entry.instructions = [
            LoadConst(i_var, Constant(0), (1, 1)),
            Jump("header", (1, 1)),
        ]
        func.cfg.connect(entry, header)

        # Header
        cond = Temp(MIRType.BOOL, 40)
        header.instructions = [
            BinaryOp(cond, "<", i_var, n_var, (1, 1)),
            ConditionalJump(cond, "body", (1, 1), "exit"),
        ]
        func.cfg.connect(header, body)
        func.cfg.connect(header, exit_block)

        # Body - all depend on i
        i_plus_one = Temp(MIRType.INT, 41)
        body.instructions = [
            BinaryOp(x_var, "*", i_var, Constant(2), (1, 1)),  # Depends on i
            BinaryOp(y_var, "+", x_var, i_var, (1, 1)),  # Depends on i and x
            BinaryOp(i_plus_one, "+", i_var, Constant(1), (1, 1)),
            Copy(i_var, i_plus_one, (1, 1)),
            Jump("header", (1, 1)),
        ]
        func.cfg.connect(body, header)

        # Exit
        exit_block.instructions = [Return((1, 1), y_var)]

        # Run LICM with proper analysis setup
        from machine_dialect.mir.tests.test_optimization_helpers import run_optimization_with_analyses

        run_optimization_with_analyses(
            self.pass_manager,
            "licm",
            func,
            required_analyses=["dominance", "loop-analysis", "use-def-chains"],
        )

        # Check that loop-variant instructions were not hoisted
        if hasattr(self.pass_manager, "_last_run_pass"):
            licm = self.pass_manager._last_run_pass
            stats = licm.get_statistics()
            assert stats["hoisted"] == 0, "No loop-variant instructions should be hoisted"
