"""Integration tests for list compilation to bytecode.

Tests the full compilation pipeline from source code to bytecode
for list literal types.
"""

from pathlib import Path

from machine_dialect.codegen.register_codegen import generate_bytecode_from_mir
from machine_dialect.compiler.config import CompilerConfig
from machine_dialect.compiler.pipeline import CompilationPipeline


class TestListCompilation:
    """Test compilation of list literals to bytecode."""

    def test_compile_unordered_list(self) -> None:
        """Test compiling an unordered list."""
        source = """
Define `shopping` as unordered list.
Set `shopping` to:
- _"milk"_.
- _"bread"_.
- _"eggs"_.
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        # Create temp file
        test_file = Path("test_unordered.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)

            # Check no errors
            assert not context.has_errors(), f"Compilation errors: {context.errors}"

            # Check MIR was generated
            assert hasattr(context, "mir_module"), "No MIR module generated"
            assert context.mir_module is not None

            # Generate bytecode
            bytecode_module, _metadata = generate_bytecode_from_mir(context.mir_module)

            # Check bytecode was generated
            assert bytecode_module is not None
            serialized = bytecode_module.serialize()
            assert len(serialized) > 0, "No bytecode generated"

            # Verify bytecode contains array creation opcode (0x21 = NEW_ARRAY_R)
            assert b"\x21" in serialized, "No array creation instruction found"

        finally:
            test_file.unlink(missing_ok=True)

    def test_compile_ordered_list(self) -> None:
        """Test compiling an ordered list."""
        source = """
Define `steps` as ordered list.
Set `steps` to:
1. _"First"_.
2. _"Second"_.
3. _"Third"_.
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        test_file = Path("test_ordered.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)

            assert not context.has_errors(), f"Compilation errors: {context.errors}"
            assert hasattr(context, "mir_module")
            assert context.mir_module is not None

            bytecode_module, _metadata = generate_bytecode_from_mir(context.mir_module)
            serialized = bytecode_module.serialize()

            # Check for array creation
            assert b"\x21" in serialized, "No array creation instruction"
            # Check for array set operations (0x23 = ARRAY_SET_R)
            assert b"\x23" in serialized, "No array set instructions"

        finally:
            test_file.unlink(missing_ok=True)

    def test_compile_named_list(self) -> None:
        """Test compiling a named list (dictionary)."""
        source = """
Define `person` as named list.
Set `person` to:
- _"name"_: _"Alice"_.
- _"age"_: _30_.
- _"active"_: _yes_.
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        test_file = Path("test_named.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)

            assert not context.has_errors(), f"Compilation errors: {context.errors}"
            assert hasattr(context, "mir_module")
            assert context.mir_module is not None

            # Check that dictionary operations are generated in MIR
            main_func = context.mir_module.get_function("__main__")
            assert main_func is not None

            # Verify DictCreate instruction exists in MIR
            from machine_dialect.mir.mir_instructions import DictCreate, DictSet

            dict_creates = []
            dict_sets = []
            for block in main_func.cfg.blocks.values():
                for inst in block.instructions:
                    if isinstance(inst, DictCreate):
                        dict_creates.append(inst)
                    elif isinstance(inst, DictSet):
                        dict_sets.append(inst)

            assert len(dict_creates) > 0, "No DictCreate instructions found in MIR"
            assert len(dict_sets) >= 3, "Expected at least 3 DictSet instructions for name, age, and active"

            # TODO: Bytecode generation for dictionary operations not yet implemented
            # Once implemented, the bytecode should contain dictionary creation/set instructions
            # For now, we just verify the MIR is correct

        finally:
            test_file.unlink(missing_ok=True)

    def test_compile_mixed_type_list(self) -> None:
        """Test compiling a list with mixed types."""
        source = """
Define `data` as unordered list.
Set `data` to:
- _42_.
- _"text"_.
- _3.14_.
- _yes_.
- _empty_.
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        test_file = Path("test_mixed.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)

            assert not context.has_errors(), f"Compilation errors: {context.errors}"
            assert context.mir_module is not None

            bytecode_module, _metadata = generate_bytecode_from_mir(context.mir_module)
            serialized = bytecode_module.serialize()

            # Should handle all types
            assert len(serialized) > 50, "Bytecode too small for mixed list"
            assert b"\x21" in serialized, "No array creation"
            assert b"\x23" in serialized, "No array set operations"

        finally:
            test_file.unlink(missing_ok=True)

    def test_compile_nested_lists(self) -> None:
        """Test compiling nested lists."""
        source = """
Define `matrix` as unordered list.
Define `row1` as unordered list.
Define `row2` as unordered list.

Set `row1` to:
- _1_.
- _2_.
- _3_.

Set `row2` to:
- _4_.
- _5_.
- _6_.

Set `matrix` to:
- `row1`.
- `row2`.
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        test_file = Path("test_nested.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)

            assert not context.has_errors(), f"Compilation errors: {context.errors}"
            assert context.mir_module is not None

            bytecode_module, _metadata = generate_bytecode_from_mir(context.mir_module)
            serialized = bytecode_module.serialize()

            # Should have multiple array creations
            array_create_count = serialized.count(b"\x21")
            assert array_create_count >= 3, f"Expected at least 3 arrays, found {array_create_count}"

        finally:
            test_file.unlink(missing_ok=True)

    def test_empty_list_compilation(self) -> None:
        """Test compiling an empty list."""
        source = """
Define `empty_list` as unordered list.
Set `empty_list` to:
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        test_file = Path("test_empty.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)

            # Empty list should compile successfully
            assert not context.has_errors(), f"Compilation errors: {context.errors}"
            assert context.mir_module is not None

            bytecode_module, _metadata = generate_bytecode_from_mir(context.mir_module)
            serialized = bytecode_module.serialize()

            # Should create array with size 0
            assert b"\x21" in serialized, "No array creation"

        finally:
            test_file.unlink(missing_ok=True)

    def test_list_type_mismatch_error(self) -> None:
        """Test that mismatched list types produce an error."""
        source = """
Define `mylist` as unordered list.
Set `mylist` to:
1. _"This is ordered"_
2. _"Not unordered"_
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        test_file = Path("test_mismatch.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)

            # Should have type mismatch error
            assert context.has_errors(), "Should have type mismatch error"
            error_messages = " ".join(context.errors)
            assert "Ordered List" in error_messages or "type" in error_messages.lower()

        finally:
            test_file.unlink(missing_ok=True)


class TestListBytecodeStructure:
    """Test the structure of generated bytecode for lists."""

    def test_bytecode_constants_for_list_elements(self) -> None:
        """Test that list elements are properly stored in constant pool."""
        source = """
Define `nums` as ordered list.
Set `nums` to:
1. _100_.
2. _200_.
3. _300_.
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        test_file = Path("test_constants.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)
            assert not context.has_errors()
            assert context.mir_module is not None

            # Generate bytecode
            bytecode_module, _metadata = generate_bytecode_from_mir(context.mir_module)

            # Check constant pool contains our values
            # Constants are stored as (tag, value) tuples
            constants_values = [val for tag, val in bytecode_module.chunks[0].constants]
            assert 100 in constants_values
            assert 200 in constants_values
            assert 300 in constants_values

            # Also verify bytecode contains array operations
            serialized = bytecode_module.serialize()
            assert b"\x21" in serialized, "No array creation instruction"
            assert b"\x23" in serialized, "No array set operations"

        finally:
            test_file.unlink(missing_ok=True)

    def test_bytecode_constants_all_types(self) -> None:
        """Test that all data types are properly stored in constant pool."""
        source = """
Define `mixed` as unordered list.
Set `mixed` to:
- _"hello world"_.
- _42_.
- _3.14_.
- _yes_.
- _no_.
"""
        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        test_file = Path("test_all_types.md")
        test_file.write_text(source)

        try:
            context = pipeline.compile_file(test_file)
            assert not context.has_errors()
            assert context.mir_module is not None

            bytecode_module, _metadata = generate_bytecode_from_mir(context.mir_module)

            # Check constant pool contains our values
            from machine_dialect.codegen.bytecode_module import ConstantTag

            constants = bytecode_module.chunks[0].constants

            # Extract values by type
            strings = [val for tag, val in constants if tag == ConstantTag.STRING]
            ints = [val for tag, val in constants if tag == ConstantTag.INT]
            floats = [val for tag, val in constants if tag == ConstantTag.FLOAT]
            bools = [val for tag, val in constants if tag == ConstantTag.BOOL]

            # Check all values are in the pool
            assert "hello world" in strings, f"String not in pool. Strings: {strings}"
            assert 42 in ints, f"Integer not in pool. Ints: {ints}"
            assert 3.14 in floats, f"Float not in pool. Floats: {floats}"
            assert True in bools, f"True not in pool. Bools: {bools}"
            assert False in bools, f"False not in pool. Bools: {bools}"

        finally:
            test_file.unlink(missing_ok=True)

    def test_bytecode_size_scaling(self) -> None:
        """Test that bytecode size scales with list size."""
        # Small list
        small_source = """
Define `small` as unordered list.
Set `small` to:
- _1_.
- _2_.
"""
        # Large list
        large_items = "\n".join([f"- _{i}_." for i in range(20)])
        large_source = f"""
Define `large` as unordered list.
Set `large` to:
{large_items}
"""

        config = CompilerConfig(verbose=False)
        pipeline = CompilationPipeline(config)

        # Compile small list
        test_file = Path("test_size.md")
        test_file.write_text(small_source)
        context = pipeline.compile_file(test_file)
        assert not context.has_errors()
        assert context.mir_module is not None
        small_bytecode, _ = generate_bytecode_from_mir(context.mir_module)
        small_size = len(small_bytecode.serialize())

        # Compile large list
        test_file.write_text(large_source)
        context = pipeline.compile_file(test_file)
        assert not context.has_errors()
        assert context.mir_module is not None
        large_bytecode, _ = generate_bytecode_from_mir(context.mir_module)
        large_size = len(large_bytecode.serialize())

        test_file.unlink(missing_ok=True)

        # Large list should generate more bytecode
        assert large_size > small_size * 2, f"Large list ({large_size}) should be much bigger than small ({small_size})"
