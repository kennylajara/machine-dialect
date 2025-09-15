//! Instruction decoder
//!
//! This module decodes bytecode into instructions.

use crate::instructions::{Instruction, AssertType};
use crate::errors::{RuntimeError, Result};

/// Instruction decoder
pub struct InstructionDecoder;

impl InstructionDecoder {
    /// Decode bytecode into instructions
    pub fn decode(bytecode: &[u8]) -> Result<Vec<Instruction>> {
        let mut instructions = Vec::new();
        let mut cursor = Cursor::new(bytecode);

        while cursor.has_remaining() {
            let inst = Self::decode_instruction(&mut cursor)?;
            instructions.push(inst);
        }

        Ok(instructions)
    }

    /// Decode a single instruction
    fn decode_instruction(cursor: &mut Cursor) -> Result<Instruction> {
        let opcode = cursor.read_u8()?;

        match opcode {
            // Basic Operations
            0 => { // LoadConstR
                let dst = cursor.read_u8()?;
                let const_idx = cursor.read_u16()?;
                Ok(Instruction::LoadConstR { dst, const_idx })
            }
            1 => { // MoveR
                let dst = cursor.read_u8()?;
                let src = cursor.read_u8()?;
                Ok(Instruction::MoveR { dst, src })
            }
            2 => { // LoadGlobalR
                let dst = cursor.read_u8()?;
                let name_idx = cursor.read_u16()?;
                Ok(Instruction::LoadGlobalR { dst, name_idx })
            }
            3 => { // StoreGlobalR
                let src = cursor.read_u8()?;
                let name_idx = cursor.read_u16()?;
                Ok(Instruction::StoreGlobalR { src, name_idx })
            }

            // Type Operations
            4 => { // DefineR
                let dst = cursor.read_u8()?;
                let type_id = cursor.read_u16()?;
                Ok(Instruction::DefineR { dst, type_id })
            }
            5 => { // CheckTypeR
                let dst = cursor.read_u8()?;
                let src = cursor.read_u8()?;
                let type_id = cursor.read_u16()?;
                Ok(Instruction::CheckTypeR { dst, src, type_id })
            }
            6 => { // CastR
                let dst = cursor.read_u8()?;
                let src = cursor.read_u8()?;
                let to_type = cursor.read_u16()?;
                Ok(Instruction::CastR { dst, src, to_type })
            }

            // Arithmetic
            7 => { // AddR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::AddR { dst, left, right })
            }
            8 => { // SubR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::SubR { dst, left, right })
            }
            9 => { // MulR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::MulR { dst, left, right })
            }
            10 => { // DivR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::DivR { dst, left, right })
            }
            11 => { // ModR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::ModR { dst, left, right })
            }
            12 => { // NegR
                let dst = cursor.read_u8()?;
                let src = cursor.read_u8()?;
                Ok(Instruction::NegR { dst, src })
            }

            // Logical Operations
            13 => { // NotR
                let dst = cursor.read_u8()?;
                let src = cursor.read_u8()?;
                Ok(Instruction::NotR { dst, src })
            }
            14 => { // AndR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::AndR { dst, left, right })
            }
            15 => { // OrR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::OrR { dst, left, right })
            }

            // Comparisons
            16 => { // EqR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::EqR { dst, left, right })
            }
            17 => { // NeqR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::NeqR { dst, left, right })
            }
            18 => { // LtR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::LtR { dst, left, right })
            }
            19 => { // GtR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::GtR { dst, left, right })
            }
            20 => { // LteR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::LteR { dst, left, right })
            }
            21 => { // GteR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::GteR { dst, left, right })
            }

            // Control Flow
            22 => { // JumpR
                let offset = cursor.read_i32()?;
                Ok(Instruction::JumpR { offset })
            }
            23 => { // JumpIfR
                let cond = cursor.read_u8()?;
                let offset = cursor.read_i32()?;
                Ok(Instruction::JumpIfR { cond, offset })
            }
            24 => { // JumpIfNotR
                let cond = cursor.read_u8()?;
                let offset = cursor.read_i32()?;
                Ok(Instruction::JumpIfNotR { cond, offset })
            }
            25 => { // CallR
                let func = cursor.read_u8()?;
                let dst = cursor.read_u8()?;
                let arg_count = cursor.read_u8()?;
                let mut args = Vec::with_capacity(arg_count as usize);
                for _ in 0..arg_count {
                    args.push(cursor.read_u8()?);
                }
                Ok(Instruction::CallR { func, args, dst })
            }
            26 => { // ReturnR
                let has_value = cursor.read_u8()? != 0;
                let src = if has_value {
                    Some(cursor.read_u8()?)
                } else {
                    None
                };
                Ok(Instruction::ReturnR { src })
            }

            // MIR Support
            27 => { // PhiR
                let dst = cursor.read_u8()?;
                let count = cursor.read_u8()?;
                let mut sources = Vec::with_capacity(count as usize);
                for _ in 0..count {
                    let src = cursor.read_u8()?;
                    let label = cursor.read_u16()?;
                    sources.push((src, label));
                }
                Ok(Instruction::PhiR { dst, sources })
            }
            28 => { // AssertR
                let reg = cursor.read_u8()?;
                let assert_type_tag = cursor.read_u8()?;
                let msg_idx = cursor.read_u16()?;
                let assert_type = match assert_type_tag {
                    0 => AssertType::True,
                    1 => AssertType::NonNull,
                    2 => {
                        let min = cursor.read_i64()?;
                        let max = cursor.read_i64()?;
                        AssertType::Range { min, max }
                    }
                    _ => return Err(RuntimeError::InvalidOpcode(assert_type_tag).into()),
                };
                Ok(Instruction::AssertR { reg, assert_type, msg_idx })
            }
            29 => { // ScopeEnterR
                let scope_id = cursor.read_u16()?;
                Ok(Instruction::ScopeEnterR { scope_id })
            }
            30 => { // ScopeExitR
                let scope_id = cursor.read_u16()?;
                Ok(Instruction::ScopeExitR { scope_id })
            }

            // String Operations
            31 => { // ConcatStrR
                let dst = cursor.read_u8()?;
                let left = cursor.read_u8()?;
                let right = cursor.read_u8()?;
                Ok(Instruction::ConcatStrR { dst, left, right })
            }
            32 => { // StrLenR
                let dst = cursor.read_u8()?;
                let str_reg = cursor.read_u8()?;
                Ok(Instruction::StrLenR { dst, str_reg })
            }

            // Arrays
            33 => { // NewArrayR
                let dst = cursor.read_u8()?;
                let size = cursor.read_u8()?;
                Ok(Instruction::NewArrayR { dst, size })
            }
            34 => { // ArrayGetR
                let dst = cursor.read_u8()?;
                let array = cursor.read_u8()?;
                let index = cursor.read_u8()?;
                Ok(Instruction::ArrayGetR { dst, array, index })
            }
            35 => { // ArraySetR
                let array = cursor.read_u8()?;
                let index = cursor.read_u8()?;
                let value = cursor.read_u8()?;
                Ok(Instruction::ArraySetR { array, index, value })
            }
            36 => { // ArrayLenR
                let dst = cursor.read_u8()?;
                let array = cursor.read_u8()?;
                Ok(Instruction::ArrayLenR { dst, array })
            }

            // Debug
            37 => { // DebugPrint
                let src = cursor.read_u8()?;
                Ok(Instruction::DebugPrint { src })
            }
            38 => { // BreakPoint
                Ok(Instruction::BreakPoint)
            }

            // Halt
            39 => { // Halt
                Ok(Instruction::Halt)
            }

            // NOP
            40 => { // No operation
                Ok(Instruction::Nop)
            }

            // Dictionary operations
            41 => { // DictNewR
                let dst = cursor.read_u8()?;
                Ok(Instruction::DictNewR { dst })
            }
            42 => { // DictGetR
                let dst = cursor.read_u8()?;
                let dict = cursor.read_u8()?;
                let key = cursor.read_u8()?;
                Ok(Instruction::DictGetR { dst, dict, key })
            }
            43 => { // DictSetR
                let dict = cursor.read_u8()?;
                let key = cursor.read_u8()?;
                let value = cursor.read_u8()?;
                Ok(Instruction::DictSetR { dict, key, value })
            }
            44 => { // DictRemoveR
                let dict = cursor.read_u8()?;
                let key = cursor.read_u8()?;
                Ok(Instruction::DictRemoveR { dict, key })
            }
            45 => { // DictContainsR
                let dst = cursor.read_u8()?;
                let dict = cursor.read_u8()?;
                let key = cursor.read_u8()?;
                Ok(Instruction::DictContainsR { dst, dict, key })
            }
            46 => { // DictKeysR
                let dst = cursor.read_u8()?;
                let dict = cursor.read_u8()?;
                Ok(Instruction::DictKeysR { dst, dict })
            }
            47 => { // DictValuesR
                let dst = cursor.read_u8()?;
                let dict = cursor.read_u8()?;
                Ok(Instruction::DictValuesR { dst, dict })
            }
            48 => { // DictClearR
                let dict = cursor.read_u8()?;
                Ok(Instruction::DictClearR { dict })
            }
            49 => { // DictLenR
                let dst = cursor.read_u8()?;
                let dict = cursor.read_u8()?;
                Ok(Instruction::DictLenR { dst, dict })
            }

            _ => Err(RuntimeError::InvalidOpcode(opcode).into()),
        }
    }
}

/// Cursor for reading bytecode
struct Cursor<'a> {
    data: &'a [u8],
    position: usize,
}

impl<'a> Cursor<'a> {
    fn new(data: &'a [u8]) -> Self {
        Self { data, position: 0 }
    }

    fn has_remaining(&self) -> bool {
        self.position < self.data.len()
    }

    fn read_u8(&mut self) -> Result<u8> {
        if self.position >= self.data.len() {
            return Err(RuntimeError::UnexpectedEof.into());
        }
        let value = self.data[self.position];
        self.position += 1;
        Ok(value)
    }

    fn read_u16(&mut self) -> Result<u16> {
        if self.position + 2 > self.data.len() {
            return Err(RuntimeError::UnexpectedEof.into());
        }
        let value = u16::from_le_bytes([
            self.data[self.position],
            self.data[self.position + 1],
        ]);
        self.position += 2;
        Ok(value)
    }

    fn read_i32(&mut self) -> Result<i32> {
        if self.position + 4 > self.data.len() {
            return Err(RuntimeError::UnexpectedEof.into());
        }
        let value = i32::from_le_bytes([
            self.data[self.position],
            self.data[self.position + 1],
            self.data[self.position + 2],
            self.data[self.position + 3],
        ]);
        self.position += 4;
        Ok(value)
    }

    fn read_i64(&mut self) -> Result<i64> {
        if self.position + 8 > self.data.len() {
            return Err(RuntimeError::UnexpectedEof.into());
        }
        let bytes = &self.data[self.position..self.position + 8];
        let value = i64::from_le_bytes(bytes.try_into().unwrap());
        self.position += 8;
        Ok(value)
    }
}
