"""Tests for function inlining optimization."""

from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    Call,
    ConditionalJump,
    Copy,
    Jump,
    MIRInstruction,
    Return,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, MIRValue, Temp, Variable
from machine_dialect.mir.optimizations.inlining import FunctionInlining, InliningCost


def create_simple_module() -> MIRModule:
    """Create a module with simple functions for inlining tests.

    Contains:
    - add(a, b): Simple function that returns a + b
    - multiply(x, y): Simple function that returns x * y
    - compute(n): Calls add and multiply
    """
    module = MIRModule("test_module")

    # Create add function: return a + b
    add_func = MIRFunction("add", [Variable("a", MIRType.INT), Variable("b", MIRType.INT)])
    add_entry = add_func.cfg.get_or_create_block("entry")
    a_var = Variable("a", MIRType.INT)
    b_var = Variable("b", MIRType.INT)
    result = Temp(MIRType.INT, 0)
    add_entry.instructions = [
        BinaryOp(result, "+", a_var, b_var, (1, 1)),
        Return((1, 1), result),
    ]
    module.functions["add"] = add_func

    # Create multiply function: return x * y
    mul_func = MIRFunction("multiply", [Variable("x", MIRType.INT), Variable("y", MIRType.INT)])
    mul_entry = mul_func.cfg.get_or_create_block("entry")
    x_var = Variable("x", MIRType.INT)
    y_var = Variable("y", MIRType.INT)
    result2 = Temp(MIRType.INT, 1)
    mul_entry.instructions = [
        BinaryOp(result2, "*", x_var, y_var, (1, 1)),
        Return((1, 1), result2),
    ]
    module.functions["multiply"] = mul_func

    # Create compute function that calls add and multiply
    compute_func = MIRFunction("compute", [Variable("n", MIRType.INT)])
    compute_entry = compute_func.cfg.get_or_create_block("entry")
    n_var = Variable("n", MIRType.INT)
    sum_result = Temp(MIRType.INT, 10)
    prod_result = Temp(MIRType.INT, 11)
    final_result = Temp(MIRType.INT, 12)
    compute_entry.instructions = [
        Call(sum_result, "add", [n_var, Constant(10)], (1, 1)),
        Call(prod_result, "multiply", [sum_result, Constant(2)], (1, 1)),
        BinaryOp(final_result, "+", prod_result, Constant(5), (1, 1)),
        Return((1, 1), final_result),
    ]
    module.functions["compute"] = compute_func

    return module


def create_conditional_module() -> MIRModule:
    """Create a module with conditional functions.

    Contains:
    - abs(x): Returns absolute value with conditional
    - max(a, b): Returns maximum with conditional
    - process(x, y): Calls abs and max
    """
    module = MIRModule("conditional_module")

    # Create abs function
    abs_func = MIRFunction("abs", [Variable("x", MIRType.INT)])
    entry = abs_func.cfg.get_or_create_block("entry")
    positive = abs_func.cfg.get_or_create_block("positive")
    negative = abs_func.cfg.get_or_create_block("negative")
    exit_block = abs_func.cfg.get_or_create_block("exit")

    x_var = Variable("x", MIRType.INT)
    is_negative = Temp(MIRType.BOOL, 20)
    neg_x = Temp(MIRType.INT, 21)
    result_var = Variable("result", MIRType.INT)

    # Entry: check if x < 0
    entry.instructions = [
        BinaryOp(is_negative, "<", x_var, Constant(0), (1, 1)),
        ConditionalJump(is_negative, "negative", (1, 1), "positive"),
    ]
    abs_func.cfg.connect(entry, negative)
    abs_func.cfg.connect(entry, positive)

    # Negative branch: result = -x
    negative.instructions = [
        UnaryOp(neg_x, "-", x_var, (1, 1)),
        Copy(result_var, neg_x, (1, 1)),
        Jump("exit", (1, 1)),
    ]
    abs_func.cfg.connect(negative, exit_block)

    # Positive branch: result = x
    positive.instructions = [
        Copy(result_var, x_var, (1, 1)),
        Jump("exit", (1, 1)),
    ]
    abs_func.cfg.connect(positive, exit_block)

    # Exit: return result
    exit_block.instructions = [Return((1, 1), result_var)]

    module.functions["abs"] = abs_func

    # Create process function that calls abs
    process_func = MIRFunction("process", [Variable("x", MIRType.INT)])
    process_entry = process_func.cfg.get_or_create_block("entry")
    x_param = Variable("x", MIRType.INT)
    abs_result = Temp(MIRType.INT, 30)
    doubled = Temp(MIRType.INT, 31)
    process_entry.instructions = [
        Call(abs_result, "abs", [x_param], (1, 1)),
        BinaryOp(doubled, "*", abs_result, Constant(2), (1, 1)),
        Return((1, 1), doubled),
    ]
    module.functions["process"] = process_func

    return module


def create_large_function_module() -> MIRModule:
    """Create a module with a large function that shouldn't be inlined."""
    module = MIRModule("large_module")

    # Create a large function with many instructions
    large_func = MIRFunction("large_func", [Variable("x", MIRType.INT)])
    entry = large_func.cfg.get_or_create_block("entry")
    x_var = Variable("x", MIRType.INT)

    instructions: list[MIRInstruction] = []
    current: MIRValue = x_var
    for i in range(100):  # Create 100 instructions
        temp = Temp(MIRType.INT, 100 + i)
        instructions.append(BinaryOp(temp, "+", current, Constant(i), (1, 1)))
        current = temp
    instructions.append(Return((1, 1), current))
    entry.instructions = instructions

    module.functions["large_func"] = large_func

    # Create caller
    caller_func = MIRFunction("caller", [Variable("n", MIRType.INT)])
    caller_entry = caller_func.cfg.get_or_create_block("entry")
    n_var = Variable("n", MIRType.INT)
    result = Temp(MIRType.INT, 500)
    caller_entry.instructions = [
        Call(result, "large_func", [n_var], (1, 1)),
        Return((1, 1), result),
    ]
    module.functions["caller"] = caller_func

    return module


def create_recursive_module() -> MIRModule:
    """Create a module with recursive function."""
    module = MIRModule("recursive_module")

    # Create factorial function (recursive)
    fact_func = MIRFunction("factorial", [Variable("n", MIRType.INT)])
    entry = fact_func.cfg.get_or_create_block("entry")
    base_case = fact_func.cfg.get_or_create_block("base_case")
    recursive_case = fact_func.cfg.get_or_create_block("recursive_case")

    n_var = Variable("n", MIRType.INT)
    is_base = Temp(MIRType.BOOL, 40)
    n_minus_one = Temp(MIRType.INT, 41)
    recursive_result = Temp(MIRType.INT, 42)
    final_result = Temp(MIRType.INT, 43)

    # Entry: check if n <= 1
    entry.instructions = [
        BinaryOp(is_base, "<=", n_var, Constant(1), (1, 1)),
        ConditionalJump(is_base, "base_case", (1, 1), "recursive_case"),
    ]
    fact_func.cfg.connect(entry, base_case)
    fact_func.cfg.connect(entry, recursive_case)

    # Base case: return 1
    base_case.instructions = [Return((1, 1), Constant(1))]

    # Recursive case: return n * factorial(n-1)
    recursive_case.instructions = [
        BinaryOp(n_minus_one, "-", n_var, Constant(1), (1, 1)),
        Call(recursive_result, "factorial", [n_minus_one], (1, 1)),
        BinaryOp(final_result, "*", n_var, recursive_result, (1, 1)),
        Return((1, 1), final_result),
    ]

    module.functions["factorial"] = fact_func

    return module


class TestInliningCost:
    """Test the inlining cost model."""

    def test_small_function_always_inlined(self) -> None:
        """Test that small functions are always inlined."""
        cost = InliningCost(
            instruction_count=3,
            call_site_benefit=5.0,
            size_threshold=50,
            depth=0,
        )
        assert cost.should_inline()

    def test_large_function_not_inlined(self) -> None:
        """Test that large functions are not inlined."""
        cost = InliningCost(
            instruction_count=100,
            call_site_benefit=10.0,
            size_threshold=50,
            depth=0,
        )
        assert not cost.should_inline()

    def test_deep_recursion_prevented(self) -> None:
        """Test that deep inlining is prevented."""
        cost = InliningCost(
            instruction_count=5,
            call_site_benefit=20.0,
            size_threshold=50,
            depth=5,  # Too deep
        )
        assert not cost.should_inline()

    def test_cost_benefit_analysis(self) -> None:
        """Test cost-benefit analysis for medium functions."""
        # High benefit should inline
        cost_high_benefit = InliningCost(
            instruction_count=20,
            call_site_benefit=25.0,
            size_threshold=50,
            depth=1,
        )
        assert cost_high_benefit.should_inline()

        # Low benefit should not inline
        cost_low_benefit = InliningCost(
            instruction_count=20,
            call_site_benefit=15.0,
            size_threshold=50,
            depth=1,
        )
        assert not cost_low_benefit.should_inline()


class TestFunctionInlining:
    """Test suite for function inlining."""

    def test_simple_inlining(self) -> None:
        """Test inlining of simple functions."""
        module = create_simple_module()
        inliner = FunctionInlining(size_threshold=50)

        # Run inlining
        modified = inliner.run_on_module(module)
        assert modified, "Module should be modified"

        # Check statistics
        stats = inliner.get_statistics()
        assert stats["inlined"] >= 2, "Should inline add and multiply calls"
        assert stats["call_sites_processed"] >= 2

        # Check that compute function has inlined code
        compute_func = module.functions["compute"]
        has_add_op = False
        has_mul_op = False
        for block in compute_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, BinaryOp):
                    if inst.op == "+":
                        has_add_op = True
                    elif inst.op == "*":
                        has_mul_op = True

        assert has_add_op, "Add operation should be inlined"
        assert has_mul_op, "Multiply operation should be inlined"

    def test_conditional_inlining(self) -> None:
        """Test inlining of functions with conditionals."""
        module = create_conditional_module()
        inliner = FunctionInlining(size_threshold=50)

        # Run inlining
        modified = inliner.run_on_module(module)
        assert modified, "Module should be modified"

        # Check that process function has inlined abs
        process_func = module.functions["process"]

        # Should have conditional jump from inlined abs
        has_conditional = False
        for block in process_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, ConditionalJump):
                    has_conditional = True
                    break

        assert has_conditional, "Conditional from abs should be inlined"

        # Check statistics
        stats = inliner.get_statistics()
        assert stats["inlined"] >= 1, "Should inline abs call"

    def test_large_function_not_inlined(self) -> None:
        """Test that large functions are not inlined."""
        module = create_large_function_module()
        inliner = FunctionInlining(size_threshold=50)

        # Run inlining
        modified = inliner.run_on_module(module)
        assert not modified, "Large function should not be inlined"

        # Check that call remains
        caller_func = module.functions["caller"]
        has_call = False
        for block in caller_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, Call):
                    has_call = True
                    break

        assert has_call, "Call to large function should remain"

        # Check statistics
        stats = inliner.get_statistics()
        assert stats["inlined"] == 0, "No functions should be inlined"

    def test_recursive_not_directly_inlined(self) -> None:
        """Test that recursive functions are not directly inlined."""
        module = create_recursive_module()
        inliner = FunctionInlining(size_threshold=50)

        # Run inlining
        inliner.run_on_module(module)

        # The recursive call should not be inlined into itself
        fact_func = module.functions["factorial"]
        has_recursive_call = False
        for block in fact_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, Call) and inst.func.name == "factorial":
                    has_recursive_call = True
                    break

        assert has_recursive_call, "Recursive call should not be inlined"

    def test_constant_propagation_benefit(self) -> None:
        """Test that constant arguments increase inlining benefit."""
        module = MIRModule("const_module")

        # Create simple function
        simple_func = MIRFunction("simple", [Variable("x", MIRType.INT)])
        entry = simple_func.cfg.get_or_create_block("entry")
        x_var = Variable("x", MIRType.INT)
        result = Temp(MIRType.INT, 60)
        entry.instructions = [
            BinaryOp(result, "*", x_var, Constant(2), (1, 1)),
            Return((1, 1), result),
        ]
        module.functions["simple"] = simple_func

        # Create caller with constant argument
        caller_func = MIRFunction("caller", [])
        caller_entry = caller_func.cfg.get_or_create_block("entry")
        call_result = Temp(MIRType.INT, 61)
        caller_entry.instructions = [
            Call(call_result, "simple", [Constant(5)], (1, 1)),  # Constant argument
            Return((1, 1), call_result),
        ]
        module.functions["caller"] = caller_func

        # Run inlining
        inliner = FunctionInlining(size_threshold=10)
        modified = inliner.run_on_module(module)

        assert modified, "Function with constant argument should be inlined"

        # Check that the call was inlined
        caller_func = module.functions["caller"]
        has_call = False
        has_binary_op = False
        for block in caller_func.cfg.blocks.values():
            for inst in block.instructions:
                if isinstance(inst, Call):
                    has_call = True
                elif isinstance(inst, BinaryOp):
                    has_binary_op = True

        assert not has_call, "Call should be inlined"
        assert has_binary_op, "Binary operation should be present"

    def test_no_functions_to_inline(self) -> None:
        """Test module with no inlinable functions."""
        module = MIRModule("empty_module")

        # Single function with no calls
        func = MIRFunction("no_calls", [Variable("x", MIRType.INT)])
        entry = func.cfg.get_or_create_block("entry")
        x_var = Variable("x", MIRType.INT)
        result = Temp(MIRType.INT, 70)
        entry.instructions = [
            BinaryOp(result, "*", x_var, Constant(2), (1, 1)),
            Return((1, 1), result),
        ]
        module.functions["no_calls"] = func

        # Run inlining
        inliner = FunctionInlining()
        modified = inliner.run_on_module(module)

        assert not modified, "Module should not be modified"

        stats = inliner.get_statistics()
        assert stats["inlined"] == 0
        assert stats["call_sites_processed"] == 0
