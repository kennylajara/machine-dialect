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
        // Load bytecode file - use path as-is if it already has .mdbc extension
        let bytecode_path = if path.extension().and_then(|s| s.to_str()) == Some("mdbc") {
            path.to_path_buf()
        } else {
            path.with_extension("mdbc")
        };
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

        let mut cursor = Cursor::new(data);

        // Check magic number
        let magic = cursor.read_bytes(4)?;
        if magic != b"MDBC" {
            return Err(LoadError::InvalidMagic);
        }

        // Read header
        let version = cursor.read_u32()?;
        let flags = cursor.read_u32()?;
        let name_offset = cursor.read_u32()? as usize;
        let constant_offset = cursor.read_u32()? as usize;
        let function_offset = cursor.read_u32()? as usize;
        let instruction_offset = cursor.read_u32()? as usize;

        // Read module name
        cursor.seek(name_offset)?;
        let name = cursor.read_string()?;

        // Read constant pool
        cursor.seek(constant_offset)?;
        let constants = Self::parse_constants(&mut cursor)?;

        // Read function table
        cursor.seek(function_offset)?;
        let function_table = Self::parse_functions(&mut cursor)?;

        // Read instructions
        cursor.seek(instruction_offset)?;
        let instructions = Self::parse_instructions(&mut cursor)?;

        // Global names are not included in the basic format for now
        // They would need a separate offset in the header
        let global_names = Vec::new();

        Ok(BytecodeModule {
            name,
            version,
            flags,
            constants,
            instructions,
            function_table,
            global_names,
        })
    }

    /// Parse constant pool
    fn parse_constants(cursor: &mut Cursor) -> std::result::Result<ConstantPool, LoadError> {
        let count = cursor.read_u32()? as usize;
        let mut pool = ConstantPool::new();

        for _ in 0..count {
            let tag = cursor.read_u8()?;
            match tag {
                0x01 => { // Integer
                    let value = cursor.read_i64()?;
                    pool.add_int(value);
                }
                0x02 => { // Float
                    let value = cursor.read_f64()?;
                    pool.add_float(value);
                }
                0x03 => { // String
                    let value = cursor.read_string()?;
                    pool.add_string(value);
                }
                0x04 => { // Boolean
                    let value = cursor.read_u8()? != 0;
                    pool.add_bool(value);
                }
                0x05 => { // Empty/None
                    pool.add_empty();
                }
                _ => return Err(LoadError::InvalidConstantTag(tag)),
            }
        }

        Ok(pool)
    }

    /// Parse function table
    fn parse_functions(cursor: &mut Cursor) -> std::result::Result<HashMap<String, usize>, LoadError> {
        let count = cursor.read_u32()? as usize;
        let mut table = HashMap::new();

        for _ in 0..count {
            let name = cursor.read_string()?;
            let offset = cursor.read_u32()? as usize;
            table.insert(name, offset);
        }

        Ok(table)
    }

    /// Parse instructions
    fn parse_instructions(cursor: &mut Cursor) -> std::result::Result<Vec<Instruction>, LoadError> {
        let count = cursor.read_u32()? as usize;
        let mut instructions = Vec::with_capacity(count);

        // Use the InstructionDecoder for each instruction
        for _ in 0..count {
            let inst = Self::parse_instruction(cursor)?;
            instructions.push(inst);
        }

        Ok(instructions)
    }

    /// Parse a single instruction
    fn parse_instruction(cursor: &mut Cursor) -> std::result::Result<Instruction, LoadError> {
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

            // Logical
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

            // String operations
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

            // Array operations
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
            39 => { // Halt
                Ok(Instruction::Halt)
            }
            40 => { // Nop
                Ok(Instruction::Nop)
            }

            // Dictionary Operations
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

            // For now, return error for unimplemented opcodes
            _ => Err(LoadError::InvalidOpcode(opcode)),
        }
    }

    /// Parse global names
    #[allow(dead_code)]
    fn parse_global_names(cursor: &mut Cursor) -> std::result::Result<Vec<String>, LoadError> {
        let count = cursor.read_u32()? as usize;
        let mut names = Vec::with_capacity(count);

        for _ in 0..count {
            names.push(cursor.read_string()?);
        }

        Ok(names)
    }
}

/// Binary data cursor for reading bytecode
struct Cursor<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> Cursor<'a> {
    /// Create a new cursor
    fn new(data: &'a [u8]) -> Self {
        Self { data, pos: 0 }
    }

    /// Check if there's remaining data
    #[allow(dead_code)]
    fn has_remaining(&self) -> bool {
        self.pos < self.data.len()
    }

    /// Seek to a position
    fn seek(&mut self, pos: usize) -> Result<(), LoadError> {
        if pos > self.data.len() {
            return Err(LoadError::InvalidOffset);
        }
        self.pos = pos;
        Ok(())
    }

    /// Read bytes
    fn read_bytes(&mut self, len: usize) -> Result<&'a [u8], LoadError> {
        if self.pos + len > self.data.len() {
            return Err(LoadError::UnexpectedEof);
        }
        let bytes = &self.data[self.pos..self.pos + len];
        self.pos += len;
        Ok(bytes)
    }

    /// Read u8
    fn read_u8(&mut self) -> Result<u8, LoadError> {
        if self.pos >= self.data.len() {
            return Err(LoadError::UnexpectedEof);
        }
        let value = self.data[self.pos];
        self.pos += 1;
        Ok(value)
    }

    /// Read u16 (little-endian)
    fn read_u16(&mut self) -> Result<u16, LoadError> {
        let bytes = self.read_bytes(2)?;
        Ok(u16::from_le_bytes([bytes[0], bytes[1]]))
    }

    /// Read u32 (little-endian)
    fn read_u32(&mut self) -> Result<u32, LoadError> {
        let bytes = self.read_bytes(4)?;
        Ok(u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
    }

    /// Read i32 (little-endian)
    fn read_i32(&mut self) -> Result<i32, LoadError> {
        let bytes = self.read_bytes(4)?;
        Ok(i32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
    }

    /// Read i64 (little-endian)
    fn read_i64(&mut self) -> Result<i64, LoadError> {
        let bytes = self.read_bytes(8)?;
        Ok(i64::from_le_bytes([
            bytes[0], bytes[1], bytes[2], bytes[3],
            bytes[4], bytes[5], bytes[6], bytes[7]
        ]))
    }

    /// Read f64 (little-endian)
    fn read_f64(&mut self) -> Result<f64, LoadError> {
        let bytes = self.read_bytes(8)?;
        Ok(f64::from_le_bytes([
            bytes[0], bytes[1], bytes[2], bytes[3],
            bytes[4], bytes[5], bytes[6], bytes[7]
        ]))
    }

    /// Read string (length-prefixed)
    fn read_string(&mut self) -> Result<String, LoadError> {
        let len = self.read_u32()? as usize;
        let bytes = self.read_bytes(len)?;
        String::from_utf8(bytes.to_vec())
            .map_err(|_| LoadError::InvalidUtf8)
    }
}
