"""Binary serialization for compiled Machine Dialect modules.

This module provides serialization and deserialization of compiled
bytecode modules with proper magic number validation.
"""

import struct
from typing import BinaryIO

from machine_dialect.codegen.constpool import ConstantValue
from machine_dialect.codegen.objects import Chunk, Module

# Magic number: "¾¾Êþ" (BE BE CA FE)
MAGIC_NUMBER = 0xBEBECAFE

# Format version
FORMAT_VERSION = 0x0001

# Flags
FLAG_LITTLE_ENDIAN = 0x0001

# Constant type tags
TAG_INT = 0x01
TAG_FLOAT = 0x02
TAG_STRING = 0x03
TAG_BOOL = 0x04
TAG_NONE = 0x05
TAG_IDENT = 0x06  # Interned identifier


class SerializationError(Exception):
    """Raised when serialization/deserialization fails."""

    pass


class InvalidMagicError(SerializationError):
    """Raised when file has invalid magic number."""

    pass


def serialize_module(module: Module, output: BinaryIO) -> None:
    """Serialize a module to binary format.

    Args:
        module: The module to serialize.
        output: Binary file to write to.

    Raises:
        SerializationError: If serialization fails.
    """
    # Write file header with magic number FIRST (big-endian for correct display)
    output.write(struct.pack(">I", MAGIC_NUMBER))  # Magic number at offset 0 (big-endian)
    output.write(struct.pack("<H", FORMAT_VERSION))  # Version (little-endian)
    output.write(struct.pack("<H", FLAG_LITTLE_ENDIAN))  # Flags (little-endian)

    # Write module name
    name_bytes = module.name.encode("utf-8")
    output.write(struct.pack("<I", len(name_bytes)))
    output.write(name_bytes)

    # Write main chunk (without its own magic number)
    _write_chunk_data(module.main_chunk, output)

    # Write function count
    output.write(struct.pack("<I", len(module.functions)))

    # Write each function chunk
    for name, chunk in module.functions.items():
        # Write function name
        name_bytes = name.encode("utf-8")
        output.write(struct.pack("<I", len(name_bytes)))
        output.write(name_bytes)

        # Write function chunk (without magic number)
        _write_chunk_data(chunk, output)

    # Write metadata count
    output.write(struct.pack("<I", len(module.metadata)))

    # Write metadata
    for key, value in module.metadata.items():
        key_bytes = key.encode("utf-8")
        value_bytes = value.encode("utf-8")
        output.write(struct.pack("<I", len(key_bytes)))
        output.write(key_bytes)
        output.write(struct.pack("<I", len(value_bytes)))
        output.write(value_bytes)


def deserialize_module(input_file: BinaryIO) -> Module:
    """Deserialize a module from binary format.

    Args:
        input_file: Binary file to read from.

    Returns:
        The deserialized module.

    Raises:
        InvalidMagicError: If magic number is invalid.
        SerializationError: If deserialization fails.
    """
    # Read and validate magic number FIRST (at offset 0, big-endian)
    magic_bytes = input_file.read(4)
    if len(magic_bytes) != 4:
        raise SerializationError("Unexpected EOF reading magic number")

    magic = struct.unpack(">I", magic_bytes)[0]
    if magic != MAGIC_NUMBER:
        raise InvalidMagicError(f"Invalid magic number: expected 0x{MAGIC_NUMBER:08X}, got 0x{magic:08X}")

    # Read version and flags
    version_bytes = input_file.read(2)
    if len(version_bytes) != 2:
        raise SerializationError("Unexpected EOF reading version")
    version = struct.unpack("<H", version_bytes)[0]

    if version != FORMAT_VERSION:
        raise SerializationError(f"Unsupported format version: {version:#06x} (expected {FORMAT_VERSION:#06x})")

    flags_bytes = input_file.read(2)
    if len(flags_bytes) != 2:
        raise SerializationError("Unexpected EOF reading flags")
    # flags = struct.unpack("<H", flags_bytes)[0]  # Currently unused

    # Read module name
    name_len_bytes = input_file.read(4)
    if len(name_len_bytes) != 4:
        raise SerializationError("Unexpected EOF reading module name length")
    name_len = struct.unpack("<I", name_len_bytes)[0]

    name_bytes = input_file.read(name_len)
    if len(name_bytes) != name_len:
        raise SerializationError("Unexpected EOF reading module name")
    module_name = name_bytes.decode("utf-8")

    # Read main chunk (without magic number)
    main_chunk = _read_chunk_data(input_file)

    # Create module with main chunk
    module = Module(name=module_name, main_chunk=main_chunk)

    # Read function count
    func_count_bytes = input_file.read(4)
    if len(func_count_bytes) != 4:
        raise SerializationError("Unexpected EOF reading function count")
    func_count = struct.unpack("<I", func_count_bytes)[0]

    # Read functions
    for _ in range(func_count):
        # Read function name
        name_len_bytes = input_file.read(4)
        if len(name_len_bytes) != 4:
            raise SerializationError("Unexpected EOF reading function name length")
        name_len = struct.unpack("<I", name_len_bytes)[0]

        name_bytes = input_file.read(name_len)
        if len(name_bytes) != name_len:
            raise SerializationError("Unexpected EOF reading function name")
        name = name_bytes.decode("utf-8")

        # Read function chunk (without magic number)
        chunk = _read_chunk_data(input_file)
        module.add_function(name, chunk)

    # Read metadata count
    meta_count_bytes = input_file.read(4)
    if len(meta_count_bytes) != 4:
        raise SerializationError("Unexpected EOF reading metadata count")
    meta_count = struct.unpack("<I", meta_count_bytes)[0]

    # Read metadata
    for _ in range(meta_count):
        # Read key
        key_len_bytes = input_file.read(4)
        if len(key_len_bytes) != 4:
            raise SerializationError("Unexpected EOF reading metadata key length")
        key_len = struct.unpack("<I", key_len_bytes)[0]

        key_bytes = input_file.read(key_len)
        if len(key_bytes) != key_len:
            raise SerializationError("Unexpected EOF reading metadata key")
        key = key_bytes.decode("utf-8")

        # Read value
        value_len_bytes = input_file.read(4)
        if len(value_len_bytes) != 4:
            raise SerializationError("Unexpected EOF reading metadata value length")
        value_len = struct.unpack("<I", value_len_bytes)[0]

        value_bytes = input_file.read(value_len)
        if len(value_bytes) != value_len:
            raise SerializationError("Unexpected EOF reading metadata value")
        value = value_bytes.decode("utf-8")

        module.metadata[key] = value

    return module


def _write_chunk_data(chunk: Chunk, output: BinaryIO) -> None:
    """Write chunk data to binary format (without magic number).

    Args:
        chunk: The chunk to write.
        output: Binary file to write to.
    """
    # Write chunk name
    name_bytes = chunk.name.encode("utf-8")
    output.write(struct.pack("<I", len(name_bytes)))
    output.write(name_bytes)

    # Write constants
    constants = chunk.constants.constants()
    output.write(struct.pack("<H", len(constants)))

    for const in constants:
        _write_constant(const, output)

    # Write bytecode
    output.write(struct.pack("<I", len(chunk.bytecode)))
    output.write(chunk.bytecode)

    # Write metadata
    output.write(struct.pack("<H", chunk.num_locals))
    output.write(struct.pack("<B", chunk.num_params))


def _read_chunk_data(input_file: BinaryIO) -> Chunk:
    """Read chunk data from binary format (without magic number).

    Args:
        input_file: Binary file to read from.

    Returns:
        The deserialized chunk.

    Raises:
        SerializationError: If deserialization fails.
    """
    # Read chunk name
    name_len_bytes = input_file.read(4)
    if len(name_len_bytes) != 4:
        raise SerializationError("Unexpected EOF reading chunk name length")
    name_len = struct.unpack("<I", name_len_bytes)[0]

    name_bytes = input_file.read(name_len)
    if len(name_bytes) != name_len:
        raise SerializationError("Unexpected EOF reading chunk name")
    name = name_bytes.decode("utf-8")

    # Create chunk
    chunk = Chunk(name=name)

    # Read constants
    const_count_bytes = input_file.read(2)
    if len(const_count_bytes) != 2:
        raise SerializationError("Unexpected EOF reading constant count")
    const_count = struct.unpack("<H", const_count_bytes)[0]

    for _ in range(const_count):
        const = _read_constant(input_file)
        chunk.add_constant(const)

    # Read bytecode
    code_size_bytes = input_file.read(4)
    if len(code_size_bytes) != 4:
        raise SerializationError("Unexpected EOF reading code size")
    code_size = struct.unpack("<I", code_size_bytes)[0]

    bytecode = input_file.read(code_size)
    if len(bytecode) != code_size:
        raise SerializationError("Unexpected EOF reading bytecode")
    chunk.bytecode = bytearray(bytecode)

    # Read metadata
    locals_bytes = input_file.read(2)
    if len(locals_bytes) != 2:
        raise SerializationError("Unexpected EOF reading num_locals")
    chunk.num_locals = struct.unpack("<H", locals_bytes)[0]

    params_bytes = input_file.read(1)
    if len(params_bytes) != 1:
        raise SerializationError("Unexpected EOF reading num_params")
    chunk.num_params = struct.unpack("<B", params_bytes)[0]

    return chunk


def _write_constant(const: ConstantValue, output: BinaryIO) -> None:
    """Write a constant value with type tag.

    Args:
        const: The constant to write.
        output: Binary file to write to.
    """
    if isinstance(const, int):
        output.write(struct.pack("<B", TAG_INT))
        # Clamp to i64 range
        if const < -(2**63) or const >= 2**63:
            raise SerializationError(f"Integer constant out of i64 range: {const}")
        output.write(struct.pack("<q", const))

    elif isinstance(const, float):
        output.write(struct.pack("<B", TAG_FLOAT))
        output.write(struct.pack("<d", const))

    elif isinstance(const, str):
        output.write(struct.pack("<B", TAG_STRING))
        str_bytes = const.encode("utf-8")
        output.write(struct.pack("<I", len(str_bytes)))
        output.write(str_bytes)

    elif isinstance(const, bool):
        output.write(struct.pack("<B", TAG_BOOL))
        output.write(struct.pack("<B", 1 if const else 0))

    elif const is None:
        output.write(struct.pack("<B", TAG_NONE))

    else:
        raise SerializationError(f"Unsupported constant type: {type(const).__name__}")


def _read_constant(input_file: BinaryIO) -> ConstantValue:
    """Read a constant value with type tag.

    Args:
        input_file: Binary file to read from.

    Returns:
        The deserialized constant.

    Raises:
        SerializationError: If deserialization fails.
    """
    tag_bytes = input_file.read(1)
    if len(tag_bytes) != 1:
        raise SerializationError("Unexpected EOF reading constant tag")
    tag = struct.unpack("<B", tag_bytes)[0]

    if tag == TAG_INT:
        value_bytes = input_file.read(8)
        if len(value_bytes) != 8:
            raise SerializationError("Unexpected EOF reading integer constant")
        return int(struct.unpack("<q", value_bytes)[0])

    elif tag == TAG_FLOAT:
        value_bytes = input_file.read(8)
        if len(value_bytes) != 8:
            raise SerializationError("Unexpected EOF reading float constant")
        return float(struct.unpack("<d", value_bytes)[0])

    elif tag == TAG_STRING:
        len_bytes = input_file.read(4)
        if len(len_bytes) != 4:
            raise SerializationError("Unexpected EOF reading string length")
        str_len = struct.unpack("<I", len_bytes)[0]

        str_bytes = input_file.read(str_len)
        if len(str_bytes) != str_len:
            raise SerializationError("Unexpected EOF reading string constant")
        return str(str_bytes.decode("utf-8"))

    elif tag == TAG_BOOL:
        value_bytes = input_file.read(1)
        if len(value_bytes) != 1:
            raise SerializationError("Unexpected EOF reading boolean constant")
        # Return actual boolean, not integer
        return bool(struct.unpack("<B", value_bytes)[0])

    elif tag == TAG_NONE:
        return None

    else:
        raise SerializationError(f"Unknown constant tag: {tag:#04x}")
