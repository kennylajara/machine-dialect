//! Arithmetic operations
//!
//! This module implements arithmetic operations for the VM.

use std::sync::Arc;

use crate::values::Value;
use crate::errors::{RuntimeError, Result};

/// Arithmetic operations implementation
pub struct ArithmeticOps;

impl ArithmeticOps {
    /// Add two values
    pub fn add(left: &Value, right: &Value) -> Result<Value> {
        match (left, right) {
            (Value::Int(a), Value::Int(b)) => {
                a.checked_add(*b)
                    .map(Value::Int)
                    .ok_or(RuntimeError::IntegerOverflow)
            }
            (Value::Float(a), Value::Float(b)) => {
                Ok(Value::Float(a + b))
            }
            (Value::String(a), Value::String(b)) => {
                Ok(Value::String(Arc::new(format!("{}{}", a, b))))
            }
            (Value::Int(a), Value::Float(b)) | (Value::Float(b), Value::Int(a)) => {
                Ok(Value::Float(*a as f64 + b))
            }
            _ => Err(RuntimeError::TypeMismatch {
                expected: "numeric or string".to_string(),
                found: format!("{:?} and {:?}", left.type_of(), right.type_of()),
            })
        }
    }

    /// Subtract two values
    pub fn sub(left: &Value, right: &Value) -> Result<Value> {
        match (left, right) {
            (Value::Int(a), Value::Int(b)) => {
                a.checked_sub(*b)
                    .map(Value::Int)
                    .ok_or(RuntimeError::IntegerOverflow)
            }
            (Value::Float(a), Value::Float(b)) => {
                Ok(Value::Float(a - b))
            }
            (Value::Int(a), Value::Float(b)) => {
                Ok(Value::Float(*a as f64 - b))
            }
            (Value::Float(a), Value::Int(b)) => {
                Ok(Value::Float(a - *b as f64))
            }
            _ => Err(RuntimeError::TypeMismatch {
                expected: "numeric".to_string(),
                found: format!("{:?} and {:?}", left.type_of(), right.type_of()),
            })
        }
    }

    /// Multiply two values
    pub fn mul(left: &Value, right: &Value) -> Result<Value> {
        match (left, right) {
            (Value::Int(a), Value::Int(b)) => {
                a.checked_mul(*b)
                    .map(Value::Int)
                    .ok_or(RuntimeError::IntegerOverflow)
            }
            (Value::Float(a), Value::Float(b)) => {
                Ok(Value::Float(a * b))
            }
            (Value::Int(a), Value::Float(b)) | (Value::Float(b), Value::Int(a)) => {
                Ok(Value::Float(*a as f64 * b))
            }
            _ => Err(RuntimeError::TypeMismatch {
                expected: "numeric".to_string(),
                found: format!("{:?} and {:?}", left.type_of(), right.type_of()),
            })
        }
    }

    /// Divide two values
    pub fn div(left: &Value, right: &Value) -> Result<Value> {
        // Check for division by zero
        match right {
            Value::Int(0) => {
                return Err(RuntimeError::DivisionByZero);
            }
            Value::Float(f) if *f == 0.0 => {
                return Err(RuntimeError::DivisionByZero);
            }
            _ => {}
        }

        match (left, right) {
            (Value::Int(a), Value::Int(b)) => {
                // Integer division
                a.checked_div(*b)
                    .map(Value::Int)
                    .ok_or(RuntimeError::IntegerOverflow)
            }
            (Value::Float(a), Value::Float(b)) => {
                Ok(Value::Float(a / b))
            }
            (Value::Int(a), Value::Float(b)) => {
                Ok(Value::Float(*a as f64 / b))
            }
            (Value::Float(a), Value::Int(b)) => {
                Ok(Value::Float(a / *b as f64))
            }
            _ => Err(RuntimeError::TypeMismatch {
                expected: "numeric".to_string(),
                found: format!("{:?} and {:?}", left.type_of(), right.type_of()),
            })
        }
    }

    /// Modulo operation
    pub fn modulo(left: &Value, right: &Value) -> Result<Value> {
        // Check for modulo by zero
        match right {
            Value::Int(0) => {
                return Err(RuntimeError::DivisionByZero);
            }
            Value::Float(f) if *f == 0.0 => {
                return Err(RuntimeError::DivisionByZero);
            }
            _ => {}
        }

        match (left, right) {
            (Value::Int(a), Value::Int(b)) => {
                a.checked_rem(*b)
                    .map(Value::Int)
                    .ok_or(RuntimeError::IntegerOverflow)
            }
            (Value::Float(a), Value::Float(b)) => {
                Ok(Value::Float(a % b))
            }
            (Value::Int(a), Value::Float(b)) => {
                Ok(Value::Float(*a as f64 % b))
            }
            (Value::Float(a), Value::Int(b)) => {
                Ok(Value::Float(a % *b as f64))
            }
            _ => Err(RuntimeError::TypeMismatch {
                expected: "numeric".to_string(),
                found: format!("{:?} and {:?}", left.type_of(), right.type_of()),
            })
        }
    }

    /// Negate a value
    pub fn negate(value: &Value) -> Result<Value> {
        match value {
            Value::Int(n) => {
                n.checked_neg()
                    .map(Value::Int)
                    .ok_or(RuntimeError::IntegerOverflow)
            }
            Value::Float(f) => Ok(Value::Float(-f)),
            _ => Err(RuntimeError::InvalidOperation {
                op: "negation".to_string(),
                type_name: format!("{:?}", value.type_of()),
            })
        }
    }

    /// Compare for equality
    pub fn eq(left: &Value, right: &Value) -> bool {
        left == right
    }

    /// Compare for inequality
    pub fn neq(left: &Value, right: &Value) -> bool {
        left != right
    }

    /// Less than comparison
    pub fn lt(left: &Value, right: &Value) -> Result<bool> {
        match (left, right) {
            (Value::Int(a), Value::Int(b)) => Ok(a < b),
            (Value::Float(a), Value::Float(b)) => Ok(a < b),
            (Value::String(a), Value::String(b)) => Ok(a < b),
            (Value::Int(a), Value::Float(b)) => Ok((*a as f64) < *b),
            (Value::Float(a), Value::Int(b)) => Ok(*a < (*b as f64)),
            _ => Err(RuntimeError::InvalidComparison {
                left_type: format!("{:?}", left.type_of()),
                right_type: format!("{:?}", right.type_of()),
            })
        }
    }

    /// Greater than comparison
    pub fn gt(left: &Value, right: &Value) -> Result<bool> {
        Self::lt(right, left)
    }

    /// Less than or equal comparison
    pub fn lte(left: &Value, right: &Value) -> Result<bool> {
        match (left, right) {
            (Value::Int(a), Value::Int(b)) => Ok(a <= b),
            (Value::Float(a), Value::Float(b)) => Ok(a <= b),
            (Value::String(a), Value::String(b)) => Ok(a <= b),
            (Value::Int(a), Value::Float(b)) => Ok((*a as f64) <= *b),
            (Value::Float(a), Value::Int(b)) => Ok(*a <= (*b as f64)),
            _ => Err(RuntimeError::InvalidComparison {
                left_type: format!("{:?}", left.type_of()),
                right_type: format!("{:?}", right.type_of()),
            })
        }
    }

    /// Greater than or equal comparison
    pub fn gte(left: &Value, right: &Value) -> Result<bool> {
        Self::lte(right, left)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_addition() {
        assert_eq!(ArithmeticOps::add(&Value::Int(2), &Value::Int(3)).unwrap(), Value::Int(5));
        assert_eq!(ArithmeticOps::add(&Value::Float(2.5), &Value::Float(3.5)).unwrap(), Value::Float(6.0));
        assert_eq!(ArithmeticOps::add(&Value::Int(2), &Value::Float(3.5)).unwrap(), Value::Float(5.5));

        let s1 = Value::String(Arc::new("hello".to_string()));
        let s2 = Value::String(Arc::new(" world".to_string()));
        match ArithmeticOps::add(&s1, &s2).unwrap() {
            Value::String(s) => assert_eq!(s.as_ref(), "hello world"),
            _ => panic!("Expected string"),
        }
    }

    #[test]
    fn test_division() {
        assert_eq!(ArithmeticOps::div(&Value::Int(10), &Value::Int(2)).unwrap(), Value::Int(5));
        assert_eq!(ArithmeticOps::div(&Value::Float(10.0), &Value::Float(4.0)).unwrap(), Value::Float(2.5));

        // Division by zero
        assert!(ArithmeticOps::div(&Value::Int(10), &Value::Int(0)).is_err());
        assert!(ArithmeticOps::div(&Value::Float(10.0), &Value::Float(0.0)).is_err());
    }

    #[test]
    fn test_comparisons() {
        assert!(ArithmeticOps::lt(&Value::Int(2), &Value::Int(3)).unwrap());
        assert!(!ArithmeticOps::lt(&Value::Int(3), &Value::Int(2)).unwrap());
        assert!(ArithmeticOps::lt(&Value::Float(2.5), &Value::Float(3.5)).unwrap());
        assert!(ArithmeticOps::lt(&Value::Int(2), &Value::Float(3.5)).unwrap());
    }
}
