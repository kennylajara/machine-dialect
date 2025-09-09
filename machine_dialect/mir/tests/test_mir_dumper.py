"""Tests for MIR dumper utility."""

import sys
from io import StringIO

from machine_dialect.mir.basic_block import BasicBlock
from machine_dialect.mir.mir_dumper import (
    ColorCode,
    DumpVerbosity,
    MIRDumper,
    dump_mir,
)
from machine_dialect.mir.mir_function import MIRFunction
from machine_dialect.mir.mir_instructions import (
    BinaryOp,
    LoadConst,
    Return,
)
from machine_dialect.mir.mir_module import MIRModule
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Constant, Temp, Variable


class TestMIRDumper:
    """Test MIR dumper functionality."""

    def create_test_module(self) -> MIRModule:
        """Create a test MIR module."""
        module = MIRModule("test_module")

        # Create main function
        main_func = MIRFunction("main", return_type=MIRType.INT)

        # Create entry block
        entry_block = BasicBlock("entry")

        # Add instructions
        t0 = Temp(MIRType.INT, 0)
        t1 = Temp(MIRType.INT, 1)
        t2 = Temp(MIRType.INT, 2)

        entry_block.add_instruction(LoadConst(t0, Constant(10, MIRType.INT), (1, 1)))
        entry_block.add_instruction(LoadConst(t1, Constant(20, MIRType.INT), (1, 1)))
        entry_block.add_instruction(BinaryOp(t2, "+", t0, t1, (1, 1)))
        entry_block.add_instruction(Return((1, 1), t2))

        # Set up CFG
        main_func.cfg.add_block(entry_block)
        main_func.cfg.entry_block = entry_block

        module.add_function(main_func)
        return module

    def test_basic_dump(self) -> None:
        """Test basic MIR dumping."""
        module = self.create_test_module()
        dumper = MIRDumper(use_color=False, verbosity=DumpVerbosity.NORMAL)

        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "MIR Module: test_module" in result
        assert "Function main" in result
        assert "entry:" in result
        assert "return" in result.lower()

    def test_dump_with_colors(self) -> None:
        """Test MIR dumping with colors."""
        module = self.create_test_module()

        # Force color output
        original_isatty = sys.stdout.isatty
        sys.stdout.isatty = lambda: True  # type: ignore[method-assign]

        try:
            dumper = MIRDumper(use_color=True, verbosity=DumpVerbosity.NORMAL)
            output = StringIO()
            result = dumper.dump_module(module, output)

            # Check for color codes
            assert ColorCode.CYAN in result or ColorCode.GREEN in result
        finally:
            sys.stdout.isatty = original_isatty  # type: ignore[method-assign]

    def test_verbosity_minimal(self) -> None:
        """Test minimal verbosity level."""
        module = self.create_test_module()
        dumper = MIRDumper(use_color=False, verbosity=DumpVerbosity.MINIMAL)

        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "Function main" in result
        # Minimal verbosity should not include block details
        assert "t0 =" not in result

    def test_verbosity_detailed(self) -> None:
        """Test detailed verbosity level."""
        module = self.create_test_module()
        dumper = MIRDumper(use_color=False, verbosity=DumpVerbosity.DETAILED)

        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "Function main" in result
        assert "entry:" in result

    def test_verbosity_debug(self) -> None:
        """Test debug verbosity level."""
        module = self.create_test_module()
        dumper = MIRDumper(use_color=False, verbosity=DumpVerbosity.DEBUG)

        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "Function main" in result
        assert "entry:" in result

    def test_dump_with_statistics(self) -> None:
        """Test dumping with statistics enabled."""
        module = self.create_test_module()
        dumper = MIRDumper(use_color=False, show_stats=True)

        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "Statistics" in result
        assert "Functions: 1" in result
        assert "Basic Blocks: 1" in result
        assert "Instructions: 4" in result

    def test_dump_with_optimization_stats(self) -> None:
        """Test dumping with optimization statistics."""
        module = self.create_test_module()

        # Add fake optimization stats
        module.optimization_stats = {  # type: ignore[attr-defined]
            "constant-propagation": {
                "constants_propagated": 5,
                "expressions_folded": 2,
            },
            "dce": {
                "dead_instructions_removed": 3,
            },
        }

        dumper = MIRDumper(use_color=False, show_stats=True)

        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "Optimizations Applied:" in result
        assert "constant-propagation:" in result
        assert "constants_propagated: 5" in result

    def test_dump_function(self) -> None:
        """Test dumping a single function."""
        func = MIRFunction("test_func", return_type=MIRType.INT)

        # Create a simple block
        entry = BasicBlock("entry")
        entry.add_instruction(Return((1, 1), Constant(42, MIRType.INT)))
        func.cfg.add_block(entry)
        func.cfg.entry_block = entry

        dumper = MIRDumper(use_color=False)

        output = StringIO()
        result = dumper.dump_function(func, output)

        assert "Function test_func" in result
        assert "entry:" in result
        assert "return 42" in result.lower()

    def test_dump_with_parameters(self) -> None:
        """Test dumping function with parameters."""
        params = [
            Variable("x", MIRType.INT),
            Variable("y", MIRType.INT),
        ]
        func = MIRFunction("add", params=params, return_type=MIRType.INT)

        entry = BasicBlock("entry")
        t0 = Temp(MIRType.INT, 0)
        entry.add_instruction(BinaryOp(t0, "+", params[0], params[1], (1, 1)))
        entry.add_instruction(Return((1, 1), t0))

        func.cfg.add_block(entry)
        func.cfg.entry_block = entry

        dumper = MIRDumper(use_color=False)
        output = StringIO()
        result = dumper.dump_function(func, output)

        assert "Function add" in result
        assert "-> 1" in result  # Return type MIRType.INT has value 1

    def test_dump_with_control_flow(self) -> None:
        """Test dumping with multiple basic blocks."""
        module = MIRModule("cf_test")
        func = MIRFunction("branch_test", return_type=MIRType.INT)

        # Create blocks
        entry = BasicBlock("entry")
        then_block = BasicBlock("then")
        else_block = BasicBlock("else")
        merge = BasicBlock("merge")

        # Add control flow
        entry.add_successor(then_block)
        entry.add_successor(else_block)
        then_block.add_successor(merge)
        else_block.add_successor(merge)

        # Add to CFG
        func.cfg.add_block(entry)
        func.cfg.add_block(then_block)
        func.cfg.add_block(else_block)
        func.cfg.add_block(merge)
        func.cfg.entry_block = entry

        module.add_function(func)

        dumper = MIRDumper(use_color=False)
        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "entry:" in result
        assert "then:" in result
        assert "else:" in result
        assert "merge:" in result

    def test_dump_mir_convenience_function(self) -> None:
        """Test the convenience dump_mir function."""
        module = self.create_test_module()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            dump_mir(module, use_color=False, verbosity="normal")
            output = sys.stdout.getvalue()

            assert "MIR Module: test_module" in output
            assert "Function main" in output
        finally:
            sys.stdout = old_stdout

    def test_dump_with_annotations(self) -> None:
        """Test dumping with annotations enabled."""
        module = self.create_test_module()
        func = module.functions["main"]

        # Add some fake annotations
        if func.cfg.entry_block:
            func.cfg.entry_block.loop_depth = 1  # type: ignore[attr-defined]
            func.cfg.entry_block.frequency = 0.95  # type: ignore[attr-defined]

        dumper = MIRDumper(
            use_color=False,
            verbosity=DumpVerbosity.NORMAL,
            show_annotations=True,
        )

        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "loop depth: 1" in result
        assert "frequency: 0.95" in result

    def test_empty_module(self) -> None:
        """Test dumping an empty module."""
        module = MIRModule("empty")
        dumper = MIRDumper(use_color=False)

        output = StringIO()
        result = dumper.dump_module(module, output)

        assert "MIR Module: empty" in result

    def test_instruction_coloring(self) -> None:
        """Test that different instruction types get colored differently."""
        module = self.create_test_module()

        # Add various instruction types
        func = module.functions["main"]
        if func.cfg.entry_block:
            from machine_dialect.mir.mir_instructions import Call

            # Add a call instruction
            func.cfg.entry_block.add_instruction(
                Call(
                    Temp(MIRType.INT, 10),
                    "helper",
                    [],
                    (1, 1),
                )
            )

        # Force colors
        original_isatty = sys.stdout.isatty
        sys.stdout.isatty = lambda: True  # type: ignore[method-assign]

        try:
            dumper = MIRDumper(use_color=True)
            output = StringIO()
            result = dumper.dump_module(module, output)

            # Different instruction types should have different colors
            assert ColorCode.YELLOW in result or ColorCode.RED in result
        finally:
            sys.stdout.isatty = original_isatty  # type: ignore[method-assign]
