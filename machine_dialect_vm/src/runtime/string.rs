//! String operations
//!
//! This module implements string operations for the VM.

use std::sync::Arc;

use crate::values::Value;
use crate::errors::{RuntimeError, Result};

/// String operations implementation
pub struct StringOps;

impl StringOps {
    /// Concatenate two strings
    pub fn concat(left: &Value, right: &Value) -> Result<Value> {
        match (left, right) {
            (Value::String(a), Value::String(b)) => {
                Ok(Value::String(Arc::new(format!("{}{}", a, b))))
            }
            _ => {
                // Convert to strings and concatenate
                let left_str = left.to_string();
                let right_str = right.to_string();
                Ok(Value::String(Arc::new(format!("{}{}", left_str, right_str))))
            }
        }
    }

    /// Get string length
    pub fn len(value: &Value) -> Result<Value> {
        match value {
            Value::String(s) => Ok(Value::Int(s.len() as i64)),
            _ => Err(RuntimeError::TypeMismatch {
                expected: "string".to_string(),
                found: value.type_of().to_string(),
            })
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_concat() {
        let s1 = Value::String(Arc::new("hello".to_string()));
        let s2 = Value::String(Arc::new(" world".to_string()));

        match StringOps::concat(&s1, &s2).unwrap() {
            Value::String(s) => assert_eq!(s.as_ref(), "hello world"),
            _ => panic!("Expected string"),
        }

        // Test with non-string values
        let result = StringOps::concat(&Value::Int(42), &Value::String(Arc::new(" test".to_string()))).unwrap();
        match result {
            Value::String(s) => assert_eq!(s.as_ref(), "42 test"),
            _ => panic!("Expected string"),
        }
    }

    #[test]
    fn test_len() {
        let s = Value::String(Arc::new("hello".to_string()));
        assert_eq!(StringOps::len(&s).unwrap(), Value::Int(5));

        let empty = Value::String(Arc::new("".to_string()));
        assert_eq!(StringOps::len(&empty).unwrap(), Value::Int(0));

        // Test with non-string
        assert!(StringOps::len(&Value::Int(42)).is_err());
    }
}
