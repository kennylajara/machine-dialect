//! Metadata file handling
//!
//! This module loads and parses metadata files (.mdbm).

use std::collections::HashMap;

use crate::values::Type;
use crate::errors::LoadError;

/// Metadata file
#[derive(Clone, Debug)]
pub struct MetadataFile {
    /// Version
    pub version: u32,
    /// Bytecode hash for verification
    pub bytecode_hash: [u8; 8],
    /// Register type information
    pub register_types: HashMap<u8, Type>,
    /// Symbol table
    pub symbol_table: HashMap<String, SymbolInfo>,
    /// Source map
    pub source_map: Vec<SourceLocation>,
}

/// Symbol information
#[derive(Clone, Debug)]
pub struct SymbolInfo {
    /// Symbol name
    pub name: String,
    /// Symbol type
    pub symbol_type: Type,
    /// Register assignment
    pub register: Option<u8>,
}

/// Source location
#[derive(Clone, Debug)]
pub struct SourceLocation {
    /// Bytecode offset
    pub offset: usize,
    /// Source line
    pub line: usize,
    /// Source column
    pub column: usize,
}

impl MetadataFile {
    /// Parse metadata from bytes
    pub fn parse(data: &[u8]) -> Result<Self, LoadError> {
        if data.len() < 20 {
            return Err(LoadError::InvalidFormat);
        }

        // Check magic number
        if &data[0..4] != b"MDBM" {
            return Err(LoadError::InvalidMagic);
        }

        // TODO: Implement full metadata parsing
        // For now, return empty metadata
        Ok(MetadataFile {
            version: 1,
            bytecode_hash: [0; 8],
            register_types: HashMap::new(),
            symbol_table: HashMap::new(),
            source_map: Vec::new(),
        })
    }
}
