"""Opcode definitions for the Rust VM.

This module defines the opcodes that match the Rust VM implementation.
These must stay in sync with machine_dialect_vm/src/instructions/decoder.rs
"""

from __future__ import annotations

from enum import IntEnum


class Opcode(IntEnum):
    """VM instruction opcodes."""

    # Basic Operations (0-3)
    LOAD_CONST_R = 0  # LoadConstR { dst: u8, const_idx: u16 }
    MOVE_R = 1  # MoveR { dst: u8, src: u8 }
    LOAD_GLOBAL_R = 2  # LoadGlobalR { dst: u8, name_idx: u16 }
    STORE_GLOBAL_R = 3  # StoreGlobalR { src: u8, name_idx: u16 }

    # Type Operations (4-6)
    DEFINE_R = 4  # DefineR { dst: u8, type_id: u16 }
    CHECK_TYPE_R = 5  # CheckTypeR { dst: u8, src: u8, type_id: u16 }
    CAST_R = 6  # CastR { dst: u8, src: u8, to_type: u16 }

    # Arithmetic (7-12)
    ADD_R = 7  # AddR { dst: u8, left: u8, right: u8 }
    SUB_R = 8  # SubR { dst: u8, left: u8, right: u8 }
    MUL_R = 9  # MulR { dst: u8, left: u8, right: u8 }
    DIV_R = 10  # DivR { dst: u8, left: u8, right: u8 }
    MOD_R = 11  # ModR { dst: u8, left: u8, right: u8 }
    NEG_R = 12  # NegR { dst: u8, src: u8 }

    # Logical Operations (13-15)
    NOT_R = 13  # NotR { dst: u8, src: u8 }
    AND_R = 14  # AndR { dst: u8, left: u8, right: u8 }
    OR_R = 15  # OrR { dst: u8, left: u8, right: u8 }

    # Comparisons (16-21)
    EQ_R = 16  # EqR { dst: u8, left: u8, right: u8 }
    NEQ_R = 17  # NeqR { dst: u8, left: u8, right: u8 }
    LT_R = 18  # LtR { dst: u8, left: u8, right: u8 }
    GT_R = 19  # GtR { dst: u8, left: u8, right: u8 }
    LTE_R = 20  # LteR { dst: u8, left: u8, right: u8 }
    GTE_R = 21  # GteR { dst: u8, left: u8, right: u8 }

    # Control Flow (22-26)
    JUMP_R = 22  # JumpR { offset: i32 }
    JUMP_IF_R = 23  # JumpIfR { cond: u8, offset: i32 }
    JUMP_IF_NOT_R = 24  # JumpIfNotR { cond: u8, offset: i32 }
    CALL_R = 25  # CallR { func: u8, args: Vec<u8>, dst: u8 }
    RETURN_R = 26  # ReturnR { src: Option<u8> }

    # MIR Support (27-30)
    PHI_R = 27  # PhiR { dst: u8, sources: Vec<(u8, u16)> }
    ASSERT_R = 28  # AssertR { reg: u8, msg_idx: u16 }
    SCOPE_ENTER_R = 29  # ScopeEnterR { scope_id: u16 }
    SCOPE_EXIT_R = 30  # ScopeExitR { scope_id: u16 }

    # String Operations (31-32)
    CONCAT_STR_R = 31  # ConcatStrR { dst: u8, left: u8, right: u8 }
    STR_LEN_R = 32  # StrLenR { dst: u8, str: u8 }

    # Arrays (33-36)
    NEW_ARRAY_R = 33  # NewArrayR { dst: u8, size: u8 }
    ARRAY_GET_R = 34  # ArrayGetR { dst: u8, array: u8, index: u8 }
    ARRAY_SET_R = 35  # ArraySetR { array: u8, index: u8, value: u8 }
    ARRAY_LEN_R = 36  # ArrayLenR { dst: u8, array: u8 }

    # Debug (37-40)
    DEBUG_PRINT = 37  # DebugPrint { src: u8 }
    BREAKPOINT = 38  # BreakPoint
    HALT = 39  # Halt execution
    NOP = 40  # No operation

    # Dictionaries (41-49) - Now match VM implementation
    DICT_NEW_R = 41  # DictNewR { dst: u8 }
    DICT_GET_R = 42  # DictGetR { dst: u8, dict: u8, key: u8 }
    DICT_SET_R = 43  # DictSetR { dict: u8, key: u8, value: u8 }
    DICT_REMOVE_R = 44  # DictRemoveR { dict: u8, key: u8 }
    DICT_CONTAINS_R = 45  # DictContainsR { dst: u8, dict: u8, key: u8 }
    DICT_KEYS_R = 46  # DictKeysR { dst: u8, dict: u8 }
    DICT_VALUES_R = 47  # DictValuesR { dst: u8, dict: u8 }
    DICT_CLEAR_R = 48  # DictClearR { dict: u8 }
    DICT_LEN_R = 49  # DictLenR { dst: u8, dict: u8 }


# Type IDs for type operations
class TypeId(IntEnum):
    """Type identifiers."""

    EMPTY = 0x00
    BOOL = 0x01
    INT = 0x02
    FLOAT = 0x03
    STRING = 0x04
    FUNCTION = 0x05
    URL = 0x06
    ARRAY = 0x07
    DICT = 0x08
    UNKNOWN = 0xFF
