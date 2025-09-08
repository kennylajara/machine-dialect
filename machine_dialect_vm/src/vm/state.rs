//! VM state management
//!
//! This module defines the VM state including call stack, globals, and execution context.

use std::collections::HashMap;

use crate::values::Value;
use crate::values::FunctionRef;
use crate::errors::{RuntimeError, Result};

/// Maximum call stack depth to prevent stack overflow
const MAX_CALL_DEPTH: usize = 1000;

/// Call frame for function calls
#[derive(Clone, Debug)]
pub struct CallFrame {
    /// Return address (instruction pointer)
    pub return_address: usize,
    /// Saved frame pointer
    pub saved_fp: usize,
    /// Saved registers (register number, value)
    pub saved_registers: Vec<(u8, Value)>,
    /// Function being called
    pub function: Option<FunctionRef>,
    /// Local variable name to register mapping
    pub local_symbols: HashMap<String, u8>,
    /// Destination register for return value
    pub return_dst: Option<u8>,
}

impl CallFrame {
    /// Create a new call frame
    pub fn new(return_address: usize, saved_fp: usize) -> Self {
        Self {
            return_address,
            saved_fp,
            saved_registers: Vec::new(),
            function: None,
            local_symbols: HashMap::new(),
            return_dst: None,
        }
    }
}

/// VM execution state
#[derive(Debug)]
pub struct VMState {
    /// Program counter
    pub pc: usize,
    /// Stack pointer (for call stack)
    pub sp: usize,
    /// Frame pointer
    pub fp: usize,
    /// Call stack
    pub call_stack: Vec<CallFrame>,
    /// Global variables
    pub globals: HashMap<String, Value>,
    /// Whether the VM is halted
    pub halted: bool,
    /// Current predecessor block (for phi nodes)
    pub predecessor_block: Option<u16>,
    /// Active scopes
    pub scope_stack: Vec<u16>,
}

impl VMState {
    /// Create a new VM state
    pub fn new() -> Self {
        Self {
            pc: 0,
            sp: 0,
            fp: 0,
            call_stack: Vec::new(),
            globals: HashMap::new(),
            halted: false,
            predecessor_block: None,
            scope_stack: Vec::new(),
        }
    }

    /// Push a new call frame with stack overflow protection
    pub fn push_frame(&mut self, frame: CallFrame) -> Result<()> {
        if self.call_stack.len() >= MAX_CALL_DEPTH {
            return Err(RuntimeError::StackOverflow);
        }
        self.call_stack.push(frame);
        self.sp = self.call_stack.len();
        Ok(())
    }

    /// Pop a call frame
    pub fn pop_frame(&mut self) -> Option<CallFrame> {
        let frame = self.call_stack.pop();
        self.sp = self.call_stack.len();
        frame
    }

    /// Get the current call frame
    pub fn current_frame(&self) -> Option<&CallFrame> {
        self.call_stack.last()
    }

    /// Get the current call frame mutably
    pub fn current_frame_mut(&mut self) -> Option<&mut CallFrame> {
        self.call_stack.last_mut()
    }

    /// Enter a scope
    pub fn enter_scope(&mut self, scope_id: u16) {
        self.scope_stack.push(scope_id);
    }

    /// Exit a scope
    pub fn exit_scope(&mut self, scope_id: u16) {
        if let Some(last) = self.scope_stack.last() {
            if *last == scope_id {
                self.scope_stack.pop();
            }
        }
    }

    /// Check if VM should continue executing
    #[inline]
    pub fn is_running(&self) -> bool {
        !self.halted
    }

    /// Halt the VM
    pub fn halt(&mut self) {
        self.halted = true;
    }

    /// Reset the VM state
    pub fn reset(&mut self) {
        self.pc = 0;
        self.sp = 0;
        self.fp = 0;
        self.call_stack.clear();
        self.globals.clear();
        self.halted = false;
        self.predecessor_block = None;
        self.scope_stack.clear();
    }
}

impl Default for VMState {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;

    #[test]
    fn test_call_stack() {
        let mut state = VMState::new();

        let frame1 = CallFrame::new(100, 0);
        let frame2 = CallFrame::new(200, 1);

        state.push_frame(frame1).unwrap();
        assert_eq!(state.sp, 1);
        assert_eq!(state.current_frame().unwrap().return_address, 100);

        state.push_frame(frame2).unwrap();
        assert_eq!(state.sp, 2);
        assert_eq!(state.current_frame().unwrap().return_address, 200);

        let popped = state.pop_frame().unwrap();
        assert_eq!(popped.return_address, 200);
        assert_eq!(state.sp, 1);
    }

    #[test]
    fn test_globals() {
        let mut state = VMState::new();

        state.globals.insert("x".to_string(), Value::Int(42));
        state.globals.insert("y".to_string(), Value::String(Arc::new("test".to_string())));

        assert_eq!(state.globals.get("x"), Some(&Value::Int(42)));
        assert_eq!(state.globals.get("y"), Some(&Value::String(Arc::new("test".to_string()))));
    }

    #[test]
    fn test_scopes() {
        let mut state = VMState::new();

        state.enter_scope(1);
        state.enter_scope(2);
        assert_eq!(state.scope_stack, vec![1, 2]);

        state.exit_scope(2);
        assert_eq!(state.scope_stack, vec![1]);

        state.exit_scope(1);
        assert!(state.scope_stack.is_empty());
    }
}
