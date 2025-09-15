//! Instruction executor
//!
//! This module provides instruction execution utilities.

use crate::instructions::Instruction;

/// Instruction executor utilities
pub struct InstructionExecutor;

impl InstructionExecutor {
    /// Get the opcode for an instruction
    pub fn get_opcode(inst: &Instruction) -> u8 {
        match inst {
            Instruction::LoadConstR { .. } => 0,
            Instruction::MoveR { .. } => 1,
            Instruction::LoadGlobalR { .. } => 2,
            Instruction::StoreGlobalR { .. } => 3,
            Instruction::DefineR { .. } => 4,
            Instruction::CheckTypeR { .. } => 5,
            Instruction::CastR { .. } => 6,
            Instruction::AddR { .. } => 7,
            Instruction::SubR { .. } => 8,
            Instruction::MulR { .. } => 9,
            Instruction::DivR { .. } => 10,
            Instruction::ModR { .. } => 11,
            Instruction::NegR { .. } => 12,
            Instruction::NotR { .. } => 13,
            Instruction::AndR { .. } => 14,
            Instruction::OrR { .. } => 15,
            Instruction::EqR { .. } => 16,
            Instruction::NeqR { .. } => 17,
            Instruction::LtR { .. } => 18,
            Instruction::GtR { .. } => 19,
            Instruction::LteR { .. } => 20,
            Instruction::GteR { .. } => 21,
            Instruction::JumpR { .. } => 22,
            Instruction::JumpIfR { .. } => 23,
            Instruction::JumpIfNotR { .. } => 24,
            Instruction::CallR { .. } => 25,
            Instruction::ReturnR { .. } => 26,
            Instruction::PhiR { .. } => 27,
            Instruction::AssertR { .. } => 28,
            Instruction::ScopeEnterR { .. } => 29,
            Instruction::ScopeExitR { .. } => 30,
            Instruction::ConcatStrR { .. } => 31,
            Instruction::StrLenR { .. } => 32,
            Instruction::NewArrayR { .. } => 33,
            Instruction::ArrayGetR { .. } => 34,
            Instruction::ArraySetR { .. } => 35,
            Instruction::ArrayLenR { .. } => 36,
            Instruction::DebugPrint { .. } => 37,
            Instruction::BreakPoint => 38,
            Instruction::Halt => 39,
            Instruction::Nop => 40,

            // Dictionary operations
            Instruction::DictNewR { .. } => 41,
            Instruction::DictGetR { .. } => 42,
            Instruction::DictSetR { .. } => 43,
            Instruction::DictRemoveR { .. } => 44,
            Instruction::DictContainsR { .. } => 45,
            Instruction::DictKeysR { .. } => 46,
            Instruction::DictValuesR { .. } => 47,
            Instruction::DictClearR { .. } => 48,
            Instruction::DictLenR { .. } => 49,
        }
    }
}
