"""Tests for tail call optimization."""

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import Call, Copy, Return
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp, Variable
from machine_dialect.mir.optimizations.tail_call import TailCallOptimization


def test_simple_tail_call() -> None:
    """Test detection of simple tail call pattern."""
    # Create a function with a tail call
    module = MIRModule("test")
    func = MIRFunction("factorial", [Variable("n", MIRType.INT)])
    module.add_function(func)

    # Create basic block with tail call pattern
    block = BasicBlock("entry")

    # result = call factorial(n-1)
    result = Temp(MIRType.INT, 0)
    call_inst = Call(result, "factorial", [Variable("n", MIRType.INT)], (1, 1))
    block.add_instruction(call_inst)

    # return result
    block.add_instruction(Return((1, 1), result))

    func.cfg.add_block(block)
    func.cfg.entry_block = block

    # Run optimization
    optimizer = TailCallOptimization()
    modified = optimizer.run_on_module(module)

    # Check that the call was marked as tail call
    assert modified
    assert call_inst.is_tail_call
    assert optimizer.stats["tail_calls_found"] == 1
    assert optimizer.stats["recursive_tail_calls"] == 1


def test_tail_call_with_copy() -> None:
    """Test detection of tail call with intermediate copy."""
    module = MIRModule("test")
    func = MIRFunction("process", [Variable("x", MIRType.INT)])
    module.add_function(func)

    block = BasicBlock("entry")

    # temp = call helper(x)
    temp = Temp(MIRType.INT, 0)
    call_inst = Call(temp, "helper", [Variable("x", MIRType.INT)], (1, 1))
    block.add_instruction(call_inst)

    # result = temp
    result = Variable("result", MIRType.INT)
    block.add_instruction(Copy(result, temp, (1, 1)))

    # return result
    block.add_instruction(Return((1, 1), result))

    func.cfg.add_block(block)
    func.cfg.entry_block = block

    # Run optimization
    optimizer = TailCallOptimization()
    modified = optimizer.run_on_module(module)

    # Check that the call was marked as tail call
    assert modified
    assert call_inst.is_tail_call
    assert optimizer.stats["tail_calls_found"] == 1


def test_void_tail_call() -> None:
    """Test detection of void tail call (no return value)."""
    module = MIRModule("test")
    func = MIRFunction("cleanup", [])
    module.add_function(func)

    block = BasicBlock("entry")

    # call finalize()
    call_inst = Call(None, "finalize", [], (1, 1))
    block.add_instruction(call_inst)

    # return
    block.add_instruction(Return((1, 1), None))

    func.cfg.add_block(block)
    func.cfg.entry_block = block

    # Run optimization
    optimizer = TailCallOptimization()
    modified = optimizer.run_on_module(module)

    # Check that the call was marked as tail call
    assert modified
    assert call_inst.is_tail_call
    assert optimizer.stats["tail_calls_found"] == 1


def test_non_tail_call() -> None:
    """Test that non-tail calls are not marked."""
    module = MIRModule("test")
    func = MIRFunction("compute", [Variable("x", MIRType.INT)])
    module.add_function(func)

    block = BasicBlock("entry")

    # temp = call helper(x)
    temp = Temp(MIRType.INT, 0)
    call_inst = Call(temp, "helper", [Variable("x", MIRType.INT)], (1, 1))
    block.add_instruction(call_inst)

    # result = temp + 1 (additional computation after call)
    # We would add a BinaryOp here in real code

    # return something else
    block.add_instruction(Return((1, 1), Constant(42, MIRType.INT)))

    func.cfg.add_block(block)
    func.cfg.entry_block = block

    # Run optimization
    optimizer = TailCallOptimization()
    modified = optimizer.run_on_module(module)

    # Check that the call was NOT marked as tail call
    assert not modified
    assert not call_inst.is_tail_call
    assert optimizer.stats["tail_calls_found"] == 0


def test_multiple_tail_calls() -> None:
    """Test function with multiple tail calls in different blocks."""
    module = MIRModule("test")
    func = MIRFunction("fibonacci", [Variable("n", MIRType.INT)])
    module.add_function(func)

    # Block 1: tail call to fib(n-1)
    block1 = BasicBlock("block1")
    temp1 = Temp(MIRType.INT, 0)
    call1 = Call(temp1, "fibonacci", [Variable("n", MIRType.INT)], (1, 1))
    block1.add_instruction(call1)
    block1.add_instruction(Return((1, 1), temp1))

    # Block 2: tail call to fib(n-2)
    block2 = BasicBlock("block2")
    temp2 = Temp(MIRType.INT, 1)
    call2 = Call(temp2, "fibonacci", [Variable("n", MIRType.INT)], (1, 1))
    block2.add_instruction(call2)
    block2.add_instruction(Return((1, 1), temp2))

    func.cfg.add_block(block1)
    func.cfg.add_block(block2)
    func.cfg.entry_block = block1

    # Run optimization
    optimizer = TailCallOptimization()
    modified = optimizer.run_on_module(module)

    # Check that both calls were marked as tail calls
    assert modified
    assert call1.is_tail_call
    assert call2.is_tail_call
    assert optimizer.stats["tail_calls_found"] == 2
    assert optimizer.stats["recursive_tail_calls"] == 2


def test_mutual_recursion() -> None:
    """Test tail calls in mutually recursive functions."""
    module = MIRModule("test")

    # Function even calls odd
    even_func = MIRFunction("even", [Variable("n", MIRType.INT)])
    even_block = BasicBlock("entry")
    even_result = Temp(MIRType.BOOL, 0)
    even_call = Call(even_result, "odd", [Variable("n", MIRType.INT)], (1, 1))
    even_block.add_instruction(even_call)
    even_block.add_instruction(Return((1, 1), even_result))
    even_func.cfg.add_block(even_block)
    even_func.cfg.entry_block = even_block
    module.add_function(even_func)

    # Function odd calls even
    odd_func = MIRFunction("odd", [Variable("n", MIRType.INT)])
    odd_block = BasicBlock("entry")
    odd_result = Temp(MIRType.BOOL, 1)
    odd_call = Call(odd_result, "even", [Variable("n", MIRType.INT)], (1, 1))
    odd_block.add_instruction(odd_call)
    odd_block.add_instruction(Return((1, 1), odd_result))
    odd_func.cfg.add_block(odd_block)
    odd_func.cfg.entry_block = odd_block
    module.add_function(odd_func)

    # Run optimization
    optimizer = TailCallOptimization()
    modified = optimizer.run_on_module(module)

    # Check that both mutual recursive calls were marked as tail calls
    assert modified
    assert even_call.is_tail_call
    assert odd_call.is_tail_call
    assert optimizer.stats["tail_calls_found"] == 2
    # These are not self-recursive, so recursive count should be 0
    assert optimizer.stats["recursive_tail_calls"] == 0


def test_already_optimized() -> None:
    """Test that already marked tail calls are not counted again."""
    module = MIRModule("test")
    func = MIRFunction("test", [])
    module.add_function(func)

    block = BasicBlock("entry")

    # Create a call already marked as tail call
    result = Temp(MIRType.INT, 0)
    call_inst = Call(result, "helper", [], (1, 1), is_tail_call=True)
    block.add_instruction(call_inst)
    block.add_instruction(Return((1, 1), result))

    func.cfg.add_block(block)
    func.cfg.entry_block = block

    # Run optimization
    optimizer = TailCallOptimization()
    modified = optimizer.run_on_module(module)

    # Check that no modifications were made
    assert not modified
    assert call_inst.is_tail_call  # Still marked
    assert optimizer.stats["tail_calls_found"] == 0  # Not counted as new
