//! Bytecode loading
//!
//! This module handles loading bytecode and metadata files.

mod bytecode;
mod metadata;

pub use bytecode::{BytecodeModule, BytecodeLoader};
pub use metadata::MetadataFile;
