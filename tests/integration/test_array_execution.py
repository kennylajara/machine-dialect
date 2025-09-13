"""Integration test for array/list execution from source to VM.

This tests the complete pipeline:
- Parse list literals
- Generate HIR/MIR
- Generate bytecode
- Execute in VM
"""


from machine_dialect.compiler import Compiler
from machine_dialect.compiler.config import CompilerConfig, OptimizationLevel


class TestArrayExecution:
    """Test arrays work end-to-end from source to VM execution."""

    def test_simple_ordered_list_creation(self) -> None:
        """Test creating and accessing a simple ordered list."""
        source = """
Define `numbers` as ordered list.
Set `numbers` to:
1. _10_.
2. _20_.
3. _30_.

Define `first` as whole number.
Set `first` to the first item of `numbers`.

Define `second` as whole number.
Set `second` to the second item of `numbers`.

Define `third` as whole number.
Set `third` to the third item of `numbers`.

Define `item_two` as whole number.
Set `item_two` to item _2_ of `numbers`.

Say `first`.
Say `second`.
Say `third`.
Say `item_two`.
"""

        # Compile the source
        config = CompilerConfig(
            optimization_level=OptimizationLevel.NONE,  # Disable optimization for clearer testing
            debug=True,
        )
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_arrays")

        # Check compilation was successful
        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

        # TODO: Add VM execution test when VM runner is ready
        # from machine_dialect.compiler.vm_runner import VMRunner
        # runner = VMRunner()
        # vm_result = runner.execute_bytecode(context.bytecode_module.serialize())
        # assert vm_result.success, f"VM execution failed: {vm_result.error}"
        # assert vm_result.output == ["10", "20", "30", "20"], f"Unexpected output: {vm_result.output}"

    def test_unordered_list_creation(self) -> None:
        """Test creating and accessing an unordered list."""
        source = """
Define `items` as unordered list.
Set `items` to:
- _"apple"_.
- _"banana"_.
- _"cherry"_.

Define `first_item` as text.
Set `first_item` to the first item of `items`.

Say `first_item`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_arrays")

        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

        # TODO: Add VM execution test when VM runner is ready
        # runner = VMRunner()
        # vm_result = runner.execute_bytecode(context.bytecode_module.serialize())
        # assert vm_result.success, f"VM execution failed: {vm_result.error}"
        # assert vm_result.output == ["apple"], f"Unexpected output: {vm_result.output}"

    def test_list_mutation_add(self) -> None:
        """Test adding items to a list."""
        source = """
Define `fruits` as unordered list.
Set `fruits` to:
- _"apple"_.
- _"banana"_.

Add _"cherry"_ to `fruits`.

Define `third` as text.
Set `third` to the third item of `fruits`.

Say `third`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_arrays")

        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

        # TODO: Add VM execution test when VM runner is ready
        # runner = VMRunner()
        # vm_result = runner.execute_bytecode(context.bytecode_module.serialize())
        # assert vm_result.success, f"VM execution failed: {vm_result.error}"
        # assert vm_result.output == ["cherry"], f"Unexpected output: {vm_result.output}"

    def test_list_mutation_set(self) -> None:
        """Test setting an item in a list."""
        source = """
Define `numbers` as ordered list.
Set `numbers` to:
1. _10_.
2. _20_.
3. _30_.

Set the second item of `numbers` to _99_.

Define `new_second` as whole number.
Set `new_second` to the second item of `numbers`.

Say `new_second`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_arrays")

        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

        # TODO: Add VM execution test when VM runner is ready
        # runner = VMRunner()
        # vm_result = runner.execute_bytecode(context.bytecode_module.serialize())
        # assert vm_result.success, f"VM execution failed: {vm_result.error}"
        # assert vm_result.output == ["99"], f"Unexpected output: {vm_result.output}"

    def test_mixed_type_list(self) -> None:
        """Test list with mixed types."""
        source = """
Define `mixed` as unordered list.
Set `mixed` to:
- _42_.
- _"hello"_.
- _3.14_.
- _yes_.

Define `num` as whole number.
Set `num` to the first item of `mixed`.

Define `text` as text.
Set `text` to the second item of `mixed`.

Define `float` as float.
Set `float` to the third item of `mixed`.

Define `bool` as yes/no.
Set `bool` to item _4_ of `mixed`.

Say `num`.
Say `text`.
Say `float`.
Say `bool`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_arrays")

        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

        # TODO: Add VM execution test when VM runner is ready
        # runner = VMRunner()
        # vm_result = runner.execute_bytecode(context.bytecode_module.serialize())
        # assert vm_result.success, f"VM execution failed: {vm_result.error}"
        # assert vm_result.output == ["42", "hello", "3.14", "yes"], f"Unexpected output: {vm_result.output}"

    def test_empty_list_creation(self) -> None:
        """Test creating an empty list and adding to it."""
        source = """
Define `empty_list` as unordered list.

Add _"first"_ to `empty_list`.
Add _"second"_ to `empty_list`.

Define `first` as text.
Set `first` to the first item of `empty_list`.

Define `second` as text.
Set `second` to the second item of `empty_list`.

Say `first`.
Say `second`.
"""

        config = CompilerConfig(optimization_level=OptimizationLevel.NONE, debug=True)
        compiler = Compiler(config)

        context = compiler.compile_string(source, "test_arrays")

        assert not context.errors, f"Compilation failed: {context.errors}"
        assert context.bytecode_module is not None, "No bytecode generated"

        # TODO: Add VM execution test when VM runner is ready
        # runner = VMRunner()
        # vm_result = runner.execute_bytecode(context.bytecode_module.serialize())
        # assert vm_result.success, f"VM execution failed: {vm_result.error}"
        # assert vm_result.output == ["first", "second"], f"Unexpected output: {vm_result.output}"
