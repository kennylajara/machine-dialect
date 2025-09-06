//! Bytecode loader
//!
//! This module loads bytecode files (.mdbc) into memory.

use std::path::Path;
use std::fs;
use std::collections::HashMap;

use crate::values::ConstantPool;
use crate::instructions::Instruction;
use crate::errors::LoadError;
use super::metadata::MetadataFile;

/// Bytecode module
#[derive(Clone, Debug)]
pub struct BytecodeModule {
    /// Module name
    pub name: String,
    /// Version
    pub version: u32,
    /// Flags
    pub flags: u32,
    /// Constant pool
    pub constants: ConstantPool,
    /// Instructions
    pub instructions: Vec<Instruction>,
    /// Function table
    pub function_table: HashMap<String, usize>,
    /// Global names
    pub global_names: Vec<String>,
}

/// Bytecode loader
pub struct BytecodeLoader;

impl BytecodeLoader {
    /// Load a module from file
    pub fn load_module(path: &Path) -> std::result::Result<(BytecodeModule, Option<MetadataFile>), LoadError> {
        // Load bytecode file
        let bytecode_path = path.with_extension("mdbc");
        let bytecode_data = fs::read(&bytecode_path)?;

        // Load optional metadata file
        let metadata_path = path.with_extension("mdbm");
        let metadata = if metadata_path.exists() {
            let metadata_data = fs::read(&metadata_path)?;
            Some(MetadataFile::parse(&metadata_data)?)
        } else {
            None
        };

        // Parse bytecode
        let module = Self::parse_bytecode(&bytecode_data)?;

        Ok((module, metadata))
    }

    /// Parse bytecode data
    fn parse_bytecode(data: &[u8]) -> std::result::Result<BytecodeModule, LoadError> {
        if data.len() < 24 {
            return Err(LoadError::InvalidFormat);
        }

        // Check magic number
        if &data[0..4] != b"MDBC" {
            return Err(LoadError::InvalidMagic);
        }

        // TODO: Implement full bytecode parsing
        // For now, return a dummy module
        Ok(BytecodeModule {
            name: "main".to_string(),
            version: 1,
            flags: 0,
            constants: ConstantPool::new(),
            instructions: Vec::new(),
            function_table: HashMap::new(),
            global_names: Vec::new(),
        })
    }
}
