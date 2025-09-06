//! Logical operations
//!
//! This module implements logical operations for the VM.

use crate::values::Value;
use crate::errors::Result;

/// Logical operations implementation
pub struct LogicOps;

impl LogicOps {
    /// Logical NOT operation
    pub fn not(value: &Value) -> Result<Value> {
        Ok(Value::Bool(!value.is_truthy()))
    }

    /// Logical AND operation
    pub fn and(left: &Value, right: &Value) -> Result<Value> {
        Ok(Value::Bool(left.is_truthy() && right.is_truthy()))
    }

    /// Logical OR operation
    pub fn or(left: &Value, right: &Value) -> Result<Value> {
        Ok(Value::Bool(left.is_truthy() || right.is_truthy()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    #[test]
    fn test_not() {
        assert_eq!(LogicOps::not(&Value::Bool(true)).unwrap(), Value::Bool(false));
        assert_eq!(LogicOps::not(&Value::Bool(false)).unwrap(), Value::Bool(true));
        assert_eq!(LogicOps::not(&Value::Int(0)).unwrap(), Value::Bool(true));
        assert_eq!(LogicOps::not(&Value::Int(1)).unwrap(), Value::Bool(false));
        assert_eq!(LogicOps::not(&Value::Empty).unwrap(), Value::Bool(true));
    }

    #[test]
    fn test_and() {
        assert_eq!(LogicOps::and(&Value::Bool(true), &Value::Bool(true)).unwrap(), Value::Bool(true));
        assert_eq!(LogicOps::and(&Value::Bool(true), &Value::Bool(false)).unwrap(), Value::Bool(false));
        assert_eq!(LogicOps::and(&Value::Bool(false), &Value::Bool(true)).unwrap(), Value::Bool(false));
        assert_eq!(LogicOps::and(&Value::Bool(false), &Value::Bool(false)).unwrap(), Value::Bool(false));

        // Test with different types
        assert_eq!(LogicOps::and(&Value::Int(1), &Value::String(Arc::new("test".to_string()))).unwrap(), Value::Bool(true));
        assert_eq!(LogicOps::and(&Value::Int(0), &Value::String(Arc::new("test".to_string()))).unwrap(), Value::Bool(false));
    }

    #[test]
    fn test_or() {
        assert_eq!(LogicOps::or(&Value::Bool(true), &Value::Bool(true)).unwrap(), Value::Bool(true));
        assert_eq!(LogicOps::or(&Value::Bool(true), &Value::Bool(false)).unwrap(), Value::Bool(true));
        assert_eq!(LogicOps::or(&Value::Bool(false), &Value::Bool(true)).unwrap(), Value::Bool(true));
        assert_eq!(LogicOps::or(&Value::Bool(false), &Value::Bool(false)).unwrap(), Value::Bool(false));

        // Test with different types
        assert_eq!(LogicOps::or(&Value::Int(0), &Value::String(Arc::new("".to_string()))).unwrap(), Value::Bool(false));
        assert_eq!(LogicOps::or(&Value::Int(0), &Value::String(Arc::new("test".to_string()))).unwrap(), Value::Bool(true));
    }
}
