//! Register file management
//!
//! This module implements the 256-register file used by the VM.

use crate::values::{Value, Type};
use crate::MAX_REGISTERS;

/// Metadata for a register
#[derive(Clone, Debug, Default)]
pub struct RegisterMetadata {
    /// Instruction counter when last modified
    pub last_modified: usize,
    /// True if value is known at compile time
    pub is_constant: bool,
    /// True if unchanged in loop
    pub is_loop_invariant: bool,
}

/// Register file with 256 general-purpose registers
#[derive(Debug)]
pub struct RegisterFile {
    /// Register values
    registers: [Value; MAX_REGISTERS],
    /// Type information for each register
    register_types: [Type; MAX_REGISTERS],
    /// Metadata for each register
    register_metadata: [RegisterMetadata; MAX_REGISTERS],
}

impl RegisterFile {
    /// Create a new register file
    pub fn new() -> Self {
        const EMPTY_VALUE: Value = Value::Empty;
        const EMPTY_TYPE: Type = Type::Empty;
        const EMPTY_META: RegisterMetadata = RegisterMetadata {
            last_modified: 0,
            is_constant: false,
            is_loop_invariant: false,
        };

        Self {
            registers: [EMPTY_VALUE; MAX_REGISTERS],
            register_types: [EMPTY_TYPE; MAX_REGISTERS],
            register_metadata: [EMPTY_META; MAX_REGISTERS],
        }
    }

    /// Get a register value
    #[inline]
    pub fn get(&self, reg: u8) -> &Value {
        &self.registers[reg as usize]
    }

    /// Get a mutable register value
    #[inline]
    pub fn get_mut(&mut self, reg: u8) -> &mut Value {
        &mut self.registers[reg as usize]
    }

    /// Set a register value
    #[inline]
    pub fn set(&mut self, reg: u8, value: Value) {
        let idx = reg as usize;
        let value_type = value.type_of();
        self.registers[idx] = value;
        self.register_types[idx] = value_type;
    }

    /// Set a register value with type
    #[inline]
    pub fn set_with_type(&mut self, reg: u8, value: Value, value_type: Type) {
        let idx = reg as usize;
        self.registers[idx] = value;
        self.register_types[idx] = value_type;
    }

    /// Get the type of a register
    #[inline]
    pub fn get_type(&self, reg: u8) -> &Type {
        &self.register_types[reg as usize]
    }

    /// Set the type of a register
    #[inline]
    pub fn set_type(&mut self, reg: u8, value_type: Type) {
        self.register_types[reg as usize] = value_type;
    }

    /// Get metadata for a register
    #[inline]
    pub fn get_metadata(&self, reg: u8) -> &RegisterMetadata {
        &self.register_metadata[reg as usize]
    }

    /// Get mutable metadata for a register
    #[inline]
    pub fn get_metadata_mut(&mut self, reg: u8) -> &mut RegisterMetadata {
        &mut self.register_metadata[reg as usize]
    }

    /// Clear all registers
    pub fn clear(&mut self) {
        for i in 0..MAX_REGISTERS {
            self.registers[i] = Value::Empty;
            self.register_types[i] = Type::Empty;
            self.register_metadata[i] = RegisterMetadata::default();
        }
    }

    /// Save registers for a function call (caller-save)
    pub fn save_caller_registers(&self, start: u8, end: u8) -> Vec<(u8, Value)> {
        let mut saved = Vec::new();
        for reg in start..=end {
            let idx = reg as usize;
            if !matches!(self.registers[idx], Value::Empty) {
                saved.push((reg, self.registers[idx].clone()));
            }
        }
        saved
    }

    /// Restore saved registers
    pub fn restore_registers(&mut self, saved: &[(u8, Value)]) {
        for (reg, value) in saved {
            self.set(*reg, value.clone());
        }
    }
}

impl Default for RegisterFile {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    #[test]
    fn test_register_operations() {
        let mut regs = RegisterFile::new();

        // Test set and get
        regs.set(0, Value::Int(42));
        assert_eq!(regs.get(0), &Value::Int(42));
        assert_eq!(regs.get_type(0), &Type::Int);

        // Test set with type
        regs.set_with_type(1, Value::Float(3.14), Type::Float);
        assert_eq!(regs.get(1), &Value::Float(3.14));
        assert_eq!(regs.get_type(1), &Type::Float);

        // Test metadata
        regs.get_metadata_mut(0).is_constant = true;
        assert!(regs.get_metadata(0).is_constant);
    }

    #[test]
    fn test_save_restore() {
        let mut regs = RegisterFile::new();

        regs.set(32, Value::Int(100));
        regs.set(33, Value::String(Arc::new("test".to_string())));
        regs.set(34, Value::Bool(true));

        let saved = regs.save_caller_registers(32, 34);
        assert_eq!(saved.len(), 3);

        regs.clear();
        assert_eq!(regs.get(32), &Value::Empty);

        regs.restore_registers(&saved);
        assert_eq!(regs.get(32), &Value::Int(100));
        assert_eq!(regs.get(33), &Value::String(Arc::new("test".to_string())));
        assert_eq!(regs.get(34), &Value::Bool(true));
    }
}
