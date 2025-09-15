//! Type system for the VM
//!
//! This module defines the type system used by the VM for type checking
//! and optimization.

use std::fmt;

/// Type enumeration
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum Type {
    /// Empty/null type
    Empty,
    /// Boolean type
    Bool,
    /// Integer type
    Int,
    /// Floating-point type
    Float,
    /// String type
    String,
    /// Function type
    Function,
    /// URL type
    URL,
    /// Array type
    Array,
    /// Dictionary type
    Dict,
    /// Unknown type (for type inference)
    Unknown,
}

impl Type {
    /// Check if two types are compatible for operations
    pub fn is_compatible_with(&self, other: &Type) -> bool {
        match (self, other) {
            // Same type is always compatible
            (a, b) if a == b => true,
            // Unknown is compatible with anything
            (Type::Unknown, _) | (_, Type::Unknown) => true,
            // Numeric types are compatible
            (Type::Int, Type::Float) | (Type::Float, Type::Int) => true,
            // Everything else is incompatible
            _ => false,
        }
    }

    /// Check if type is numeric
    pub fn is_numeric(&self) -> bool {
        matches!(self, Type::Int | Type::Float)
    }

    /// Check if type is comparable
    pub fn is_comparable(&self) -> bool {
        matches!(self, Type::Int | Type::Float | Type::String | Type::Bool)
    }

    /// Get the result type of a binary operation
    pub fn binary_op_result(&self, op: &str, other: &Type) -> Option<Type> {
        match op {
            "+" | "-" | "*" | "/" | "%" | "**" => {
                match (self, other) {
                    (Type::Int, Type::Int) => Some(Type::Int),
                    (Type::Float, Type::Float) => Some(Type::Float),
                    (Type::Int, Type::Float) | (Type::Float, Type::Int) => Some(Type::Float),
                    (Type::String, Type::String) if op == "+" => Some(Type::String),
                    _ => None,
                }
            }
            "==" | "!=" | "<" | ">" | "<=" | ">=" => {
                if self.is_comparable() && other.is_comparable() {
                    Some(Type::Bool)
                } else {
                    None
                }
            }
            "and" | "or" => Some(Type::Bool),
            _ => None,
        }
    }
}

impl fmt::Display for Type {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Type::Empty => write!(f, "empty"),
            Type::Bool => write!(f, "bool"),
            Type::Int => write!(f, "int"),
            Type::Float => write!(f, "float"),
            Type::String => write!(f, "string"),
            Type::Function => write!(f, "function"),
            Type::URL => write!(f, "url"),
            Type::Array => write!(f, "array"),
            Type::Dict => write!(f, "dict"),
            Type::Unknown => write!(f, "unknown"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_type_compatibility() {
        assert!(Type::Int.is_compatible_with(&Type::Int));
        assert!(Type::Int.is_compatible_with(&Type::Float));
        assert!(Type::Float.is_compatible_with(&Type::Int));
        assert!(Type::Unknown.is_compatible_with(&Type::String));
        assert!(!Type::String.is_compatible_with(&Type::Int));
    }

    #[test]
    fn test_numeric_types() {
        assert!(Type::Int.is_numeric());
        assert!(Type::Float.is_numeric());
        assert!(!Type::String.is_numeric());
        assert!(!Type::Bool.is_numeric());
    }

    #[test]
    fn test_binary_op_result() {
        assert_eq!(Type::Int.binary_op_result("+", &Type::Int), Some(Type::Int));
        assert_eq!(Type::Int.binary_op_result("+", &Type::Float), Some(Type::Float));
        assert_eq!(Type::String.binary_op_result("+", &Type::String), Some(Type::String));
        assert_eq!(Type::Int.binary_op_result("<", &Type::Float), Some(Type::Bool));
        assert_eq!(Type::String.binary_op_result("*", &Type::String), None);
    }
}
