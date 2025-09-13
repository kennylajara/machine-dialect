//! Machine Dialect™ Virtual Machine
//!
//! A high-performance register-based VM for executing Machine Dialect™ bytecode.

pub mod vm;
pub mod values;
pub mod instructions;
pub mod runtime;
pub mod memory;
pub mod loader;
pub mod errors;

#[cfg(feature = "pyo3")]
pub mod bindings;

// Re-export the PyO3 module function at the crate level
#[cfg(feature = "pyo3")]
pub use bindings::pyo3_vm::machine_dialect_vm;

pub use vm::VM;
pub use values::{Value, Type};
pub use errors::{RuntimeError, Result};
pub use loader::{BytecodeLoader, BytecodeModule};

/// Version of the VM
pub const VM_VERSION: &str = "0.1.0";

/// Maximum number of registers
pub const MAX_REGISTERS: usize = 256;

/// Register conventions
pub mod registers {
    /// Function argument registers (r0-r15)
    pub const ARG_START: u8 = 0;
    pub const ARG_END: u8 = 15;

    /// Return value registers (r16-r31)
    pub const RET_START: u8 = 16;
    pub const RET_END: u8 = 31;

    /// Caller-save temporaries (r32-r127)
    pub const TEMP_START: u8 = 32;
    pub const TEMP_END: u8 = 127;

    /// Callee-save registers (r128-r239)
    pub const SAVED_START: u8 = 128;
    pub const SAVED_END: u8 = 239;

    /// Reserved for VM internal use (r240-r255)
    pub const RESERVED_START: u8 = 240;
    pub const RESERVED_END: u8 = 255;
}
