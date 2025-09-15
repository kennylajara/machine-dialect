//! Value representation
//!
//! This module defines the Value enum which represents all possible values
//! in the Machine Dialect™ VM.

use std::collections::HashMap;
use std::fmt;
use std::sync::Arc;

use crate::errors::{RuntimeError, Result};
use crate::values::Type;

/// Reference to a function
#[derive(Clone, Debug, PartialEq)]
pub struct FunctionRef {
    /// Index of the function chunk
    pub chunk_index: usize,
    /// Number of parameters
    pub arity: usize,
    /// Function name
    pub name: String,
}

/// Value representation using tagged union
#[derive(Clone, Debug)]
pub enum Value {
    /// Empty/null value
    Empty,
    /// Boolean value
    Bool(bool),
    /// Integer value (64-bit)
    Int(i64),
    /// Floating-point value (64-bit)
    Float(f64),
    /// String value (reference-counted)
    String(Arc<String>),
    /// Function reference
    Function(FunctionRef),
    /// URL value
    URL(Arc<String>),
    /// Array value (reference-counted)
    Array(Arc<Vec<Value>>),
    /// Dictionary value (reference-counted)
    Dict(Arc<HashMap<String, Value>>),
}

impl Value {
    /// Get the type of this value
    pub fn type_of(&self) -> Type {
        match self {
            Value::Empty => Type::Empty,
            Value::Bool(_) => Type::Bool,
            Value::Int(_) => Type::Int,
            Value::Float(_) => Type::Float,
            Value::String(_) => Type::String,
            Value::Function(_) => Type::Function,
            Value::URL(_) => Type::URL,
            Value::Array(_) => Type::Array,
            Value::Dict(_) => Type::Dict,
        }
    }

    /// Check if value is truthy
    pub fn is_truthy(&self) -> bool {
        match self {
            Value::Empty => false,
            Value::Bool(b) => *b,
            Value::Int(n) => *n != 0,
            Value::Float(f) => *f != 0.0 && !f.is_nan(),
            Value::String(s) => !s.is_empty(),
            Value::Array(a) => !a.is_empty(),
            Value::Dict(d) => !d.is_empty(),
            _ => true,
        }
    }

    /// Convert to boolean
    pub fn to_bool(&self) -> bool {
        self.is_truthy()
    }

    /// Try to convert to integer
    pub fn to_int(&self) -> Result<i64> {
        match self {
            Value::Int(n) => Ok(*n),
            Value::Float(f) => {
                if f.is_finite() && f.fract() == 0.0 && *f >= i64::MIN as f64 && *f <= i64::MAX as f64 {
                    Ok(*f as i64)
                } else {
                    Err(RuntimeError::TypeMismatch {
                        expected: "integer".to_string(),
                        found: format!("float {}", f),
                    })
                }
            }
            Value::Bool(b) => Ok(if *b { 1 } else { 0 }),
            _ => Err(RuntimeError::TypeMismatch {
                expected: "integer".to_string(),
                found: self.type_of().to_string(),
            }),
        }
    }

    /// Try to convert to float
    pub fn to_float(&self) -> Result<f64> {
        match self {
            Value::Float(f) => Ok(*f),
            Value::Int(n) => Ok(*n as f64),
            _ => Err(RuntimeError::TypeMismatch {
                expected: "float".to_string(),
                found: self.type_of().to_string(),
            }),
        }
    }

    /// Try to convert to string
    pub fn to_string(&self) -> String {
        match self {
            Value::Empty => "empty".to_string(),
            Value::Bool(b) => b.to_string(),
            Value::Int(n) => n.to_string(),
            Value::Float(f) => {
                if f.fract() == 0.0 && f.is_finite() {
                    format!("{:.0}", f)
                } else {
                    f.to_string()
                }
            }
            Value::String(s) => s.as_ref().clone(),
            Value::Function(f) => format!("function<{}>", f.name),
            Value::URL(u) => u.as_ref().clone(),
            Value::Array(a) => {
                let items: Vec<String> = a.iter().map(|v| v.to_string()).collect();
                format!("[{}]", items.join(", "))
            }
            Value::Dict(d) => {
                let items: Vec<String> = d.iter()
                    .map(|(k, v)| format!("{}: {}", k, v.to_string()))
                    .collect();
                format!("{{{}}}", items.join(", "))
            }
        }
    }
}

impl PartialEq for Value {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Value::Empty, Value::Empty) => true,
            (Value::Bool(a), Value::Bool(b)) => a == b,
            (Value::Int(a), Value::Int(b)) => a == b,
            (Value::Float(a), Value::Float(b)) => {
                // Handle NaN correctly
                a == b && !a.is_nan() && !b.is_nan()
            }
            (Value::String(a), Value::String(b)) => a == b,
            (Value::URL(a), Value::URL(b)) => a == b,
            (Value::Function(a), Value::Function(b)) => a == b,
            (Value::Array(a), Value::Array(b)) => a == b,
            (Value::Dict(a), Value::Dict(b)) => a == b,
            // Cross-type comparisons
            (Value::Int(a), Value::Float(b)) | (Value::Float(b), Value::Int(a)) => {
                *a as f64 == *b && !b.is_nan()
            }
            _ => false,
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_value_types() {
        assert_eq!(Value::Empty.type_of(), Type::Empty);
        assert_eq!(Value::Bool(true).type_of(), Type::Bool);
        assert_eq!(Value::Int(42).type_of(), Type::Int);
        assert_eq!(Value::Float(3.14).type_of(), Type::Float);
        assert_eq!(Value::String(Arc::new("test".to_string())).type_of(), Type::String);
    }

    #[test]
    fn test_truthiness() {
        assert!(!Value::Empty.is_truthy());
        assert!(!Value::Bool(false).is_truthy());
        assert!(Value::Bool(true).is_truthy());
        assert!(!Value::Int(0).is_truthy());
        assert!(Value::Int(1).is_truthy());
        assert!(!Value::Float(0.0).is_truthy());
        assert!(Value::Float(1.0).is_truthy());
        assert!(!Value::Float(f64::NAN).is_truthy());
        assert!(!Value::String(Arc::new("".to_string())).is_truthy());
        assert!(Value::String(Arc::new("test".to_string())).is_truthy());
    }

    #[test]
    fn test_equality() {
        assert_eq!(Value::Int(42), Value::Int(42));
        assert_eq!(Value::Int(42), Value::Float(42.0));
        assert_ne!(Value::Int(42), Value::Int(43));
        assert_ne!(Value::Float(f64::NAN), Value::Float(f64::NAN));
    }
}
