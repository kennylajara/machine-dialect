//! Constant pool management
//!
//! This module handles the constant pool for bytecode modules.

use std::sync::Arc;

use crate::values::{Value, FunctionRef};

/// Constant value in the pool
#[derive(Clone, Debug)]
pub enum ConstantValue {
    /// Integer constant
    Int(i64),
    /// Float constant
    Float(f64),
    /// String constant
    String(String),
    /// Boolean constant
    Bool(bool),
    /// Empty constant
    Empty,
    /// URL constant
    URL(String),
    /// Function reference
    Function(FunctionRef),
}

impl ConstantValue {
    /// Convert to a runtime value
    pub fn to_value(&self) -> Value {
        match self {
            ConstantValue::Int(n) => Value::Int(*n),
            ConstantValue::Float(f) => Value::Float(*f),
            ConstantValue::String(s) => Value::String(Arc::new(s.clone())),
            ConstantValue::Bool(b) => Value::Bool(*b),
            ConstantValue::Empty => Value::Empty,
            ConstantValue::URL(u) => Value::URL(Arc::new(u.clone())),
            ConstantValue::Function(f) => Value::Function(f.clone()),
        }
    }
}

/// Constant pool for a bytecode module
#[derive(Clone, Debug, Default)]
pub struct ConstantPool {
    /// Constants in the pool
    constants: Vec<ConstantValue>,
}

impl ConstantPool {
    /// Create a new empty constant pool
    pub fn new() -> Self {
        Self {
            constants: Vec::new(),
        }
    }

    /// Add a constant to the pool and return its index
    pub fn add(&mut self, value: ConstantValue) -> u16 {
        let index = self.constants.len();
        self.constants.push(value);
        index as u16
    }

    /// Get a constant by index
    pub fn get(&self, index: u16) -> Option<&ConstantValue> {
        self.constants.get(index as usize)
    }

    /// Get the number of constants
    pub fn len(&self) -> usize {
        self.constants.len()
    }

    /// Check if the pool is empty
    pub fn is_empty(&self) -> bool {
        self.constants.is_empty()
    }

    /// Add an integer constant
    pub fn add_int(&mut self, value: i64) -> u16 {
        self.add(ConstantValue::Int(value))
    }

    /// Add a float constant
    pub fn add_float(&mut self, value: f64) -> u16 {
        self.add(ConstantValue::Float(value))
    }

    /// Add a string constant
    pub fn add_string(&mut self, value: String) -> u16 {
        self.add(ConstantValue::String(value))
    }

    /// Add a boolean constant
    pub fn add_bool(&mut self, value: bool) -> u16 {
        self.add(ConstantValue::Bool(value))
    }

    /// Add an empty constant
    pub fn add_empty(&mut self) -> u16 {
        self.add(ConstantValue::Empty)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_constant_pool() {
        let mut pool = ConstantPool::new();
        assert!(pool.is_empty());

        let idx1 = pool.add(ConstantValue::Int(42));
        let idx2 = pool.add(ConstantValue::String("hello".to_string()));

        assert_eq!(pool.len(), 2);
        assert_eq!(idx1, 0);
        assert_eq!(idx2, 1);

        match pool.get(0) {
            Some(ConstantValue::Int(42)) => {},
            _ => panic!("Expected Int(42)"),
        }

        match pool.get(1) {
            Some(ConstantValue::String(s)) if s == "hello" => {},
            _ => panic!("Expected String(hello)"),
        }
    }
}
