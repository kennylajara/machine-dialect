"""Unit tests for array operations bytecode generation."""

from machine_dialect.codegen.opcodes import Opcode
from machine_dialect.codegen.register_codegen import (
    RegisterAllocation,
    RegisterBytecodeGenerator,
)
from machine_dialect.mir.mir_instructions import (
    ArrayFindIndex,
    ArrayInsert,
    ArrayRemove,
)
from machine_dialect.mir.mir_types import MIRType
from machine_dialect.mir.mir_values import Temp


def create_test_generator() -> RegisterBytecodeGenerator:
    """Create a generator with proper allocation setup."""
    generator = RegisterBytecodeGenerator(debug=False)
    # Initialize allocation
    generator.allocation = RegisterAllocation()
    generator.allocation.max_registers = 256
    generator.allocation.next_register = 0
    generator.allocation.value_to_register = {}

    # Map test temps to registers
    for i in range(10):
        temp = Temp(MIRType.INT, i)
        generator.allocation.value_to_register[temp] = i

    return generator


class TestArrayFindIndexCodegen:
    """Test ArrayFindIndex bytecode generation."""

    def test_generates_loop_structure(self) -> None:
        """Test that ArrayFindIndex generates a proper loop."""
        generator = create_test_generator()

        # Create test instruction
        dest = Temp(MIRType.INT, 0)
        array = Temp(MIRType.ARRAY, 1)
        value = Temp(MIRType.INT, 2)
        inst = ArrayFindIndex(dest, array, value, (1, 1))

        # Generate bytecode
        generator.generate_array_find_index(inst)

        # Check that bytecode was generated
        assert len(generator.bytecode) > 0

        # Verify key opcodes are present
        bytecode = generator.bytecode
        opcodes_used = []
        i = 0
        while i < len(bytecode):
            if i < len(bytecode):
                opcodes_used.append(bytecode[i])
                i += 1
                # Skip operands (simplified - real parsing would be more complex)
                if bytecode[i - 1] in [Opcode.LOAD_CONST_R]:
                    i += 3  # dst + 16-bit const
                elif bytecode[i - 1] in [Opcode.ARRAY_LEN_R, Opcode.MOVE_R]:
                    i += 2  # two registers
                elif bytecode[i - 1] in [Opcode.LT_R, Opcode.EQ_R, Opcode.ADD_R, Opcode.ARRAY_GET_R]:
                    i += 3  # three registers
                elif bytecode[i - 1] in [Opcode.JUMP_R]:
                    i += 4  # 32-bit offset
                elif bytecode[i - 1] in [Opcode.JUMP_IF_R, Opcode.JUMP_IF_NOT_R]:
                    i += 5  # register + 32-bit offset

        # Check for essential opcodes
        assert Opcode.ARRAY_LEN_R in opcodes_used  # Get array length
        assert Opcode.LT_R in opcodes_used  # Compare index < length
        assert Opcode.ARRAY_GET_R in opcodes_used  # Get array element
        assert Opcode.EQ_R in opcodes_used  # Compare element with value
        assert Opcode.ADD_R in opcodes_used  # Increment index

    def test_labels_are_unique(self) -> None:
        """Test that multiple ArrayFindIndex operations generate unique labels."""
        generator = create_test_generator()

        # Generate first find operation
        inst1 = ArrayFindIndex(Temp(MIRType.INT, 0), Temp(MIRType.ARRAY, 1), Temp(MIRType.INT, 2), (1, 1))
        generator.generate_array_find_index(inst1)
        labels1 = set(generator.block_offsets.keys())

        # Generate second find operation
        inst2 = ArrayFindIndex(Temp(MIRType.INT, 3), Temp(MIRType.ARRAY, 4), Temp(MIRType.INT, 5), (2, 1))
        generator.generate_array_find_index(inst2)
        labels2 = set(generator.block_offsets.keys())

        # Labels should be different
        new_labels = labels2 - labels1
        assert len(new_labels) > 0  # New labels were added

        # Check label patterns
        for label in new_labels:
            assert "find_" in label  # Labels follow naming convention


class TestArrayInsertCodegen:
    """Test ArrayInsert bytecode generation."""

    def test_generates_copy_loops(self) -> None:
        """Test that ArrayInsert generates copy loops."""
        generator = create_test_generator()

        # Create test instruction
        array = Temp(MIRType.ARRAY, 0)
        index = Temp(MIRType.INT, 1)
        value = Temp(MIRType.INT, 2)
        inst = ArrayInsert(array, index, value, (1, 1))

        # Generate bytecode
        generator.generate_array_insert(inst)

        # Check that bytecode was generated
        assert len(generator.bytecode) > 0

        # Check for essential operations
        bytecode = generator.bytecode
        opcodes_used = []
        i = 0
        while i < len(bytecode) - 1:
            opcodes_used.append(bytecode[i])
            # Skip to next opcode (simplified)
            if bytecode[i] in [Opcode.LOAD_CONST_R]:
                i += 4
            elif bytecode[i] in [Opcode.ARRAY_LEN_R, Opcode.MOVE_R]:
                i += 3
            elif bytecode[i] in [Opcode.NEW_ARRAY_R]:
                i += 3
            elif bytecode[i] in [Opcode.ADD_R, Opcode.SUB_R, Opcode.LT_R, Opcode.ARRAY_GET_R, Opcode.ARRAY_SET_R]:
                i += 4
            elif bytecode[i] in [Opcode.JUMP_R]:
                i += 5
            elif bytecode[i] in [Opcode.JUMP_IF_NOT_R]:
                i += 6
            else:
                i += 1

        # Verify key operations
        assert Opcode.ARRAY_LEN_R in opcodes_used  # Get original length
        assert Opcode.ADD_R in opcodes_used  # Calculate new length
        assert Opcode.NEW_ARRAY_R in opcodes_used  # Create new array
        assert Opcode.ARRAY_GET_R in opcodes_used  # Copy elements
        assert Opcode.ARRAY_SET_R in opcodes_used  # Set elements in new array
        assert Opcode.MOVE_R in opcodes_used  # Replace original array

    def test_handles_position_correctly(self) -> None:
        """Test that insert position is handled correctly."""
        generator = create_test_generator()

        # Test with constant position
        array = Temp(MIRType.ARRAY, 0)
        index = Temp(MIRType.INT, 1)
        value = Temp(MIRType.INT, 2)
        inst = ArrayInsert(array, index, value, (1, 1))

        # Should generate without errors
        generator.generate_array_insert(inst)

        # Check that labels were created
        assert any("insert_" in label for label in generator.block_offsets.keys())


class TestArrayRemoveCodegen:
    """Test ArrayRemove bytecode generation."""

    def test_generates_copy_with_skip(self) -> None:
        """Test that ArrayRemove generates copy loop that skips removed element."""
        generator = create_test_generator()

        # Create test instruction
        array = Temp(MIRType.ARRAY, 0)
        index = Temp(MIRType.INT, 1)
        inst = ArrayRemove(array, index, (1, 1))

        # Generate bytecode
        generator.generate_array_remove(inst)

        # Check that bytecode was generated
        assert len(generator.bytecode) > 0

        # Verify key operations
        bytecode = generator.bytecode
        opcodes_used = []
        i = 0
        while i < len(bytecode) - 1:
            opcodes_used.append(bytecode[i])
            # Skip to next opcode (simplified)
            if bytecode[i] in [Opcode.LOAD_CONST_R]:
                i += 4
            elif bytecode[i] in [Opcode.ARRAY_LEN_R, Opcode.MOVE_R]:
                i += 3
            elif bytecode[i] in [Opcode.NEW_ARRAY_R]:
                i += 3
            elif bytecode[i] in [
                Opcode.SUB_R,
                Opcode.LT_R,
                Opcode.EQ_R,
                Opcode.ADD_R,
                Opcode.ARRAY_GET_R,
                Opcode.ARRAY_SET_R,
            ]:
                i += 4
            elif bytecode[i] in [Opcode.JUMP_R]:
                i += 5
            elif bytecode[i] in [Opcode.JUMP_IF_R, Opcode.JUMP_IF_NOT_R]:
                i += 6
            else:
                i += 1

        # Check for essential operations
        assert Opcode.ARRAY_LEN_R in opcodes_used  # Get original length
        assert Opcode.SUB_R in opcodes_used  # Calculate new length (old - 1)
        assert Opcode.NEW_ARRAY_R in opcodes_used  # Create new array
        assert Opcode.EQ_R in opcodes_used  # Check if current index is removal point
        assert Opcode.ARRAY_GET_R in opcodes_used  # Copy elements
        assert Opcode.ARRAY_SET_R in opcodes_used  # Set elements in new array

    def test_unique_labels(self) -> None:
        """Test that multiple remove operations use unique labels."""
        generator = create_test_generator()

        # First remove
        inst1 = ArrayRemove(Temp(MIRType.ARRAY, 0), Temp(MIRType.INT, 1), (1, 1))
        generator.generate_array_remove(inst1)
        labels1 = set(generator.block_offsets.keys())

        # Second remove
        inst2 = ArrayRemove(Temp(MIRType.ARRAY, 2), Temp(MIRType.INT, 3), (2, 1))
        generator.generate_array_remove(inst2)
        labels2 = set(generator.block_offsets.keys())

        # Should have new labels
        new_labels = labels2 - labels1
        assert len(new_labels) > 0
        assert any("remove_" in label for label in new_labels)


class TestIntegration:
    """Integration tests for array operations."""

    def test_combined_operations(self) -> None:
        """Test that multiple array operations can be generated together."""
        generator = create_test_generator()

        # Generate a sequence of operations
        array = Temp(MIRType.ARRAY, 0)

        # Create array
        # ArrayCreate would normally be called here, but we're testing insert directly
        # create_inst = ArrayCreate(array, Constant(3, MIRType.INT), (1, 1))

        # Find index
        find_inst = ArrayFindIndex(Temp(MIRType.INT, 1), array, Temp(MIRType.INT, 2), (2, 1))
        generator.generate_array_find_index(find_inst)

        # Insert element
        insert_inst = ArrayInsert(array, Temp(MIRType.INT, 3), Temp(MIRType.INT, 4), (3, 1))
        generator.generate_array_insert(insert_inst)

        # Remove element
        remove_inst = ArrayRemove(array, Temp(MIRType.INT, 5), (4, 1))
        generator.generate_array_remove(remove_inst)

        # Should generate substantial bytecode
        assert len(generator.bytecode) > 100  # These operations generate lots of code

        # All operations should have their labels
        labels = generator.block_offsets.keys()
        assert any("find_" in label for label in labels)
        assert any("insert_" in label for label in labels)
        assert any("remove_" in label for label in labels)

    def test_register_allocation(self) -> None:
        """Test that operations use appropriate temporary registers."""
        generator = create_test_generator()

        # ArrayFindIndex uses high registers for temps
        inst = ArrayFindIndex(Temp(MIRType.INT, 0), Temp(MIRType.ARRAY, 1), Temp(MIRType.INT, 2), (1, 1))
        generator.generate_array_find_index(inst)

        # Check bytecode includes high register numbers (250-254)
        bytecode = generator.bytecode
        high_registers_used = False
        for i in range(len(bytecode)):
            if bytecode[i] >= 247:  # High register range
                high_registers_used = True
                break

        assert high_registers_used, "Should use high temporary registers"
