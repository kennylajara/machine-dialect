//! Instruction set and execution
//!
//! This module defines the VM instruction set and execution logic.

mod opcodes;
mod decoder;
mod executor;

pub use opcodes::{Instruction, AssertType};
pub use decoder::InstructionDecoder;
pub use executor::InstructionExecutor;
