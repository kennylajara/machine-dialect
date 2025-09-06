//! Runtime error types
//!
//! This module defines error types that can occur during VM execution.

use std::fmt;
use thiserror::Error;

/// Runtime error that can occur during VM execution
#[derive(Debug, Clone, Error)]
pub enum RuntimeError {
    #[error("Type mismatch: expected {expected}, found {found}")]
    TypeMismatch { expected: String, found: String },

    #[error("Division by zero")]
    DivisionByZero,

    #[error("Integer overflow")]
    IntegerOverflow,

    #[error("Index out of bounds: index {index} for length {length}")]
    IndexOutOfBounds { index: i64, length: usize },

    #[error("Undefined variable: {0}")]
    UndefinedVariable(String),

    #[error("Undefined function: {0}")]
    UndefinedFunction(String),

    #[error("Invalid operation: {op} on type {type_name}")]
    InvalidOperation { op: String, type_name: String },

    #[error("Invalid comparison: {left_type} and {right_type}")]
    InvalidComparison { left_type: String, right_type: String },

    #[error("Assertion failed: {0}")]
    AssertionFailed(String),

    #[error("Stack overflow")]
    StackOverflow,

    #[error("Out of memory")]
    OutOfMemory,

    #[error("Invalid register: {0}")]
    InvalidRegister(u8),

    #[error("Invalid constant index: {0}")]
    InvalidConstant(u16),

    #[error("Invalid instruction at PC {0}")]
    InvalidInstruction(usize),

    #[error("Invalid bytecode")]
    InvalidBytecode,

    #[error("Module not loaded")]
    ModuleNotLoaded,

    #[error("Invalid opcode: {0}")]
    InvalidOpcode(u8),

    #[error("Unexpected end of file")]
    UnexpectedEof,
}

/// Error that can occur during bytecode loading
#[derive(Debug, Error)]
pub enum LoadError {
    #[error("IO error: {0}")]
    IO(#[from] std::io::Error),

    #[error("Invalid magic number")]
    InvalidMagic,

    #[error("Unsupported version: {0}")]
    UnsupportedVersion(u32),

    #[error("Invalid bytecode format")]
    InvalidFormat,

    #[error("Metadata hash mismatch")]
    MetadataMismatch,

    #[error("Invalid constant tag: {0}")]
    InvalidConstantTag(u8),

    #[error("Invalid opcode: {0}")]
    InvalidOpcode(u8),

    #[error("Invalid offset")]
    InvalidOffset,

    #[error("Unexpected EOF")]
    UnexpectedEof,

    #[error("Invalid UTF-8")]
    InvalidUtf8,
}

/// Exception with stack trace
#[derive(Debug, Clone)]
pub struct Exception {
    /// Error type
    pub error_type: String,
    /// Error message
    pub message: String,
    /// Stack trace
    pub stack_trace: Vec<StackFrame>,
}

/// Stack frame in a stack trace
#[derive(Debug, Clone)]
pub struct StackFrame {
    /// Function name
    pub function: String,
    /// Program counter
    pub pc: usize,
    /// Source location (line, column) if available
    pub source_location: Option<(usize, usize)>,
}

impl fmt::Display for Exception {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "{}: {}", self.error_type, self.message)?;
        writeln!(f, "Stack trace:")?;
        for frame in &self.stack_trace {
            write!(f, "  at {} (pc: {})", frame.function, frame.pc)?;
            if let Some((line, col)) = frame.source_location {
                write!(f, " [{}:{}]", line, col)?;
            }
            writeln!(f)?;
        }
        Ok(())
    }
}
