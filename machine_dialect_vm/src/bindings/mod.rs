//! PyO3 bindings for Python integration
//!
//! This module provides Python bindings for the VM.

#[cfg(feature = "pyo3")]
pub mod pyo3_vm;

#[cfg(feature = "pyo3")]
pub use pyo3_vm::RustVM;
