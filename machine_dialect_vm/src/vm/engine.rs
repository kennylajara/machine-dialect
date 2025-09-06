//! VM execution engine
//!
//! This module implements the main VM execution engine.

use std::collections::HashMap;

use crate::{MAX_REGISTERS, registers};
use crate::values::{Value, Type, ConstantPool};
use crate::vm::{RegisterFile, VMState, CallFrame};
use crate::instructions::{Instruction, AssertType};
use crate::runtime::{ArithmeticOps, LogicOps, StringOps};
use crate::errors::{RuntimeError, Result, Exception, StackFrame};
use crate::loader::{BytecodeModule, MetadataFile};

/// Virtual Machine
pub struct VM {
    /// Register file
    pub registers: RegisterFile,
    /// VM state
    pub state: VMState,
    /// Loaded module
    pub module: Option<BytecodeModule>,
    /// Instructions
    pub instructions: Vec<Instruction>,
    /// Constants
    pub constants: ConstantPool,
    /// Metadata
    pub metadata: Option<MetadataFile>,
    /// Debug mode
    pub debug_mode: bool,
    /// Instruction count (for profiling)
    pub instruction_count: usize,
}

impl VM {
    /// Create a new VM
    pub fn new() -> Self {
        Self {
            registers: RegisterFile::new(),
            state: VMState::new(),
            module: None,
            instructions: Vec::new(),
            constants: ConstantPool::new(),
            metadata: None,
            debug_mode: false,
            instruction_count: 0,
        }
    }

    /// Load a module and metadata
    pub fn load_module(&mut self, module: BytecodeModule, metadata: Option<MetadataFile>) -> Result<()> {
        self.instructions = module.instructions.clone();
        self.constants = module.constants.clone();
        self.module = Some(module);
        self.metadata = metadata;
        self.state.reset();
        self.registers.clear();
        Ok(())
    }

    /// Run the VM until completion
    pub fn run(&mut self) -> Result<Option<Value>> {
        if self.module.is_none() {
            return Err(RuntimeError::ModuleNotLoaded);
        }

        let mut last_value = None;

        while self.state.is_running() && self.state.pc < self.instructions.len() {
            let result = self.step()?;
            if let Some(value) = result {
                last_value = Some(value);
            }
        }

        Ok(last_value)
    }

    /// Execute a single instruction
    pub fn step(&mut self) -> Result<Option<Value>> {
        if self.state.pc >= self.instructions.len() {
            self.state.halt();
            return Ok(None);
        }

        let inst = self.instructions[self.state.pc].clone();
        self.state.pc += 1;
        self.instruction_count += 1;

        if self.debug_mode {
            println!("PC: {}, Instruction: {:?}", self.state.pc - 1, inst);
        }

        self.execute_instruction(inst)
    }

    /// Execute an instruction
    fn execute_instruction(&mut self, inst: Instruction) -> Result<Option<Value>> {
        match inst {
            // Basic Operations
            Instruction::LoadConstR { dst, const_idx } => {
                let value = self.constants.get(const_idx)
                    .ok_or(RuntimeError::InvalidConstant(const_idx))?
                    .to_value();
                self.registers.set(dst, value);
            }

            Instruction::MoveR { dst, src } => {
                let value = self.registers.get(src).clone();
                self.registers.set(dst, value);
            }

            Instruction::LoadGlobalR { dst, name_idx } => {
                let name = self.get_string_constant(name_idx)?;
                let value = self.state.globals.get(&name)
                    .cloned()
                    .unwrap_or(Value::Empty);
                self.registers.set(dst, value);
            }

            Instruction::StoreGlobalR { src, name_idx } => {
                let name = self.get_string_constant(name_idx)?;
                let value = self.registers.get(src).clone();
                self.state.globals.insert(name, value);
            }

            // Type Operations
            Instruction::DefineR { dst, type_id } => {
                let value_type = self.get_type_from_id(type_id);
                self.registers.set_type(dst, value_type);
            }

            Instruction::CheckTypeR { dst, src, type_id } => {
                let value_type = self.registers.get_type(src);
                let expected_type = self.get_type_from_id(type_id);
                let result = value_type == &expected_type;
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::CastR { dst, src, to_type } => {
                let value = self.registers.get(src);
                let target_type = self.get_type_from_id(to_type);
                let casted = self.cast_value(value, target_type)?;
                self.registers.set(dst, casted);
            }

            // Arithmetic
            Instruction::AddR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::add(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::SubR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::sub(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::MulR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::mul(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::DivR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::div(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::ModR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::modulo(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::NegR { dst, src } => {
                let value = self.registers.get(src);
                let result = ArithmeticOps::negate(value)?;
                self.registers.set(dst, result);
            }

            // Logical
            Instruction::NotR { dst, src } => {
                let value = self.registers.get(src);
                let result = LogicOps::not(value)?;
                self.registers.set(dst, result);
            }

            Instruction::AndR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = LogicOps::and(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::OrR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = LogicOps::or(lval, rval)?;
                self.registers.set(dst, result);
            }

            // Comparisons
            Instruction::EqR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::eq(lval, rval);
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::NeqR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::neq(lval, rval);
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::LtR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::lt(lval, rval)?;
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::GtR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::gt(lval, rval)?;
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::LteR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::lte(lval, rval)?;
                self.registers.set(dst, Value::Bool(result));
            }

            Instruction::GteR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = ArithmeticOps::gte(lval, rval)?;
                self.registers.set(dst, Value::Bool(result));
            }

            // Control Flow
            Instruction::JumpR { offset } => {
                self.state.pc = (self.state.pc as i32 + offset) as usize;
            }

            Instruction::JumpIfR { cond, offset } => {
                let condition = self.registers.get(cond);
                if condition.is_truthy() {
                    self.state.pc = (self.state.pc as i32 + offset) as usize;
                }
            }

            Instruction::JumpIfNotR { cond, offset } => {
                let condition = self.registers.get(cond);
                if !condition.is_truthy() {
                    self.state.pc = (self.state.pc as i32 + offset) as usize;
                }
            }

            Instruction::CallR { func, args, dst } => {
                // TODO: Implement function calls
                self.registers.set(dst, Value::Empty);
            }

            Instruction::ReturnR { src } => {
                let value = src.map(|r| self.registers.get(r).clone());

                if let Some(frame) = self.state.pop_frame() {
                    self.state.pc = frame.return_address;
                    self.state.fp = frame.saved_fp;
                    self.registers.restore_registers(&frame.saved_registers);
                } else {
                    self.state.halt();
                }

                return Ok(value);
            }

            // MIR Support
            Instruction::PhiR { dst, sources } => {
                // Phi resolution based on predecessor block
                if let Some(predecessor) = self.state.predecessor_block {
                    for (src_reg, block_id) in sources {
                        if block_id == predecessor {
                            let value = self.registers.get(src_reg).clone();
                            self.registers.set(dst, value);
                            break;
                        }
                    }
                }
            }

            Instruction::AssertR { reg, assert_type, msg_idx } => {
                let value = self.registers.get(reg);
                let assertion_failed = match assert_type {
                    AssertType::True => !value.is_truthy(),
                    AssertType::NonNull => matches!(value, Value::Empty),
                    AssertType::Range { min, max } => {
                        match value {
                            Value::Int(n) => *n < min || *n > max,
                            _ => true,
                        }
                    }
                };

                if assertion_failed {
                    let msg = self.get_string_constant(msg_idx)?;
                    return Err(RuntimeError::AssertionFailed(msg));
                }
            }

            Instruction::ScopeEnterR { scope_id } => {
                self.state.enter_scope(scope_id);
            }

            Instruction::ScopeExitR { scope_id } => {
                self.state.exit_scope(scope_id);
            }

            // String Operations
            Instruction::ConcatStrR { dst, left, right } => {
                let lval = self.registers.get(left);
                let rval = self.registers.get(right);
                let result = StringOps::concat(lval, rval)?;
                self.registers.set(dst, result);
            }

            Instruction::StrLenR { dst, str_reg } => {
                let value = self.registers.get(str_reg);
                let result = StringOps::len(value)?;
                self.registers.set(dst, result);
            }

            // Arrays - TODO: Implement in Phase 2
            Instruction::NewArrayR { dst, size } => {
                self.registers.set(dst, Value::Empty);
            }

            Instruction::ArrayGetR { dst, array, index } => {
                self.registers.set(dst, Value::Empty);
            }

            Instruction::ArraySetR { array, index, value } => {
                // TODO: Implement array operations
            }

            Instruction::ArrayLenR { dst, array } => {
                self.registers.set(dst, Value::Int(0));
            }

            // Debug
            Instruction::DebugPrint { src } => {
                let value = self.registers.get(src);
                println!("DEBUG: {:?}", value);
            }

            Instruction::BreakPoint => {
                if self.debug_mode {
                    println!("BREAKPOINT at PC: {}", self.state.pc - 1);
                    // TODO: Implement debugger
                }
            }

            Instruction::Halt => {
                self.state.halt();
            }
        }

        Ok(None)
    }

    /// Get a string constant by index
    fn get_string_constant(&self, idx: u16) -> Result<String> {
        use crate::values::ConstantValue;

        match self.constants.get(idx) {
            Some(ConstantValue::String(s)) => Ok(s.clone()),
            _ => Err(RuntimeError::InvalidConstant(idx)),
        }
    }

    /// Get type from type ID
    fn get_type_from_id(&self, type_id: u16) -> Type {
        match type_id {
            0 => Type::Empty,
            1 => Type::Bool,
            2 => Type::Int,
            3 => Type::Float,
            4 => Type::String,
            5 => Type::Function,
            6 => Type::URL,
            _ => Type::Unknown,
        }
    }

    /// Cast a value to a type
    fn cast_value(&self, value: &Value, target_type: Type) -> Result<Value> {
        match target_type {
            Type::Bool => Ok(Value::Bool(value.to_bool())),
            Type::Int => value.to_int().map(Value::Int),
            Type::Float => value.to_float().map(Value::Float),
            Type::String => Ok(Value::String(std::sync::Arc::new(value.to_string()))),
            _ => Err(RuntimeError::TypeMismatch {
                expected: target_type.to_string(),
                found: value.type_of().to_string(),
            })
        }
    }

    /// Build a stack trace for errors
    pub fn build_stack_trace(&self) -> Vec<StackFrame> {
        let mut trace = Vec::new();

        // Add current location
        trace.push(StackFrame {
            function: "main".to_string(),
            pc: self.state.pc,
            source_location: None,
        });

        // Add call frames
        for frame in &self.state.call_stack {
            let func_name = frame.function.as_ref()
                .map(|f| f.name.clone())
                .unwrap_or_else(|| "anonymous".to_string());

            trace.push(StackFrame {
                function: func_name,
                pc: frame.return_address,
                source_location: None,
            });
        }

        trace
    }
}

impl Default for VM {
    fn default() -> Self {
        Self::new()
    }
}
