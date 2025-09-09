"""Tests for MIR printer and dumper."""

from __future__ import annotations

import io

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    Assert,
    BinaryOp,
    ConditionalJump,
    Copy,
    GetAttr,
    Jump,
    LoadConst,
    LoadVar,
    Phi,
    Print,
    Return,
    Scope,
    Select,
    SetAttr,
    StoreVar,
    UnaryOp,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_printer import (
    dump_mir_function,
    dump_mir_module,
    export_cfg_dot,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Variable


class TestMIRPrinter:
    """Test MIR text printer."""

    def test_print_empty_module(self) -> None:
        """Test printing empty module."""
        module = MIRModule("empty_module")

        output = dump_mir_module(module)

        assert "Module: empty_module" in output

    def test_print_module_with_functions(self) -> None:
        """Test printing module with multiple functions."""
        module = MIRModule("test_module")

        # Add main function
        main = MIRFunction("main", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        main.cfg.add_block(entry)
        main.cfg.set_entry_block(entry)
        entry.add_instruction(Return((1, 1)))

        # Add helper function with parameters
        param = Variable("x", MIRType.INT)
        helper = MIRFunction("helper", [param], MIRType.INT)
        helper_entry = BasicBlock("entry")
        helper.cfg.add_block(helper_entry)
        helper.cfg.set_entry_block(helper_entry)
        helper_entry.add_instruction(Return((1, 1), param))

        module.add_function(main)
        module.add_function(helper)
        module.set_main_function("main")

        output = dump_mir_module(module)

        assert "Module: test_module" in output
        assert "Function main()" in output
        assert "Function helper(x: INT)" in output
        assert "Main: main" in output

    def test_print_function_with_locals(self) -> None:
        """Test printing function with local variables."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        # Add locals
        x = Variable("x", MIRType.INT)
        y = Variable("y", MIRType.FLOAT)
        func.add_local(x)
        func.add_local(y)

        # Add temporaries
        func.new_temp(MIRType.BOOL)
        func.new_temp(MIRType.STRING)

        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        entry.add_instruction(Return((1, 1)))

        output = dump_mir_function(func)

        assert "Locals:" in output
        assert "x: INT" in output
        assert "y: FLOAT" in output
        assert "Temporaries:" in output

    def test_print_basic_block(self) -> None:
        """Test printing basic blocks with predecessors and successors."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        # Create blocks
        entry = BasicBlock("entry")
        block1 = BasicBlock("block1")
        exit_block = BasicBlock("exit")

        func.cfg.add_block(entry)
        func.cfg.add_block(block1)
        func.cfg.add_block(exit_block)
        func.cfg.set_entry_block(entry)

        func.cfg.connect(entry, block1)
        func.cfg.connect(block1, exit_block)

        # Add instructions
        entry.add_instruction(Jump("block1", (1, 1)))
        block1.add_instruction(Jump("exit", (1, 1)))
        exit_block.add_instruction(Return((1, 1)))

        output = dump_mir_function(func)

        assert "entry:" in output
        assert "block1: (preds: entry)" in output
        assert "exit: (preds: block1)" in output
        assert "// successors: block1" in output

    def test_print_all_instruction_types(self) -> None:
        """Test printing all instruction types."""
        func = MIRFunction("test", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Create various values
        x = Variable("x", MIRType.INT)
        y = Variable("y", MIRType.INT)
        t1 = func.new_temp(MIRType.INT)
        t2 = func.new_temp(MIRType.BOOL)
        Constant(42, MIRType.INT)

        # Add various instructions
        entry.add_instruction(LoadConst(t1, 42, (1, 1)))
        entry.add_instruction(StoreVar(x, t1, (1, 1)))
        entry.add_instruction(LoadVar(t1, x, (1, 1)))
        entry.add_instruction(Copy(y, x, (1, 1)))
        entry.add_instruction(BinaryOp(t1, "+", x, y, (1, 1)))
        entry.add_instruction(UnaryOp(t1, "-", x, (1, 1)))
        entry.add_instruction(Print(x, (1, 1)))
        entry.add_instruction(Assert(t2, (1, 1), "check failed"))
        entry.add_instruction(Scope((1, 1), is_begin=True))
        entry.add_instruction(Scope((1, 1), is_begin=False))
        entry.add_instruction(Select(t1, t2, x, y, (1, 1)))

        # Object operations
        obj = func.new_temp(MIRType.UNKNOWN)
        entry.add_instruction(GetAttr(t1, obj, "field"))
        entry.add_instruction(SetAttr(obj, "field", t1))

        # Control flow
        entry.add_instruction(Jump("next", (1, 1)))

        output = dump_mir_function(func)

        # Check various instruction formats
        assert "const" in output
        assert "store" in output
        assert "load" in output
        assert "print" in output
        assert "assert" in output
        assert "begin_scope" in output
        assert "end_scope" in output
        assert "select" in output
        assert ".field" in output
        assert "goto" in output

    def test_print_phi_nodes(self) -> None:
        """Test printing phi nodes."""
        func = MIRFunction("test", [], MIRType.INT)

        # Create diamond CFG
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge)
        func.cfg.set_entry_block(entry)

        func.cfg.connect(entry, then_block)
        func.cfg.connect(entry, else_block)
        func.cfg.connect(then_block, merge)
        func.cfg.connect(else_block, merge)

        # Add phi node
        result = func.new_temp(MIRType.INT)
        val1 = Constant(1, MIRType.INT)
        val2 = Constant(2, MIRType.INT)
        phi = Phi(result, [(val1, "then"), (val2, "else")], (1, 1))

        merge.add_instruction(phi)
        merge.add_instruction(Return((1, 1), result))

        output = dump_mir_function(func)

        assert "φ(" in output
        assert "1:then" in output
        assert "2:else" in output

    def test_print_value_formatting(self) -> None:
        """Test formatting of different value types."""
        func = MIRFunction("test", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Test different constant types
        entry.add_instruction(LoadConst(func.new_temp(MIRType.INT), 42, (1, 1)))
        entry.add_instruction(LoadConst(func.new_temp(MIRType.STRING), "hello", (1, 1)))
        entry.add_instruction(LoadConst(func.new_temp(MIRType.BOOL), True, (1, 1)))
        entry.add_instruction(LoadConst(func.new_temp(MIRType.BOOL), False, (1, 1)))
        entry.add_instruction(LoadConst(func.new_temp(MIRType.EMPTY), None, (1, 1)))

        output = dump_mir_function(func)

        assert "42" in output
        assert '"hello"' in output
        assert "true" in output
        assert "false" in output
        assert "null" in output

    def test_custom_output_stream(self) -> None:
        """Test printing to custom output stream."""
        func = MIRFunction("test", [], MIRType.EMPTY)
        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)
        entry.add_instruction(Return((1, 1)))

        # Print to custom stream
        output_stream = io.StringIO()
        dump_mir_function(func, output_stream)

        output = output_stream.getvalue()
        assert "Function test" in output


class TestMIRDotExporter:
    """Test MIR DOT format exporter."""

    def test_export_simple_cfg(self) -> None:
        """Test exporting simple CFG to DOT."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        exit_block = BasicBlock("exit")

        func.cfg.add_block(entry)
        func.cfg.add_block(exit_block)
        func.cfg.set_entry_block(entry)
        func.cfg.connect(entry, exit_block)

        entry.add_instruction(Jump("exit", (1, 1)))
        exit_block.add_instruction(Return((1, 1)))

        dot = export_cfg_dot(func)

        assert 'digraph "test"' in dot
        assert "entry" in dot
        assert "exit" in dot
        assert "->" in dot

    def test_export_diamond_cfg(self) -> None:
        """Test exporting diamond CFG with conditional branches."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        # Create diamond
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge)
        func.cfg.set_entry_block(entry)

        func.cfg.connect(entry, then_block)
        func.cfg.connect(entry, else_block)
        func.cfg.connect(then_block, merge)
        func.cfg.connect(else_block, merge)

        # Add conditional jump
        cond = func.new_temp(MIRType.BOOL)
        entry.add_instruction(ConditionalJump(cond, "then", (1, 1), "else"))
        then_block.add_instruction(Jump("merge", (1, 1)))
        else_block.add_instruction(Jump("merge", (1, 1)))
        merge.add_instruction(Return((1, 1)))

        dot = export_cfg_dot(func)

        # Check for labeled edges
        assert '[label="true"]' in dot
        assert '[label="false"]' in dot

        # Check entry block is marked differently
        assert "lightgreen" in dot  # Entry block color

    def test_export_with_many_instructions(self) -> None:
        """Test exporting blocks with many instructions."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Add many instructions
        for i in range(10):
            t = func.new_temp(MIRType.INT)
            entry.add_instruction(LoadConst(t, i, (1, 1)))

        entry.add_instruction(Return((1, 1)))

        dot = export_cfg_dot(func)

        # Should truncate and show count
        assert "more)" in dot

    def test_export_loop_cfg(self) -> None:
        """Test exporting CFG with loop (back edge)."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        loop_header = BasicBlock("loop_header")
        loop_body = BasicBlock("loop_body")
        exit_block = BasicBlock("exit")

        func.cfg.add_block(entry)
        func.cfg.add_block(loop_header)
        func.cfg.add_block(loop_body)
        func.cfg.add_block(exit_block)
        func.cfg.set_entry_block(entry)

        func.cfg.connect(entry, loop_header)
        func.cfg.connect(loop_header, loop_body)
        func.cfg.connect(loop_header, exit_block)
        func.cfg.connect(loop_body, loop_header)  # Back edge

        entry.add_instruction(Jump("loop_header", (1, 1)))

        cond = func.new_temp(MIRType.BOOL)
        loop_header.add_instruction(ConditionalJump(cond, "loop_body", (1, 1), "exit"))

        loop_body.add_instruction(Jump("loop_header", (1, 1)))
        exit_block.add_instruction(Return((1, 1)))

        dot = export_cfg_dot(func)

        # Check all edges exist
        assert dot.count("->") >= 4  # At least 4 edges

    def test_export_escapes_quotes(self) -> None:
        """Test that quotes in instructions are properly escaped."""
        func = MIRFunction("test", [], MIRType.EMPTY)

        entry = BasicBlock("entry")
        func.cfg.add_block(entry)
        func.cfg.set_entry_block(entry)

        # Add instruction with quotes
        t = func.new_temp(MIRType.STRING)
        entry.add_instruction(LoadConst(t, 'string with "quotes"', (1, 1)))
        entry.add_instruction(Return((1, 1)))

        dot = export_cfg_dot(func)

        # Should escape quotes properly
        assert '\\"' in dot
