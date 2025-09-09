//! Error handling for the VM
//!
//! This module defines error types and result types for the VM.

mod runtime;

pub use runtime::{RuntimeError, LoadError, Exception, StackFrame};

/// Result type for VM operations
pub type Result<T> = std::result::Result<T, RuntimeError>;
