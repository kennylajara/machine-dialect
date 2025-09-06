//! Virtual Machine core
//!
//! This module contains the VM implementation including register management,
//! execution engine, and state tracking.

mod engine;
mod registers;
mod state;

pub use engine::VM;
pub use registers::{RegisterFile, RegisterMetadata};
pub use state::{CallFrame, VMState};
