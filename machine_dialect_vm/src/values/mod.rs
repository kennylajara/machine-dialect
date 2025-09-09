//! Value system for the VM
//!
//! This module defines the value representation and type system.

mod value;
mod types;
mod constants;

pub use value::{Value, FunctionRef};
pub use types::Type;
pub use constants::{ConstantPool, ConstantValue};
